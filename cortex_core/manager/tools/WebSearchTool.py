import asyncio
import time
from typing import Type
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from pydantic import BaseModel, Field
import json
from contextlib import nullcontext

from langchain_core.tools import BaseTool
from langchain_community.document_loaders import WebBaseLoader
from langsmith import traceable
try:
    from langsmith.run_helpers import tracing_context
except Exception:  # pragma: no cover - fallback for environments without this helper
    tracing_context = None
    
class WebSearchInput(BaseModel):
    """Input schema for web search tool."""
    query: list[str] = Field(..., description="The list of strings where each string has relevant keywords to search for.")

class WebSearchTool(BaseTool):
    """
    Use this tool to search the web for up-to-date information. \n
    Use it when user query involve information, facts, or any kind of context which required web search. \n
    Instructions should include specifc keywords or context to search for. \n
    """

    name: str = "WebSearchTool"
    description: str = __doc__
    args_schema: Type[BaseModel] = WebSearchInput
    max_results: int = 2
    max_query_workers: int = 6
    max_url_workers: int = 8
    max_urls_per_query: int = 4
    ddg_timeout_s: int = 8
    scrape_timeout_s: float = 8.0
    overall_search_timeout_s: float = 40.0

    def _no_trace_context(self):
        """Return a context manager that disables LangSmith tracing when available."""
        if tracing_context is None:
            return nullcontext()
        return tracing_context(enabled=False)

    @traceable(enabled=False)
    def _run(
        self,
        query: str,
    ) -> str:
        """Execute a synchronous web search."""
        with self._no_trace_context():
            from ddgs import DDGS

            with DDGS(timeout=self.ddg_timeout_s) as ddgs:
                raw_results = ddgs.text(
                    query,
                    max_results=self.max_results,
                    backend="auto",
                )

            normalized_results = [
                {
                    "snippet": item.get("body", ""),
                    "title": item.get("title", ""),
                    "link": item.get("href", ""),
                }
                for item in raw_results or []
            ]
            return json.dumps(normalized_results)

    async def _arun(
        self,
        query: str,
    ) -> str:
        """Execute an asynchronous web search."""
        return await asyncio.to_thread(self._run, query)

    def _search_single_query(self, query: str) -> list[dict]:
        """Search one query and scrape a small bounded set of result URLs."""
        res = self._run(query)
        parsed = json.loads(res)
        urls = [
            item.get("link")
            for item in parsed
            if item.get("link") and "youtube" not in item.get("link", "")
        ]
        urls = list(dict.fromkeys(urls))[: self.max_urls_per_query]
        return self.web_scrap(urls)
    
    def _load_single_url(self, url: str) -> dict | None:
        try:
            with self._no_trace_context():
                loader = WebBaseLoader(
                    url,
                    requests_kwargs={"timeout": self.scrape_timeout_s},
                    continue_on_failure=True,
                    raise_for_status=False,
                    show_progress=False,
                )
                data = loader.load()
            if not data:
                return None
            formatted_data = " ".join((data[0].page_content or "").split())
            if not formatted_data:
                return None
            return {
                "url": url,
                "data": formatted_data,
            }
        except Exception:
            return None
    
    def web_scrap(self, urls: list[str]) -> list[dict]:
        """Perform web search using the tool."""
        if not urls:
            return []

        results: list[dict] = []
        deadline = time.monotonic() + (self.scrape_timeout_s * max(1, len(urls)))
        executor = ThreadPoolExecutor(max_workers=self.max_url_workers)
        try:
            futures = [executor.submit(self._load_single_url, url) for url in urls]
            while futures:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                try:
                    completed_iter = as_completed(futures, timeout=remaining)
                    future = next(completed_iter)
                except (FutureTimeoutError, StopIteration):
                    break

                futures.remove(future)
                try:
                    item = future.result()
                    if item is not None:
                        results.append(item)
                except Exception:
                    continue
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
        return results

    def search(
        self,
        input: WebSearchInput,
    ) -> list[dict]:
        """Perform web search using the tool."""
        query_value = input.query
        queries = [query_value] if isinstance(query_value, str) else list(query_value)

        cleaned_queries = [str(query).strip() for query in queries if str(query).strip()]
        if not cleaned_queries:
            return []

        results: list[dict] = []
        start_time = time.monotonic()
        executor = ThreadPoolExecutor(max_workers=self.max_query_workers)
        try:
            future_to_query = {
                executor.submit(self._search_single_query, query): query
                for query in cleaned_queries
            }
            pending = list(future_to_query.keys())

            while pending:
                remaining_timeout = self.overall_search_timeout_s - (time.monotonic() - start_time)
                if remaining_timeout <= 0:
                    break
                try:
                    completed_iter = as_completed(pending, timeout=remaining_timeout)
                    future = next(completed_iter)
                except (FutureTimeoutError, StopIteration):
                    break

                pending.remove(future)
                try:
                    docs = future.result()
                    if docs:
                        results.extend(docs)
                except Exception:
                    continue

            for future in pending:
                future.cancel()
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        return results
    
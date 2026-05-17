import asyncio
import time
from typing import Type
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
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
    max_url_workers: int = 10
    max_urls_per_query: int = 4
    ddg_timeout_s: int = 8
    scrape_timeout_s: float = 8.0
    overall_timeout_s: float = 30.0

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
        """Execute a synchronous web search using DuckDuckGo."""
        with self._no_trace_context():
            try:
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
            except Exception as e:
                print(f"[WebSearch] DDG Search failed for '{query}': {e}")
                return "[]"

    async def _arun(
        self,
        query: str,
    ) -> str:
        """Execute an asynchronous web search."""
        return await asyncio.to_thread(self._run, query)

    def _load_single_url(self, url: str) -> dict | None:
        """Load and scrape a single URL."""
        try:
            print(f"[WebSearch] Scraping URL: {url}")
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
        except Exception as e:
            print(f"[WebSearch] Failed to scrape {url}: {e}")
            return None
    
    def web_scrap(self, urls: list[str]) -> list[dict]:
        """Parallel scraping of a list of URLs with an overall timeout."""
        if not urls:
            return []

        results: list[dict] = []
        # Use a single executor for all URLs
        executor = ThreadPoolExecutor(max_workers=self.max_url_workers)
        try:
            future_to_url = {executor.submit(self._load_single_url, url): url for url in urls}
            
            # Simplified overall timeout for all scraping tasks
            try:
                for future in as_completed(future_to_url, timeout=self.overall_timeout_s):
                    item = future.result()
                    if item:
                        results.append(item)
            except TimeoutError:
                print(f"[WebSearch] Scraping timed out after {self.overall_timeout_s}s. Returning partial results.")
            except Exception as e:
                print(f"[WebSearch] Error during scraping loop: {e}")
                
        finally:
            # Shutdown without waiting to avoid hanging if threads are stuck
            executor.shutdown(wait=False, cancel_futures=True)

        return results

    @classmethod
    def search(
        cls,
        input: WebSearchInput,
    ) -> list[dict]:
        """
        Entry point for web search. 
        Performs sequential DDG searches followed by parallel scraping.
        """
        instance = cls()
        queries = input.query
        if isinstance(queries, str):
            queries = [queries]

        print(f"[WebSearch] Starting search for {len(queries)} queries...")
        
        # 1. Gather all URLs from all queries sequentially (Safer for DDG)
        all_urls = []
        for q in queries:
            print(f"[WebSearch] Searching DDG for: {q}")
            res_json = instance._run(q)
            try:
                res_data = json.loads(res_json)
                for item in res_data:
                    url = item.get("link")
                    if url and "youtube" not in url:
                        all_urls.append(url)
            except Exception:
                continue
        
        # Remove duplicates
        unique_urls = list(dict.fromkeys(all_urls))[:instance.max_urls_per_query * len(queries)]
        
        if not unique_urls:
            print("[WebSearch] No URLs found to scrape.")
            return []

        # 2. Scrape all unique URLs in a single parallel batch
        print(f"[WebSearch] Starting parallel scraping of {len(unique_urls)} URLs...")
        return instance.web_scrap(unique_urls)

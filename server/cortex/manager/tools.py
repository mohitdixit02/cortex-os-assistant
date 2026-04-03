from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import tool

@tool("web_search")
def web_search(query: str) -> DuckDuckGoSearchResults:
    """Perform a web search using DuckDuckGo."""
    search_results = DuckDuckGoSearchResults.run(query)
    return search_results
"""
Alicia Web Search Engine
Provides web search capabilities using Tavily API, DuckDuckGo fallback, and Wikipedia lookups.
"""

import json
import urllib.parse
from typing import Dict, List, Optional
import requests

from config.settings import settings


class SearchEngine:
    """Handles online searching with multi-provider fallbacks."""

    def __init__(self, tavily_api_key: Optional[str] = None):
        self.tavily_api_key = tavily_api_key or settings.ai.tavily_api_key

    def search_tavily(self, query: str, max_results: int = 4) -> Dict:
        """Query Tavily REST API directly."""
        if not self.tavily_api_key:
            return {"error": "Tavily API key not configured"}

        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self.tavily_api_key,
            "query": query,
            "search_depth": "basic",
            "include_answer": True,
            "max_results": max_results
        }
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer")
                results = []
                for res in data.get("results", []):
                    results.append({
                        "title": res.get("title", ""),
                        "url": res.get("url", ""),
                        "snippet": res.get("content", "")
                    })
                return {
                    "success": True,
                    "answer": answer,
                    "results": results
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_duckduckgo(self, query: str) -> Dict:
        """Instant answer search fallback using DuckDuckGo Instant Answer API."""
        try:
            encoded = urllib.parse.quote(query)
            url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
            res = requests.get(url, timeout=8)
            if res.status_code == 200:
                data = res.json()
                answer = data.get("AbstractText") or data.get("Answer")
                if answer:
                    return {
                        "success": True,
                        "answer": answer,
                        "source": data.get("AbstractSource", "DuckDuckGo")
                    }
            return {"success": False, "error": "No instant answer found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_wikipedia(self, query: str) -> Dict:
        """Search Wikipedia summaries using Wikipedia REST API."""
        try:
            encoded = urllib.parse.quote(query)
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
            headers = {"User-Agent": "AliciaAssistant/1.0 (Desktop Assistant)"}
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code == 200:
                data = res.json()
                extract = data.get("extract")
                if extract:
                    return {
                        "success": True,
                        "title": data.get("title"),
                        "answer": extract,
                        "url": data.get("content_urls", {}).get("desktop", {}).get("page")
                    }
            return {"success": False, "error": "Wikipedia article not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search(self, query: str) -> str:
        """
        Unified search method. Attempts Tavily -> DuckDuckGo -> Wikipedia.
        Returns a human/voice friendly summary string.
        """
        query_clean = query.strip()
        if not query_clean:
            return "Please specify what you would like me to search for."

        # 1. Try Tavily
        tavily_res = self.search_tavily(query_clean)
        if tavily_res.get("success"):
            if tavily_res.get("answer"):
                return tavily_res["answer"]
            results = tavily_res.get("results", [])
            if results:
                snippets = [r["snippet"] for r in results[:2] if r.get("snippet")]
                if snippets:
                    return " ".join(snippets)

        # 2. Try Wikipedia
        wiki_res = self.search_wikipedia(query_clean)
        if wiki_res.get("success") and wiki_res.get("answer"):
            return wiki_res["answer"]

        # 3. Try DuckDuckGo
        ddg_res = self.search_duckduckgo(query_clean)
        if ddg_res.get("success") and ddg_res.get("answer"):
            return ddg_res["answer"]

        return f"I searched for '{query_clean}', but couldn't find a direct answer. Let me know if you'd like me to open the browser for you."


search_engine = SearchEngine()

def web_search(query: str) -> str:
    return search_engine.search(query)

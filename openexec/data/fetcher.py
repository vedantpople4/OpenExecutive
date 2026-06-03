"""Real-time data fetching service for OpenExec."""

import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import requests


@dataclass
class WebDataResult:
    """Result from web data fetching."""
    source: str
    content: str
    timestamp: str
    relevance_score: float
    category: str
    url: str = ""


@dataclass
class DataSource:
    """Data source configuration."""
    url: str
    name: str
    category: str
    credibility_score: float = 0.8
    update_frequency: str = "daily"


class RealTimeDataFetcher:
    """Service for fetching real-time data from the internet."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the data fetcher.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.sources = self._load_data_sources()
        self.cache: Dict[str, WebDataResult] = {}
        self.cache_duration = 3600  # 1 hour cache

    def _load_data_sources(self) -> List[DataSource]:
        """Load default data sources."""
        return [
            DataSource(
                url="https://techcrunch.com/category/fintech/",
                name="TechCrunch Fintech",
                category="fintech",
                credibility_score=0.9
            ),
            DataSource(
                url="https://techcrunch.com/category/artificial-intelligence/",
                name="TechCrunch AI",
                category="ai",
                credibility_score=0.9
            ),
            DataSource(
                url="https://news.ycombinator.com/",
                name="Hacker News",
                category="technology",
                credibility_score=0.85
            ),
            DataSource(
                url="https://venturebeat.com/category/ai/",
                name="VentureBeat AI",
                category="ai",
                credibility_score=0.85
            ),
        ]

    def fetch_market_trends(self, industry: str = "fintech") -> tuple[List[WebDataResult], List[str]]:
        """Fetch current market trends for specific industry.

        Args:
            industry: Industry to fetch trends for (fintech, ai, technology)

        Returns:
            Tuple of (results list, failed sources list)
        """
        results = []
        failed_sources = []

        # Filter sources by category
        relevant_sources = [s for s in self.sources if s.category == industry or industry == "all"]

        for source in relevant_sources:
            try:
                result = self._fetch_from_source(source)
                if result:
                    results.append(result)
                    print(f"✓ Successfully fetched data from {source.name}")
                else:
                    failed_sources.append(source.url)
                    print(f"✗ Failed to fetch data from {source.name}")
            except Exception as e:
                failed_sources.append(source.url)
                print(f"✗ Error fetching from {source.name}: {e}")
                continue

        return results, failed_sources

    def fetch_competitor_intelligence(self, query: str) -> tuple[List[WebDataResult], List[str]]:
        """Fetch recent news and developments about competitors.

        Args:
            query: Search query for competitor information

        Returns:
            Tuple of (results list, failed sources list)
        """
        # This would use WebSearch in production
        # For now, return cached results or fetch from general sources
        results = []
        failed_sources = []

        for source in self.sources:
            try:
                result = self._fetch_from_source(source)
                if result and query.lower() in result.content.lower():
                    results.append(result)
                    print(f"✓ Found relevant competitor data from {source.name}")
                else:
                    failed_sources.append(source.url)
                    print(f"✗ No relevant competitor data from {source.name}")
            except Exception as e:
                failed_sources.append(source.url)
                print(f"✗ Error fetching competitor data: {e}")
                continue

        return results, failed_sources

    def fetch_technology_trends(self, domain: str = "ai") -> tuple[List[WebDataResult], List[str]]:
        """Fetch current technology trends and developments.

        Args:
            domain: Technology domain (ai, cloud, infrastructure)

        Returns:
            Tuple of (results list, failed sources list)
        """
        return self.fetch_market_trends(domain)

    def fetch_regulatory_updates(self, jurisdiction: str = "us") -> tuple[List[WebDataResult], List[str]]:
        """Fetch recent regulatory changes and compliance updates.

        Args:
            jurisdiction: Jurisdiction for regulatory updates

        Returns:
            Tuple of (results list, failed sources list)
        """
        # This would fetch from regulatory sources
        # For now, return empty list as regulatory sources need specific handling
        return [], []

    def _fetch_from_source(self, source: DataSource) -> Optional[WebDataResult]:
        """Fetch data from a specific source.

        Args:
            source: Data source to fetch from

        Returns:
            WebDataResult or None if fetch fails
        """
        # Check cache first
        cache_key = f"{source.url}_{source.category}"
        if cache_key in self.cache:
            cached_result = self.cache[cache_key]
            # Check if cache is still valid
            cache_age = time.time() - time.strptime(cached_result.timestamp, "%Y-%m-%d %H:%M:%S").timestamp()
            if cache_age < self.cache_duration:
                return cached_result

        try:
            # In production, this would use WebFetch
            # For now, we'll simulate with a simple request
            response = requests.get(source.url, timeout=10)
            response.raise_for_status()

            # Extract relevant content (simplified)
            content = self._extract_content(response.text)

            result = WebDataResult(
                source=source.name,
                content=content,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                relevance_score=source.credibility_score,
                category=source.category,
                url=source.url
            )

            # Cache the result
            self.cache[cache_key] = result

            return result

        except Exception as e:
            print(f"Error fetching from {source.url}: {e}")
            return None

    def _extract_content(self, html: str) -> str:
        """Extract relevant content from HTML.

        Args:
            html: HTML content to extract from

        Returns:
            Extracted text content
        """
        # Simplified content extraction
        # In production, this would use proper HTML parsing
        lines = html.split('\n')
        content_lines = []

        for line in lines[:50]:  # Limit to first 50 lines for demo
            line = line.strip()
            # Filter out empty lines and scripts
            if line and not line.startswith('<') and not line.startswith('var '):
                if len(line) > 20:  # Only meaningful lines
                    content_lines.append(line)

        return ' '.join(content_lines[:10])  # Return first 10 meaningful lines

    def get_context_for_decision(self, business_problem: str) -> Dict[str, Any]:
        """Get relevant context for a business decision.

        Args:
            business_problem: The business problem or decision context

        Returns:
            Dictionary with relevant context data and source tracking
        """
        context = {
            "market_trends": [],
            "technology_trends": [],
            "competitor_intelligence": [],
            "regulatory_updates": [],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sources_accessed": [],
            "sources_failed": [],
            "all_available_sources": [source.url for source in self.sources]
        }

        # Determine relevant categories based on business problem
        problem_lower = business_problem.lower()

        if any(keyword in problem_lower for keyword in ['fintech', 'financial', 'banking', 'payment']):
            trends, failed = self.fetch_market_trends("fintech")
            context["market_trends"] = trends
            context["sources_accessed"].extend([t.url for t in trends])
            context["sources_failed"].extend(failed)

        if any(keyword in problem_lower for keyword in ['ai', 'ml', 'machine learning', 'gpu', 'infrastructure']):
            trends, failed = self.fetch_technology_trends("ai")
            context["technology_trends"] = trends
            context["sources_accessed"].extend([t.url for t in trends])
            context["sources_failed"].extend(failed)

        if any(keyword in problem_lower for keyword in ['competitor', 'competition', 'market']):
            # Extract potential competitor names from problem
            intel, failed = self.fetch_competitor_intelligence(business_problem)
            context["competitor_intelligence"] = intel
            context["sources_accessed"].extend([t.url for t in intel])
            context["sources_failed"].extend(failed)

        return context

    def format_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """Format context data for inclusion in AI prompts.

        Args:
            context: Context dictionary from get_context_for_decision

        Returns:
            Formatted string for prompt inclusion
        """
        sections = []

        if context.get("market_trends"):
            sections.append("## Current Market Trends")
            for trend in context["market_trends"]:
                sections.append(f"**Source:** {trend.source}")
                sections.append(f"**URL:** {trend.url}")
                sections.append(f"**Update:** {trend.content[:200]}...")
                sections.append("")

        if context.get("technology_trends"):
            sections.append("## Technology Trends")
            for trend in context["technology_trends"]:
                sections.append(f"**Source:** {trend.source}")
                sections.append(f"**URL:** {trend.url}")
                sections.append(f"**Update:** {trend.content[:200]}...")
                sections.append("")

        if context.get("competitor_intelligence"):
            sections.append("## Competitive Intelligence")
            for intel in context["competitor_intelligence"]:
                sections.append(f"**Source:** {intel.source}")
                sections.append(f"**URL:** {intel.url}")
                sections.append(f"**Update:** {intel.content[:200]}...")
                sections.append("")

        return '\n'.join(sections) if sections else "No current market data available."

    def get_sources_summary(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary of sources accessed and failed.

        Args:
            context: Context dictionary from get_context_for_decision

        Returns:
            Dictionary with source access summary
        """
        return {
            "sources_accessed": list(set(context.get("sources_accessed", []))),
            "sources_failed": list(set(context.get("sources_failed", []))),
            "all_available_sources": context.get("all_available_sources", []),
            "access_success_rate": self._calculate_success_rate(context),
            "timestamp": context.get("timestamp", "unknown")
        }

    def _calculate_success_rate(self, context: Dict[str, Any]) -> float:
        """Calculate data fetch success rate.

        Args:
            context: Context dictionary from get_context_for_decision

        Returns:
            Success rate as percentage (0.0 to 1.0)
        """
        accessed = len(set(context.get("sources_accessed", [])))
        failed = len(set(context.get("sources_failed", [])))
        total = accessed + failed

        if total == 0:
            return 0.0

        return accessed / total
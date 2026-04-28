"""Data module for OpenExec - Real-time data fetching and integration."""

from .fetcher import RealTimeDataFetcher, WebDataResult, DataSource

__all__ = ["RealTimeDataFetcher", "WebDataResult", "DataSource"]
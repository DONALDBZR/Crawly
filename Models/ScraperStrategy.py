from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class Scraper_Strategy(ABC):
    """
    Strategy contract for target-specific scraping.
    """

    @abstractmethod
    def identifier(self) -> str:
        """Unique strategy identifier used in metadata and logging."""
        raise NotImplementedError

    @abstractmethod
    def fetch(self, context: Dict[str, Any]) -> str:
        """
        Retrieve raw content needed for extraction.

        Implementations may use HTTP, files, APIs, etc. Keep network specifics encapsulated
        inside the strategy. Must return raw text/HTML/JSON as a string.
        """
        raise NotImplementedError

    @abstractmethod
    def extract(self, raw: str) -> Dict[str, Any]:
        """
        Extract target-specific fields from the raw content, returning a dict of fields.
        Avoid normalizing here — only parse and collect.
        """
        raise NotImplementedError

    @abstractmethod
    def normalize(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert extracted fields into the standardized Crawly JSON schema.
        Output must be a clean JSON-ready dict compliant with downstream expectations.
        """
        raise NotImplementedError

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Optional retry hook. Orchestrator will call this on failure.
        Return True to retry, False to abort. Default: up to 3 attempts.
        """
        return attempt < 3

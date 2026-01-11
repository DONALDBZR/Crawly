from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict


class Scraper_Strategy(ABC):
    """
    Strategy contract for target-specific scraping.
    """

    @abstractmethod
    def identifier(self) -> str:
        """
        Unique ID for the strategy.

        Returns:
            str: The strategy ID.
        """
        raise NotImplementedError

    @abstractmethod
    def fetch(self, context: Dict[str, Any]) -> str:
        """
        Retrieves raw content needed for extraction.

        Args:
            context (Dict[str, Any]): Contextual info for fetching (e.g., URLs, headers).

        Returns:
            str: The raw content as a string.

        Raises:
            Exception: On fetch failures.
        """
        raise NotImplementedError

    @abstractmethod
    def extract(self, raw: str) -> Dict[str, Any]:
        """
        Extracts target-specific fields from the raw content, returning a dict of fields.

        Args:
            raw (str): The raw content fetched.

        Returns:
            Dict[str, Any]: Extracted fields.

        Raises:
            Exception: On extraction failures.
        """
        raise NotImplementedError

    @abstractmethod
    def normalize(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts extracted fields into the standardized Crawly JSON schema.

        Args:
            extracted (Dict[str, Any]): The extracted fields.

        Returns:
            Dict[str, Any]: Normalized data in standard schema.

        Raises:
            Exception: On normalization failures.
        """
        raise NotImplementedError

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determines if a fetch should be retried based on the exception and attempt count.

        Args:
            exception (Exception): The exception raised during fetch.
            attempt (int): The current attempt number (1-based).

        Returns:
            bool: True to retry, False to abort.
        """
        return attempt < 3

from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union
from Models.ScraperStrategy import Scraper_Strategy
from Errors.Scraper import Scraper_Exception
from time import sleep
from Models.Logger import Crawly_Logger


class Scraper_Orchestrator:
    """
    It orchestrates the scraping process by coordinating fetching, extracting, and normalizing data using a defined strategy.

    Attributes:
        _strategy (Scraper_Strategy): The scraping strategy to use for fetching, extracting, and normalizing data.
        _logger (Optional[Crawly_Logger]): Logger instance for debug/error logging.
        _max_attempts (int): Maximum number of fetch attempts before giving up.
        _backoff_base (float): Base seconds for exponential backoff between retries.

    Methods:
        run(context: Dict[str, Any]) -> Dict[str, Any]: Executes the scraping process: fetch -> extract -> normalize.

    """
    _strategy: Scraper_Strategy
    """The scraping strategy to use for fetching, extracting, and normalizing data."""
    _logger: Optional[Crawly_Logger]
    """Logger instance for debug/error logging."""
    _max_attempts: int
    """Maximum number of fetch attempts before giving up."""
    _backoff_base: float
    """Base seconds for exponential backoff between retries."""

    def __init__(
        self,
        strategy: Scraper_Strategy,
        logger: Optional[Crawly_Logger] = None,
        max_attempts: Optional[int] = None,
        backoff_base_seconds: float = 0.5,
    ) -> None:
        """
        Initializing the orchestrator with a scraping strategy and optional settings.

        Args:
            strategy (Scraper_Strategy): The scraping strategy to use.
            logger (Optional[Crawly_Logger]): Logger instance for debug/error logging.
            max_attempts (Optional[int]): Max fetch attempts before giving up.
            backoff_base_seconds (float): Base seconds for exponential backoff between retries.
        """
        self._strategy = strategy
        self._logger = logger
        self._max_attempts = max_attempts if max_attempts is not None else 3
        self._backoff_base = backoff_base_seconds

    def __log_debug(self, message: str) -> None:
        """
        Logging a debug message.

        Procedures:
            1. Checks if a logger is configured.
            2. Logs the debug message.

        Parameters:
            message (str): The debug message to log.

        Returns:
            None

        Raises:
            Scraper_Exception: If the logger is not properly configured.
        """
        if self._logger and hasattr(self._logger, "debug"):
            self._logger.debug(message)
            return
        raise Scraper_Exception("Logger is not properly configured for debug logging.")

    def __log_info(self, message: str) -> None:
        """
        Logging an informational message.

        Procedures:
            1. Checks if a logger is configured.
            2. Logs the informational message.

        Parameters:
            message (str): The informational message to log.

        Returns:
            None

        Raises:
            Scraper_Exception: If the logger is not properly configured.
        """
        if self._logger and hasattr(self._logger, "inform"):
            self._logger.inform(message)
            return
        raise Scraper_Exception("Logger is not properly configured for informative logging.")

    def __log_error(self, message: str) -> None:
        """
        Logging an error message.

        Procedures:
            1. Checks if a logger is configured.
            2. Logs the error message.

        Parameters:
            message (str): The error message to log.

        Returns:
            None

        Raises:
            Scraper_Exception: If the logger is not properly configured.
        """
        if self._logger and hasattr(self._logger, "error"):
            self._logger.error(message)
            return
        raise Scraper_Exception("Logger is not properly configured for error logging.")

    def _get_data(
        self,
        context: Dict[str, Any],
        attempts: int = 0
    ) -> Optional[str]:
        """
        Fetching data using the strategy with retry logic.

        Procedures:
            1. Attempts to fetch data using the strategy.
            2. If fetching fails, logs the error and checks if a retry is allowed.
            3. If allowed, waits for an exponential backoff period and retries fetching.

        Parameters:
            context (Dict[str, Any]): Contextual info for the strategy (e.g., URLs, headers).
            attempts (int): Current attempt count.

        Returns:
            Optional[str]: The fetched data if successful, otherwise None.
        """
        try:
            self.__log_debug(f"Scraping the data needed. - Identifier: {self._strategy.identifier()} | Fetch attempt {attempts + 1}")
            response: str = self._strategy.fetch(context)
            self.__log_info(f"Data successfully scraped. - Identifier: {self._strategy.identifier()}")
            return response
        except Scraper_Exception as error:
            attempts += 1
            self.__log_error(f"The data needed cannot be scraped. - Error: {error.message} | Status: {error.code} | Attempt: {attempts}")
            is_allowed: bool = (self._strategy.should_retry(error, attempts) and (attempts < self._max_attempts))
            delay: float = self._backoff_base * (2 ** attempts)
            sleep(delay)
            if not is_allowed:
                raise Scraper_Exception(f"The data cannot be scraped and no more retries are allowed. - Error: {error.message} | Status: {error.code} | Attempts: {attempts}")
            return self._get_data(context, attempts)

    def _validate_data(self, data: Optional[str]) -> None:
        """
        Validating that fetched data is not None.

        Procedures:
            1. Checks if the data is None.
            2. If None, raises a Scraper_Exception.

        Parameters:
            data (Optional[str]): The fetched data to validate.

        Returns:
            None
        
        Raises:
            Scraper_Exception: If the fetched data is None.
        """
        if data is not None:
            return
        raise Scraper_Exception("Fetched data is null.", 404)

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executing the scraping process.

        Procedures:
            1. Logs the start of the scraping process.
            2. Fetches data using the strategy.
            3. Validates the fetched data.
            4. Extracts fields from the data using the strategy.
            5. Normalizes the extracted fields into the standard schema using the strategy.
            6. Logs the successful completion of the scraping process.
            7. Returns the normalized data.

        Parameters:
            context (Dict[str, Any]): Contextual info for the strategy (e.g., URLs, headers).

        Returns:
            Dict[str, Any]: The normalized data in standard schema.
        """
        self.__log_debug("Starting the scraping orchestration process.")
        try:
            data: Optional[str] = self._get_data(context)
            self._validate_data(data)
            extracted: Dict[str, Any] = self._strategy.extract(str(data))
            normalized: Dict[str, Any] = self._strategy.normalize(extracted)
            self.__log_info("Scraping orchestration process completed successfully.")
            return normalized
        except Scraper_Exception as error:
            message: str = f"The scraping orchestration has failed."
            self.__log_error(f"{message} - Error: {error.message} | Status: {error.code}")
            return {}

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
        raise Scraper_Exception("Fetched data is None.", 404)

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            data: Optional[str] = self._get_data(context)
            pass
        except Scraper_Exception as error:
            pass
        last_error: Optional[Exception] = None
        if data is None:
            return self._error_response("FETCH_ERROR", last_error, attempts)
        try:
            self._log_debug("Extracting fields from data content...")
            extracted = self._strategy.extract(data)
        except Exception as error:
            self._log_error(f"The extraction has failed. - Error: {error!r}")
            return self._error_response("EXTRACT_ERROR", error, attempts)
        try:
            self._log_debug("Normalizing extracted fields to schema...")
            normalized = self._strategy.normalize(extracted)
        except Exception as error:
            self._log_error(f"The normalization has failed. Error: {error!r}")
            return self._error_response("NORMALIZE_ERROR", error, attempts)
        return self._success_response(normalized, attempts)

    # ---- Internal helpers -------------------------------------------------

    def _meta(self, status: str, attempts: int) -> Dict[str, Any]:
        return {
            "strategy": self._strategy.identifier(),
            "status": status,
            "attempts": attempts,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _success_response(self, data: Dict[str, Any], attempts: int) -> Dict[str, Any]:
        return {
            "meta": self._meta("success", attempts),
            "data": data,
            "error": None,
        }

    def _error_response(
        self, code: str, error: Optional[Exception], attempts: int
    ) -> Dict[str, Any]:
        err_payload = None
        if error is not None:
            err_payload = {
                "code": code,
                "message": str(error),
                "type": error.__class__.__name__,
            }
        return {
            "meta": self._meta("error", attempts),
            "data": None,
            "error": err_payload,
        }

    def _log_debug(self, msg: str) -> None:
        if self._logger and hasattr(self._logger, "debug"):
            try:
                self._logger.debug(msg)
            except Exception:
                pass

    def _log_error(self, msg: str) -> None:
        if self._logger and hasattr(self._logger, "error"):
            try:
                self._logger.error(msg)
            except Exception:
                pass

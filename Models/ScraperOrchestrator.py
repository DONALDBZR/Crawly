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
            Exception: If the logger is not properly configured.
        """
        if self._logger and hasattr(self._logger, "debug"):
            self._logger.debug(message)
            return
        raise Exception("Logger is not properly configured for debug logging.")

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
            Exception: If the logger is not properly configured.
        """
        if self._logger and hasattr(self._logger, "inform"):
            self._logger.inform(message)
            return
        raise Exception("Logger is not properly configured for informative logging.")

    def _get_data(
        self,
        context: Dict[str, Any],
        attempts: int = 0
    ) -> Optional[str]:
        try:
            self.__log_debug(f"Scraping the data needed. - Identifier: {self._strategy.identifier()} | Fetch attempt {attempts + 1}")
            response: str = self._strategy.fetch(context)

        except Exception as error:
            attempts += 1
            last_error = error
            self._log_error(f"The data needed cannot be scraped. - Error: {error!r}")
            is_allowed: bool = (self._strategy.should_retry(error, attempts) and (attempts < self._max_attempts))
            if not is_allowed:
                return self._error_response("FETCH_ERROR", error, attempts + 1)
            delay: float = self._backoff_base * (2 ** attempts)
            sleep(delay)

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executing the scraping process.

        Procedures:
            1. Fetches raw content using the strategy.
            2. Extracts fields from the raw content.
            3. Normalizes extracted fields into standard schema.

        Parameters:
            context (Dict[str, Any]): Contextual info for the strategy (e.g., URLs, headers).

        Returns:
            Dict[str, Any]: Standardized response with meta, data, and error sections.
        """
        attempts: int = 0
        data: Optional[str] = None
        last_error: Optional[Exception] = None
        for index in range(0, self._max_attempts, 1):
            attempts = index
            self._get_data()
            try:
                self._log_debug(f"Scraping the data needed. - Identifier: {self._strategy.identifier()} | Fetch attempt {attempts + 1}")
                data = self._strategy.fetch(context)
                break
            except Exception as error:
                last_error = error
                self._log_error(f"The data needed cannot be scraped. - Error: {error!r}")
                is_allowed: bool = (self._strategy.should_retry(error, attempts + 1) and (attempts + 1 < self._max_attempts))
                if not is_allowed:
                    return self._error_response("FETCH_ERROR", error, attempts + 1)
                delay: float = self._backoff_base * (2 ** attempts)
                sleep(delay)
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

from __future__ import annotations
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from Models.ScraperStrategy import Scraper_Strategy
from Errors.Scraper import Scraper_Exception


class ScraperOrchestrator:
    """
    Coordinates the scraping flow while staying agnostic of the target website.

    Responsibilities:
    - Drives the Strategy: fetch -> extract -> normalize.
    - Handles retries using the strategy's `should_retry` guidance.
    - Produces standardized JSON responses with rich metadata.

    Non-responsibilities:
    - Target-specific selectors or parsing logic (delegated to strategies).
    - Long-term storage or analytics (handled by other microservices).
    """

    def __init__(
        self,
        strategy: Scraper_Strategy,
        logger: Optional[Any] = None,
        max_attempts: Optional[int] = None,
        backoff_base_seconds: float = 0.5,
    ) -> None:
        """
        Initializes the orchestrator with a scraping strategy and optional settings.

        Args:
            strategy (Scraper_Strategy): The scraping strategy to use.
            logger (Optional[Any]): Logger instance for debug/error logging.
            max_attempts (Optional[int]): Max fetch attempts before giving up.
            backoff_base_seconds (float): Base seconds for exponential backoff between retries.
        """
        self._strategy = strategy
        self._logger = logger
        self._max_attempts = max_attempts if max_attempts is not None else 3
        self._backoff_base = backoff_base_seconds

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the scraping pipeline using the injected strategy.
        Returns a standardized JSON response.
        """
        attempts = 0
        raw: Optional[str] = None
        last_error: Optional[Exception] = None

        while attempts < self._max_attempts:
            attempts += 1
            try:
                self._log_debug(f"[{self._strategy.identifier()}] Fetch attempt {attempts}")
                raw = self._strategy.fetch(context)
                break
            except Exception as e:  # noqa: BLE001 broad by design to centralize handling
                last_error = e
                self._log_error(f"Fetch failed: {e!r}")
                # Strategy-specific retry decision
                if not self._strategy.should_retry(e, attempts):
                    self._log_debug("Strategy advised not to retry.")
                    return self._error_response("FETCH_ERROR", e, attempts)
                if attempts >= self._max_attempts:
                    self._log_debug("Max attempts reached.")
                    return self._error_response("FETCH_ERROR", e, attempts)
                # Exponential backoff
                sleep_secs = self._backoff_base * (2 ** (attempts - 1))
                self._log_debug(f"Backing off for {sleep_secs:.2f}s before retry...")
                time.sleep(sleep_secs)

        if raw is None:
            # Defensive: if loop exits without raw
            return self._error_response("FETCH_ERROR", last_error, attempts)

        try:
            self._log_debug("Extracting fields from raw content...")
            extracted = self._strategy.extract(raw)
        except Exception as e:  # noqa: BLE001
            self._log_error(f"Extract failed: {e!r}")
            return self._error_response("EXTRACT_ERROR", e, attempts)

        try:
            self._log_debug("Normalizing extracted fields to schema...")
            normalized = self._strategy.normalize(extracted)
        except Exception as e:  # noqa: BLE001
            self._log_error(f"Normalize failed: {e!r}")
            return self._error_response("NORMALIZE_ERROR", e, attempts)

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

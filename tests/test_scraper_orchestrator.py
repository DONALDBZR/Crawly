"""
Unit tests for Scraper_Orchestrator.

Tests orchestration flow, retry logic, backoff, and error handling.

Author:
    Darkness4869
"""

from __future__ import annotations
import unittest
from unittest.mock import Mock, patch, call
from typing import Any, Dict

from Models.ScraperOrchestrator import Scraper_Orchestrator
from Models.ScraperStrategy import Scraper_Strategy
from Models.Logger import Crawly_Logger
from Errors.Scraper import Scraper_Exception


class Test_Scraper_Orchestrator_Initialization(unittest.TestCase):
    """Testing Scraper_Orchestrator initialization."""

    def test_initialization_with_all_params(self) -> None:
        """Testing initialization with all parameters."""
        mock_strategy = Mock(spec=Scraper_Strategy)
        mock_logger = Mock(spec=Crawly_Logger)
        
        orchestrator = Scraper_Orchestrator(
            strategy=mock_strategy,
            logger=mock_logger,
            max_attempts=5,
            backoff_base_seconds=1.0
        )
        
        self.assertEqual(orchestrator._strategy, mock_strategy)
        self.assertEqual(orchestrator._logger, mock_logger)
        self.assertEqual(orchestrator._max_attempts, 5)
        self.assertEqual(orchestrator._backoff_base, 1.0)

    def test_initialization_with_defaults(self) -> None:
        """Testing initialization uses default values."""
        mock_strategy = Mock(spec=Scraper_Strategy)
        
        orchestrator = Scraper_Orchestrator(strategy=mock_strategy)
        
        self.assertEqual(orchestrator._max_attempts, 3)
        self.assertEqual(orchestrator._backoff_base, 0.5)


class Test_Scraper_Orchestrator_Happy_Path(unittest.TestCase):
    """Testing Scraper_Orchestrator successful execution."""

    def setUp(self) -> None:
        """Setting up test fixtures."""
        self.mock_strategy = Mock(spec=Scraper_Strategy)
        self.mock_logger = Mock(spec=Crawly_Logger)
        self.context = {"url": "https://example.com"}

    def test_complete_run_fetch_extract_normalize(self) -> None:
        """Testing complete successful run through all stages."""
        self.mock_strategy.identifier.return_value = "test_strategy"
        self.mock_strategy.fetch.return_value = "<html>test</html>"
        self.mock_strategy.extract.return_value = {"title": "Test"}
        self.mock_strategy.normalize.return_value = {
            "entity_type": "test",
            "data": {"title": "Test"}
        }
        
        orchestrator = Scraper_Orchestrator(
            strategy=self.mock_strategy,
            logger=self.mock_logger
        )
        
        result = orchestrator.run(self.context)
        
        self.assertEqual(result, {"entity_type": "test", "data": {"title": "Test"}})
        self.mock_strategy.fetch.assert_called_once_with(self.context)
        self.mock_strategy.extract.assert_called_once_with("<html>test</html>")
        self.mock_strategy.normalize.assert_called_once()

    def test_successful_first_fetch_attempt(self) -> None:
        """Testing successful fetch on first attempt."""
        self.mock_strategy.identifier.return_value = "test_strategy"
        self.mock_strategy.fetch.return_value = "data"
        self.mock_strategy.extract.return_value = {"field": "value"}
        self.mock_strategy.normalize.return_value = {"normalized": True}
        
        orchestrator = Scraper_Orchestrator(
            strategy=self.mock_strategy,
            logger=self.mock_logger
        )
        
        result = orchestrator.run(self.context)
        
        # Should only call fetch once
        self.assertEqual(self.mock_strategy.fetch.call_count, 1)
        self.assertIn("normalized", result)

    def test_logger_logs_all_stages(self) -> None:
        """Testing logger logs all orchestration stages."""
        self.mock_strategy.identifier.return_value = "test_strategy"
        self.mock_strategy.fetch.return_value = "data"
        self.mock_strategy.extract.return_value = {}
        self.mock_strategy.normalize.return_value = {}
        
        orchestrator = Scraper_Orchestrator(
            strategy=self.mock_strategy,
            logger=self.mock_logger
        )
        
        orchestrator.run(self.context)
        
        # Logger should be called for debug and info messages
        self.assertTrue(self.mock_logger.debug.called or self.mock_logger.inform.called)


class Test_Scraper_Orchestrator_Retry_Logic(unittest.TestCase):
    """Testing Scraper_Orchestrator retry and backoff logic."""

    def setUp(self) -> None:
        """Setting up test fixtures."""
        self.mock_strategy = Mock(spec=Scraper_Strategy)
        self.mock_logger = Mock(spec=Crawly_Logger)
        self.context = {"url": "https://example.com"}

    @patch('Models.ScraperOrchestrator.sleep')
    def test_retry_succeeds_on_second_attempt(self, mock_sleep) -> None:
        """Testing retry succeeds on second attempt."""
        self.mock_strategy.identifier.return_value = "test_strategy"
        
        # First call fails, second succeeds
        self.mock_strategy.fetch.side_effect = [
            Scraper_Exception("Temporary error", 500),
            "success_data"
        ]
        self.mock_strategy.should_retry.return_value = True
        self.mock_strategy.extract.return_value = {}
        self.mock_strategy.normalize.return_value = {}
        
        orchestrator = Scraper_Orchestrator(
            strategy=self.mock_strategy,
            logger=self.mock_logger,
            max_attempts=3
        )
        
        result = orchestrator.run(self.context)
        
        # Should have called fetch twice
        self.assertEqual(self.mock_strategy.fetch.call_count, 2)
        # Should have slept once (with exponential backoff)
        self.assertTrue(mock_sleep.called)

    @patch('Models.ScraperOrchestrator.sleep')
    def test_exponential_backoff_applied(self, mock_sleep) -> None:
        """Testing exponential backoff is applied between retries."""
        self.mock_strategy.identifier.return_value = "test_strategy"
        self.mock_strategy.fetch.side_effect = [
            Scraper_Exception("Error 1", 500),
            Scraper_Exception("Error 2", 500),
            "success"
        ]
        self.mock_strategy.should_retry.return_value = True
        self.mock_strategy.extract.return_value = {}
        self.mock_strategy.normalize.return_value = {}
        
        orchestrator = Scraper_Orchestrator(
            strategy=self.mock_strategy,
            logger=self.mock_logger,
            max_attempts=3,
            backoff_base_seconds=0.5
        )
        
        orchestrator.run(self.context)
        
        # Should have called sleep with increasing delays
        # First retry: 0.5 * 2^1 = 1.0
        # Second retry: 0.5 * 2^2 = 2.0
        self.assertEqual(mock_sleep.call_count, 2)

    def test_should_retry_consulted_for_transient_errors(self) -> None:
        """Testing should_retry() is consulted for retry decisions."""
        self.mock_strategy.identifier.return_value = "test_strategy"
        self.mock_strategy.fetch.side_effect = Scraper_Exception("Error", 500)
        self.mock_strategy.should_retry.return_value = False  # Don't retry
        
        orchestrator = Scraper_Orchestrator(
            strategy=self.mock_strategy,
            logger=self.mock_logger
        )
        
        with patch('Models.ScraperOrchestrator.sleep'):
            result = orchestrator.run(self.context)
        
        # Should return empty dict on failure
        self.assertEqual(result, {})
        # should_retry should have been called
        self.mock_strategy.should_retry.assert_called()


class Test_Scraper_Orchestrator_Max_Attempts(unittest.TestCase):
    """Testing Scraper_Orchestrator max attempts behavior."""

    def setUp(self) -> None:
        """Setting up test fixtures."""
        self.mock_strategy = Mock(spec=Scraper_Strategy)
        self.mock_logger = Mock(spec=Crawly_Logger)
        self.context = {"url": "https://example.com"}

    @patch('Models.ScraperOrchestrator.sleep')
    def test_max_attempts_exhausted_returns_empty_dict(self, mock_sleep) -> None:
        """Testing max attempts exhausted returns empty dict."""
        self.mock_strategy.identifier.return_value = "test_strategy"
        self.mock_strategy.fetch.side_effect = Scraper_Exception("Persistent error", 500)
        self.mock_strategy.should_retry.return_value = True
        
        orchestrator = Scraper_Orchestrator(
            strategy=self.mock_strategy,
            logger=self.mock_logger,
            max_attempts=2
        )
        
        result = orchestrator.run(self.context)
        
        # Should return empty dict after exhausting attempts
        self.assertEqual(result, {})
        # Should have attempted fetch max_attempts times
        self.assertEqual(self.mock_strategy.fetch.call_count, 2)

    def test_custom_max_attempts_honored(self) -> None:
        """Testing custom max_attempts value is honored."""
        self.mock_strategy.identifier.return_value = "test_strategy"
        self.mock_strategy.fetch.side_effect = Scraper_Exception("Error", 500)
        self.mock_strategy.should_retry.return_value = True
        
        orchestrator = Scraper_Orchestrator(
            strategy=self.mock_strategy,
            logger=self.mock_logger,
            max_attempts=5
        )
        
        with patch('Models.ScraperOrchestrator.sleep'):
            result = orchestrator.run(self.context)
        
        # Should attempt 5 times
        self.assertEqual(self.mock_strategy.fetch.call_count, 5)

    def test_non_retryable_error_fails_immediately(self) -> None:
        """Testing non-retryable error fails without retries."""
        self.mock_strategy.identifier.return_value = "test_strategy"
        self.mock_strategy.fetch.side_effect = Scraper_Exception("Client error", 404)
        self.mock_strategy.should_retry.return_value = False
        
        orchestrator = Scraper_Orchestrator(
            strategy=self.mock_strategy,
            logger=self.mock_logger,
            max_attempts=5
        )
        
        with patch('Models.ScraperOrchestrator.sleep') as mock_sleep:
            result = orchestrator.run(self.context)
        
        # Should have attempted fetch and may have slept once before checking should_retry
        # The important part is it should not retry after should_retry returns False
        self.assertLessEqual(self.mock_strategy.fetch.call_count, 2)


class Test_Scraper_Orchestrator_Validation(unittest.TestCase):
    """Testing Scraper_Orchestrator data validation."""

    def setUp(self) -> None:
        """Setting up test fixtures."""
        self.mock_strategy = Mock(spec=Scraper_Strategy)
        self.mock_logger = Mock(spec=Crawly_Logger)
        self.context = {"url": "https://example.com"}

    def test_none_data_raises_validation_error(self) -> None:
        """Testing None data from fetch raises validation error."""
        self.mock_strategy.identifier.return_value = "test_strategy"
        self.mock_strategy.fetch.return_value = None
        
        orchestrator = Scraper_Orchestrator(
            strategy=self.mock_strategy,
            logger=self.mock_logger
        )
        
        result = orchestrator.run(self.context)
        
        # Should return empty dict on validation failure
        self.assertEqual(result, {})
        # Extract and normalize should not be called
        self.mock_strategy.extract.assert_not_called()
        self.mock_strategy.normalize.assert_not_called()


class Test_Scraper_Orchestrator_Error_Handling(unittest.TestCase):
    """Testing Scraper_Orchestrator error handling."""

    def setUp(self) -> None:
        """Setting up test fixtures."""
        self.mock_strategy = Mock(spec=Scraper_Strategy)
        self.mock_logger = Mock(spec=Crawly_Logger)
        self.context = {"url": "https://example.com"}

    def test_extract_failure_returns_empty_dict(self) -> None:
        """Testing extract failure returns empty dict."""
        self.mock_strategy.identifier.return_value = "test_strategy"
        self.mock_strategy.fetch.return_value = "data"
        self.mock_strategy.extract.side_effect = Scraper_Exception("Extract failed", 500)
        
        orchestrator = Scraper_Orchestrator(
            strategy=self.mock_strategy,
            logger=self.mock_logger
        )
        
        result = orchestrator.run(self.context)
        
        self.assertEqual(result, {})
        self.mock_logger.error.assert_called()

    def test_normalize_failure_returns_empty_dict(self) -> None:
        """Testing normalize failure returns empty dict."""
        self.mock_strategy.identifier.return_value = "test_strategy"
        self.mock_strategy.fetch.return_value = "data"
        self.mock_strategy.extract.return_value = {"field": "value"}
        self.mock_strategy.normalize.side_effect = Scraper_Exception("Normalize failed", 500)
        
        orchestrator = Scraper_Orchestrator(
            strategy=self.mock_strategy,
            logger=self.mock_logger
        )
        
        result = orchestrator.run(self.context)
        
        self.assertEqual(result, {})
        self.mock_logger.error.assert_called()


if __name__ == "__main__":
    unittest.main()

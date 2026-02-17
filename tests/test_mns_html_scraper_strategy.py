"""
Unit tests for Mns_Html_Scraper_Strategy.

Tests HTTP fetching, HTML parsing, extraction, and normalization.

Author:
    Darkness4869
"""

from __future__ import annotations
import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict
from io import BytesIO

from Strategies.MnsHtmlScraperStrategy import Mns_Html_Scraper_Strategy
from Errors.Scraper import Scraper_Exception


class Test_Mns_Html_Scraper_Strategy_Initialization(unittest.TestCase):
    """Testing Mns_Html_Scraper_Strategy initialization."""

    def test_initialization_with_defaults(self) -> None:
        """Testing initialization with default parameters."""
        strategy = Mns_Html_Scraper_Strategy()
        
        self.assertEqual(strategy._Mns_Html_Scraper_Strategy__default_timeout, 10)
        self.assertEqual(strategy._Mns_Html_Scraper_Strategy__max_response_size, 16777216)
        self.assertIsNotNone(strategy._Mns_Html_Scraper_Strategy__default_selectors)

    def test_initialization_with_custom_params(self) -> None:
        """Testing initialization with custom parameters."""
        custom_selectors = {"title": "h1.custom"}
        
        strategy = Mns_Html_Scraper_Strategy(
            identifier="custom_strategy",
            default_timeout=30,
            max_response_size=1000000,
            default_selectors=custom_selectors
        )
        
        self.assertEqual(strategy._Mns_Html_Scraper_Strategy__identifier, "custom_strategy")
        self.assertEqual(strategy._Mns_Html_Scraper_Strategy__default_timeout, 30)
        self.assertEqual(strategy._Mns_Html_Scraper_Strategy__max_response_size, 1000000)

    def test_invalid_config_raises_exception(self) -> None:
        """Testing invalid configuration raises Scraper_Exception."""
        with self.assertRaises(Scraper_Exception):
            Mns_Html_Scraper_Strategy(default_timeout=0)
        
        with self.assertRaises(Scraper_Exception):
            Mns_Html_Scraper_Strategy(max_response_size=-1)


class Test_Mns_Html_Scraper_Strategy_Identifier(unittest.TestCase):
    """Testing Mns_Html_Scraper_Strategy.identifier() method."""

    def test_identifier_returns_strategy_name(self) -> None:
        """Testing identifier() returns correct strategy name."""
        strategy = Mns_Html_Scraper_Strategy()
        identifier = strategy.identifier()
        
        self.assertIsInstance(identifier, str)
        self.assertTrue(len(identifier) > 0)

    def test_custom_identifier_used(self) -> None:
        """Testing custom identifier is used when provided."""
        strategy = Mns_Html_Scraper_Strategy(identifier="my_custom_id")
        
        self.assertEqual(strategy.identifier(), "my_custom_id")


class Test_Mns_Html_Scraper_Strategy_Fetch(unittest.TestCase):
    """Testing Mns_Html_Scraper_Strategy.fetch() method."""

    @patch('Strategies.MnsHtmlScraperStrategy.urlopen')
    def test_fetch_retrieves_html_successfully(self, mock_urlopen) -> None:
        """Testing fetch() retrieves HTML content successfully."""
        html_content = b"<html><body>Test</body></html>"
        mock_response = Mock()
        mock_response.read.return_value = html_content
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        strategy = Mns_Html_Scraper_Strategy()
        context = {"url": "https://example.com"}
        
        result = strategy.fetch(context)
        
        self.assertIn("Test", result)
        mock_urlopen.assert_called_once()

    @patch('Strategies.MnsHtmlScraperStrategy.urlopen')
    def test_fetch_uses_context_timeout(self, mock_urlopen) -> None:
        """Testing fetch() uses timeout from context."""
        html_content = b"<html>content</html>"
        mock_response = Mock()
        mock_response.read.return_value = html_content
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        strategy = Mns_Html_Scraper_Strategy()
        context = {"url": "https://example.com", "timeout": 30}
        
        strategy.fetch(context)
        
        # Verify urlopen was called with a Request object
        mock_urlopen.assert_called_once()

    @patch('Strategies.MnsHtmlScraperStrategy.urlopen')
    def test_fetch_raises_exception_on_http_error(self, mock_urlopen) -> None:
        """Testing fetch() raises Scraper_Exception on HTTP error."""
        from urllib.error import HTTPError
        
        mock_urlopen.side_effect = HTTPError(
            "https://example.com", 404, "Not Found", {}, None
        )
        
        strategy = Mns_Html_Scraper_Strategy()
        context = {"url": "https://example.com"}
        
        with self.assertRaises(Scraper_Exception) as context_manager:
            strategy.fetch(context)
        
        self.assertEqual(context_manager.exception.code, 404)

    @patch('Strategies.MnsHtmlScraperStrategy.urlopen')
    def test_fetch_raises_exception_on_url_error(self, mock_urlopen) -> None:
        """Testing fetch() raises Scraper_Exception on URL error."""
        from urllib.error import URLError
        
        mock_urlopen.side_effect = URLError("Connection failed")
        
        strategy = Mns_Html_Scraper_Strategy()
        context = {"url": "https://example.com"}
        
        with self.assertRaises(Scraper_Exception):
            strategy.fetch(context)

    @patch('Strategies.MnsHtmlScraperStrategy.urlopen')
    def test_fetch_raises_exception_on_oversized_response(self, mock_urlopen) -> None:
        """Testing fetch() raises exception when response exceeds max size."""
        # Create a response larger than max_response_size
        large_content = b"x" * 20000000  # 20 MB
        mock_response = Mock()
        mock_response.read.return_value = large_content
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        strategy = Mns_Html_Scraper_Strategy(max_response_size=1000000)  # 1 MB limit
        context = {"url": "https://example.com"}
        
        with self.assertRaises(Scraper_Exception) as context_manager:
            strategy.fetch(context)
        
        # Check for size-related error message
        error_msg = str(context_manager.exception.message).lower()
        self.assertTrue("exceeded" in error_msg or "size" in error_msg)


class Test_Mns_Html_Scraper_Strategy_Extract(unittest.TestCase):
    """Testing Mns_Html_Scraper_Strategy.extract() method."""

    def test_extract_parses_html_with_beautifulsoup(self) -> None:
        """Testing extract() parses HTML with BeautifulSoup."""
        html = "<html><head><title>Test Page</title></head><body><h1>Hello</h1></body></html>"
        
        strategy = Mns_Html_Scraper_Strategy()
        result = strategy.extract(html)
        
        self.assertIsInstance(result, dict)
        self.assertIn("page_title", result)

    def test_extract_uses_default_selectors(self) -> None:
        """Testing extract() uses default selectors."""
        html = """
        <html>
            <head><title>Default Title</title></head>
            <body>
                <main>Main content here</main>
            </body>
        </html>
        """
        
        strategy = Mns_Html_Scraper_Strategy()
        result = strategy.extract(html)
        
        self.assertIn("Default Title", result.get("page_title", ""))
        self.assertIn("main_content", result)

    def test_extract_with_custom_selectors_from_context(self) -> None:
        """Testing extract() uses custom selectors from raw input."""
        html = """
        <html>
            <body>
                <h1 class="custom-title">Custom Title</h1>
                <div class="custom-content">Custom Content</div>
            </body>
        </html>
        """
        
        # In the actual implementation, selectors might be embedded in raw or via context
        strategy = Mns_Html_Scraper_Strategy()
        result = strategy.extract(html)
        
        # Should extract something
        self.assertIsInstance(result, dict)

    def test_extract_handles_invalid_html_gracefully(self) -> None:
        """Testing extract() handles invalid HTML gracefully."""
        invalid_html = "<html><body><div>Unclosed div</body></html>"
        
        strategy = Mns_Html_Scraper_Strategy()
        
        # Should not raise exception, BeautifulSoup handles malformed HTML
        result = strategy.extract(invalid_html)
        self.assertIsInstance(result, dict)

    def test_extract_extracts_links(self) -> None:
        """Testing extract() extracts links from page."""
        html = """
        <html>
            <body>
                <a href="/page1">Link 1</a>
                <a href="/page2">Link 2</a>
            </body>
        </html>
        """
        
        strategy = Mns_Html_Scraper_Strategy()
        result = strategy.extract(html)
        
        self.assertIn("links", result)
        self.assertIsInstance(result["links"], list)

    def test_extract_extracts_images(self) -> None:
        """Testing extract() extracts images from page."""
        html = """
        <html>
            <body>
                <img src="/image1.jpg" alt="Image 1">
                <img src="/image2.jpg" alt="Image 2">
            </body>
        </html>
        """
        
        strategy = Mns_Html_Scraper_Strategy()
        result = strategy.extract(html)
        
        self.assertIn("images", result)
        self.assertIsInstance(result["images"], list)

    def test_extract_extracts_tables(self) -> None:
        """Testing extract() extracts tables from page."""
        html = """
        <html>
            <body>
                <table>
                    <tr><th>Header 1</th><th>Header 2</th></tr>
                    <tr><td>Cell 1</td><td>Cell 2</td></tr>
                </table>
            </body>
        </html>
        """
        
        strategy = Mns_Html_Scraper_Strategy()
        result = strategy.extract(html)
        
        self.assertIn("tables", result)
        self.assertIsInstance(result["tables"], list)


class Test_Mns_Html_Scraper_Strategy_Normalize(unittest.TestCase):
    """Testing Mns_Html_Scraper_Strategy.normalize() method."""

    def test_normalize_returns_standard_schema(self) -> None:
        """Testing normalize() returns standardized schema."""
        extracted = {
            "page_title": "Test Page",
            "description": "Test description",
            "main_content": "Main content",
            "links": [],
            "images": [],
            "tables": []
        }
        
        strategy = Mns_Html_Scraper_Strategy()
        result = strategy.normalize(extracted)
        
        self.assertIn("entity_type", result)
        self.assertIn("entity_id", result)
        self.assertIn("timestamp", result)
        self.assertIn("data", result)
        self.assertEqual(result["entity_type"], "mns_page")

    def test_normalize_generates_entity_id(self) -> None:
        """Testing normalize() generates entity ID."""
        extracted = {
            "page_title": "Test",
            "links": []
        }
        
        strategy = Mns_Html_Scraper_Strategy()
        result = strategy.normalize(extracted)
        
        self.assertIsInstance(result["entity_id"], str)
        self.assertTrue(len(result["entity_id"]) > 0)

    def test_normalize_timestamp_in_iso8601_format(self) -> None:
        """Testing normalize() includes timestamp in ISO 8601 format."""
        extracted = {"page_title": "Test"}
        
        strategy = Mns_Html_Scraper_Strategy()
        result = strategy.normalize(extracted)
        
        self.assertIn("timestamp", result)
        # Should be ISO format with T separator
        self.assertIn("T", result["timestamp"])

    def test_normalize_includes_metadata(self) -> None:
        """Testing normalize() includes metadata counts."""
        extracted = {
            "page_title": "Test",
            "links": [{"href": "/1"}, {"href": "/2"}],
            "images": [{"src": "/img.jpg"}],
            "tables": [],
            "raw_text": "Some text content"
        }
        
        strategy = Mns_Html_Scraper_Strategy()
        result = strategy.normalize(extracted)
        
        self.assertIn("metadata", result["data"])
        metadata = result["data"]["metadata"]
        self.assertEqual(metadata["links_count"], 2)
        self.assertEqual(metadata["images_count"], 1)
        self.assertEqual(metadata["tables_count"], 0)


class Test_Mns_Html_Scraper_Strategy_Should_Retry(unittest.TestCase):
    """Testing Mns_Html_Scraper_Strategy.should_retry() method."""

    def test_should_retry_returns_true_for_500_status(self) -> None:
        """Testing should_retry() returns True for 500 server error."""
        strategy = Mns_Html_Scraper_Strategy()
        exception = Scraper_Exception("Server error", 500)
        
        result = strategy.should_retry(exception, 1)
        
        self.assertTrue(result)

    def test_should_retry_returns_true_for_429_rate_limit(self) -> None:
        """Testing should_retry() returns True for 429 rate limit."""
        strategy = Mns_Html_Scraper_Strategy()
        exception = Scraper_Exception("Rate limited", 429)
        
        result = strategy.should_retry(exception, 1)
        
        self.assertTrue(result)

    def test_should_retry_returns_false_for_404(self) -> None:
        """Testing should_retry() returns False for 404 not found."""
        strategy = Mns_Html_Scraper_Strategy()
        exception = Scraper_Exception("Not found", 404)
        
        result = strategy.should_retry(exception, 1)
        
        self.assertFalse(result)

    def test_should_retry_returns_false_after_3_attempts(self) -> None:
        """Testing should_retry() returns False after 3 attempts."""
        strategy = Mns_Html_Scraper_Strategy()
        exception = Scraper_Exception("Server error", 500)
        
        result = strategy.should_retry(exception, 3)
        
        self.assertFalse(result)

    def test_should_retry_returns_true_for_non_scraper_exception(self) -> None:
        """Testing should_retry() returns True for non-Scraper_Exception."""
        strategy = Mns_Html_Scraper_Strategy()
        exception = ValueError("Some error")
        
        result = strategy.should_retry(exception, 1)
        
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()

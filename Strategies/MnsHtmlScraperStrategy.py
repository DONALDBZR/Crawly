from __future__ import annotations
import re
from typing import Any, Dict, Optional
from urllib.request import _UrlopenRet, Request, urlopen
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup, Tag
from Models.ScraperStrategy import Scraper_Strategy
from Errors.Scraper import Scraper_Exception
from hashlib import sha256
from datetime import datetime, timezone


class Mns_Html_Scraper_Strategy(Scraper_Strategy):
    """
    Concrete scraper strategy for fetching and normalizing data from MNS HTML pages.

    This strategy demonstrates HTML-based scraping using BeautifulSoup4:
    - Fetches raw HTML content from MNS web pages
    - Parses HTML using BeautifulSoup4
    - Extracts data using CSS selectors (configurable per request)
    - Normalizes extracted data into a stable, predictable schema
    - Handles errors gracefully with domain-specific exceptions

    Expected context keys:
        - url (str, required): The MNS page URL to scrape
        - headers (Dict[str, str], optional): HTTP headers for the request
        - timeout (int, optional): Request timeout in seconds (default: 10)
        - method (str, optional): HTTP method (default: "GET")
        - selectors (Dict[str, str], optional): CSS selectors for field extraction
            Example: {"title": "h1.page-title", "content": "div.main-content"}

    Normalized output schema:
        {
            "entity_type": "mns_page",
            "entity_id": str,
            "timestamp": str (ISO 8601 format),
            "data": {
                "page_url": str,
                "page_title": str,
                "extracted_fields": Dict[str, Any],
                "metadata": Dict[str, Any]
            }
        }
    """

    __identifier: str
    """Unique identifier for this strategy instance."""
    __default_timeout: int
    """Default timeout for HTTP requests in seconds."""
    __max_response_size: int
    """Maximum allowed response size in bytes to prevent memory issues."""
    __default_selectors: Dict[str, str]
    """Default CSS selectors for common MNS page elements."""

    def __init__(
        self,
        identifier: Optional[str] = None,
        default_timeout: int = 10,
        max_response_size: int = 16777216,
        default_selectors: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Initializing the MNS HTML scraper strategy.

        Parameters:
            identifier (Optional[str]): Unique identifier for this strategy. Defaults to class name.
            default_timeout (int): Default timeout for HTTP requests in seconds. Defaults to 10.
            max_response_size (int): Maximum response size in bytes. Defaults to 16 MB.
            default_selectors (Optional[Dict[str, str]]): Default CSS selectors for extraction.

        Raises:
            Scraper_Exception: If initialization parameters are invalid.
        """
        self.__validate_strategy(default_timeout, max_response_size)
        self.__identifier = identifier if identifier else self.__class__.__name__
        self.__default_timeout = default_timeout
        self.__max_response_size = max_response_size
        self.__default_selectors = default_selectors if default_selectors else {
            "page_title": "title, h1",
            "main_content": "main, article, .content, #content",
            "description": "meta[name='description']",
        }

    def __validate_strategy(self, timeout: int, max_response_size: int) -> None:
        """
        Validating strategy configuration parameters.

        Parameters:
            timeout (int): The timeout value to validate.
            max_response_size (int): The maximum response size to validate.

        Raises:
            Scraper_Exception: If validation fails due to invalid parameters.
        """
        is_allowed: bool = (timeout > 0 and max_response_size > 0)
        if not is_allowed:
            raise Scraper_Exception("Invalid strategy configuration: timeout and max_response_size must be positive.", 400)

    def identifier(self) -> str:
        """
        Returning the unique identifier for this strategy.

        Returns:
            str: The strategy identifier.
        """
        return self.__identifier

    def _validate_context_url(self, context: Dict[str, Any]) -> str:
        """
        Validating that the context contains a valid URL.

        Procedures:
            1. Checks if context is provided and contains 'url' key.
            2. Validates that the URL is a non-empty string.
            3. Returns the URL if valid, otherwise raises an exception.

        Parameters:
            context (Dict[str, Any]): The context dictionary to validate.

        Returns:
            str: The validated URL from the context.

        Raises:
            Scraper_Exception: If the URL is missing or invalid.
        """
        if not context or "url" not in context:
            raise Scraper_Exception("Missing required context key: 'url'", 400)
        response: str = context["url"]
        if not response or not isinstance(response, str):
            raise Scraper_Exception("URL must be a non-empty string.", 400)
        return response

    def __add_header(self,
        request: Request,
        name: str,
        value: str
    ) -> Request:
        """
        Adding a header to the HTTP request if both name and value are provided.

        Parameters:
            request (Request): The HTTP request object to modify.
            name (str): The name of the header to add.
            value (str): The value of the header to add.

        Returns:
            Request: The modified HTTP request object with the new header added.
        """
        if name and value:
            request.add_header(name, value)
        return request

    def _fetch(
        self,
        url: str,
        method: str,
        headers: Dict[str, str],
        timeout: int
    ) -> str:
        """
        Internal method to perform the HTTP request and fetch raw HTML content.

        Procedures:
            1. Constructs the HTTP request with the specified method and headers.
            2. Executes the request with the given timeout.
            3. Reads the response while enforcing the maximum response size limit.
            4. Decodes the response bytes into a string using multiple encoding attempts.
            5. Handles various exceptions and raises Scraper_Exception with appropriate messages.

        Parameters:
            url (str): The URL to fetch.
            method (str): The HTTP method to use (e.g., "GET").
            headers (Dict[str, str]): HTTP headers to include in the request.
            timeout (int): The timeout for the request in seconds.

        Returns:
            str: The raw HTML response body as a string.

        Raises:
            Scraper_Exception: If the request fails or the response is invalid.
        """
        try:
            request: Request = Request(
                url,
                method=method
            )
            request = self.__add_header(request, "Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
            request = self.__add_header(request, "Accept-Language", "en-US,en;q=0.9")
            request = self.__add_header(request, "User-Agent", "Impact Radar/1.0")
            for header_name, header_value in headers.items():
                request = self.__add_header(request, header_name, str(header_value))
            response: _UrlopenRet = urlopen(
                request,
                timeout=timeout
            )
            raw_data: bytes = response.read(self.__max_response_size + 1)
            if len(raw_data) > self.__max_response_size:
                raise Scraper_Exception("The response has exceeded the maximum allowed size.", 413)
            return self._decode_html(raw_data)
        except HTTPError as error:
            raise Scraper_Exception(f"There is an HTTP error while fetching the URL. - Reason: {error.reason}", error.code)
        except URLError as error:
            raise Scraper_Exception(f"There is an error in the URL. - Reason: {error.reason}", 503)
        except UnicodeDecodeError as error:
            raise Scraper_Exception(f"The response cannot be decoded. - Error: {str(error)}", 500)
        except Exception as error:
            raise Scraper_Exception(f"An unexpected error occured. - Error: {str(error)}", 500)

    def fetch(self, context: Dict[str, Any]) -> str:
        """
        Fetching raw HTML content from the URL specified in the context.

        Procedures:
            1. Validates that the context contains a valid URL.
            2. Extracts headers, timeout, and method from the context with defaults.
            3. Calls the internal `_fetch` method to perform the HTTP request and get raw HTML
            4. Returns the raw HTML string.

        Parameters:
            context (Dict[str, Any]): The context containing the URL and optional request parameters.

        Returns:
            str: The raw HTML response body as a string.

        Raises:
            Scraper_Exception: If the context is invalid or the fetch operation fails.
        """
        url: str = self._validate_context_url(context)
        headers: Dict[str, str] = context.get("headers", {})
        timeout: int = context.get("timeout", self.__default_timeout)
        method: str = context.get("method", "GET")
        return self._fetch(
            url,
            method,
            headers,
            timeout
        )

    def _decode_html(self, raw_data: bytes) -> str:
        """
        Decoding raw bytes to string, trying multiple encodings.

        Parameters:
            raw_data (bytes): The raw response bytes.

        Returns:
            str: The decoded HTML string.

        Raises:
            UnicodeDecodeError: If all decoding attempts fail.
        """
        encodings: list[str] = ["utf-8", "iso-8859-1", "windows-1252"]
        for encoding in encodings:
            try:
                return raw_data.decode(encoding)
            except UnicodeDecodeError:
                continue
        # Last resort: decode with errors replaced
        return raw_data.decode("utf-8", errors="replace")

    def _validate_input(self, raw: str) -> None:
        """
        Validating that the raw input is a non-empty string.

        Parameters:
            raw (str): The raw input string to validate.

        Raises:
            Scraper_Exception: If the raw input is empty or not a string.
        """
        if not raw or not isinstance(raw, str):
            raise Scraper_Exception("Raw input must be a non-empty string.", 400)

    def _parse_html(self, raw: str) -> BeautifulSoup:
        """
        Parsing raw HTML string into a BeautifulSoup object.

        Parameters:
            raw (str): The raw HTML response string.

        Returns:
            BeautifulSoup: The parsed HTML document.

        Raises:
            Scraper_Exception: If parsing fails due to invalid HTML.
        """
        try:
            return BeautifulSoup(raw, "html.parser")
        except Exception as error:
            raise Scraper_Exception(f"It has failed to parse HTML. - Error: {str(error)}", 422)

    def _set_extracted_page_title(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensuring that the extracted page title is set, using a default if necessary.

        Parameters:
            extracted (Dict[str, Any]): The dictionary of extracted fields.

        Returns:
            Dict[str, Any]: The updated extracted fields with a guaranteed page title.
        """
        if not extracted["page_title"]:
            extracted["page_title"] = "Untitled MNS Page"
        return extracted

    def extract(self, raw: str) -> Dict[str, Any]:
        """
        Extracting structured data from raw HTML content.

        Procedures:
            1. Validates that the raw input is a non-empty string.
            2. Parses the raw HTML into a BeautifulSoup object.
            3. Extracts fields using default CSS selectors and helper methods.
            4. Sets a default page title if none is found.
            5. Returns a dictionary of extracted fields.

        Parameters:
            raw (str): The raw HTML response string.

        Returns:
            Dict[str, Any]: A dictionary containing extracted fields such as:
                - page_title: The title of the page
                - main_content: The main content of the page
                - description: The meta description of the page
                - extracted_fields: A dictionary of additional fields extracted using custom selectors
                - links: A list of links found on the page
                - images: A list of images found on the page
                - tables: A list of tables found on the page
                - raw_text: The full text content of the page

        Raises:
            Scraper_Exception: If the raw input is invalid or parsing fails.
        """
        self._validate_input(raw)
        soup: BeautifulSoup = self._parse_html(raw)
        extracted: Dict[str, Any] = {
            "page_title": self._extract_text(soup, self.__default_selectors["page_title"]),
            "main_content": self._extract_text(soup, self.__default_selectors["main_content"]),
            "description": self._extract_meta_content(soup, "description"),
            "extracted_fields": {},
            "links": self._extract_links(soup),
            "images": self._extract_images(soup),
            "tables": self._extract_tables(soup),
            "raw_text": soup.get_text(
                separator=" ",
                strip=True
            )
        }
        extracted = self._set_extracted_page_title(extracted)
        return extracted

    def _normalize_validate_extracted(self, extracted: Dict[str, Any]) -> None:
        """
        Validating that the extracted data is a dictionary.

        Parameters:
            extracted (Dict[str, Any]): The extracted data to validate.

        Raises:
            Scraper_Exception: If the extracted data is not a dictionary.
        """
        if not isinstance(extracted, dict):
            raise Scraper_Exception("Extracted data must be a dictionary.", 422)

    def _generate_entity_id(self, extracted: Dict[str, Any]) -> str:
        """
        Generating a unique entity ID based on the content of the page.

        Parameters:
            extracted (Dict[str, Any]): The extracted data from which to generate the ID.

        Returns:
            str: A unique entity ID generated from the page content.
        """
        content_for_hash: str = str(extracted.get("page_title", "")) + str(extracted.get("main_content", ""))
        return sha256(content_for_hash.encode()).hexdigest()[:16]

    def normalize(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalizing extracted data into a stable schema.

        Procedures:
            1. Validates that the extracted data is a dictionary.
            2. Generates a unique entity ID based on the page content.
            3. Constructs a normalized dictionary with a consistent schema.
            4. Returns the normalized data.

        Parameters:
            extracted (Dict[str, Any]): The dictionary of extracted fields.

        Returns:
            Dict[str, Any]: A normalized dictionary with the following structure:
                {
                    "entity_type": "mns_page",
                    "entity_id": str,
                    "timestamp": str (ISO 8601 format),
                    "data": {
                        "page_title": str,
                        "description": str,
                        "main_content": str,
                        "extracted_fields": Dict[str, Any],
                        "metadata": Dict[str, Any]
                    }
                }

        Raises:
            Scraper_Exception: If the extracted data is invalid.
        """
        self._normalize_validate_extracted(extracted)
        entity_id: str = self._generate_entity_id(extracted)
        timestamp: str = datetime.now(timezone.utc).isoformat()
        normalized: Dict[str, Any] = {
            "entity_type": "mns_page",
            "entity_id": entity_id,
            "timestamp": timestamp,
            "data": {
                "page_title": str(extracted.get("page_title", "")),
                "description": str(extracted.get("description", "")),
                "main_content": str(extracted.get("main_content", "")),
                "extracted_fields": extracted.get("extracted_fields", {}),
                "metadata": {
                    "links_count": len(extracted.get("links", [])),
                    "images_count": len(extracted.get("images", [])),
                    "tables_count": len(extracted.get("tables", [])),
                    "text_length": len(extracted.get("raw_text", "")),
                    "links": extracted.get("links", [])[:10],  # Limit to first 10
                    "images": extracted.get("images", [])[:10],  # Limit to first 10
                    "tables": extracted.get("tables", [])
                }
            }
        }
        return normalized

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determining if a fetch should be retried based on exception type and attempt count.

        Procedures:
            1. Checks if exception is a Scraper_Exception.
            2. Evaluates status code to determine if retry is appropriate.
            3. Returns True for transient errors (5xx, 429), False for client errors (4xx).
            4. Limits retries to 3 attempts maximum.

        Parameters:
            exception (Exception): The exception raised during fetch.
            attempt (int): The current attempt number (1-based).

        Returns:
            bool: True if retry should be attempted, False otherwise.
        """
        # Limit total attempts
        if attempt >= 3:
            return False

        # Retry on transient errors
        if isinstance(exception, Scraper_Exception):
            # Retry on server errors (5xx) and rate limiting (429)
            if exception.code >= 500 or exception.code == 429:
                return True
            # Don't retry on client errors (4xx except 429)
            if 400 <= exception.code < 500:
                return False

        # Default: retry on unknown errors
        return attempt < 3

    # ========== Helper Methods for HTML Extraction ==========

    def _extract_text(self, soup: BeautifulSoup, selector: str) -> str:
        """
        Extracting text content using CSS selector.

        Parameters:
            soup (BeautifulSoup): The parsed HTML document.
            selector (str): CSS selector (can be comma-separated for alternatives).

        Returns:
            str: The extracted text or empty string if not found.
        """
        selectors: list[str] = [s.strip() for s in selector.split(",")]
        for sel in selectors:
            try:
                element: Optional[Tag] = soup.select_one(sel)
                if element:
                    return element.get_text(strip=True)
            except Exception:
                continue
        return ""

    def _extract_meta_content(self, soup: BeautifulSoup, name: str) -> str:
        """
        Extracting content from meta tag by name.

        Parameters:
            soup (BeautifulSoup): The parsed HTML document.
            name (str): The meta tag name attribute.

        Returns:
            str: The content attribute value or empty string.
        """
        try:
            meta = soup.find("meta", attrs={"name": name})
            if meta and isinstance(meta, Tag):
                return str(meta.get("content", ""))
        except Exception:
            pass
        return ""

    def _extract_links(self, soup: BeautifulSoup) -> list[Dict[str, str]]:
        """
        Extracting all links from the page.

        Parameters:
            soup (BeautifulSoup): The parsed HTML document.

        Returns:
            list[Dict[str, str]]: List of link dictionaries with 'href' and 'text'.
        """
        links: list[Dict[str, str]] = []
        try:
            for link in soup.find_all("a", href=True):
                href: str = str(link.get("href", ""))
                text: str = link.get_text(strip=True)
                if href:
                    links.append({"href": href, "text": text})
        except Exception:
            pass
        return links

    def _extract_images(self, soup: BeautifulSoup) -> list[Dict[str, str]]:
        """
        Extracting all images from the page.

        Parameters:
            soup (BeautifulSoup): The parsed HTML document.

        Returns:
            list[Dict[str, str]]: List of image dictionaries with 'src' and 'alt'.
        """
        images: list[Dict[str, str]] = []
        try:
            for img in soup.find_all("img", src=True):
                src: str = str(img.get("src", ""))
                alt: str = str(img.get("alt", ""))
                if src:
                    images.append({"src": src, "alt": alt})
        except Exception:
            pass
        return images

    def _extract_tables(self, soup: BeautifulSoup) -> list[Dict[str, Any]]:
        """
        Extracting table data from the page.

        Parameters:
            soup (BeautifulSoup): The parsed HTML document.

        Returns:
            list[Dict[str, Any]]: List of table dictionaries with headers and rows.
        """
        tables_data: list[Dict[str, Any]] = []
        try:
            for table in soup.find_all("table"):
                table_dict: Dict[str, Any] = {
                    "headers": [],
                    "rows": []
                }

                # Extract headers
                headers = table.find_all("th")
                if headers:
                    table_dict["headers"] = [h.get_text(strip=True) for h in headers]

                # Extract rows
                for row in table.find_all("tr"):
                    cells = row.find_all(["td", "th"])
                    if cells:
                        row_data = [cell.get_text(strip=True) for cell in cells]
                        table_dict["rows"].append(row_data)

                if table_dict["rows"]:
                    tables_data.append(table_dict)
        except Exception:
            pass
        return tables_data

    def extract_with_custom_selectors(
        self,
        soup: BeautifulSoup,
        selectors: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Extracting fields using custom CSS selectors provided in context.

        Parameters:
            soup (BeautifulSoup): The parsed HTML document.
            selectors (Dict[str, str]): Dictionary mapping field names to CSS selectors.

        Returns:
            Dict[str, Any]: Dictionary of extracted field values.
        """
        extracted_fields: Dict[str, Any] = {}
        for field_name, selector in selectors.items():
            try:
                extracted_fields[field_name] = self._extract_text(soup, selector)
            except Exception as error:
                # Log but don't fail on individual selector errors
                extracted_fields[field_name] = None
        return extracted_fields

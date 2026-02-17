from __future__ import annotations
import json
from typing import Any, Dict, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from Models.ScraperStrategy import Scraper_Strategy
from Errors.Scraper import Scraper_Exception


class Product_Api_Scraper_Strategy(Scraper_Strategy):
    """
    Concrete scraper strategy for fetching and normalizing product data from JSON APIs.

    This strategy demonstrates a complete implementation of the Scraper_Strategy interface:
    - Fetches raw JSON data from a product API endpoint
    - Extracts product-specific fields (id, name, price, description, etc.)
    - Normalizes extracted data into a stable, predictable schema
    - Handles errors gracefully with domain-specific exceptions

    Expected context keys:
        - url (str, required): The API endpoint URL to fetch product data from
        - headers (Dict[str, str], optional): HTTP headers for the request
        - timeout (int, optional): Request timeout in seconds (default: 10)
        - method (str, optional): HTTP method (default: "GET")

    Normalized output schema:
        {
            "entity_type": "product",
            "entity_id": str,
            "timestamp": str (ISO 8601 format),
            "data": {
                "product_id": str,
                "product_name": str,
                "price": float,
                "currency": str,
                "description": str,
                "category": str,
                "in_stock": bool,
                "metadata": Dict[str, Any]
            }
        }
    """

    _identifier: str
    """Unique identifier for this strategy instance."""
    _default_timeout: int
    """Default timeout for HTTP requests in seconds."""
    _max_response_size: int
    """Maximum allowed response size in bytes to prevent memory issues."""

    def __init__(
        self,
        identifier: Optional[str] = None,
        default_timeout: int = 10,
        max_response_size: int = 10485760
    ) -> None:
        """
        Initializing the Product API scraper strategy.

        Parameters:
            identifier (Optional[str]): Unique identifier for this strategy. Defaults to class name.
            default_timeout (int): Default timeout for HTTP requests in seconds. Defaults to 10.
            max_response_size (int): Maximum response size in bytes. Defaults to 10MB.

        Raises:
            Scraper_Exception: If initialization parameters are invalid.
        """
        if default_timeout <= 0:
            raise Scraper_Exception("Default timeout must be positive.", 400)
        if max_response_size <= 0:
            raise Scraper_Exception("Max response size must be positive.", 400)

        self._identifier = identifier if identifier else self.__class__.__name__
        self._default_timeout = default_timeout
        self._max_response_size = max_response_size

    def identifier(self) -> str:
        """
        Returning the unique identifier for this strategy.

        Returns:
            str: The strategy identifier.
        """
        return self._identifier

    def fetch(self, context: Dict[str, Any]) -> str:
        """
        Fetching raw JSON product data from the specified API endpoint.

        Procedures:
            1. Validates that required context keys are present.
            2. Extracts URL, headers, timeout, and method from context.
            3. Constructs HTTP request with appropriate headers.
            4. Executes the request with timeout and size constraints.
            5. Reads and validates the response.
            6. Returns the raw response body as a string.

        Parameters:
            context (Dict[str, Any]): Context containing:
                - url (str, required): The API endpoint URL
                - headers (Dict[str, str], optional): HTTP headers
                - timeout (int, optional): Request timeout in seconds
                - method (str, optional): HTTP method (default: "GET")

        Returns:
            str: The raw response body as a string.

        Raises:
            Scraper_Exception: If URL is missing, request fails, or response is invalid.
        """
        # Step 1: Validate required context
        if not context or "url" not in context:
            raise Scraper_Exception("Missing required context key: 'url'", 400)

        url: str = context["url"]
        if not url or not isinstance(url, str):
            raise Scraper_Exception("URL must be a non-empty string.", 400)

        # Step 2: Extract optional parameters
        headers: Dict[str, str] = context.get("headers", {})
        timeout: int = context.get("timeout", self._default_timeout)
        method: str = context.get("method", "GET")

        # Step 3: Construct request
        try:
            request: Request = Request(url, method=method)

            # Add default headers for JSON API
            request.add_header("Accept", "application/json")
            request.add_header("User-Agent", "Crawly/1.0 (Product API Scraper)")

            # Add custom headers
            for header_name, header_value in headers.items():
                if header_name and header_value:
                    request.add_header(header_name, str(header_value))

            # Step 4: Execute request with timeout
            response = urlopen(request, timeout=timeout)

            # Step 5: Read response with size limit
            raw_data: bytes = response.read(self._max_response_size + 1)
            if len(raw_data) > self._max_response_size:
                raise Scraper_Exception(
                    f"Response exceeds maximum size of {self._max_response_size} bytes.",
                    413
                )

            # Step 6: Decode and return
            return raw_data.decode("utf-8")

        except HTTPError as error:
            raise Scraper_Exception(
                f"HTTP error during fetch: {error.code} - {error.reason}",
                error.code
            )
        except URLError as error:
            raise Scraper_Exception(
                f"URL error during fetch: {str(error.reason)}",
                503
            )
        except UnicodeDecodeError as error:
            raise Scraper_Exception(
                f"Failed to decode response as UTF-8: {str(error)}",
                500
            )
        except Exception as error:
            raise Scraper_Exception(
                f"Unexpected error during fetch: {str(error)}",
                500
            )

    def extract(self, raw: str) -> Dict[str, Any]:
        """
        Extracting product fields from raw JSON response.

        Procedures:
            1. Validates that raw input is not empty.
            2. Parses raw string as JSON.
            3. Extracts product-specific fields with fallbacks.
            4. Validates that critical fields are present.
            5. Returns extracted fields as a dictionary.

        Parameters:
            raw (str): The raw JSON response string.

        Returns:
            Dict[str, Any]: Extracted product fields containing:
                - product_id: Product identifier
                - product_name: Product name
                - price: Product price (numeric)
                - currency: Price currency code
                - description: Product description
                - category: Product category
                - in_stock: Stock availability
                - raw_data: Original parsed JSON for reference

        Raises:
            Scraper_Exception: If parsing fails or critical fields are missing.
        """
        # Step 1: Validate input
        if not raw or not isinstance(raw, str):
            raise Scraper_Exception("Raw input must be a non-empty string.", 400)

        # Step 2: Parse JSON
        try:
            parsed: Dict[str, Any] = json.loads(raw)
        except json.JSONDecodeError as error:
            raise Scraper_Exception(
                f"Failed to parse JSON: {str(error)}",
                422
            )

        if not isinstance(parsed, dict):
            raise Scraper_Exception("Parsed JSON must be a dictionary.", 422)

        # Step 3: Extract fields with fallbacks
        extracted: Dict[str, Any] = {
            "product_id": self._extract_field(parsed, ["id", "product_id", "productId", "sku"]),
            "product_name": self._extract_field(parsed, ["name", "title", "product_name", "productName"]),
            "price": self._extract_numeric_field(parsed, ["price", "amount", "cost"]),
            "currency": self._extract_field(parsed, ["currency", "currency_code"], "USD"),
            "description": self._extract_field(parsed, ["description", "desc", "details"], ""),
            "category": self._extract_field(parsed, ["category", "type", "product_type"], ""),
            "in_stock": self._extract_boolean_field(parsed, ["in_stock", "inStock", "available"], True),
            "raw_data": parsed
        }

        # Step 4: Validate critical fields
        if not extracted["product_id"]:
            raise Scraper_Exception("Missing critical field: product_id", 422)
        if not extracted["product_name"]:
            raise Scraper_Exception("Missing critical field: product_name", 422)

        return extracted

    def normalize(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converting extracted product fields into the standardized Crawly schema.

        Procedures:
            1. Validates that extracted data is a dictionary.
            2. Constructs standard entity envelope with metadata.
            3. Maps extracted fields to normalized field names.
            4. Adds timestamp and entity type information.
            5. Returns the normalized data structure.

        Parameters:
            extracted (Dict[str, Any]): Extracted product fields from extract().

        Returns:
            Dict[str, Any]: Normalized data in standard schema with:
                - entity_type: Always "product"
                - entity_id: Unique product identifier
                - timestamp: ISO 8601 timestamp
                - data: Normalized product data fields

        Raises:
            Scraper_Exception: If extracted data is invalid or missing required fields.
        """
        # Step 1: Validate input
        if not isinstance(extracted, dict):
            raise Scraper_Exception("Extracted data must be a dictionary.", 422)

        if "product_id" not in extracted or not extracted["product_id"]:
            raise Scraper_Exception("Cannot normalize without product_id.", 422)

        # Step 2: Get current timestamp
        from datetime import datetime, timezone
        timestamp: str = datetime.now(timezone.utc).isoformat()

        # Step 3: Construct normalized schema
        normalized: Dict[str, Any] = {
            "entity_type": "product",
            "entity_id": str(extracted["product_id"]),
            "timestamp": timestamp,
            "data": {
                "product_id": str(extracted["product_id"]),
                "product_name": str(extracted.get("product_name", "")),
                "price": float(extracted.get("price", 0.0)),
                "currency": str(extracted.get("currency", "USD")),
                "description": str(extracted.get("description", "")),
                "category": str(extracted.get("category", "")),
                "in_stock": bool(extracted.get("in_stock", False)),
                "metadata": self._extract_metadata(extracted)
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
            # Don't retry on client errors (4xx)
            if 400 <= exception.code < 500:
                return False

        # Default: retry on unknown errors
        return attempt < 3

    def _extract_field(
        self,
        data: Dict[str, Any],
        field_names: list[str],
        default: Any = None
    ) -> Any:
        """
        Extracting a field from data using multiple possible field names.

        Parameters:
            data (Dict[str, Any]): The data dictionary to search.
            field_names (list[str]): List of possible field names to try.
            default (Any): Default value if no field is found.

        Returns:
            Any: The field value or default.
        """
        for name in field_names:
            if name in data and data[name] is not None:
                return data[name]
        return default

    def _extract_numeric_field(
        self,
        data: Dict[str, Any],
        field_names: list[str],
        default: float = 0.0
    ) -> float:
        """
        Extracting a numeric field and converting to float.

        Parameters:
            data (Dict[str, Any]): The data dictionary to search.
            field_names (list[str]): List of possible field names to try.
            default (float): Default value if no valid numeric field is found.

        Returns:
            float: The numeric value or default.
        """
        value = self._extract_field(data, field_names)
        if value is None:
            return default

        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def _extract_boolean_field(
        self,
        data: Dict[str, Any],
        field_names: list[str],
        default: bool = False
    ) -> bool:
        """
        Extracting a boolean field and converting to bool.

        Parameters:
            data (Dict[str, Any]): The data dictionary to search.
            field_names (list[str]): List of possible field names to try.
            default (bool): Default value if no valid boolean field is found.

        Returns:
            bool: The boolean value or default.
        """
        value = self._extract_field(data, field_names)
        if value is None:
            return default

        # Handle various truthy/falsy representations
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "1", "available", "in-stock")
        if isinstance(value, (int, float)):
            return bool(value)

        return default

    def _extract_metadata(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracting additional metadata fields from extracted data.

        Parameters:
            extracted (Dict[str, Any]): The extracted data dictionary.

        Returns:
            Dict[str, Any]: Metadata dictionary with non-core fields.
        """
        # Define core fields that go into main data structure
        core_fields: set[str] = {
            "product_id", "product_name", "price", "currency",
            "description", "category", "in_stock", "raw_data"
        }

        # Extract any additional fields as metadata
        metadata: Dict[str, Any] = {}
        for key, value in extracted.items():
            if key not in core_fields and key != "raw_data":
                metadata[key] = value

        # Include selected fields from raw_data if present
        if "raw_data" in extracted and isinstance(extracted["raw_data"], dict):
            raw: Dict[str, Any] = extracted["raw_data"]
            # Add common supplementary fields
            supplementary_fields: list[str] = [
                "brand", "manufacturer", "weight", "dimensions",
                "color", "size", "rating", "reviews_count", "tags"
            ]
            for field in supplementary_fields:
                if field in raw and field not in metadata:
                    metadata[field] = raw[field]

        return metadata

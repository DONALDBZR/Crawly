"""
Unit tests for Data_Sanitizer.

Tests SQL injection prevention and input validation.

Author:
    Darkness4869
"""

from __future__ import annotations
import unittest
from typing import Any

from Models.DataSanitizer import Data_Sanitizer


class Test_Data_Sanitizer_Happy_Path(unittest.TestCase):
    """Testing Data_Sanitizer with valid inputs."""

    def setUp(self) -> None:
        """Setting up test fixtures."""
        self.sanitizer = Data_Sanitizer()

    def test_clean_alphanumeric_string_passes(self) -> None:
        """Testing clean alphanumeric string passes validation."""
        result = self.sanitizer.sanitize("test123")
        self.assertEqual(result, "test123")

    def test_none_input_returns_none(self) -> None:
        """Testing None input returns None."""
        result = self.sanitizer.sanitize(None)
        self.assertIsNone(result)

    def test_non_string_types_return_unchanged(self) -> None:
        """Testing non-string types pass through unchanged."""
        self.assertEqual(self.sanitizer.sanitize(123), 123)
        self.assertEqual(self.sanitizer.sanitize(45.67), 45.67)
        self.assertEqual(self.sanitizer.sanitize(True), True)

    def test_string_with_allowed_special_chars(self) -> None:
        """Testing string with allowed special characters."""
        test_string = "test-value_123.45"
        result = self.sanitizer.sanitize(test_string)
        self.assertEqual(result, test_string)

    def test_empty_string_passes(self) -> None:
        """Testing empty string passes validation."""
        result = self.sanitizer.sanitize("")
        self.assertEqual(result, "")

    def test_string_with_spaces(self) -> None:
        """Testing string with spaces is allowed."""
        test_string = "hello world test"
        result = self.sanitizer.sanitize(test_string)
        self.assertEqual(result, test_string)

    def test_string_with_various_allowed_chars(self) -> None:
        """Testing string with various allowed special characters."""
        test_string = "test-value_123.45:port#id&param=true"
        result = self.sanitizer.sanitize(test_string)
        self.assertEqual(result, test_string)


class Test_Data_Sanitizer_SQL_Injection(unittest.TestCase):
    """Testing Data_Sanitizer SQL injection prevention."""

    def setUp(self) -> None:
        """Setting up test fixtures."""
        self.sanitizer = Data_Sanitizer()

    def test_drop_table_keyword_rejected(self) -> None:
        """Testing DROP TABLE SQL keyword is rejected."""
        with self.assertRaises(ValueError) as context:
            self.sanitizer.sanitize("test DROP TABLE users")
        self.assertIn("restricted SQL keywords", str(context.exception))

    def test_insert_keyword_rejected(self) -> None:
        """Testing INSERT keyword is rejected."""
        with self.assertRaises(ValueError) as context:
            self.sanitizer.sanitize("data INSERT INTO table")
        self.assertIn("restricted SQL keywords", str(context.exception))

    def test_delete_keyword_rejected(self) -> None:
        """Testing DELETE keyword is rejected."""
        with self.assertRaises(ValueError) as context:
            self.sanitizer.sanitize("value DELETE FROM users")
        self.assertIn("restricted SQL keywords", str(context.exception))

    def test_multiple_sql_keywords_rejected(self) -> None:
        """Testing multiple SQL keywords are rejected."""
        with self.assertRaises(ValueError) as context:
            self.sanitizer.sanitize("DROP TABLE users; DELETE FROM admins")
        self.assertIn("restricted SQL keywords", str(context.exception))


class Test_Data_Sanitizer_Invalid_Characters(unittest.TestCase):
    """Testing Data_Sanitizer invalid character handling."""

    def setUp(self) -> None:
        """Setting up test fixtures."""
        self.sanitizer = Data_Sanitizer()

    def test_invalid_characters_rejected(self) -> None:
        """Testing string with invalid characters is rejected."""
        with self.assertRaises(ValueError) as context:
            self.sanitizer.sanitize("test`value")
        self.assertIn("invalid", str(context.exception))


class Test_Data_Sanitizer_Initialization(unittest.TestCase):
    """Testing Data_Sanitizer initialization options."""

    def test_custom_sql_keywords_list(self) -> None:
        """Testing custom SQL keywords list is used."""
        custom_keywords = ["CUSTOM", "FORBIDDEN"]
        sanitizer = Data_Sanitizer(structured_query_language_keywords=custom_keywords)
        
        # Should reject custom keyword
        with self.assertRaises(ValueError):
            sanitizer.sanitize("test CUSTOM value")
        
        # Should allow standard SQL keywords not in custom list
        result = sanitizer.sanitize("test drop value")
        self.assertEqual(result, "test drop value")

    def test_custom_safe_string_pattern(self) -> None:
        """Testing custom safe string regex pattern."""
        # Only allow lowercase letters
        sanitizer = Data_Sanitizer(
            structured_query_language_keywords=[],
            safe_string=r"^[a-z]*$"
        )
        
        # Should pass
        result = sanitizer.sanitize("lowercase")
        self.assertEqual(result, "lowercase")
        
        # Should fail with uppercase
        with self.assertRaises(ValueError):
            sanitizer.sanitize("Uppercase")


if __name__ == "__main__":
    unittest.main()

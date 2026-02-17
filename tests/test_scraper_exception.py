"""
Unit tests for Scraper_Exception.

Tests custom exception creation and traceback capture.

Author:
    Darkness4869
"""

from __future__ import annotations
import unittest

from Errors.Scraper import Scraper_Exception


class Test_Scraper_Exception_Creation(unittest.TestCase):
    """Testing Scraper_Exception creation and attributes."""

    def test_exception_created_with_message(self) -> None:
        """Testing exception is created with message."""
        message = "Test error message"
        exception = Scraper_Exception(message)
        
        self.assertEqual(exception.message, message)
        self.assertEqual(str(exception), message)

    def test_exception_created_with_custom_code(self) -> None:
        """Testing exception is created with custom error code."""
        message = "Custom error"
        code = 404
        exception = Scraper_Exception(message, code)
        
        self.assertEqual(exception.message, message)
        self.assertEqual(exception.code, 404)

    def test_default_code_is_500(self) -> None:
        """Testing default error code is 500."""
        exception = Scraper_Exception("Error")
        self.assertEqual(exception.code, 500)

    def test_file_and_line_number_captured(self) -> None:
        """Testing file and line number are captured."""
        exception = Scraper_Exception("Test")
        
        self.assertIsInstance(exception.file, str)
        self.assertIn("test_scraper_exception.py", exception.file)
        self.assertIsInstance(exception.line, int)
        self.assertGreater(exception.line, 0)

    def test_traceback_string_captured(self) -> None:
        """Testing traceback string is captured."""
        exception = Scraper_Exception("Test traceback")
        
        self.assertIsInstance(exception.trace, str)
        self.assertIn("test_scraper_exception.py", exception.trace)


class Test_Scraper_Exception_Inheritance(unittest.TestCase):
    """Testing Scraper_Exception inheritance behavior."""

    def test_is_exception_subclass(self) -> None:
        """Testing Scraper_Exception is an Exception subclass."""
        exception = Scraper_Exception("Test")
        self.assertIsInstance(exception, Exception)

    def test_can_be_raised_and_caught(self) -> None:
        """Testing exception can be raised and caught."""
        with self.assertRaises(Scraper_Exception) as context:
            raise Scraper_Exception("Raised exception", 400)
        
        self.assertEqual(context.exception.code, 400)
        self.assertEqual(context.exception.message, "Raised exception")


if __name__ == "__main__":
    unittest.main()

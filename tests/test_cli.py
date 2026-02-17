"""
Unit tests for CLI module.

Tests argument parsing, validation, context building, and error handling.

Author:
    Darkness4869
"""

from __future__ import annotations
import unittest
import json
import sys
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
import argparse

# Import CLI functions
from cli import (
    create_argument_parser,
    validate_arguments,
    build_context,
    format_output,
    EXIT_SUCCESS,
    EXIT_VALIDATION_ERROR,
    EXIT_RUNTIME_ERROR,
    EXIT_INTERNAL_ERROR,
)


class Test_Argument_Parser(unittest.TestCase):
    """Testing argument parser creation and parsing."""

    def setUp(self) -> None:
        """Setting up test fixtures."""
        self.parser = create_argument_parser()

    def test_parser_creation(self) -> None:
        """Testing parser is created successfully."""
        self.assertIsInstance(self.parser, argparse.ArgumentParser)
        self.assertEqual(self.parser.prog, "crawly")

    def test_required_url_argument(self) -> None:
        """Testing URL argument is required."""
        with self.assertRaises(SystemExit):
            self.parser.parse_args([])

    def test_url_argument_parsing(self) -> None:
        """Testing URL argument is parsed correctly."""
        args = self.parser.parse_args(["--url", "https://example.com"])
        self.assertEqual(args.url, "https://example.com")

    def test_strategy_default(self) -> None:
        """Testing strategy has correct default."""
        args = self.parser.parse_args(["--url", "https://example.com"])
        self.assertEqual(args.strategy, "mns")

    def test_strategy_choice_validation(self) -> None:
        """Testing invalid strategy is rejected."""
        with self.assertRaises(SystemExit):
            self.parser.parse_args(["--url", "https://example.com", "--strategy", "invalid"])

    def test_log_level_default(self) -> None:
        """Testing log level has correct default."""
        args = self.parser.parse_args(["--url", "https://example.com"])
        self.assertEqual(args.log_level, "INFO")

    def test_log_level_choices(self) -> None:
        """Testing log level accepts valid choices."""
        for level in ["DEBUG", "INFO", "WARN", "ERROR"]:
            args = self.parser.parse_args(["--url", "https://example.com", "--log-level", level])
            self.assertEqual(args.log_level, level)

    def test_output_default(self) -> None:
        """Testing output default is stdout."""
        args = self.parser.parse_args(["--url", "https://example.com"])
        self.assertEqual(args.output, "-")

    def test_output_format_default(self) -> None:
        """Testing output format default is json."""
        args = self.parser.parse_args(["--url", "https://example.com"])
        self.assertEqual(args.output_format, "json")

    def test_dry_run_default(self) -> None:
        """Testing dry-run default is False."""
        args = self.parser.parse_args(["--url", "https://example.com"])
        self.assertFalse(args.dry_run)

    def test_dry_run_flag(self) -> None:
        """Testing dry-run flag is parsed."""
        args = self.parser.parse_args(["--url", "https://example.com", "--dry-run"])
        self.assertTrue(args.dry_run)

    def test_quiet_flag(self) -> None:
        """Testing quiet flag is parsed."""
        args = self.parser.parse_args(["--url", "https://example.com", "--quiet"])
        self.assertTrue(args.quiet)

    def test_max_attempts_default(self) -> None:
        """Testing max attempts default is 3."""
        args = self.parser.parse_args(["--url", "https://example.com"])
        self.assertEqual(args.max_attempts, 3)

    def test_timeout_default(self) -> None:
        """Testing timeout default is 10."""
        args = self.parser.parse_args(["--url", "https://example.com"])
        self.assertEqual(args.timeout, 10)

    def test_all_arguments_together(self) -> None:
        """Testing all arguments can be parsed together."""
        args = self.parser.parse_args([
            "--url", "https://example.com",
            "--strategy", "mns",
            "--log-level", "DEBUG",
            "--output", "test.json",
            "--output-format", "pretty",
            "--dry-run",
            "--quiet",
            "--max-attempts", "5",
            "--timeout", "30",
            "--config", ".env.test",
            "--headers", '{"User-Agent": "Test"}',
            "--selectors", '{"title": "h1"}',
        ])
        self.assertEqual(args.url, "https://example.com")
        self.assertEqual(args.strategy, "mns")
        self.assertEqual(args.log_level, "DEBUG")
        self.assertEqual(args.output, "test.json")
        self.assertEqual(args.output_format, "pretty")
        self.assertTrue(args.dry_run)
        self.assertTrue(args.quiet)
        self.assertEqual(args.max_attempts, 5)
        self.assertEqual(args.timeout, 30)
        self.assertEqual(args.config, ".env.test")
        self.assertEqual(args.headers, '{"User-Agent": "Test"}')
        self.assertEqual(args.selectors, '{"title": "h1"}')


class Test_Argument_Validation(unittest.TestCase):
    """Testing argument validation logic."""

    def test_validate_empty_url(self) -> None:
        """Testing empty URL raises ValueError."""
        args = Mock()
        args.url = ""
        args.config = ".env"
        args.headers = None
        args.selectors = None
        args.max_attempts = 3
        args.timeout = 10

        with self.assertRaises(ValueError) as context:
            validate_arguments(args)
        self.assertIn("URL cannot be empty", str(context.exception))

    def test_validate_missing_config_file(self) -> None:
        """Testing non-existent config file raises ValueError."""
        args = Mock()
        args.url = "https://example.com"
        args.config = "/nonexistent/config.env"
        args.headers = None
        args.selectors = None
        args.max_attempts = 3
        args.timeout = 10

        with self.assertRaises(ValueError) as context:
            validate_arguments(args)
        self.assertIn("Config file not found", str(context.exception))

    def test_validate_invalid_headers_json(self) -> None:
        """Testing invalid headers JSON raises ValueError."""
        args = Mock()
        args.url = "https://example.com"
        args.config = ".env"
        args.headers = "{invalid json}"
        args.selectors = None
        args.max_attempts = 3
        args.timeout = 10

        with self.assertRaises(ValueError) as context:
            validate_arguments(args)
        self.assertIn("Invalid JSON for --headers", str(context.exception))

    def test_validate_invalid_selectors_json(self) -> None:
        """Testing invalid selectors JSON raises ValueError."""
        args = Mock()
        args.url = "https://example.com"
        args.config = ".env"
        args.headers = None
        args.selectors = "{invalid json}"
        args.max_attempts = 3
        args.timeout = 10

        with self.assertRaises(ValueError) as context:
            validate_arguments(args)
        self.assertIn("Invalid JSON for --selectors", str(context.exception))

    def test_validate_negative_max_attempts(self) -> None:
        """Testing negative max_attempts raises ValueError."""
        args = Mock()
        args.url = "https://example.com"
        args.config = ".env"
        args.headers = None
        args.selectors = None
        args.max_attempts = -1
        args.timeout = 10

        with self.assertRaises(ValueError) as context:
            validate_arguments(args)
        self.assertIn("--max-attempts must be positive", str(context.exception))

    def test_validate_zero_timeout(self) -> None:
        """Testing zero timeout raises ValueError."""
        args = Mock()
        args.url = "https://example.com"
        args.config = ".env"
        args.headers = None
        args.selectors = None
        args.max_attempts = 3
        args.timeout = 0

        with self.assertRaises(ValueError) as context:
            validate_arguments(args)
        self.assertIn("--timeout must be positive", str(context.exception))

    def test_validate_valid_arguments(self) -> None:
        """Testing valid arguments pass validation."""
        args = Mock()
        args.url = "https://example.com"
        args.config = ".env"
        args.headers = '{"User-Agent": "Test"}'
        args.selectors = '{"title": "h1"}'
        args.max_attempts = 3
        args.timeout = 10

        # Should not raise
        validate_arguments(args)


class Test_Context_Building(unittest.TestCase):
    """Testing context dictionary building."""

    def test_build_basic_context(self) -> None:
        """Testing basic context without optional fields."""
        args = Mock()
        args.url = "https://example.com"
        args.timeout = 10
        args.headers = None
        args.selectors = None

        context = build_context(args)

        self.assertEqual(context["url"], "https://example.com")
        self.assertEqual(context["timeout"], 10)
        self.assertEqual(context["method"], "GET")
        self.assertNotIn("headers", context)
        self.assertNotIn("selectors", context)

    def test_build_context_with_headers(self) -> None:
        """Testing context with headers."""
        args = Mock()
        args.url = "https://example.com"
        args.timeout = 10
        args.headers = '{"User-Agent": "Test", "Accept": "text/html"}'
        args.selectors = None

        context = build_context(args)

        self.assertIn("headers", context)
        self.assertEqual(context["headers"]["User-Agent"], "Test")
        self.assertEqual(context["headers"]["Accept"], "text/html")

    def test_build_context_with_selectors(self) -> None:
        """Testing context with selectors."""
        args = Mock()
        args.url = "https://example.com"
        args.timeout = 10
        args.headers = None
        args.selectors = '{"title": "h1", "content": "article"}'

        context = build_context(args)

        self.assertIn("selectors", context)
        self.assertEqual(context["selectors"]["title"], "h1")
        self.assertEqual(context["selectors"]["content"], "article")

    def test_build_context_with_all_fields(self) -> None:
        """Testing context with all optional fields."""
        args = Mock()
        args.url = "https://example.com"
        args.timeout = 30
        args.headers = '{"User-Agent": "Test"}'
        args.selectors = '{"title": "h1"}'

        context = build_context(args)

        self.assertEqual(context["url"], "https://example.com")
        self.assertEqual(context["timeout"], 30)
        self.assertEqual(context["method"], "GET")
        self.assertIn("headers", context)
        self.assertIn("selectors", context)


class Test_Output_Formatting(unittest.TestCase):
    """Testing output formatting functions."""

    def setUp(self) -> None:
        """Setting up test data."""
        self.sample_result = {
            "entity_type": "mns_page",
            "entity_id": "test123",
            "timestamp": "2026-02-17T10:00:00Z",
            "data": {
                "page_url": "https://example.com",
                "page_title": "Test Page",
                "extracted_fields": {
                    "title": "Example",
                    "content": "Test content"
                }
            }
        }

    def test_format_json(self) -> None:
        """Testing JSON output formatting."""
        output = format_output(self.sample_result, "json")
        
        # Should be valid JSON
        parsed = json.loads(output)
        self.assertEqual(parsed["entity_type"], "mns_page")
        self.assertEqual(parsed["entity_id"], "test123")

    def test_format_pretty(self) -> None:
        """Testing pretty output formatting."""
        output = format_output(self.sample_result, "pretty")
        
        # Should contain key information
        self.assertIn("mns_page", output)
        self.assertIn("test123", output)
        self.assertIn("2026-02-17T10:00:00Z", output)
        self.assertIn("Example", output)

    def test_format_csv(self) -> None:
        """Testing CSV output formatting."""
        output = format_output(self.sample_result, "csv")
        
        # Should contain CSV headers and data
        lines = output.strip().split("\n")
        self.assertEqual(len(lines), 2)  # Header + data row
        self.assertIn("entity_type", lines[0])
        self.assertIn("entity_id", lines[0])
        self.assertIn("mns_page", lines[1])
        self.assertIn("test123", lines[1])

    def test_format_invalid_type(self) -> None:
        """Testing invalid format type raises ValueError."""
        with self.assertRaises(ValueError) as context:
            format_output(self.sample_result, "invalid")
        self.assertIn("Unknown output format", str(context.exception))


class Test_Exit_Codes(unittest.TestCase):
    """Testing exit code constants."""

    def test_exit_codes_defined(self) -> None:
        """Testing all exit codes are defined correctly."""
        self.assertEqual(EXIT_SUCCESS, 0)
        self.assertEqual(EXIT_VALIDATION_ERROR, 1)
        self.assertEqual(EXIT_RUNTIME_ERROR, 2)
        self.assertEqual(EXIT_INTERNAL_ERROR, 3)


if __name__ == "__main__":
    unittest.main()

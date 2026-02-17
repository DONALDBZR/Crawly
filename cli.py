"""
CLI module for Crawly scraping infrastructure.

This module provides command-line interface functionality for executing
scraping operations using the Scraper_Orchestrator and registered strategies.

Exit Codes:
    0: Success - Scraping completed successfully
    1: Validation Error - Invalid arguments or configuration
    2: Runtime Error - Network error, parsing failure, or strategy execution error
    3: Internal Error - Unexpected exception or system error

Author:
    Darkness4869
"""

from __future__ import annotations
import argparse
import sys
import json
import os
import csv
import io
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from Models.ScraperOrchestrator import Scraper_Orchestrator
from Models.Logger import Crawly_Logger
from Models.LoggerConfigurator import Logger_Configurator
from Strategies import STRATEGY_REGISTRY
from Errors.Scraper import Scraper_Exception

# Exit codes
EXIT_SUCCESS = 0
EXIT_VALIDATION_ERROR = 1
EXIT_RUNTIME_ERROR = 2
EXIT_INTERNAL_ERROR = 3


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Creating the CLI argument parser with all required and optional arguments.

    Returns:
        argparse.ArgumentParser: Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="crawly",
        description="Crawly - Data scraping and normalization service",
        epilog="For more information, see CLI_ARCHITECTURE.md",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Required arguments
    parser.add_argument(
        "--url", "-u",
        type=str,
        required=True,
        help="Target URL to scrape (required)"
    )

    # Strategy selection
    parser.add_argument(
        "--strategy", "-s",
        type=str,
        default="mns",
        choices=list(STRATEGY_REGISTRY.keys()),
        help="Scraping strategy to use (default: mns)"
    )

    # Logging configuration
    parser.add_argument(
        "--log-level", "-l",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARN", "ERROR"],
        help="Logging level (default: INFO)"
    )

    # Output configuration
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="-",
        help="Output file path, or '-' for stdout (default: stdout)"
    )

    parser.add_argument(
        "--output-format", "-f",
        type=str,
        default="json",
        choices=["json", "pretty", "csv"],
        help="Output format (default: json)"
    )

    # Execution control
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Validate configuration without executing scrape"
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress non-error output to stdout"
    )

    # Scraper configuration
    parser.add_argument(
        "--max-attempts", "-m",
        type=int,
        default=3,
        help="Maximum retry attempts for fetch (default: 3)"
    )

    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=10,
        help="HTTP request timeout in seconds (default: 10)"
    )

    # Environment configuration
    parser.add_argument(
        "--config", "-c",
        type=str,
        default=".env",
        help="Path to environment configuration file (default: .env)"
    )

    # Strategy-specific overrides
    parser.add_argument(
        "--headers", "-H",
        type=str,
        default=None,
        help="JSON string of HTTP headers (e.g., '{\"User-Agent\": \"...\"}')"
    )

    parser.add_argument(
        "--selectors", "-S",
        type=str,
        default=None,
        help="JSON string of CSS selectors (e.g., '{\"title\": \"h1\"}')"
    )

    # Version
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="Crawly 0.1.0"
    )

    return parser


def validate_arguments(args: argparse.Namespace) -> None:
    """
    Validating CLI arguments for consistency and required values.

    Procedures:
        1. Check if URL is provided and non-empty
        2. Validate config file exists if not default
        3. Validate JSON strings (headers, selectors) if provided
        4. Validate numeric ranges (max_attempts > 0, timeout > 0)

    Parameters:
        args (argparse.Namespace): Parsed command-line arguments.

    Returns:
        None

    Raises:
        ValueError: If validation fails with descriptive message.
    """
    # URL validation
    if not args.url or not args.url.strip():
        raise ValueError("URL cannot be empty")

    # Config file validation (skip if it's the default and doesn't exist)
    if args.config != ".env" and not os.path.isfile(args.config):
        raise ValueError(f"Config file not found: {args.config}")

    # JSON validation
    if args.headers:
        try:
            json.loads(args.headers)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON for --headers: {e}")

    if args.selectors:
        try:
            json.loads(args.selectors)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON for --selectors: {e}")

    # Numeric validations
    if args.max_attempts <= 0:
        raise ValueError("--max-attempts must be positive")

    if args.timeout <= 0:
        raise ValueError("--timeout must be positive")


def build_context(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Building execution context dictionary from CLI arguments.

    Procedures:
        1. Create base context with url, timeout, method
        2. Parse and add headers if provided
        3. Parse and add selectors if provided
        4. Add any additional strategy-specific parameters

    Parameters:
        args (argparse.Namespace): Parsed command-line arguments.

    Returns:
        Dict[str, Any]: Context dictionary for strategy execution.
    """
    context: Dict[str, Any] = {
        "url": args.url,
        "timeout": args.timeout,
        "method": "GET",
    }

    # Add optional headers
    if args.headers:
        context["headers"] = json.loads(args.headers)

    # Add optional selectors
    if args.selectors:
        context["selectors"] = json.loads(args.selectors)

    return context


def initialize_logger(log_level: str) -> Crawly_Logger:
    """
    Initializing logger with specified log level.

    Procedures:
        1. Create Logger_Configurator with default settings
        2. Create Crawly_Logger with configurator
        3. Set log level on underlying logger

    Parameters:
        log_level (str): Logging level (DEBUG, INFO, WARN, ERROR).

    Returns:
        Crawly_Logger: Configured logger instance.
    """
    import logging

    # Map string level to logging constant
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARN": logging.WARNING,
        "ERROR": logging.ERROR,
    }

    configurator = Logger_Configurator()
    logger = Crawly_Logger("crawly.cli", configurator)
    logger.getLogger().setLevel(level_map[log_level])

    return logger


def load_strategy(strategy_name: str, logger: Crawly_Logger) -> Any:
    """
    Loading and instantiating strategy from registry.

    Procedures:
        1. Look up strategy class in STRATEGY_REGISTRY
        2. Instantiate strategy with default parameters
        3. Return strategy instance

    Parameters:
        strategy_name (str): Name of strategy to load.
        logger (Crawly_Logger): Logger instance for debug output.

    Returns:
        Scraper_Strategy: Instantiated strategy.

    Raises:
        KeyError: If strategy not found in registry.
    """
    logger.debug(f"Loading strategy: {strategy_name}")

    strategy_class = STRATEGY_REGISTRY.get(strategy_name)
    if not strategy_class:
        available = ", ".join(STRATEGY_REGISTRY.keys())
        raise KeyError(
            f"Unknown strategy '{strategy_name}'. "
            f"Available: {available}"
        )

    strategy = strategy_class()
    logger.debug(f"Strategy loaded: {strategy.identifier()}")

    return strategy


def format_output(result: Dict[str, Any], format_type: str) -> str:
    """
    Formatting scraping result according to specified format.

    Procedures:
        1. Check format type
        2. Convert result to requested format
        3. Return formatted string

    Parameters:
        result (Dict[str, Any]): Normalized scraping result.
        format_type (str): Output format (json, pretty, csv).

    Returns:
        str: Formatted output string.
    """
    if format_type == "json":
        return json.dumps(result, indent=2, ensure_ascii=False)

    elif format_type == "pretty":
        lines = [
            "─" * 50,
            f"Scrape Result: {result.get('entity_type', 'unknown')}",
            "─" * 50,
            f"Entity ID:    {result.get('entity_id', 'N/A')}",
            f"Timestamp:    {result.get('timestamp', 'N/A')}",
        ]

        data = result.get("data", {})
        if data:
            lines.append("─" * 50)
            lines.append("Data:")
            for key, value in data.items():
                if isinstance(value, dict):
                    lines.append(f"  {key}:")
                    for k, v in value.items():
                        lines.append(f"    {k}: {v}")
                else:
                    lines.append(f"  {key}: {value}")

        lines.append("─" * 50)
        return "\n".join(lines)

    elif format_type == "csv":
        # Flatten nested structure for CSV
        flat = {
            "entity_type": result.get("entity_type", ""),
            "entity_id": result.get("entity_id", ""),
            "timestamp": result.get("timestamp", ""),
        }

        # Add data fields
        data = result.get("data", {})
        for key, value in data.items():
            if isinstance(value, dict):
                for k, v in value.items():
                    flat[f"{key}_{k}"] = v
            else:
                flat[key] = value

        # Generate CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=flat.keys())
        writer.writeheader()
        writer.writerow(flat)
        return output.getvalue()

    else:
        raise ValueError(f"Unknown output format: {format_type}")


def write_output(content: str, output_path: str, quiet: bool) -> None:
    """
    Writing formatted output to file or stdout.

    Procedures:
        1. If output is stdout and not quiet, print to stdout
        2. If output is file path, write to file (overwrite)
        3. Handle write errors gracefully

    Parameters:
        content (str): Formatted output content.
        output_path (str): Output destination ('-' for stdout, or file path).
        quiet (bool): Whether to suppress stdout output.

    Returns:
        None

    Raises:
        IOError: If file write fails.
    """
    if output_path == "-":
        if not quiet:
            print(content)
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
            f.write("\n")
        if not quiet:
            print(f"Output written to: {output_path}", file=sys.stderr)


def execute_dry_run(
    args: argparse.Namespace,
    context: Dict[str, Any],
    logger: Crawly_Logger
) -> None:
    """
    Executing dry-run mode to validate configuration.

    Procedures:
        1. Log configuration summary
        2. Log context dictionary
        3. Validate strategy can be loaded
        4. Exit successfully

    Parameters:
        args (argparse.Namespace): Parsed arguments.
        context (Dict[str, Any]): Built execution context.
        logger (Crawly_Logger): Logger instance.

    Returns:
        None
    """
    if not args.quiet:
        print("=== DRY RUN MODE ===", file=sys.stderr)
        print(f"Strategy:     {args.strategy}", file=sys.stderr)
        print(f"URL:          {args.url}", file=sys.stderr)
        print(f"Timeout:      {args.timeout}s", file=sys.stderr)
        print(f"Max Attempts: {args.max_attempts}", file=sys.stderr)
        print(f"Log Level:    {args.log_level}", file=sys.stderr)
        print(f"Output:       {args.output}", file=sys.stderr)
        print(f"Format:       {args.output_format}", file=sys.stderr)
        print("\nContext:", file=sys.stderr)
        print(json.dumps(context, indent=2), file=sys.stderr)
        print("\n✓ Configuration valid", file=sys.stderr)

    logger.inform("Dry-run completed successfully")


def execute_scrape(
    args: argparse.Namespace,
    context: Dict[str, Any],
    logger: Crawly_Logger
) -> Dict[str, Any]:
    """
    Executing scraping operation with orchestrator.

    Procedures:
        1. Load strategy from registry
        2. Create Scraper_Orchestrator with strategy and logger
        3. Execute orchestrator.run(context)
        4. Return normalized result

    Parameters:
        args (argparse.Namespace): Parsed arguments.
        context (Dict[str, Any]): Execution context.
        logger (Crawly_Logger): Logger instance.

    Returns:
        Dict[str, Any]: Normalized scraping result.

    Raises:
        Scraper_Exception: On scraping failures.
    """
    logger.inform(f"Starting scrape: {args.url}")

    # Load strategy
    strategy = load_strategy(args.strategy, logger)

    # Create orchestrator
    orchestrator = Scraper_Orchestrator(
        strategy=strategy,
        logger=logger,
        max_attempts=args.max_attempts,
        backoff_base_seconds=0.5
    )

    # Execute scrape
    result = orchestrator.run(context)

    # Check for empty result (orchestrator returns {} on failure)
    if not result:
        raise Scraper_Exception(
            "Scraping failed - orchestrator returned empty result",
            code=500
        )

    logger.inform(f"Scrape completed: {result.get('entity_id', 'unknown')}")
    return result


def main() -> None:
    """
    Main entry point for Crawly CLI.

    Procedures:
        1. Parse command-line arguments
        2. Load environment configuration
        3. Validate environment variables (startup checkpoint)
        4. Validate arguments
        5. Initialize logger
        6. Build execution context
        7. Execute dry-run or actual scrape
        8. Format and write output
        9. Handle errors and exit with appropriate code

    Returns:
        None (exits with status code)
    """
    try:
        # Parse arguments
        parser = create_argument_parser()
        args = parser.parse_args()

        # Load environment
        if os.path.isfile(args.config):
            load_dotenv(args.config)

        # Validate environment variables before any side effects
        from Models.EnvValidator import Environment_Validator
        validation = Environment_Validator.validate_environment(require_database=False)
        
        if not validation.success:
            for error in validation.errors:
                print(f"❌ Configuration Error: {error}", file=sys.stderr)
            sys.exit(EXIT_VALIDATION_ERROR)
        
        # Log warnings if present
        if validation.warnings and not args.quiet:
            for warning in validation.warnings:
                print(f"⚠️  {warning}", file=sys.stderr)

        # Validate arguments
        validate_arguments(args)

        # Initialize logger
        logger = initialize_logger(args.log_level)
        logger.debug("CLI initialized")

        # Build context
        context = build_context(args)
        logger.debug(f"Context built: {context}")

        # Execute dry-run or scrape
        if args.dry_run:
            execute_dry_run(args, context, logger)
            sys.exit(EXIT_SUCCESS)

        # Execute scrape
        result = execute_scrape(args, context, logger)

        # Format output
        formatted = format_output(result, args.output_format)

        # Write output
        write_output(formatted, args.output, args.quiet)

        logger.inform("CLI execution completed successfully")
        sys.exit(EXIT_SUCCESS)

    except ValueError as e:
        # Validation error
        print(f"❌ Validation Error: {e}", file=sys.stderr)
        sys.exit(EXIT_VALIDATION_ERROR)

    except KeyError as e:
        # Missing required key or unknown strategy
        print(f"❌ Configuration Error: {e}", file=sys.stderr)
        sys.exit(EXIT_VALIDATION_ERROR)

    except Scraper_Exception as e:
        # Runtime scraping error
        print(f"❌ Scraping Error: {e.message}", file=sys.stderr)
        print(f"   Error Code: {e.code}", file=sys.stderr)
        if hasattr(e, 'file') and hasattr(e, 'line'):
            print(f"   Location: {e.file}:{e.line}", file=sys.stderr)
        sys.exit(EXIT_RUNTIME_ERROR)

    except Exception as e:
        # Unexpected internal error
        import traceback
        print(f"❌ Internal Error: {e}", file=sys.stderr)
        print(f"   Please report this issue with log excerpt from Logs/Crawly.log", file=sys.stderr)
        print(f"\nTraceback:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(EXIT_INTERNAL_ERROR)


if __name__ == "__main__":
    main()

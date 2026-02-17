"""
Integration tests for CLI startup environment variable validation.

Tests that validation happens at application startup before any side effects.

Author:
    Darkness4869
"""

from __future__ import annotations
import unittest
import subprocess
import os
import sys
from typing import Tuple


class Test_CLI_Startup_Validation(unittest.TestCase):
    """Testing CLI startup validation integration."""

    def run_cli(self, env_vars: dict, extra_args: list = None) -> Tuple[int, str, str]:
        """
        Running CLI with specified environment variables.
        
        Parameters:
            env_vars (dict): Environment variables to set
            extra_args (list): Additional CLI arguments
        
        Returns:
            Tuple[int, str, str]: (exit_code, stdout, stderr)
        """
        # Create environment with test variables
        test_env = os.environ.copy()
        # Clear all env vars that might interfere
        for key in ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME', 
                    'DB_POOL_SIZE', 'DB_POOL_NAME', 'DB_POOL_RESET_SESSION', 'DB_USE_PURE',
                    'LOG_DIRECTORY', 'LOG_FILE_NAME']:
            test_env.pop(key, None)
        
        # Add test environment variables
        test_env.update(env_vars)
        
        # Build command
        cmd = [sys.executable, 'main.py', '--url', 'http://example.com', '--dry-run']
        if extra_args:
            cmd.extend(extra_args)
        
        # Run CLI
        result = subprocess.run(
            cmd,
            env=test_env,
            capture_output=True,
            text=True,
            cwd='/mnt/Data/Crawly'
        )
        
        return result.returncode, result.stdout, result.stderr

    def test_success_path_with_valid_config(self) -> None:
        """Testing CLI starts successfully with valid configuration."""
        env_vars = {
            'LOG_DIRECTORY': './Logs',
            'LOG_FILE_NAME': 'Crawly.log'
        }
        
        exit_code, stdout, stderr = self.run_cli(env_vars)
        
        self.assertEqual(exit_code, 0, f"CLI should succeed. stderr: {stderr}, stdout: {stdout}")
        # Dry run output goes to stderr
        self.assertIn("DRY RUN MODE", stderr)
        self.assertNotIn("Configuration Error", stderr)

    def test_missing_logger_config_uses_defaults(self) -> None:
        """Testing CLI succeeds when logger config missing (uses defaults)."""
        env_vars = {}  # No logger config
        
        exit_code, stdout, stderr = self.run_cli(env_vars)
        
        self.assertEqual(exit_code, 0, f"CLI should succeed with defaults. stderr: {stderr}, stdout: {stdout}")
        # Dry run output goes to stderr
        self.assertIn("DRY RUN MODE", stderr)

    def test_empty_log_file_name_fails_fast(self) -> None:
        """Testing CLI fails fast when LOG_FILE_NAME is empty."""
        env_vars = {
            'LOG_FILE_NAME': ''
        }
        
        exit_code, stdout, stderr = self.run_cli(env_vars)
        
        self.assertEqual(exit_code, 1, "CLI should exit with code 1 (validation error)")
        self.assertIn("Configuration Error", stderr)
        self.assertIn("LOG_FILE_NAME", stderr)
        self.assertIn("cannot be empty", stderr)

    def test_empty_log_directory_fails_fast(self) -> None:
        """Testing CLI fails fast when LOG_DIRECTORY is empty."""
        env_vars = {
            'LOG_DIRECTORY': ''
        }
        
        exit_code, stdout, stderr = self.run_cli(env_vars)
        
        self.assertEqual(exit_code, 1, "CLI should exit with code 1 (validation error)")
        self.assertIn("Configuration Error", stderr)
        self.assertIn("LOG_DIRECTORY", stderr)
        self.assertIn("cannot be empty", stderr)

    def test_validation_happens_before_logging_initialization(self) -> None:
        """Testing validation happens before logger initialization."""
        env_vars = {
            'LOG_FILE_NAME': ''  # Invalid config
        }
        
        exit_code, stdout, stderr = self.run_cli(env_vars)
        
        # Should fail fast in validation, not in logger initialization
        self.assertEqual(exit_code, 1)
        self.assertIn("Configuration Error", stderr)
        # Should not reach the point where dry-run output is shown
        self.assertNotIn("DRY RUN MODE", stderr)

    def test_multiple_validation_errors_are_shown(self) -> None:
        """Testing multiple validation errors are all reported."""
        env_vars = {
            'LOG_DIRECTORY': '',
            'LOG_FILE_NAME': ''
        }
        
        exit_code, stdout, stderr = self.run_cli(env_vars)
        
        self.assertEqual(exit_code, 1)
        # Both errors should be shown
        stderr_lines = stderr.split('\n')
        error_lines = [line for line in stderr_lines if 'Configuration Error' in line]
        self.assertGreaterEqual(len(error_lines), 2, "Should show both validation errors")

    def test_quiet_flag_still_shows_validation_errors(self) -> None:
        """Testing validation errors shown even with --quiet flag."""
        env_vars = {
            'LOG_FILE_NAME': ''
        }
        
        exit_code, stdout, stderr = self.run_cli(env_vars, extra_args=['--quiet'])
        
        self.assertEqual(exit_code, 1)
        self.assertIn("Configuration Error", stderr)
        self.assertIn("LOG_FILE_NAME", stderr)


class Test_CLI_Startup_Validation_Database_Not_Required(unittest.TestCase):
    """Testing CLI does not require database configuration."""

    def test_cli_succeeds_without_database_vars(self) -> None:
        """Testing CLI succeeds without any database environment variables."""
        test_env = os.environ.copy()
        
        # Explicitly remove DB vars
        for key in ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']:
            test_env.pop(key, None)
        
        cmd = [sys.executable, 'main.py', '--url', 'http://example.com', '--dry-run']
        
        result = subprocess.run(
            cmd,
            env=test_env,
            capture_output=True,
            text=True,
            cwd='/mnt/Data/Crawly'
        )
        
        self.assertEqual(result.returncode, 0, 
                        f"CLI should succeed without DB config. stderr: {result.stderr}, stdout: {result.stdout}")
        # Dry run output goes to stderr
        self.assertIn("DRY RUN MODE", result.stderr)


class Test_Database_Validation_When_Required(unittest.TestCase):
    """Testing database validation for programmatic API usage."""

    def test_database_validation_fails_when_required_vars_missing(self) -> None:
        """Testing database validation fails when required vars missing."""
        from Models.EnvValidator import Environment_Validator
        import os
        
        # Clear DB vars
        original_env = {}
        for key in ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']:
            original_env[key] = os.environ.pop(key, None)
        
        try:
            result = Environment_Validator.validate_environment(require_database=True)
            
            self.assertFalse(result.success)
            self.assertTrue(any('DB_HOST' in err for err in result.errors))
            self.assertTrue(any('DB_USER' in err for err in result.errors))
            self.assertTrue(any('DB_PASSWORD' in err for err in result.errors))
            self.assertTrue(any('DB_NAME' in err for err in result.errors))
        finally:
            # Restore original environment
            for key, value in original_env.items():
                if value is not None:
                    os.environ[key] = value

    def test_database_validation_invalid_pool_size(self) -> None:
        """Testing database validation fails with invalid pool size."""
        from Models.EnvValidator import Environment_Validator
        import os
        
        # Set up environment
        original_env = {
            'DB_HOST': os.environ.get('DB_HOST'),
            'DB_POOL_SIZE': os.environ.get('DB_POOL_SIZE')
        }
        
        os.environ['DB_HOST'] = 'localhost'
        os.environ['DB_USER'] = 'testuser'
        os.environ['DB_PASSWORD'] = 'testpass'
        os.environ['DB_NAME'] = 'testdb'
        os.environ['DB_POOL_SIZE'] = 'not_a_number'
        
        try:
            result = Environment_Validator.validate_environment(require_database=True)
            
            self.assertFalse(result.success)
            self.assertTrue(any('DB_POOL_SIZE' in err and 'integer' in err 
                              for err in result.errors))
        finally:
            # Restore original environment
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_database_validation_pool_size_below_minimum(self) -> None:
        """Testing database validation fails with pool size < 1."""
        from Models.EnvValidator import Environment_Validator
        import os
        
        os.environ['DB_HOST'] = 'localhost'
        os.environ['DB_USER'] = 'testuser'
        os.environ['DB_PASSWORD'] = 'testpass'
        os.environ['DB_NAME'] = 'testdb'
        os.environ['DB_POOL_SIZE'] = '0'
        
        result = Environment_Validator.validate_environment(require_database=True)
        
        self.assertFalse(result.success)
        self.assertTrue(any('DB_POOL_SIZE' in err and '>=' in err 
                          for err in result.errors))

    def test_database_validation_invalid_boolean(self) -> None:
        """Testing database validation fails with invalid boolean value."""
        from Models.EnvValidator import Environment_Validator
        import os
        
        os.environ['DB_HOST'] = 'localhost'
        os.environ['DB_USER'] = 'testuser'
        os.environ['DB_PASSWORD'] = 'testpass'
        os.environ['DB_NAME'] = 'testdb'
        os.environ['DB_USE_PURE'] = 'maybe'
        
        result = Environment_Validator.validate_environment(require_database=True)
        
        self.assertFalse(result.success)
        self.assertTrue(any('DB_USE_PURE' in err for err in result.errors))

    def test_database_validation_success_with_all_valid(self) -> None:
        """Testing database validation succeeds with all valid values."""
        from Models.EnvValidator import Environment_Validator
        import os
        
        os.environ['DB_HOST'] = 'localhost'
        os.environ['DB_USER'] = 'testuser'
        os.environ['DB_PASSWORD'] = 'testpass'
        os.environ['DB_NAME'] = 'testdb'
        os.environ['DB_POOL_SIZE'] = '10'
        os.environ['DB_USE_PURE'] = 'true'
        
        result = Environment_Validator.validate_environment(require_database=True)
        
        self.assertTrue(result.success)
        self.assertEqual(result.errors, [])
        self.assertIsNotNone(result.validated_config)
        self.assertEqual(result.validated_config['DB_HOST'], 'localhost')
        self.assertEqual(result.validated_config['DB_POOL_SIZE'], 10)


if __name__ == "__main__":
    unittest.main()

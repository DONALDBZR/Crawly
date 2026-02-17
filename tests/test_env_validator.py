"""
Unit tests for Environment_Validator.

Tests environment variable validation at application startup.

Author:
    Darkness4869
"""

from __future__ import annotations
import unittest
from unittest.mock import patch
from Models.EnvValidator import Environment_Validator, Validation_Result


class Test_Validate_Required_Vars(unittest.TestCase):
    """Testing Environment_Validator._validate_required_vars() method."""

    @patch('Models.EnvValidator.getenv')
    def test_all_required_vars_present(self, mock_getenv) -> None:
        """Testing validation passes when all required vars present."""
        mock_getenv.side_effect = lambda key: "value"
        
        errors = Environment_Validator._validate_required_vars(["VAR1", "VAR2"])
        
        self.assertEqual(errors, [])

    @patch('Models.EnvValidator.getenv')
    def test_missing_required_var(self, mock_getenv) -> None:
        """Testing validation fails when required var missing."""
        mock_getenv.side_effect = lambda key: None
        
        errors = Environment_Validator._validate_required_vars(["MISSING_VAR"])
        
        self.assertEqual(len(errors), 1)
        self.assertIn("MISSING_VAR", errors[0])
        self.assertIn("Missing required", errors[0])

    @patch('Models.EnvValidator.getenv')
    def test_empty_required_var(self, mock_getenv) -> None:
        """Testing validation fails when required var is empty string."""
        mock_getenv.side_effect = lambda key: "   "
        
        errors = Environment_Validator._validate_required_vars(["EMPTY_VAR"])
        
        self.assertEqual(len(errors), 1)
        self.assertIn("EMPTY_VAR", errors[0])
        self.assertIn("cannot be empty", errors[0])


class Test_Validate_Int_Var(unittest.TestCase):
    """Testing Environment_Validator._validate_int_var() method."""

    @patch('Models.EnvValidator.getenv')
    def test_int_var_not_present_uses_default(self, mock_getenv) -> None:
        """Testing uses default when var not present."""
        mock_getenv.return_value = None
        
        value, errors, warnings = Environment_Validator._validate_int_var("VAR", default=42)
        
        self.assertEqual(value, 42)
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("default", warnings[0].lower())

    @patch('Models.EnvValidator.getenv')
    def test_int_var_valid_value(self, mock_getenv) -> None:
        """Testing parses valid integer correctly."""
        mock_getenv.return_value = "123"
        
        value, errors, warnings = Environment_Validator._validate_int_var("VAR", default=0)
        
        self.assertEqual(value, 123)
        self.assertEqual(errors, [])

    @patch('Models.EnvValidator.getenv')
    def test_int_var_invalid_format(self, mock_getenv) -> None:
        """Testing fails on non-integer value."""
        mock_getenv.return_value = "not_an_int"
        
        value, errors, warnings = Environment_Validator._validate_int_var("VAR", default=0)
        
        self.assertIsNone(value)
        self.assertEqual(len(errors), 1)
        self.assertIn("must be an integer", errors[0])

    @patch('Models.EnvValidator.getenv')
    def test_int_var_below_minimum(self, mock_getenv) -> None:
        """Testing fails when value below minimum."""
        mock_getenv.return_value = "5"
        
        value, errors, warnings = Environment_Validator._validate_int_var(
            "VAR", default=0, min_val=10
        )
        
        self.assertEqual(value, 5)
        self.assertEqual(len(errors), 1)
        self.assertIn(">= 10", errors[0])

    @patch('Models.EnvValidator.getenv')
    def test_int_var_above_maximum(self, mock_getenv) -> None:
        """Testing fails when value above maximum."""
        mock_getenv.return_value = "150"
        
        value, errors, warnings = Environment_Validator._validate_int_var(
            "VAR", default=0, max_val=100
        )
        
        self.assertEqual(value, 150)
        self.assertEqual(len(errors), 1)
        self.assertIn("<= 100", errors[0])

    @patch('Models.EnvValidator.getenv')
    def test_int_var_suspiciously_high_warning(self, mock_getenv) -> None:
        """Testing warning for suspiciously high values."""
        mock_getenv.return_value = "999"
        
        value, errors, warnings = Environment_Validator._validate_int_var("VAR", default=0)
        
        self.assertEqual(value, 999)
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("unusually high", warnings[0])

    @patch('Models.EnvValidator.getenv')
    def test_int_var_empty_string(self, mock_getenv) -> None:
        """Testing fails on empty string."""
        mock_getenv.return_value = ""
        
        value, errors, warnings = Environment_Validator._validate_int_var("VAR", default=0)
        
        self.assertIsNone(value)
        self.assertEqual(len(errors), 1)
        self.assertIn("cannot be empty", errors[0])


class Test_Validate_Bool_Var(unittest.TestCase):
    """Testing Environment_Validator._validate_bool_var() method."""

    @patch('Models.EnvValidator.getenv')
    def test_bool_var_not_present_uses_default(self, mock_getenv) -> None:
        """Testing uses default when var not present."""
        mock_getenv.return_value = None
        
        value, errors, warnings = Environment_Validator._validate_bool_var("VAR", default=True)
        
        self.assertTrue(value)
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)

    @patch('Models.EnvValidator.getenv')
    def test_bool_var_parses_true_variants(self, mock_getenv) -> None:
        """Testing parses various 'true' representations."""
        for true_value in ["true", "TRUE", "True", "1", "yes", "YES"]:
            mock_getenv.return_value = true_value
            value, errors, warnings = Environment_Validator._validate_bool_var("VAR", default=False)
            self.assertTrue(value, f"Failed to parse '{true_value}' as True")
            self.assertEqual(errors, [])

    @patch('Models.EnvValidator.getenv')
    def test_bool_var_parses_false_variants(self, mock_getenv) -> None:
        """Testing parses various 'false' representations."""
        for false_value in ["false", "FALSE", "False", "0", "no", "NO"]:
            mock_getenv.return_value = false_value
            value, errors, warnings = Environment_Validator._validate_bool_var("VAR", default=True)
            self.assertFalse(value, f"Failed to parse '{false_value}' as False")
            self.assertEqual(errors, [])

    @patch('Models.EnvValidator.getenv')
    def test_bool_var_invalid_value(self, mock_getenv) -> None:
        """Testing fails on invalid boolean value."""
        mock_getenv.return_value = "maybe"
        
        value, errors, warnings = Environment_Validator._validate_bool_var("VAR", default=False)
        
        self.assertFalse(value)  # Should return default
        self.assertEqual(len(errors), 1)
        self.assertIn("must be 'true' or 'false'", errors[0])

    @patch('Models.EnvValidator.getenv')
    def test_bool_var_empty_string(self, mock_getenv) -> None:
        """Testing fails on empty string."""
        mock_getenv.return_value = ""
        
        value, errors, warnings = Environment_Validator._validate_bool_var("VAR", default=False)
        
        self.assertEqual(len(errors), 1)
        self.assertIn("cannot be empty", errors[0])


class Test_Validate_String_Var(unittest.TestCase):
    """Testing Environment_Validator._validate_string_var() method."""

    @patch('Models.EnvValidator.getenv')
    def test_string_var_not_present_uses_default(self, mock_getenv) -> None:
        """Testing uses default when var not present."""
        mock_getenv.return_value = None
        
        value, errors, warnings = Environment_Validator._validate_string_var("VAR", "default")
        
        self.assertEqual(value, "default")
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)

    @patch('Models.EnvValidator.getenv')
    def test_string_var_valid_value(self, mock_getenv) -> None:
        """Testing returns valid string value."""
        mock_getenv.return_value = "test_value"
        
        value, errors, warnings = Environment_Validator._validate_string_var("VAR", "default")
        
        self.assertEqual(value, "test_value")
        self.assertEqual(errors, [])

    @patch('Models.EnvValidator.getenv')
    def test_string_var_empty_not_allowed(self, mock_getenv) -> None:
        """Testing fails on empty string when not allowed."""
        mock_getenv.return_value = ""
        
        value, errors, warnings = Environment_Validator._validate_string_var(
            "VAR", "default", allow_empty=False
        )
        
        self.assertEqual(value, "default")
        self.assertEqual(len(errors), 1)
        self.assertIn("cannot be empty", errors[0])

    @patch('Models.EnvValidator.getenv')
    def test_string_var_empty_allowed(self, mock_getenv) -> None:
        """Testing allows empty string when specified."""
        mock_getenv.return_value = ""
        
        value, errors, warnings = Environment_Validator._validate_string_var(
            "VAR", "default", allow_empty=True
        )
        
        self.assertEqual(value, "")
        self.assertEqual(errors, [])


class Test_Validate_Database_Config(unittest.TestCase):
    """Testing Environment_Validator.validate_database_config() method."""

    @patch('Models.EnvValidator.getenv')
    def test_all_required_db_vars_present(self, mock_getenv) -> None:
        """Testing validation passes with all required DB vars."""
        def getenv_side_effect(key, default=None):
            env_vars = {
                "DB_HOST": "localhost",
                "DB_USER": "user",
                "DB_PASSWORD": "pass",
                "DB_NAME": "db"
            }
            return env_vars.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        
        result = Environment_Validator.validate_database_config()
        
        self.assertTrue(result.success)
        self.assertEqual(result.errors, [])
        self.assertIsNotNone(result.validated_config)
        self.assertEqual(result.validated_config["DB_HOST"], "localhost")

    @patch('Models.EnvValidator.getenv')
    def test_missing_db_host(self, mock_getenv) -> None:
        """Testing validation fails when DB_HOST missing."""
        def getenv_side_effect(key, default=None):
            env_vars = {
                "DB_USER": "user",
                "DB_PASSWORD": "pass",
                "DB_NAME": "db"
            }
            return env_vars.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        
        result = Environment_Validator.validate_database_config()
        
        self.assertFalse(result.success)
        self.assertTrue(any("DB_HOST" in error for error in result.errors))
        self.assertIsNone(result.validated_config)

    @patch('Models.EnvValidator.getenv')
    def test_invalid_pool_size(self, mock_getenv) -> None:
        """Testing validation fails with invalid pool size."""
        def getenv_side_effect(key, default=None):
            env_vars = {
                "DB_HOST": "localhost",
                "DB_USER": "user",
                "DB_PASSWORD": "pass",
                "DB_NAME": "db",
                "DB_POOL_SIZE": "not_a_number"
            }
            return env_vars.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        
        result = Environment_Validator.validate_database_config()
        
        self.assertFalse(result.success)
        self.assertTrue(any("DB_POOL_SIZE" in error and "integer" in error for error in result.errors))

    @patch('Models.EnvValidator.getenv')
    def test_pool_size_below_minimum(self, mock_getenv) -> None:
        """Testing validation fails with pool size < 1."""
        def getenv_side_effect(key, default=None):
            env_vars = {
                "DB_HOST": "localhost",
                "DB_USER": "user",
                "DB_PASSWORD": "pass",
                "DB_NAME": "db",
                "DB_POOL_SIZE": "0"
            }
            return env_vars.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        
        result = Environment_Validator.validate_database_config()
        
        self.assertFalse(result.success)
        self.assertTrue(any("DB_POOL_SIZE" in error and ">=" in error for error in result.errors))

    @patch('Models.EnvValidator.getenv')
    def test_invalid_boolean_config(self, mock_getenv) -> None:
        """Testing validation fails with invalid boolean value."""
        def getenv_side_effect(key, default=None):
            env_vars = {
                "DB_HOST": "localhost",
                "DB_USER": "user",
                "DB_PASSWORD": "pass",
                "DB_NAME": "db",
                "DB_USE_PURE": "maybe"
            }
            return env_vars.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        
        result = Environment_Validator.validate_database_config()
        
        self.assertFalse(result.success)
        self.assertTrue(any("DB_USE_PURE" in error for error in result.errors))

    @patch('Models.EnvValidator.getenv')
    def test_default_values_used(self, mock_getenv) -> None:
        """Testing default values are used and warnings generated."""
        def getenv_side_effect(key, default=None):
            env_vars = {
                "DB_HOST": "localhost",
                "DB_USER": "user",
                "DB_PASSWORD": "pass",
                "DB_NAME": "db"
            }
            return env_vars.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        
        result = Environment_Validator.validate_database_config()
        
        self.assertTrue(result.success)
        self.assertTrue(len(result.warnings) > 0)
        self.assertTrue(any("DB_POOL_SIZE" in warning for warning in result.warnings))


class Test_Validate_Logger_Config(unittest.TestCase):
    """Testing Environment_Validator.validate_logger_config() method."""

    @patch('Models.EnvValidator.getenv')
    def test_logger_config_with_defaults(self, mock_getenv) -> None:
        """Testing logger validation uses defaults when vars not present."""
        mock_getenv.return_value = None
        
        result = Environment_Validator.validate_logger_config()
        
        self.assertTrue(result.success)
        self.assertEqual(result.errors, [])
        self.assertIsNotNone(result.validated_config)
        self.assertEqual(result.validated_config["LOG_DIRECTORY"], "./Logs")
        self.assertEqual(result.validated_config["LOG_FILE_NAME"], "Crawly.log")

    @patch('Models.EnvValidator.getenv')
    def test_logger_config_with_custom_values(self, mock_getenv) -> None:
        """Testing logger validation with custom values."""
        def getenv_side_effect(key, default=None):
            env_vars = {
                "LOG_DIRECTORY": "/var/log/crawly",
                "LOG_FILE_NAME": "custom.log"
            }
            return env_vars.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        
        result = Environment_Validator.validate_logger_config()
        
        self.assertTrue(result.success)
        self.assertEqual(result.validated_config["LOG_DIRECTORY"], "/var/log/crawly")
        self.assertEqual(result.validated_config["LOG_FILE_NAME"], "custom.log")


class Test_Validate_Environment(unittest.TestCase):
    """Testing Environment_Validator.validate_environment() main entry point."""

    @patch('Models.EnvValidator.getenv')
    def test_validate_without_database(self, mock_getenv) -> None:
        """Testing validation succeeds without database when not required."""
        mock_getenv.return_value = None
        
        result = Environment_Validator.validate_environment(require_database=False)
        
        self.assertTrue(result.success)
        self.assertEqual(result.errors, [])

    @patch('Models.EnvValidator.getenv')
    def test_validate_with_database_missing_vars(self, mock_getenv) -> None:
        """Testing validation fails when database required but vars missing."""
        mock_getenv.return_value = None
        
        result = Environment_Validator.validate_environment(require_database=True)
        
        self.assertFalse(result.success)
        self.assertTrue(any("DB_HOST" in error for error in result.errors))
        self.assertTrue(any("DB_USER" in error for error in result.errors))

    @patch('Models.EnvValidator.getenv')
    def test_validate_with_database_all_present(self, mock_getenv) -> None:
        """Testing validation succeeds when database required and all vars present."""
        def getenv_side_effect(key, default=None):
            env_vars = {
                "DB_HOST": "localhost",
                "DB_USER": "user",
                "DB_PASSWORD": "pass",
                "DB_NAME": "db"
            }
            return env_vars.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        
        result = Environment_Validator.validate_environment(require_database=True)
        
        self.assertTrue(result.success)
        self.assertEqual(result.errors, [])
        self.assertIn("DB_HOST", result.validated_config)
        self.assertIn("LOG_DIRECTORY", result.validated_config)

    @patch('Models.EnvValidator.getenv')
    def test_combined_errors_from_both_validators(self, mock_getenv) -> None:
        """Testing combined errors from both logger and database validation."""
        def getenv_side_effect(key, default=None):
            env_vars = {
                "DB_HOST": "localhost",
                # Missing DB_USER, DB_PASSWORD, DB_NAME
                "DB_POOL_SIZE": "invalid"
            }
            return env_vars.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        
        result = Environment_Validator.validate_environment(require_database=True)
        
        self.assertFalse(result.success)
        # Should have errors for missing DB vars
        self.assertTrue(len(result.errors) > 0)


if __name__ == "__main__":
    unittest.main()

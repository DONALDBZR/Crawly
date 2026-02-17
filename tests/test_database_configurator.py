"""
Unit tests for Database_Configurator.

Tests configuration validation and environment loading.

Author:
    Darkness4869
"""

from __future__ import annotations
import unittest
from unittest.mock import patch

from Models.DatabaseConfigurator import Database_Configurator


class Test_Database_Configurator_Manual_Initialization(unittest.TestCase):
    """Testing Database_Configurator manual initialization."""

    def test_initialization_with_all_params(self) -> None:
        """Testing manual initialization with all parameters."""
        config = Database_Configurator(
            host="localhost",
            user="testuser",
            password="testpass",
            database="testdb",
            pool_name="test_pool",
            pool_size=10,
            pool_reset_session=False,
            use_pure=False
        )
        
        self.assertEqual(config.host, "localhost")
        self.assertEqual(config.user, "testuser")
        self.assertEqual(config.password, "testpass")
        self.assertEqual(config.database, "testdb")
        self.assertEqual(config.pool_name, "test_pool")
        self.assertEqual(config.pool_size, 10)
        self.assertFalse(config.pool_reset_session)
        self.assertFalse(config.use_pure)

    def test_default_values_applied(self) -> None:
        """Testing default values are applied correctly."""
        config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db"
        )
        
        self.assertEqual(config.pool_name, "crawly_pool")
        self.assertEqual(config.pool_size, 5)
        self.assertTrue(config.pool_reset_session)
        self.assertTrue(config.use_pure)


class Test_Database_Configurator_From_Environment(unittest.TestCase):
    """Testing Database_Configurator.from_environment() method."""

    @patch('Models.DatabaseConfigurator.getenv')
    def test_from_environment_loads_all_required_vars(self, mock_getenv) -> None:
        """Testing from_environment loads all required environment variables."""
        def getenv_side_effect(key, default=None):
            env_vars = {
                "DB_HOST": "prod.example.com",
                "DB_USER": "produser",
                "DB_PASSWORD": "prodpass",
                "DB_NAME": "proddb",
                "DB_POOL_NAME": "prod_pool",
                "DB_POOL_SIZE": "20",
                "DB_POOL_RESET_SESSION": "false",
                "DB_USE_PURE": "false"
            }
            return env_vars.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        
        config = Database_Configurator.from_environment()
        
        self.assertEqual(config.host, "prod.example.com")
        self.assertEqual(config.user, "produser")
        self.assertEqual(config.password, "prodpass")
        self.assertEqual(config.database, "proddb")
        self.assertEqual(config.pool_name, "prod_pool")
        self.assertEqual(config.pool_size, 20)
        self.assertFalse(config.pool_reset_session)
        self.assertFalse(config.use_pure)

    @patch('Models.DatabaseConfigurator.getenv')
    def test_missing_required_env_var_raises_error(self, mock_getenv) -> None:
        """Testing missing required environment variable raises ValueError."""
        def getenv_side_effect(key, default=None):
            env_vars = {
                "DB_HOST": "localhost",
                "DB_USER": "user",
                # DB_PASSWORD missing
                "DB_NAME": "db"
            }
            return env_vars.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        
        with self.assertRaises(ValueError) as context:
            Database_Configurator.from_environment()
        
        self.assertIn("invalid", str(context.exception).lower())

    @patch('Models.DatabaseConfigurator.getenv')
    def test_pool_size_converts_from_string_to_int(self, mock_getenv) -> None:
        """Testing pool_size is converted from string to int."""
        def getenv_side_effect(key, default=None):
            env_vars = {
                "DB_HOST": "localhost",
                "DB_USER": "user",
                "DB_PASSWORD": "pass",
                "DB_NAME": "db",
                "DB_POOL_SIZE": "15"
            }
            return env_vars.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        
        config = Database_Configurator.from_environment()
        
        self.assertIsInstance(config.pool_size, int)
        self.assertEqual(config.pool_size, 15)

    @patch('Models.DatabaseConfigurator.getenv')
    def test_boolean_flags_parsed_correctly(self, mock_getenv) -> None:
        """Testing boolean flags are parsed correctly."""
        def getenv_side_effect(key, default=None):
            env_vars = {
                "DB_HOST": "localhost",
                "DB_USER": "user",
                "DB_PASSWORD": "pass",
                "DB_NAME": "db",
                "DB_POOL_RESET_SESSION": "false",
                "DB_USE_PURE": "false"
            }
            return env_vars.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        
        config = Database_Configurator.from_environment()
        
        self.assertFalse(config.pool_reset_session)
        self.assertFalse(config.use_pure)


class Test_Database_Configurator_Dict_Methods(unittest.TestCase):
    """Testing Database_Configurator dictionary conversion methods."""

    def setUp(self) -> None:
        """Setting up test fixtures."""
        self.config = Database_Configurator(
            host="localhost",
            user="testuser",
            password="testpass",
            database="testdb",
            pool_name="test_pool",
            pool_size=10
        )

    def test_to_dict_returns_correct_format(self) -> None:
        """Testing to_dict() returns correct format for mysql.connector."""
        result = self.config.to_dict()
        
        self.assertIn("host", result)
        self.assertIn("user", result)
        self.assertIn("password", result)
        self.assertIn("database", result)
        self.assertIn("use_pure", result)
        
        # Should not include pool-specific params
        self.assertNotIn("pool_name", result)
        self.assertNotIn("pool_size", result)
        
        self.assertEqual(result["host"], "localhost")
        self.assertEqual(result["user"], "testuser")

    def test_to_pool_dict_includes_pool_params(self) -> None:
        """Testing to_pool_dict() includes pool parameters."""
        result = self.config.to_pool_dict()
        
        self.assertIn("pool_name", result)
        self.assertIn("pool_size", result)
        self.assertIn("pool_reset_session", result)
        self.assertIn("host", result)
        self.assertIn("user", result)
        self.assertIn("password", result)
        self.assertIn("database", result)
        
        self.assertEqual(result["pool_name"], "test_pool")
        self.assertEqual(result["pool_size"], 10)


if __name__ == "__main__":
    unittest.main()

"""
Unit tests for Database_Handler_Factory.

Tests factory pattern, shared resources, and initialization.

Author:
    Darkness4869
"""

from __future__ import annotations
import unittest
from unittest.mock import Mock, patch, MagicMock

from Models.DatabaseHandlerFactory import Database_Handler_Factory
from Models.DatabaseHandler import Database_Handler
from Models.DatabaseConfigurator import Database_Configurator
from Models.DatabaseConnectionPool import Database_Connection_Pool
from Models.Logger import Crawly_Logger


class Test_Database_Handler_Factory_Initialization(unittest.TestCase):
    """Testing Database_Handler_Factory initialization."""

    def setUp(self) -> None:
        """Setting up test fixtures."""
        # Reset factory state before each test
        Database_Handler_Factory._Database_Handler_Factory__default_pool = None
        Database_Handler_Factory._Database_Handler_Factory__default_config = None
        Database_Handler_Factory._Database_Handler_Factory__default_logger = None

    @patch('Models.DatabaseHandlerFactory.Database_Connection_Pool')
    @patch('Models.DatabaseHandlerFactory.Crawly_Logger')
    def test_initialize_sets_up_defaults(self, mock_logger_class, mock_pool_class) -> None:
        """Testing initialize() sets up default configuration and resources."""
        mock_logger = Mock(spec=Crawly_Logger)
        mock_logger_class.return_value = mock_logger
        
        mock_pool = Mock(spec=Database_Connection_Pool)
        mock_pool_class.return_value = mock_pool
        
        config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db"
        )
        
        Database_Handler_Factory.initialize(config=config, logger=mock_logger)
        
        # Should have set default config and logger
        self.assertIsNotNone(Database_Handler_Factory._Database_Handler_Factory__default_config)
        self.assertIsNotNone(Database_Handler_Factory._Database_Handler_Factory__default_logger)

    @patch('Models.DatabaseHandlerFactory.Database_Connection_Pool')
    @patch('Models.DatabaseHandlerFactory.Crawly_Logger')
    def test_initialize_creates_shared_pool(self, mock_logger_class, mock_pool_class) -> None:
        """Testing initialize() creates a shared connection pool."""
        mock_logger = Mock(spec=Crawly_Logger)
        mock_logger_class.return_value = mock_logger
        
        mock_pool = Mock(spec=Database_Connection_Pool)
        mock_pool_class.return_value = mock_pool
        
        config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db"
        )
        
        Database_Handler_Factory.initialize(config=config, create_pool=True)
        
        # Should have created pool
        self.assertIsNotNone(Database_Handler_Factory._Database_Handler_Factory__default_pool)
        mock_pool_class.assert_called_once()

    @patch('Models.DatabaseHandlerFactory.Crawly_Logger')
    def test_initialize_without_pool(self, mock_logger_class) -> None:
        """Testing initialize(create_pool=False) skips pool creation."""
        mock_logger = Mock(spec=Crawly_Logger)
        mock_logger_class.return_value = mock_logger
        
        config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db"
        )
        
        Database_Handler_Factory.initialize(config=config, create_pool=False)
        
        # Should not have created pool
        self.assertIsNone(Database_Handler_Factory._Database_Handler_Factory__default_pool)
        mock_logger.inform.assert_called()

    @patch('Models.DatabaseHandlerFactory.Database_Configurator')
    @patch('Models.DatabaseHandlerFactory.Crawly_Logger')
    def test_initialize_uses_environment_config_when_none_provided(self, mock_logger_class, mock_config_class) -> None:
        """Testing initialize() uses environment config when none provided."""
        mock_logger = Mock(spec=Crawly_Logger)
        mock_logger_class.return_value = mock_logger
        
        mock_config = Mock(spec=Database_Configurator)
        mock_config_class.from_environment.return_value = mock_config
        
        Database_Handler_Factory.initialize(create_pool=False)
        
        # Should have called from_environment
        mock_config_class.from_environment.assert_called_once()


class Test_Database_Handler_Factory_Create(unittest.TestCase):
    """Testing Database_Handler_Factory.create() method."""

    def setUp(self) -> None:
        """Setting up test fixtures."""
        # Reset factory state before each test
        Database_Handler_Factory._Database_Handler_Factory__default_pool = None
        Database_Handler_Factory._Database_Handler_Factory__default_config = None
        Database_Handler_Factory._Database_Handler_Factory__default_logger = None

    @patch('Models.DatabaseHandlerFactory.Database_Handler')
    @patch('Models.DatabaseHandlerFactory.Database_Connection_Pool')
    @patch('Models.DatabaseHandlerFactory.Crawly_Logger')
    def test_create_returns_handler_with_shared_pool(self, mock_logger_class, mock_pool_class, mock_handler_class) -> None:
        """Testing create() returns handler using shared pool."""
        mock_logger = Mock(spec=Crawly_Logger)
        mock_logger_class.return_value = mock_logger
        
        mock_pool = Mock(spec=Database_Connection_Pool)
        mock_pool_class.return_value = mock_pool
        
        mock_handler = Mock(spec=Database_Handler)
        mock_handler_class.return_value = mock_handler
        
        config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db"
        )
        
        Database_Handler_Factory.initialize(config=config, create_pool=True)
        handler = Database_Handler_Factory.create(use_shared_pool=True)
        
        self.assertIsNotNone(handler)
        # Should have passed shared pool to handler
        mock_handler_class.assert_called_once()

    @patch('Models.DatabaseHandlerFactory.Database_Handler')
    @patch('Models.DatabaseHandlerFactory.Crawly_Logger')
    def test_create_before_initialize_raises_error(self, mock_logger_class, mock_handler_class) -> None:
        """Testing create() before initialize() raises RuntimeError."""
        with self.assertRaises(RuntimeError) as context:
            Database_Handler_Factory.create()
        
        self.assertIn("not been initialized", str(context.exception))

    @patch('Models.DatabaseHandlerFactory.Database_Handler')
    @patch('Models.DatabaseHandlerFactory.Database_Connection_Pool')
    @patch('Models.DatabaseHandlerFactory.Crawly_Logger')
    def test_create_with_custom_config(self, mock_logger_class, mock_pool_class, mock_handler_class) -> None:
        """Testing create() with custom configuration overrides defaults."""
        mock_logger = Mock(spec=Crawly_Logger)
        mock_logger_class.return_value = mock_logger
        
        mock_pool = Mock(spec=Database_Connection_Pool)
        mock_pool_class.return_value = mock_pool
        
        mock_handler = Mock(spec=Database_Handler)
        mock_handler_class.return_value = mock_handler
        
        default_config = Database_Configurator(
            host="default",
            user="user",
            password="pass",
            database="db"
        )
        
        custom_config = Database_Configurator(
            host="custom",
            user="customuser",
            password="custompass",
            database="customdb"
        )
        
        Database_Handler_Factory.initialize(config=default_config, create_pool=True)
        handler = Database_Handler_Factory.create(config=custom_config)
        
        # Should have used custom config
        call_kwargs = mock_handler_class.call_args[1]
        self.assertEqual(call_kwargs['config'], custom_config)

    @patch('Models.DatabaseHandlerFactory.Database_Handler')
    @patch('Models.DatabaseHandlerFactory.Data_Sanitizer')
    @patch('Models.DatabaseHandlerFactory.Database_Connection_Pool')
    @patch('Models.DatabaseHandlerFactory.Crawly_Logger')
    def test_create_with_custom_sanitizer(self, mock_logger_class, mock_pool_class, mock_sanitizer_class, mock_handler_class) -> None:
        """Testing create() with custom sanitizer."""
        mock_logger = Mock(spec=Crawly_Logger)
        mock_logger_class.return_value = mock_logger
        
        mock_pool = Mock(spec=Database_Connection_Pool)
        mock_pool_class.return_value = mock_pool
        
        mock_handler = Mock(spec=Database_Handler)
        mock_handler_class.return_value = mock_handler
        
        custom_sanitizer = Mock()
        
        config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db"
        )
        
        Database_Handler_Factory.initialize(config=config, create_pool=True)
        handler = Database_Handler_Factory.create(sanitizer=custom_sanitizer)
        
        # Should have passed custom sanitizer
        call_kwargs = mock_handler_class.call_args[1]
        self.assertEqual(call_kwargs['sanitizer'], custom_sanitizer)

    @patch('Models.DatabaseHandlerFactory.Database_Handler')
    @patch('Models.DatabaseHandlerFactory.Database_Connection_Pool')
    @patch('Models.DatabaseHandlerFactory.Crawly_Logger')
    def test_create_without_shared_pool(self, mock_logger_class, mock_pool_class, mock_handler_class) -> None:
        """Testing create(use_shared_pool=False) creates new pool."""
        mock_logger = Mock(spec=Crawly_Logger)
        mock_logger_class.return_value = mock_logger
        
        mock_pool = Mock(spec=Database_Connection_Pool)
        mock_pool_class.return_value = mock_pool
        
        mock_handler = Mock(spec=Database_Handler)
        mock_handler_class.return_value = mock_handler
        
        config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db"
        )
        
        Database_Handler_Factory.initialize(config=config, create_pool=True)
        handler = Database_Handler_Factory.create(use_shared_pool=False)
        
        # Should not have passed connection_pool parameter (handler creates its own)
        call_kwargs = mock_handler_class.call_args[1]
        self.assertNotIn('connection_pool', call_kwargs)


class Test_Database_Handler_Factory_Shutdown(unittest.TestCase):
    """Testing Database_Handler_Factory.shutdown() method."""

    def setUp(self) -> None:
        """Setting up test fixtures."""
        # Reset factory state before each test
        Database_Handler_Factory._Database_Handler_Factory__default_pool = None
        Database_Handler_Factory._Database_Handler_Factory__default_config = None
        Database_Handler_Factory._Database_Handler_Factory__default_logger = None

    @patch('Models.DatabaseHandlerFactory.Database_Connection_Pool')
    @patch('Models.DatabaseHandlerFactory.Crawly_Logger')
    def test_shutdown_closes_shared_pool(self, mock_logger_class, mock_pool_class) -> None:
        """Testing shutdown() closes the shared connection pool."""
        mock_logger = Mock(spec=Crawly_Logger)
        mock_logger_class.return_value = mock_logger
        
        mock_pool = Mock(spec=Database_Connection_Pool)
        mock_pool_class.return_value = mock_pool
        
        config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db"
        )
        
        Database_Handler_Factory.initialize(config=config, create_pool=True)
        Database_Handler_Factory.shutdown()
        
        # Should have closed pool
        mock_pool.closePool.assert_called_once()
        
        # Pool should be cleared
        self.assertIsNone(Database_Handler_Factory._Database_Handler_Factory__default_pool)

    @patch('Models.DatabaseHandlerFactory.Crawly_Logger')
    def test_shutdown_logs_event(self, mock_logger_class) -> None:
        """Testing shutdown() logs the shutdown event."""
        mock_logger = Mock(spec=Crawly_Logger)
        mock_logger_class.return_value = mock_logger
        
        config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db"
        )
        
        Database_Handler_Factory.initialize(config=config, create_pool=False)
        Database_Handler_Factory.shutdown()
        
        # Should have logged shutdown
        self.assertTrue(mock_logger.inform.called)


class Test_Database_Handler_Factory_Get_Shared_Pool(unittest.TestCase):
    """Testing Database_Handler_Factory.get_shared_pool() method."""

    def setUp(self) -> None:
        """Setting up test fixtures."""
        # Reset factory state before each test
        Database_Handler_Factory._Database_Handler_Factory__default_pool = None
        Database_Handler_Factory._Database_Handler_Factory__default_config = None
        Database_Handler_Factory._Database_Handler_Factory__default_logger = None

    @patch('Models.DatabaseHandlerFactory.Database_Connection_Pool')
    @patch('Models.DatabaseHandlerFactory.Crawly_Logger')
    def test_get_shared_pool_returns_correct_pool(self, mock_logger_class, mock_pool_class) -> None:
        """Testing get_shared_pool() returns the shared pool."""
        mock_logger = Mock(spec=Crawly_Logger)
        mock_logger_class.return_value = mock_logger
        
        mock_pool = Mock(spec=Database_Connection_Pool)
        mock_pool_class.return_value = mock_pool
        
        config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db"
        )
        
        Database_Handler_Factory.initialize(config=config, create_pool=True)
        pool = Database_Handler_Factory.get_shared_pool()
        
        self.assertEqual(pool, mock_pool)


if __name__ == "__main__":
    unittest.main()

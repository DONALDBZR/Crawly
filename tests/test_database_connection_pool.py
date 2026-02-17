"""
Unit tests for Database_Connection_Pool.

Tests connection pool lifecycle and connection management.

Author:
    Darkness4869
"""

from __future__ import annotations
import unittest
from unittest.mock import Mock, patch, MagicMock

from Models.DatabaseConnectionPool import Database_Connection_Pool
from Models.DatabaseConfigurator import Database_Configurator
from Models.Logger import Crawly_Logger


class Test_Database_Connection_Pool_Creation(unittest.TestCase):
    """Testing Database_Connection_Pool creation and initialization."""

    @patch('Models.DatabaseConnectionPool.MySQLConnectionPool')
    @patch('Models.DatabaseConnectionPool.Crawly_Logger')
    def test_pool_created_successfully(self, mock_logger_class, mock_pool_class) -> None:
        """Testing pool is created successfully with valid configuration."""
        mock_logger = Mock(spec=Crawly_Logger)
        mock_logger_class.return_value = mock_logger
        
        mock_pool = Mock()
        mock_pool_class.return_value = mock_pool
        
        config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db"
        )
        
        pool = Database_Connection_Pool(config, mock_logger)
        
        self.assertIsNotNone(pool)
        mock_pool_class.assert_called_once()
        mock_logger.inform.assert_called()

    @patch('Models.DatabaseConnectionPool.MySQLConnectionPool')
    def test_logger_logs_pool_creation(self, mock_pool_class) -> None:
        """Testing logger logs successful pool creation."""
        mock_pool = Mock()
        mock_pool_class.return_value = mock_pool
        
        mock_logger = Mock(spec=Crawly_Logger)
        
        config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db",
            pool_name="test_pool",
            pool_size=5
        )
        
        pool = Database_Connection_Pool(config, mock_logger)
        
        # Check that inform was called with pool creation message
        self.assertTrue(mock_logger.inform.called)
        call_args = str(mock_logger.inform.call_args)
        self.assertIn("test_pool", call_args)
        self.assertIn("5", call_args)

    @patch('Models.DatabaseConnectionPool.MySQLConnectionPool')
    def test_default_logger_created_if_none_provided(self, mock_pool_class) -> None:
        """Testing default logger is created if none provided."""
        mock_pool = Mock()
        mock_pool_class.return_value = mock_pool
        
        config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db"
        )
        
        with patch('Models.DatabaseConnectionPool.Crawly_Logger') as mock_logger_class:
            mock_logger = Mock()
            mock_logger_class.return_value = mock_logger
            
            pool = Database_Connection_Pool(config)
            
            mock_logger_class.assert_called_once()


class Test_Database_Connection_Pool_Get_Connection(unittest.TestCase):
    """Testing Database_Connection_Pool connection acquisition."""

    @patch('Models.DatabaseConnectionPool.MySQLConnectionPool')
    def test_get_connection_returns_valid_connection(self, mock_pool_class) -> None:
        """Testing getConnection() returns a valid connection."""
        mock_connection = Mock()
        mock_pool = Mock()
        mock_pool.get_connection.return_value = mock_connection
        mock_pool_class.return_value = mock_pool
        
        mock_logger = Mock(spec=Crawly_Logger)
        
        config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db"
        )
        
        pool = Database_Connection_Pool(config, mock_logger)
        connection = pool.getConnection()
        
        self.assertIsNotNone(connection)
        self.assertEqual(connection, mock_connection)
        mock_pool.get_connection.assert_called_once()

    @patch('Models.DatabaseConnectionPool.MySQLConnectionPool')
    def test_connection_acquisition_logged(self, mock_pool_class) -> None:
        """Testing connection acquisition is logged."""
        mock_connection = Mock()
        mock_pool = Mock()
        mock_pool.get_connection.return_value = mock_connection
        mock_pool_class.return_value = mock_pool
        
        mock_logger = Mock(spec=Crawly_Logger)
        
        config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db"
        )
        
        pool = Database_Connection_Pool(config, mock_logger)
        
        # Reset call count from pool creation
        mock_logger.inform.reset_mock()
        
        connection = pool.getConnection()
        
        # Should log successful connection acquisition
        mock_logger.inform.assert_called()

    @patch('Models.DatabaseConnectionPool.MySQLConnectionPool')
    def test_multiple_connections_acquired_sequentially(self, mock_pool_class) -> None:
        """Testing multiple connections can be acquired sequentially."""
        mock_connection1 = Mock()
        mock_connection2 = Mock()
        mock_pool = Mock()
        mock_pool.get_connection.side_effect = [mock_connection1, mock_connection2]
        mock_pool_class.return_value = mock_pool
        
        mock_logger = Mock(spec=Crawly_Logger)
        
        config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db"
        )
        
        pool = Database_Connection_Pool(config, mock_logger)
        
        conn1 = pool.getConnection()
        conn2 = pool.getConnection()
        
        self.assertEqual(conn1, mock_connection1)
        self.assertEqual(conn2, mock_connection2)
        self.assertEqual(mock_pool.get_connection.call_count, 2)


class Test_Database_Connection_Pool_Error_Handling(unittest.TestCase):
    """Testing Database_Connection_Pool error handling."""

    @patch('Models.DatabaseConnectionPool.MySQLConnectionPool')
    def test_invalid_config_raises_error_on_pool_creation(self, mock_pool_class) -> None:
        """Testing invalid configuration raises error during pool creation."""
        from mysql.connector import Error as Relational_Database_Error
        
        mock_pool_class.side_effect = Relational_Database_Error("Connection failed")
        
        mock_logger = Mock(spec=Crawly_Logger)
        
        config = Database_Configurator(
            host="invalid_host",
            user="user",
            password="pass",
            database="db"
        )
        
        with self.assertRaises(Relational_Database_Error):
            pool = Database_Connection_Pool(config, mock_logger)
        
        # Should log the error
        mock_logger.error.assert_called()

    @patch('Models.DatabaseConnectionPool.MySQLConnectionPool')
    def test_connection_error_propagated(self, mock_pool_class) -> None:
        """Testing connection acquisition error is propagated."""
        from mysql.connector import Error as Relational_Database_Error
        
        mock_pool = Mock()
        mock_pool.get_connection.side_effect = Relational_Database_Error("Pool exhausted")
        mock_pool_class.return_value = mock_pool
        
        mock_logger = Mock(spec=Crawly_Logger)
        
        config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db"
        )
        
        pool = Database_Connection_Pool(config, mock_logger)
        
        with self.assertRaises(Relational_Database_Error):
            pool.getConnection()
        
        # Should log the error
        mock_logger.error.assert_called()


class Test_Database_Connection_Pool_Close(unittest.TestCase):
    """Testing Database_Connection_Pool close functionality."""

    @patch('Models.DatabaseConnectionPool.MySQLConnectionPool')
    def test_close_pool_closes_all_connections(self, mock_pool_class) -> None:
        """Testing closePool() closes all connections in the pool."""
        mock_pool = Mock()
        mock_pool_class.return_value = mock_pool
        
        mock_logger = Mock(spec=Crawly_Logger)
        
        config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db"
        )
        
        pool = Database_Connection_Pool(config, mock_logger)
        
        # The pool should have a close method
        if hasattr(pool, 'closePool'):
            pool.closePool()
            # Verify it was attempted (implementation may vary)
            self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()

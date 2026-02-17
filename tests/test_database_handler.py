"""
Unit tests for Database_Handler.

Tests query execution, transactions, connection management, and sanitization.

Author:
    Darkness4869
"""

from __future__ import annotations
import unittest
from unittest.mock import Mock, patch, MagicMock, call
from typing import List

from Models.DatabaseHandler import Database_Handler
from Models.DatabaseConfigurator import Database_Configurator
from Models.DatabaseConnectionPool import Database_Connection_Pool
from Models.Logger import Crawly_Logger
from Models.Sanitizer import Sanitizer


class Test_Database_Handler_Initialization(unittest.TestCase):
    """Testing Database_Handler initialization."""

    @patch('Models.DatabaseHandler.Database_Connection_Pool')
    @patch('Models.DatabaseHandler.Crawly_Logger')
    @patch('Models.DatabaseHandler.Data_Sanitizer')
    def test_handler_initialized_with_defaults(self, mock_sanitizer, mock_logger, mock_pool) -> None:
        """Testing handler initializes with default dependencies."""
        config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db"
        )
        
        handler = Database_Handler(config)
        
        # Should have created default logger and sanitizer
        self.assertIsNotNone(handler.getLogger())
        self.assertIsNotNone(handler.getSanitizer())


class Test_Database_Handler_Get_Data(unittest.TestCase):
    """Testing Database_Handler.getData() method."""

    def setUp(self) -> None:
        """Setting up test fixtures."""
        self.mock_connection = Mock()
        self.mock_cursor = Mock()
        self.mock_pool = Mock(spec=Database_Connection_Pool)
        self.mock_pool.getConnection.return_value = self.mock_connection
        self.mock_connection.cursor.return_value = self.mock_cursor
        self.mock_connection.is_connected.return_value = True
        self.mock_logger = Mock(spec=Crawly_Logger)
        self.mock_sanitizer = Mock(spec=Sanitizer)
        self.mock_sanitizer.sanitize.side_effect = lambda x: x
        
        self.config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db"
        )

    def test_get_data_executes_select_successfully(self) -> None:
        """Testing getData() executes SELECT query successfully."""
        test_data = [{"id": 1, "name": "test"}]
        self.mock_cursor.fetchall.return_value = test_data
        
        handler = Database_Handler(
            config=self.config,
            logger=self.mock_logger,
            sanitizer=self.mock_sanitizer,
            connection_pool=self.mock_pool
        )
        
        result = handler.getData("SELECT * FROM users")
        
        self.assertEqual(result, test_data)
        self.mock_cursor.execute.assert_called_once()

    def test_get_data_with_parameters(self) -> None:
        """Testing getData() with query parameters."""
        test_data = [{"id": 1, "name": "test"}]
        self.mock_cursor.fetchall.return_value = test_data
        
        handler = Database_Handler(
            config=self.config,
            logger=self.mock_logger,
            sanitizer=self.mock_sanitizer,
            connection_pool=self.mock_pool
        )
        
        result = handler.getData("SELECT * FROM users WHERE id = %s", (1,))
        
        self.assertEqual(result, test_data)
        # Sanitizer should be called for each parameter
        self.mock_sanitizer.sanitize.assert_called()

    def test_get_data_returns_empty_list_on_error(self) -> None:
        """Testing getData() returns empty list on error (graceful degradation)."""
        from mysql.connector import Error as Relational_Database_Error
        
        self.mock_cursor.execute.side_effect = Relational_Database_Error("Query failed")
        
        handler = Database_Handler(
            config=self.config,
            logger=self.mock_logger,
            sanitizer=self.mock_sanitizer,
            connection_pool=self.mock_pool
        )
        
        result = handler.getData("SELECT * FROM invalid_table")
        
        self.assertEqual(result, [])
        self.mock_logger.error.assert_called()


class Test_Database_Handler_Post_Data(unittest.TestCase):
    """Testing Database_Handler.postData() method."""

    def setUp(self) -> None:
        """Setting up test fixtures."""
        self.mock_connection = Mock()
        self.mock_cursor = Mock()
        self.mock_pool = Mock(spec=Database_Connection_Pool)
        self.mock_pool.getConnection.return_value = self.mock_connection
        self.mock_connection.cursor.return_value = self.mock_cursor
        self.mock_connection.is_connected.return_value = True
        self.mock_logger = Mock(spec=Crawly_Logger)
        self.mock_sanitizer = Mock(spec=Sanitizer)
        self.mock_sanitizer.sanitize.side_effect = lambda x: x
        
        self.config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db"
        )

    def test_post_data_executes_insert_successfully(self) -> None:
        """Testing postData() executes INSERT successfully."""
        handler = Database_Handler(
            config=self.config,
            logger=self.mock_logger,
            sanitizer=self.mock_sanitizer,
            connection_pool=self.mock_pool
        )
        
        result = handler.postData("INSERT INTO users (name) VALUES (%s)", ("test",))
        
        self.assertTrue(result)
        self.mock_cursor.execute.assert_called_once()
        self.mock_connection.commit.assert_called_once()

    def test_post_data_commits_transaction(self) -> None:
        """Testing postData() commits transaction after execution."""
        handler = Database_Handler(
            config=self.config,
            logger=self.mock_logger,
            sanitizer=self.mock_sanitizer,
            connection_pool=self.mock_pool
        )
        
        handler.postData("INSERT INTO users (name) VALUES (%s)", ("test",))
        
        self.mock_connection.commit.assert_called_once()


class Test_Database_Handler_Update_Data(unittest.TestCase):
    """Testing Database_Handler.updateData() method."""

    def setUp(self) -> None:
        """Setting up test fixtures."""
        self.mock_connection = Mock()
        self.mock_cursor = Mock()
        self.mock_pool = Mock(spec=Database_Connection_Pool)
        self.mock_pool.getConnection.return_value = self.mock_connection
        self.mock_connection.cursor.return_value = self.mock_cursor
        self.mock_connection.is_connected.return_value = True
        self.mock_logger = Mock(spec=Crawly_Logger)
        self.mock_sanitizer = Mock(spec=Sanitizer)
        self.mock_sanitizer.sanitize.side_effect = lambda x: x
        
        self.config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db"
        )

    def test_update_data_executes_update_successfully(self) -> None:
        """Testing updateData() executes UPDATE successfully."""
        handler = Database_Handler(
            config=self.config,
            logger=self.mock_logger,
            sanitizer=self.mock_sanitizer,
            connection_pool=self.mock_pool
        )
        
        result = handler.updateData("UPDATE users SET name = %s WHERE id = %s", ("newname", 1))
        
        self.assertTrue(result)
        self.mock_cursor.execute.assert_called_once()
        self.mock_connection.commit.assert_called_once()


class Test_Database_Handler_Delete_Data(unittest.TestCase):
    """Testing Database_Handler.deleteData() method."""

    def setUp(self) -> None:
        """Setting up test fixtures."""
        self.mock_connection = Mock()
        self.mock_cursor = Mock()
        self.mock_pool = Mock(spec=Database_Connection_Pool)
        self.mock_pool.getConnection.return_value = self.mock_connection
        self.mock_connection.cursor.return_value = self.mock_cursor
        self.mock_connection.is_connected.return_value = True
        self.mock_logger = Mock(spec=Crawly_Logger)
        self.mock_sanitizer = Mock(spec=Sanitizer)
        self.mock_sanitizer.sanitize.side_effect = lambda x: x
        
        self.config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db"
        )

    def test_delete_data_executes_delete_successfully(self) -> None:
        """Testing deleteData() executes DELETE successfully."""
        handler = Database_Handler(
            config=self.config,
            logger=self.mock_logger,
            sanitizer=self.mock_sanitizer,
            connection_pool=self.mock_pool
        )
        
        result = handler.deleteData("DELETE FROM users WHERE id = %s", (1,))
        
        self.assertTrue(result)
        self.mock_cursor.execute.assert_called_once()
        self.mock_connection.commit.assert_called_once()


class Test_Database_Handler_Sanitization(unittest.TestCase):
    """Testing Database_Handler parameter sanitization."""

    def setUp(self) -> None:
        """Setting up test fixtures."""
        self.mock_connection = Mock()
        self.mock_cursor = Mock()
        self.mock_pool = Mock(spec=Database_Connection_Pool)
        self.mock_pool.getConnection.return_value = self.mock_connection
        self.mock_connection.cursor.return_value = self.mock_cursor
        self.mock_connection.is_connected.return_value = True
        self.mock_logger = Mock(spec=Crawly_Logger)
        self.mock_sanitizer = Mock(spec=Sanitizer)
        
        self.config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db"
        )

    def test_parameters_sanitized_before_execution(self) -> None:
        """Testing parameters are sanitized before query execution."""
        self.mock_sanitizer.sanitize.side_effect = lambda x: f"sanitized_{x}"
        
        handler = Database_Handler(
            config=self.config,
            logger=self.mock_logger,
            sanitizer=self.mock_sanitizer,
            connection_pool=self.mock_pool
        )
        
        handler.postData("INSERT INTO users (name) VALUES (%s)", ("test",))
        
        # Sanitize should have been called
        self.mock_sanitizer.sanitize.assert_called_with("test")

    def test_sanitization_failure_blocks_query(self) -> None:
        """Testing sanitization failure prevents query execution."""
        self.mock_sanitizer.sanitize.side_effect = ValueError("Invalid input")
        
        handler = Database_Handler(
            config=self.config,
            logger=self.mock_logger,
            sanitizer=self.mock_sanitizer,
            connection_pool=self.mock_pool
        )
        
        result = handler.postData("INSERT INTO users (name) VALUES (%s)", ("malicious',))-- ",))
        
        self.assertFalse(result)
        # Query should not be executed
        self.mock_cursor.execute.assert_not_called()
        self.mock_logger.error.assert_called()

    def test_none_parameters_handled_correctly(self) -> None:
        """Testing None parameters are handled correctly."""
        self.mock_sanitizer.sanitize.side_effect = lambda x: x
        self.mock_cursor.fetchall.return_value = []
        
        handler = Database_Handler(
            config=self.config,
            logger=self.mock_logger,
            sanitizer=self.mock_sanitizer,
            connection_pool=self.mock_pool
        )
        
        result = handler.getData("SELECT * FROM users")
        
        # Should succeed without parameters
        self.assertEqual(result, [])


class Test_Database_Handler_Connection_Management(unittest.TestCase):
    """Testing Database_Handler connection lifecycle management."""

    def setUp(self) -> None:
        """Setting up test fixtures."""
        self.mock_connection = Mock()
        self.mock_cursor = Mock()
        self.mock_pool = Mock(spec=Database_Connection_Pool)
        self.mock_pool.getConnection.return_value = self.mock_connection
        self.mock_connection.cursor.return_value = self.mock_cursor
        self.mock_logger = Mock(spec=Crawly_Logger)
        self.mock_sanitizer = Mock(spec=Sanitizer)
        self.mock_sanitizer.sanitize.side_effect = lambda x: x
        
        self.config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db"
        )

    def test_connection_obtained_from_pool_on_demand(self) -> None:
        """Testing connection is obtained from pool when needed."""
        self.mock_connection.is_connected.return_value = True
        self.mock_cursor.fetchall.return_value = []
        
        handler = Database_Handler(
            config=self.config,
            logger=self.mock_logger,
            sanitizer=self.mock_sanitizer,
            connection_pool=self.mock_pool
        )
        
        # Initially no connection
        self.assertIsNone(handler.getConnection())
        
        # After query, connection should be obtained
        handler.getData("SELECT * FROM users")
        
        self.mock_pool.getConnection.assert_called()

    def test_reconnection_when_connection_inactive(self) -> None:
        """Testing reconnection occurs when connection is inactive."""
        # First call: connection inactive, second call: new connection active
        self.mock_connection.is_connected.side_effect = [False, True]
        self.mock_cursor.fetchall.return_value = []
        
        handler = Database_Handler(
            config=self.config,
            logger=self.mock_logger,
            sanitizer=self.mock_sanitizer,
            connection_pool=self.mock_pool
        )
        
        # Set an existing but inactive connection
        handler.setConnection(self.mock_connection)
        
        handler.getData("SELECT * FROM users")
        
        # Should have gotten a new connection
        self.assertTrue(self.mock_pool.getConnection.called)

    def test_close_connection_returns_to_pool(self) -> None:
        """Testing closeConnection() returns connection to pool."""
        self.mock_connection.is_connected.return_value = True
        
        handler = Database_Handler(
            config=self.config,
            logger=self.mock_logger,
            sanitizer=self.mock_sanitizer,
            connection_pool=self.mock_pool
        )
        
        handler.setConnection(self.mock_connection)
        handler.closeConnection()
        
        self.mock_connection.close.assert_called_once()

    def test_cursor_closed_before_new_query(self) -> None:
        """Testing cursor is closed before executing new query."""
        self.mock_connection.is_connected.return_value = True
        self.mock_cursor.fetchall.return_value = []
        
        mock_old_cursor = Mock()
        
        handler = Database_Handler(
            config=self.config,
            logger=self.mock_logger,
            sanitizer=self.mock_sanitizer,
            connection_pool=self.mock_pool
        )
        
        # Set an existing cursor
        handler.setCursor(mock_old_cursor)
        
        handler.getData("SELECT * FROM users")
        
        # Old cursor should be closed
        mock_old_cursor.close.assert_called_once()


class Test_Database_Handler_Transaction_Management(unittest.TestCase):
    """Testing Database_Handler transaction handling."""

    def setUp(self) -> None:
        """Setting up test fixtures."""
        self.mock_connection = Mock()
        self.mock_cursor = Mock()
        self.mock_pool = Mock(spec=Database_Connection_Pool)
        self.mock_pool.getConnection.return_value = self.mock_connection
        self.mock_connection.cursor.return_value = self.mock_cursor
        self.mock_connection.is_connected.return_value = True
        self.mock_logger = Mock(spec=Crawly_Logger)
        self.mock_sanitizer = Mock(spec=Sanitizer)
        self.mock_sanitizer.sanitize.side_effect = lambda x: x
        
        self.config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db"
        )

    def test_commit_failure_triggers_rollback(self) -> None:
        """Testing commit failure triggers rollback."""
        from mysql.connector import Error as Relational_Database_Error
        
        self.mock_connection.commit.side_effect = Relational_Database_Error("Commit failed")
        
        handler = Database_Handler(
            config=self.config,
            logger=self.mock_logger,
            sanitizer=self.mock_sanitizer,
            connection_pool=self.mock_pool
        )
        
        result = handler.postData("INSERT INTO users (name) VALUES (%s)", ("test",))
        
        self.assertFalse(result)
        self.mock_connection.rollback.assert_called_once()
        self.mock_logger.error.assert_called()


class Test_Database_Handler_Error_Handling(unittest.TestCase):
    """Testing Database_Handler error handling."""

    def setUp(self) -> None:
        """Setting up test fixtures."""
        self.mock_connection = Mock()
        self.mock_cursor = Mock()
        self.mock_pool = Mock(spec=Database_Connection_Pool)
        self.mock_pool.getConnection.return_value = self.mock_connection
        self.mock_connection.cursor.return_value = self.mock_cursor
        self.mock_connection.is_connected.return_value = True
        self.mock_logger = Mock(spec=Crawly_Logger)
        self.mock_sanitizer = Mock(spec=Sanitizer)
        self.mock_sanitizer.sanitize.side_effect = lambda x: x
        
        self.config = Database_Configurator(
            host="localhost",
            user="user",
            password="pass",
            database="db"
        )

    def test_invalid_sql_logged_and_handled(self) -> None:
        """Testing invalid SQL is logged and handled gracefully."""
        from mysql.connector import Error as Relational_Database_Error
        
        self.mock_cursor.execute.side_effect = Relational_Database_Error("Syntax error")
        
        handler = Database_Handler(
            config=self.config,
            logger=self.mock_logger,
            sanitizer=self.mock_sanitizer,
            connection_pool=self.mock_pool
        )
        
        result = handler.getData("INVALID SQL QUERY")
        
        self.assertEqual(result, [])
        self.mock_logger.error.assert_called()

    def test_connection_failure_handled_gracefully(self) -> None:
        """Testing connection failure is handled gracefully."""
        from mysql.connector import Error as Relational_Database_Error
        
        self.mock_pool.getConnection.side_effect = Relational_Database_Error("Connection failed")
        
        handler = Database_Handler(
            config=self.config,
            logger=self.mock_logger,
            sanitizer=self.mock_sanitizer,
            connection_pool=self.mock_pool
        )
        
        result = handler.getData("SELECT * FROM users")
        
        self.assertEqual(result, [])
        self.mock_logger.error.assert_called()


if __name__ == "__main__":
    unittest.main()

"""
It provides connection pool management for database connections, following best practices for microservices by handling reconnections gracefully.

Author:
    Darkness4869
"""

from mysql.connector.pooling import MySQLConnectionPool, PooledMySQLConnection
from mysql.connector import Error as Relational_Database_Error
from Models.DatabaseConfigurator import Database_Configurator
from Models.Logger import Crawly_Logger
from typing import Optional


class Database_Connection_Pool:
    """
    It abstracts connection pooling logic, providing a more robust solution for microservices that need to handle multiple concurrent database operations efficiently.
    
    Attributes:
        __pool (MySQLConnectionPool): The underlying MySQL connection pool.
        __configuration (Database_Configurator): Database configuration object.
        __logger (Crawly_Logger): Logger instance for logging pool operations.
    """
    __pool: MySQLConnectionPool
    """The MySQL connection pool instance."""
    __configuration: Database_Configurator
    """The database configuration object."""
    __logger: Crawly_Logger
    """Logger instance for logging pool operations and errors."""

    def __init__(
        self,
        config: Database_Configurator,
        logger: Optional[Crawly_Logger] = None
    ):
        """
        Initialize a DatabaseConnectionPool instance.
        
        Procedures:
            1. If a logger is not provided, a default Crawly_Logger is created.
            2. Stores the configuration object.
            3. Creates the MySQL connection pool using the configuration.
        
        Parameters:
            config (Database_Configurator): Database configuration object.
            logger (Optional[Crawly_Logger]): Logger instance for logging operations.

        Raises:
            Relational_Database_Error: If pool creation fails.
        """
        self.setLogger(logger or Crawly_Logger(__name__))
        self.setConfig(config)
        self.setPool(self.__createPool())
    
    def getLogger(self) -> Crawly_Logger:
        return self.__logger
    
    def setLogger(self, logger: Crawly_Logger) -> None:
        self.__logger = logger
    
    def getConfig(self) -> Database_Configurator:
        return self.__configuration
    
    def setConfig(self, config: Database_Configurator) -> None:
        self.__configuration = config
    
    def getPool(self) -> MySQLConnectionPool:
        return self.__pool
    
    def setPool(self, pool: MySQLConnectionPool) -> None:
        self.__pool = pool
    
    def __createPool(self) -> MySQLConnectionPool:
        """
        Create a MySQL connection pool using the provided configuration.

        Returns:
            MySQLConnectionPool: The created connection pool.

        Raises:
            Relational_Database_Error: If pool creation fails.
        """
        try:
            pool = MySQLConnectionPool(**self.getConfig().to_pool_dict())
            self.getLogger().inform(
                f"Database connection pool '{self.getConfig().pool_name}' "
                f"successfully created with {self.getConfig().pool_size} connections."
            )
            return pool
        except Relational_Database_Error as error:
            self.getLogger().error(f"The connection pool cannot be created. - Error: {error}")
            raise error

    def getConnection(self) -> PooledMySQLConnection:
        """
        Get a connection from the pool.

        Returns:
            PooledMySQLConnection: A pooled MySQL connection.

        Raises:
            Relational_Database_Error: If unable to get a connection from the pool.
        """
        try:
            connection: PooledMySQLConnection = self.getPool().get_connection()
            self.getLogger().inform("Successfully retrieved connection from pool.")
            return connection
        except Relational_Database_Error as error:
            self.getLogger().error(f"A connection cannot be retrieved from the pool. - Error: {error}")
            raise error

    def closePool(self) -> None:
        """
        Close all connections in the pool.
        
        This method should be called when the application is shutting down to ensure all database connections are properly closed.
        
        Note:
            MySQLConnectionPool doesn't have a built-in close method, so we log the intent.  Individual connections are returned to the pool automatically when closed.
        """
        self.getLogger().inform(f"The pool is being shut down.  All connections will be closed when returned to the pool. - Pool Name: {self.getConfig().pool_name}")

"""
The Module provides a class to handle database operations such as connecting, executing queries, and managing transactions.

Author:
    Darkness4869
"""

from mysql.connector.pooling import PooledMySQLConnection
from mysql.connector.cursor import MySQLCursor
from Models.Logger import Crawly_Logger
from mysql.connector.types import RowType
from typing import Tuple, Any, List, Optional
from mysql.connector import Error as Relational_Database_Error
from Models.Sanitizer import Sanitizer
from Models.DataSanitizer import Data_Sanitizer
from Models.DatabaseConfigurator import Database_Configurator
from Models.DatabaseConnectionPool import Database_Connection_Pool


class Database_Handler:
    __logger: Crawly_Logger
    """
    A logger instance for logging database operations and errors.
    """
    __connection_pool: Database_Connection_Pool
    """
    The database connection pool for managing connections efficiently.
    """
    __connection: Optional[PooledMySQLConnection]
    """
    The current pooled MySQL connection object used to interact with the database.
    """
    __cursor: Optional[MySQLCursor]
    """
    The MySQL cursor object used to execute database queries.
    """
    __sanitizer: Sanitizer
    """
    An instance of Sanitizer for sanitizing user input data to prevent SQL injection attacks and ensure safe string usage.
    """

    def __init__(
        self,
        config: Database_Configurator,
        logger: Optional[Crawly_Logger] = None,
        sanitizer: Optional[Sanitizer] = None,
        connection_pool: Optional[Database_Connection_Pool] = None
    ):
        """
        Initializing a `Database_Handler` instance with configuration and optional dependencies.

        Procedures:
            1. If a `logger` is not provided, a default `Crawly_Logger` is created and used.
            2. If a `connection_pool` is not provided, creates a new pool using the configuration.
            3. Initializes the connection to `None` (connections are obtained from pool as needed).
            4. Initializes the cursor to `None`.
            5. If a `sanitizer` is not provided, a default `Data_Sanitizer` is created and used.

        Parameters:
            config (Database_Configurator): Database configuration object.
            logger (Optional[Crawly_Logger]): A logger instance for logging database operations and errors.
            sanitizer (Optional[Sanitizer]): An instance of `Sanitizer` for sanitizing user input data.
            connection_pool (Optional[Database_Connection_Pool]): An existing connection pool to use.

        Raises:
            Relational_Database_Error: If the connection pool creation fails.
        """
        self.setLogger(logger or Crawly_Logger(__name__))
        self.setConnectionPool(
            connection_pool or Database_Connection_Pool(config, self.getLogger())
        )
        self.setConnection(None)
        self.setCursor(None)
        self.setSanitizer(sanitizer or Data_Sanitizer())

    def getLogger(self) -> Crawly_Logger:
        return self.__logger

    def setLogger(self, logger: Crawly_Logger) -> None:
        self.__logger = logger

    def getConnectionPool(self) -> Database_Connection_Pool:
        return self.__connection_pool

    def setConnectionPool(self, connection_pool: Database_Connection_Pool) -> None:
        self.__connection_pool = connection_pool

    def getConnection(self) -> Optional[PooledMySQLConnection]:
        return self.__connection

    def setConnection(self, connection: Optional[PooledMySQLConnection]) -> None:
        self.__connection = connection

    def getCursor(self) -> Optional[MySQLCursor]:
        return self.__cursor

    def setCursor(self, cursor: Optional[MySQLCursor]) -> None:
        self.__cursor = cursor

    def getSanitizer(self) -> Sanitizer:
        return self.__sanitizer

    def setSanitizer(self, sanitizer: Sanitizer) -> None:
        self.__sanitizer = sanitizer

    def __sanitizeParameters(self, parameters: Optional[Tuple[Any, ...]]) -> Optional[Tuple[Any, ...]]:
        """
        Sanitizing the parameters using the `Data_Sanitizer` instance.

        Parameters:
            parameters (Optional[Tuple[Any, ...]]): The parameters to sanitize.

        Returns:
            Optional[Tuple[Any, ...]]: The sanitized parameters.

        Raises:
            Relational_Database_Error: If sanitization fails.
        """
        try:
            if parameters is None:
                return None
            return tuple(self.getSanitizer().sanitize(parameter) for parameter in parameters)
        except ValueError as error:
            self.getLogger().error(f"The database handler has failed to sanitize the parameters. - Parameters: {parameters} - Error: {error}")
            raise Relational_Database_Error(str(error))

    def __getConnectionFromPool(self) -> PooledMySQLConnection:
        """
        Obtaining a connection from the connection pool.

        Returns:
            (PooledMySQLConnection): A pooled MySQL connection object.

        Raises:
            Relational_Database_Error: If the connection attempt fails.
        """
        try:
            connection: PooledMySQLConnection = self.getConnectionPool().getConnection()
            self.getLogger().inform("Successfully obtained connection from pool.")
            return connection
        except Relational_Database_Error as error:
            self.getLogger().error(f"Failed to obtain connection from pool. Error: {error}")
            raise error

    def __ensureConnection(self) -> None:
        """
        Ensuring that the database connection is active.

        Procedures:
            1. If there is no existing connection, obtains one from the pool.
            2. If the existing connection is inactive, closes it and obtains a new one from the pool.
            3. Logs the outcome of the connection check.

        Returns:
            None

        Raises:
            Relational_Database_Error: If obtaining a connection from the pool fails.
        """
        if self.getConnection() is None:
            self.setConnection(self.__getConnectionFromPool())
            self.getLogger().inform("Successfully obtained new connection from pool.")
            return
        if not self.getConnection().is_connected():  # type: ignore
            self.getLogger().warn("Connection is not active. Returning to pool and obtaining new connection.")
            self.__returnConnectionToPool()
            self.setConnection(self.__getConnectionFromPool())
            self.getLogger().inform("Successfully obtained replacement connection from pool.")
            return
        self.getLogger().inform("Database connection is active and ready.")

    def _execute(
        self,
        query: str,
        parameters: Optional[Tuple[Any, ...]] = None
    ) -> None:
        """
        Executing a query with optional parameters on the database connection.

        Procedures:
            1. Ensures a database connection is present.
            2. If a connection is not present, it establishes a new connection.
            3. If the connection is inactive, it attempts to reconnect up to 3 times with a 2-second delay between attempts.
            4. Logs the outcome of the connection check and reconnection attempts.
            5. Executes the query with the provided parameters
            6. Logs the outcome of the query execution.
            7. If the query execution fails, it logs the error and raises a Relational_Database_Error.

        Args:
            query (str): The SQL query to execute.
            parameters (Optional[Tuple[Any, ...]]): Parameters for the SQL query.

        Raises:
            Relational_Database_Error: If the query execution fails.
        """
        try:
            self.__ensureConnection()
            self.closeCursor()
            self.setCursor(
                self.getConnection().cursor( # type: ignore
                    prepared=True,
                    dictionary=True
                )
            )
            self.getCursor().execute(query, self.__sanitizeParameters(parameters)) # type: ignore
        except Relational_Database_Error as error:
            self.getLogger().error(f"The database handler has failed to execute the query. - Query: {query} - Parameters: {parameters} - Error: {error}")
            raise error

    def closeCursor(self) -> None:
        """
        Closing the current cursor if it exists.

        Raises:
            Relational_Database_Error: If the cursor closing operation fails.
        """
        if self.getCursor() is None:
            return
        try:
            self.getCursor().close() # type: ignore
            self.getLogger().inform("The database handler has successfully closed the cursor.")
            self.setCursor(None)
        except Relational_Database_Error as error:
            self.getLogger().error(f"The database handler has failed to close the cursor. - Error: {error}")
            raise error

    def _commit(self) -> None:
        """
        Committing the current database transaction.

        Raises:
            Relational_Database_Error: If the commit operation fails.
        """
        connection = self.getConnection()
        if connection is None:
            raise Relational_Database_Error("No active connection to commit.")
        try:
            connection.commit()
            self.getLogger().inform("The transaction has been successfully committed.")
        except Relational_Database_Error as error:
            connection.rollback()
            self.getLogger().error(f"The database handler has failed to commit the transaction, hence, the trasaction will roolback. - Error: {error}")
            raise error

    def _fetchAll(self) -> List[RowType]:
        """
        Fetching all rows from the last executed query.

        Returns:
            List[RowType]: A list of rows returned by the last executed query.

        Raises:
            Relational_Database_Error: If fetching rows fails.
        """
        if self.getCursor() is None:
            raise Relational_Database_Error("No cursor available to fetch data.")
        try:
            response: List[RowType] = self.getCursor().fetchall() # type: ignore
            self.getLogger().inform(f"The database handler has successfully fetched the required data.")
            return response
        except Relational_Database_Error as error:
            self.getLogger().error(f"The database handler has failed to fetch all rows. - Error: {error}")
            raise error

    def __returnConnectionToPool(self) -> None:
        """
        Returning the current connection to the pool.

        This method closes the current connection, which returns it to the pool.
        
        Raises:
            Relational_Database_Error: If the connection closing operation fails.
        """
        if self.getConnection() is None:
            return
        try:
            self.getConnection().close()  # type: ignore
            self.getLogger().inform("Connection returned to pool.")
            self.setConnection(None)
        except Relational_Database_Error as error:
            self.getLogger().error(f"Failed to return connection to pool. Error: {error}")
            self.setConnection(None)
            raise error

    def closeConnection(self) -> None:
        """
        Closing the current database connection and returning it to the pool.

        Raises:
            Relational_Database_Error: If the connection closing operation fails.
        """
        if self.getConnection() is None:
            self.getLogger().warn("No active connection to close.")
            return
        if not self.getConnection().is_connected():  # type: ignore
            self.getLogger().warn("The database connection is already closed.")
            self.setConnection(None)
            return
        self.__returnConnectionToPool()

    def getData(
        self,
        query: str,
        parameters: Optional[Tuple[Any, ...]] = None
    ) -> List[RowType]:
        """
        Fetching data from the database by executing a query with optional parameters.

        Procedures:
            1. Executes the provided SQL query with optional parameters.
            2. Returns a list of rows returned by the query.
            3. Returning an empty list when the execution fails.

        Args:
            query (str): The SQL query to execute.
            parameters (Optional[Tuple[Any, ...]]): Parameters for the SQL query.

        Returns:
            List[RowType]: A list of rows returned by the query.
        """
        try:
            self._execute(query, parameters)
            response: List[RowType] = self._fetchAll()
            return response
        except Relational_Database_Error as error:
            self.getLogger().error(f"The database handler has failed to get data. - Query: {query} - Parameters: {parameters} - Error: {error}")
            return []

    def _manipulateData(
        self,
        query: str,
        parameters: Optional[Tuple[Any, ...]] = None
    ) -> bool:
        """
        Executing the provided SQL query with optional parameters and committing the changes.

        Procedures:
            1. Executes the provided SQL query with optional parameters.
            2. Commits the changes.
            3. Returns True if the operation is successful, False otherwise.

        Args:
            query (str): The SQL query to execute.
            parameters (Optional[Tuple[Any, ...]]): Parameters for the SQL query.

        Returns:
            bool: True if the operation is successful, False otherwise.
        """
        try:
            self._execute(query, parameters)
            self._commit()
            return True
        except Relational_Database_Error as error:
            self.getLogger().error(f"The database handler has failed to post data. - Query: {query} - Parameters: {parameters} - Error: {error}")
            return False

    def postData(
        self,
        query: str,
        parameters: Optional[Tuple[Any, ...]] = None
    ) -> bool:
        """
        Posting data to the database by executing a query with optional parameters.

        Args:
            query (str): The SQL query to execute.
            parameters (Optional[Tuple[Any, ...]]): Parameters for the SQL query.

        Returns:
            bool: True if the operation is successful, False otherwise.
        """
        return self._manipulateData(query, parameters)

    def updateData(
        self,
        query: str,
        parameters: Optional[Tuple[Any, ...]] = None
    ) -> bool:
        """
        Updating data in the database by executing a query with optional parameters.

        Args:
            query (str): The SQL query to execute.
            parameters (Optional[Tuple[Any, ...]]): Parameters for the SQL query.

        Returns:
            bool: True if the operation is successful, False otherwise.
        """
        return self._manipulateData(query, parameters)

    def deleteData(
        self,
        query: str,
        parameters: Optional[Tuple[Any, ...]] = None
    ) -> bool:
        """
        Deleting data from the database by executing a query with optional parameters.

        Args:
            query (str): The SQL query to execute.
            parameters (Optional[Tuple[Any, ...]]): Parameters for the SQL query.

        Returns:
            bool: True if the operation is successful, False otherwise.
        """
        return self._manipulateData(query, parameters)

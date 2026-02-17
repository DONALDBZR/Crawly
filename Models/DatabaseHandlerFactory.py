"""
It provides a factory for creating `Database_Handler` instances, following the Factory Pattern as recommended in the architectural guidelines.

Author:
    Darkness4869
"""

from typing import Optional
from Models.DatabaseHandler import Database_Handler
from Models.DatabaseConfigurator import Database_Configurator
from Models.DatabaseConnectionPool import Database_Connection_Pool
from Models.Logger import Crawly_Logger
from Models.Sanitizer import Sanitizer
from Models.DataSanitizer import Data_Sanitizer


class Database_Handler_Factory:
    """
    It simplifies the creation of database handlers with appropriate configuration and shared resources like connection pools.

    Attributes:
        __default_pool (Optional[Database_Connection_Pool]): Shared connection pool.
        __default_config (Optional[Database_Configurator]): Default configuration.
        __default_logger (Optional[Crawly_Logger]): Default logger.

    Methods:
        initialize: Initializes the factory with default configuration and resources.
        create: Creates a new `Database_Handler` instance.
        shutdown: Shuts down the factory and closes the shared connection pool.
    """
    __default_pool: Optional[Database_Connection_Pool] = None
    """Shared connection pool for all handlers created by this factory."""
    __default_config: Optional[Database_Configurator] = None
    """Default configuration for handlers."""
    __default_logger: Optional[Crawly_Logger] = None
    """Default logger for handlers."""

    @classmethod
    def initialize(
        cls,
        config: Optional[Database_Configurator] = None,
        logger: Optional[Crawly_Logger] = None,
        create_pool: bool = True
    ) -> None:
        """
        Initializing the factory with default configuration and resources.

        NOTE: For proper configuration validation, call 
        Environment_Validator.validate_environment(require_database=True) at application
        startup before calling this method.

        Procedures:
            1. Set the default configuration using the provided config or environment variables.
            2. Set the default logger using the provided logger or create a new one.
            3. If create_pool is True, create a shared connection pool.

        Parameters:
            config (Optional[Database_Configurator]): Default database configuration.  If `None`, will use `Database_Configurator.from_environment()`.
            logger (Optional[Crawly_Logger]): Default logger instance.
            create_pool (bool): Whether to create a shared connection pool.

        Returns:
            None

        Raises:
            ValueError: If configuration cannot be loaded.
        """
        cls.__default_config = config or Database_Configurator.from_environment()
        cls.__default_logger = logger or Crawly_Logger("Database_Handler_Factory")
        if not create_pool:
            cls.__default_logger.inform("The factory is initialized without connection pool.")
            return
        cls.__default_pool = Database_Connection_Pool(cls.__default_config, cls.__default_logger)
        cls.__default_logger.inform("The factory initialized with shared connection pool.")

    @classmethod
    def create(
        cls,
        config: Optional[Database_Configurator] = None,
        logger: Optional[Crawly_Logger] = None,
        sanitizer: Optional[Sanitizer] = None,
        use_shared_pool: bool = True
    ) -> Database_Handler:
        """
        Creating a new `Database_Handler` instance.

        Procedures:
            1. Use the factory's default configuration and logger if none are provided.
            2. Use the factory's shared connection pool if use_shared_pool is True.
            3. Create and return a new `Database_Handler` instance.

        Parameters:
            config (Optional[Database_Configurator]): Configuration for this handler.
                If None, uses the factory's default configuration.
            logger (Optional[Crawly_Logger]): Logger for this handler.
                If None, uses the factory's default logger.
            sanitizer (Optional[ISanitizer]): Custom sanitizer implementation.
                If None, uses default Data_Sanitizer.
            use_shared_pool (bool): Whether to use the factory's shared connection pool.
                If False, a new pool will be created for this handler.

        Returns:
            Database_Handler: A configured database handler instance.

        Raises:
            RuntimeError: If factory has not been initialized.
            ValueError: If configuration is invalid.
        """
        if cls.__default_config is None:
            raise RuntimeError("The factory has not been initialized.")
        handler_config = config or cls.__default_config
        handler_logger = logger or cls.__default_logger
        handler_sanitizer = sanitizer or Data_Sanitizer()
        if use_shared_pool and cls.__default_pool is not None:
            handler = Database_Handler(
                config=handler_config,
                logger=handler_logger,
                sanitizer=handler_sanitizer,
                connection_pool=cls.__default_pool
            )
        else:
            handler = Database_Handler(
                config=handler_config,
                logger=handler_logger,
                sanitizer=handler_sanitizer
            )
        if handler_logger:
            handler_logger.inform("Created new `Database_Handler` instance.")
        return handler

    @classmethod
    def shutdown(cls) -> None:
        """
        Shutting down the factory and close the shared connection pool.

        Procedures:
            1. If a shared connection pool exists, close it.
            2. Log the shutdown event.

        Returns:
            None
        """
        if cls.__default_pool is not None:
            cls.__default_pool.closePool()
            cls.__default_pool = None
        if cls.__default_logger is not None:
            cls.__default_logger.inform("The factory has been shutdown.")

    @classmethod
    def get_shared_pool(cls) -> Optional[Database_Connection_Pool]:
        return cls.__default_pool

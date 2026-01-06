"""
This module provides configuration management for database connections, following the Dependency Inversion Principle by externalizing configuration.

Author:
    Darkness4869
"""

from dataclasses import dataclass
from os import getenv


@dataclass
class Database_Configurator:
    """
    It encapsulates all database connection settings, removing direct environment variable access from the `Database_Handler`.
    
    Attributes:
        host (str): Database host address.
        user (str): Database user name.
        password (str): Database password.
        database (str): Database name.
        pool_name (str): Name for the connection pool.
        pool_size (int): Size of the connection pool.
        pool_reset_session (bool): Whether to reset session variables when connection is returned to pool.
        use_pure (bool): Whether to use pure Python implementation.
    """
    host: str
    user: str
    password: str
    database: str
    pool_name: str = "crawly_pool"
    pool_size: int = 5
    pool_reset_session: bool = True
    use_pure: bool = True
    
    @classmethod
    def from_environment(cls) -> "Database_Configurator":
        """
        Creating a `Database_Configurator` instance from environment variables.

        Procedures:
            1. Reads database configuration parameters from environment variables.
            2. Constructs and returns a `Database_Configurator` instance with the retrieved values.

        Returns:
            Database_Configurator: Configuration instance populated from environment variables.

        Raises:
            ValueError: If required environment variables are missing.
        """
        host = getenv("DB_HOST")
        user = getenv("DB_USER")
        password = getenv("DB_PASSWORD")
        database = getenv("DB_NAME")
        if not all([host, user, password, database]):
            raise ValueError("The configuration is invalid for that database server.")
        return cls(
            host=host,  # type: ignore
            user=user,  # type: ignore
            password=password,  # type: ignore
            database=database,  # type: ignore
            pool_name=getenv("DB_POOL_NAME", "crawly_pool"),
            pool_size=int(getenv("DB_POOL_SIZE", "5")),
            pool_reset_session=getenv("DB_POOL_RESET_SESSION", "true").lower() == "true",
            use_pure=getenv("DB_USE_PURE", "true").lower() == "true"
        )
    
    def to_dict(self) -> dict:
        """
        Convert configuration to a dictionary suitable for mysql.connector.
        
        Returns:
            dict: Configuration dictionary with keys compatible with mysql.connector.
        """
        return {
            "host": self.host,
            "user": self.user,
            "password": self.password,
            "database": self.database,
            "use_pure": self.use_pure
        }
    
    def to_pool_dict(self) -> dict:
        """
        Convert configuration to a dictionary suitable for mysql.connector.pooling.
        
        Returns:
            dict: Configuration dictionary with keys compatible for connection pooling.
        """
        return {
            "pool_name": self.pool_name,
            "pool_size": self.pool_size,
            "pool_reset_session": self.pool_reset_session,
            "host": self.host,
            "user": self.user,
            "password": self.password,
            "database": self.database,
            "use_pure": self.use_pure
        }

"""
This module defines the interface for data sanitizers, following the Interface Segregation Principle and Dependency Inversion Principle.

Author:
    Darkness4869
"""

from abc import ABC, abstractmethod
from typing import Any


class Sanitizer(ABC):
    """
    It defines the contract that all sanitizer implementations must follow, allowing the `Database_Handler` to depend on an abstraction rather than a concrete implementation.
    
    Methods:
        sanitize(data: Any) -> Any: Sanitizes input data according to the implementation's rules.
    """

    @abstractmethod
    def sanitize(self, data: Any) -> Any:
        """
        Sanitize the input data.
        
        This method should validate and sanitize the input data according
        to the specific implementation's rules and security requirements.
        
        Args:
            data (Any): The data to be sanitized.
        
        Returns:
            Any: The sanitized data.
        
        Raises:
            ValueError: If the data is invalid or fails sanitization checks.
        """
        pass

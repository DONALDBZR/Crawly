"""
Environment variable validation module for Crawly.

Provides single startup validation checkpoint following configuration discipline:
- Validates required environment variables with clear error messages
- Performs type conversions with error handling
- Returns structured validation results
- Zero side effects during validation (no logging, connections, or filesystem ops)

This enforces the configuration boundary per copilot-instructions.md:
- Required variables must be validated explicitly
- Safe defaults for optional variables
- Clear failure messages for misconfiguration

Author:
    Darkness4869
"""

from __future__ import annotations
from dataclasses import dataclass, field
from os import getenv
from typing import List, Optional, Tuple, Dict, Any


@dataclass
class Validation_Result:
    """
    Result of environment variable validation.
    
    Attributes:
        success (bool): Whether validation passed without errors.
        errors (List[str]): List of validation error messages.
        warnings (List[str]): List of non-fatal warnings.
        validated_config (Optional[Dict[str, Any]]): Parsed configuration if successful.
    """
    success: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validated_config: Optional[Dict[str, Any]] = None


class Environment_Validator:
    """
    Centralized environment variable validator for Crawly application.
    
    This class provides static methods for validating environment configuration
    at application startup, before any runtime side effects occur.
    
    Usage:
        result = Environment_Validator.validate_environment(require_database=False)
        if not result.success:
            for error in result.errors:
                print(f"Configuration Error: {error}")
            sys.exit(1)
    """
    
    @staticmethod
    def _validate_required_vars(var_names: List[str]) -> List[str]:
        """
        Validating that required environment variables are present and non-empty.
        
        Procedures:
            1. Check each variable is present in environment.
            2. Check each variable has non-empty value.
            3. Collect errors for missing or empty variables.
        
        Parameters:
            var_names (List[str]): List of required variable names.
        
        Returns:
            List[str]: List of error messages for missing/empty variables.
        """
        errors: List[str] = []
        for var_name in var_names:
            value = getenv(var_name)
            if value is None:
                errors.append(f"Missing required environment variable: {var_name}")
            elif not value.strip():
                errors.append(f"Environment variable cannot be empty: {var_name}")
        return errors
    
    @staticmethod
    def _validate_int_var(
        var_name: str,
        default: Optional[int],
        min_val: Optional[int] = None,
        max_val: Optional[int] = None
    ) -> Tuple[Optional[int], List[str], List[str]]:
        """
        Validating and parsing an integer environment variable.
        
        Procedures:
            1. Retrieve variable from environment.
            2. If not present, return default value.
            3. Attempt to parse as integer.
            4. Validate against min/max constraints if provided.
            5. Return parsed value with any errors or warnings.
        
        Parameters:
            var_name (str): Name of environment variable.
            default (Optional[int]): Default value if not present.
            min_val (Optional[int]): Minimum allowed value (inclusive).
            max_val (Optional[int]): Maximum allowed value (inclusive).
        
        Returns:
            Tuple[Optional[int], List[str], List[str]]: 
                (parsed_value, errors, warnings)
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        value_str = getenv(var_name)
        
        # Variable not present - use default
        if value_str is None:
            if default is not None:
                warnings.append(f"Using default {var_name}={default}")
            return (default, errors, warnings)
        
        # Variable present but empty
        if not value_str.strip():
            errors.append(f"{var_name} cannot be empty")
            return (None, errors, warnings)
        
        # Attempt integer conversion
        try:
            value = int(value_str)
        except ValueError:
            errors.append(
                f"{var_name} must be an integer, got: '{value_str}'"
            )
            return (None, errors, warnings)
        
        # Validate range constraints
        if min_val is not None and value < min_val:
            errors.append(
                f"{var_name} must be >= {min_val}, got: {value}"
            )
        
        if max_val is not None and value > max_val:
            errors.append(
                f"{var_name} must be <= {max_val}, got: {value}"
            )
        
        # Warning for suspicious values
        if max_val is None and value > 100:
            warnings.append(
                f"{var_name} is unusually high ({value}), this may cause resource issues"
            )
        
        return (value, errors, warnings)
    
    @staticmethod
    def _validate_bool_var(
        var_name: str,
        default: bool
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Validating and parsing a boolean environment variable.
        
        Procedures:
            1. Retrieve variable from environment.
            2. If not present, return default value.
            3. Parse as boolean (accepts: true, false, 1, 0).
            4. Return parsed value with any errors or warnings.
        
        Parameters:
            var_name (str): Name of environment variable.
            default (bool): Default value if not present.
        
        Returns:
            Tuple[bool, List[str], List[str]]: 
                (parsed_value, errors, warnings)
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        value_str = getenv(var_name)
        
        # Variable not present - use default
        if value_str is None:
            warnings.append(f"Using default {var_name}={default}")
            return (default, errors, warnings)
        
        # Variable present but empty
        if not value_str.strip():
            errors.append(f"{var_name} cannot be empty")
            return (default, errors, warnings)
        
        # Parse boolean
        value_lower = value_str.strip().lower()
        if value_lower in ("true", "1", "yes"):
            return (True, errors, warnings)
        elif value_lower in ("false", "0", "no"):
            return (False, errors, warnings)
        else:
            errors.append(
                f"{var_name} must be 'true' or 'false' (or '1'/'0'), got: '{value_str}'"
            )
            return (default, errors, warnings)
    
    @staticmethod
    def _validate_string_var(
        var_name: str,
        default: str,
        allow_empty: bool = False
    ) -> Tuple[str, List[str], List[str]]:
        """
        Validating and retrieving a string environment variable.
        
        Procedures:
            1. Retrieve variable from environment.
            2. If not present, return default value.
            3. Validate non-empty if required.
            4. Return parsed value with any errors or warnings.
        
        Parameters:
            var_name (str): Name of environment variable.
            default (str): Default value if not present.
            allow_empty (bool): Whether empty strings are allowed.
        
        Returns:
            Tuple[str, List[str], List[str]]: 
                (parsed_value, errors, warnings)
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        value = getenv(var_name)
        
        # Variable not present - use default
        if value is None:
            if default:
                warnings.append(f"Using default {var_name}='{default}'")
            return (default, errors, warnings)
        
        # Variable present but empty (if not allowed)
        if not allow_empty and not value.strip():
            errors.append(f"{var_name} cannot be empty")
            return (default, errors, warnings)
        
        return (value, errors, warnings)
    
    @staticmethod
    def validate_database_config() -> Validation_Result:
        """
        Validating database-related environment variables.
        
        Procedures:
            1. Check required database variables (host, user, password, database).
            2. Validate optional pool configuration variables.
            3. Perform type conversions and range checks.
            4. Collect all errors and warnings.
            5. Return validation result.
        
        Required Variables:
            DB_HOST: Database server hostname/IP
            DB_USER: Database username
            DB_PASSWORD: Database password
            DB_NAME: Database name
        
        Optional Variables:
            DB_POOL_NAME: Connection pool name (default: "crawly_pool")
            DB_POOL_SIZE: Pool size (default: 5, must be > 0)
            DB_POOL_RESET_SESSION: Reset session on return (default: true)
            DB_USE_PURE: Use pure Python driver (default: true)
        
        Returns:
            Validation_Result: Result with success flag, errors, and validated config.
        """
        all_errors: List[str] = []
        all_warnings: List[str] = []
        config: Dict[str, Any] = {}
        
        # Validate required variables
        required_vars = ["DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME"]
        required_errors = Environment_Validator._validate_required_vars(required_vars)
        all_errors.extend(required_errors)
        
        # If required vars missing, fail fast
        if required_errors:
            return Validation_Result(
                success=False,
                errors=all_errors,
                warnings=all_warnings,
                validated_config=None
            )
        
        # Required vars present - retrieve them
        config["DB_HOST"] = getenv("DB_HOST")
        config["DB_USER"] = getenv("DB_USER")
        config["DB_PASSWORD"] = getenv("DB_PASSWORD")
        config["DB_NAME"] = getenv("DB_NAME")
        
        # Validate optional variables
        pool_name, name_errors, name_warnings = Environment_Validator._validate_string_var(
            "DB_POOL_NAME", "crawly_pool"
        )
        config["DB_POOL_NAME"] = pool_name
        all_errors.extend(name_errors)
        all_warnings.extend(name_warnings)
        
        pool_size, size_errors, size_warnings = Environment_Validator._validate_int_var(
            "DB_POOL_SIZE", default=5, min_val=1
        )
        config["DB_POOL_SIZE"] = pool_size
        all_errors.extend(size_errors)
        all_warnings.extend(size_warnings)
        
        reset_session, reset_errors, reset_warnings = Environment_Validator._validate_bool_var(
            "DB_POOL_RESET_SESSION", default=True
        )
        config["DB_POOL_RESET_SESSION"] = reset_session
        all_errors.extend(reset_errors)
        all_warnings.extend(reset_warnings)
        
        use_pure, pure_errors, pure_warnings = Environment_Validator._validate_bool_var(
            "DB_USE_PURE", default=True
        )
        config["DB_USE_PURE"] = use_pure
        all_errors.extend(pure_errors)
        all_warnings.extend(pure_warnings)
        
        # Return result
        success = len(all_errors) == 0
        return Validation_Result(
            success=success,
            errors=all_errors,
            warnings=all_warnings,
            validated_config=config if success else None
        )
    
    @staticmethod
    def validate_logger_config() -> Validation_Result:
        """
        Validating logger-related environment variables.
        
        Procedures:
            1. Validate optional log directory variable.
            2. Validate optional log filename variable.
            3. Collect all errors and warnings.
            4. Return validation result.
        
        Optional Variables:
            LOG_DIRECTORY: Log file directory (default: "./Logs")
            LOG_FILE_NAME: Log file name (default: "Crawly.log")
        
        Returns:
            Validation_Result: Result with success flag, errors, and validated config.
        """
        all_errors: List[str] = []
        all_warnings: List[str] = []
        config: Dict[str, Any] = {}
        
        # Validate log directory
        log_dir, dir_errors, dir_warnings = Environment_Validator._validate_string_var(
            "LOG_DIRECTORY", "./Logs"
        )
        config["LOG_DIRECTORY"] = log_dir
        all_errors.extend(dir_errors)
        all_warnings.extend(dir_warnings)
        
        # Validate log filename
        log_file, file_errors, file_warnings = Environment_Validator._validate_string_var(
            "LOG_FILE_NAME", "Crawly.log"
        )
        config["LOG_FILE_NAME"] = log_file
        all_errors.extend(file_errors)
        all_warnings.extend(file_warnings)
        
        # Return result
        success = len(all_errors) == 0
        return Validation_Result(
            success=success,
            errors=all_errors,
            warnings=all_warnings,
            validated_config=config if success else None
        )
    
    @staticmethod
    def validate_environment(require_database: bool = False) -> Validation_Result:
        """
        Single validation entry point for all environment configuration.
        
        This is the main validation function that should be called at application
        startup before any runtime side effects (logging, network, database connections).
        
        Procedures:
            1. Validate logger configuration (always required).
            2. If require_database=True, validate database configuration.
            3. Aggregate all errors and warnings.
            4. Return combined validation result.
        
        Parameters:
            require_database (bool): Whether to enforce database variable validation.
                Set to True for programmatic API usage with DB features.
                Set to False for CLI-only usage (default).
        
        Returns:
            Validation_Result: Combined result with success flag, all errors/warnings,
                and validated configuration dictionary.
        
        Example:
            >>> from Models.EnvValidator import Environment_Validator
            >>> result = Environment_Validator.validate_environment(require_database=True)
            >>> if not result.success:
            ...     for error in result.errors:
            ...         print(f"Error: {error}")
            ...     sys.exit(1)
        """
        all_errors: List[str] = []
        all_warnings: List[str] = []
        combined_config: Dict[str, Any] = {}
        
        # Always validate logger configuration
        logger_result = Environment_Validator.validate_logger_config()
        all_errors.extend(logger_result.errors)
        all_warnings.extend(logger_result.warnings)
        if logger_result.validated_config:
            combined_config.update(logger_result.validated_config)
        
        # Conditionally validate database configuration
        if require_database:
            db_result = Environment_Validator.validate_database_config()
            all_errors.extend(db_result.errors)
            all_warnings.extend(db_result.warnings)
            if db_result.validated_config:
                combined_config.update(db_result.validated_config)
        
        # Return combined result
        success = len(all_errors) == 0
        return Validation_Result(
            success=success,
            errors=all_errors,
            warnings=all_warnings,
            validated_config=combined_config if success else None
        )

from sys import exc_info, _getframe
from traceback import format_exception, format_stack
from types import FrameType


class Scraper_Exception(Exception):
    """
    A custom exception class for scraper errors, capturing detailed error information.

    Attributes:
        message (str): The error message.
        code (int): The error code.
        file (str): A file where the error occurred.
        line (int): A line number where the error occurred.
        trace (str): The full traceback of the error.
    """
    message: str
    """The error message."""
    code: int
    """The error code."""
    file: str
    """A file where the error occurred."""
    line: int
    """A line number where the error occurred."""
    trace: str
    """The full traceback of the error."""

    def __init__(
        self,
        message: str,
        code: int = 500
    ) -> None:
        """
        Initializing a `Scraper_Exception` instance with a message and optional code.

        Parameters:
            message (str): The error message.
            code (int): The error code. Defaults to 500.
        """
        super().__init__(message)
        self.message = message
        self.code = code
        error_type, error, traceback_type = exc_info()
        has_a_traceback: bool = traceback_type is not None
        frame: FrameType = _getframe(1)
        self.file = traceback_type.tb_frame.f_code.co_filename if has_a_traceback else frame.f_code.co_filename
        self.line = traceback_type.tb_lineno if has_a_traceback else frame.f_lineno
        self.trace = "".join(format_exception(error_type, error, traceback_type)) if has_a_traceback else "".join(format_stack(frame))

"""
Unit tests for Sanitizer interface.

Tests the abstract sanitizer interface contract.

Author:
    Darkness4869
"""

from __future__ import annotations
import unittest
from abc import ABC
from typing import Any

from Models.Sanitizer import Sanitizer


class Test_Sanitizer_Interface(unittest.TestCase):
    """Testing Sanitizer abstract interface."""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """Testing abstract class cannot be instantiated."""
        with self.assertRaises(TypeError):
            Sanitizer()  # type: ignore

    def test_subclass_must_implement_sanitize(self) -> None:
        """Testing subclass must implement sanitize method."""
        class Incomplete_Sanitizer(Sanitizer):
            pass

        with self.assertRaises(TypeError):
            Incomplete_Sanitizer()  # type: ignore

    def test_concrete_implementation_works(self) -> None:
        """Testing concrete implementation can be instantiated and used."""
        class Concrete_Sanitizer(Sanitizer):
            def sanitize(self, data: Any) -> Any:
                return str(data).strip()

        sanitizer = Concrete_Sanitizer()
        result = sanitizer.sanitize("  test  ")
        self.assertEqual(result, "test")
        self.assertTrue(callable(sanitizer.sanitize))


if __name__ == "__main__":
    unittest.main()

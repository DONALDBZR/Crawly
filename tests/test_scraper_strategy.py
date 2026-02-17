"""
Unit tests for Scraper_Strategy interface.

Tests the abstract scraper strategy interface contract.

Author:
    Darkness4869
"""

from __future__ import annotations
import unittest
from typing import Any, Dict

from Models.ScraperStrategy import Scraper_Strategy


class Test_Scraper_Strategy_Interface(unittest.TestCase):
    """Testing Scraper_Strategy abstract interface."""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """Testing abstract class cannot be instantiated."""
        with self.assertRaises(TypeError):
            Scraper_Strategy()  # type: ignore

    def test_subclass_must_implement_all_methods(self) -> None:
        """Testing subclass must implement all abstract methods."""
        class Incomplete_Strategy(Scraper_Strategy):
            def identifier(self) -> str:
                return "incomplete"
        
        with self.assertRaises(TypeError):
            Incomplete_Strategy()  # type: ignore

    def test_concrete_implementation_works(self) -> None:
        """Testing concrete implementation with all methods."""
        class Concrete_Strategy(Scraper_Strategy):
            def identifier(self) -> str:
                return "concrete"
            
            def fetch(self, context: Dict[str, Any]) -> str:
                return "data"
            
            def extract(self, raw: str) -> Dict[str, Any]:
                return {"field": "value"}
            
            def normalize(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
                return {"normalized": extracted}
        
        strategy = Concrete_Strategy()
        self.assertEqual(strategy.identifier(), "concrete")
        self.assertEqual(strategy.fetch({}), "data")
        self.assertEqual(strategy.extract("raw"), {"field": "value"})
        self.assertEqual(strategy.normalize({"test": "data"}), {"normalized": {"test": "data"}})


class Test_Scraper_Strategy_Should_Retry(unittest.TestCase):
    """Testing Scraper_Strategy.should_retry() default implementation."""

    def test_default_should_retry_implementation(self) -> None:
        """Testing default should_retry() returns True for attempts < 3."""
        class Minimal_Strategy(Scraper_Strategy):
            def identifier(self) -> str:
                return "minimal"
            
            def fetch(self, context: Dict[str, Any]) -> str:
                return ""
            
            def extract(self, raw: str) -> Dict[str, Any]:
                return {}
            
            def normalize(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
                return {}
        
        strategy = Minimal_Strategy()
        
        # Default implementation allows retry for attempts < 3
        self.assertTrue(strategy.should_retry(Exception("test"), 1))
        self.assertTrue(strategy.should_retry(Exception("test"), 2))
        self.assertFalse(strategy.should_retry(Exception("test"), 3))


if __name__ == "__main__":
    unittest.main()

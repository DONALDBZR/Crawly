"""
Crawly scraper strategy implementations.

This package contains concrete implementations of the Scraper_Strategy interface.
Each strategy encapsulates target-specific logic for fetching, extracting, and normalizing data from different sources.
"""

from Strategies.MnsHtmlScraperStrategy import Mns_Html_Scraper_Strategy


STRATEGY_REGISTRY = {
    "mns": Mns_Html_Scraper_Strategy,
    "mns_html": Mns_Html_Scraper_Strategy,
}
__all__ = ["Mns_Html_Scraper_Strategy", "STRATEGY_REGISTRY"]

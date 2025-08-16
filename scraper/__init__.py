"""
Modular Web Scraper System

A comprehensive web scraping solution with:
- Async scraping with Playwright and BeautifulSoup
- Pagination support
- Concurrency management
- Data validation with Pydantic
- PostgreSQL integration
- Airflow orchestration
- FastAPI control interface
- Docker containerization
"""

__version__ = "1.0.0"
__author__ = "Web Scraper Team"

from .config_loader import create_default_config, load_config
from .core_scraper import run_scraper, scrape_data, scrape_data_with_pagination
from .data_models import ScrapedItem, ScrapedItemDB, ScrapingConfig, ScrapingResult
from .load_data import DatabaseManager, insert_data, insert_raw_data

__all__ = [
    'scrape_data',
    'scrape_data_with_pagination',
    'run_scraper',
    'ScrapedItem',
    'ScrapedItemDB',
    'ScrapingConfig',
    'ScrapingResult',
    'load_config',
    'create_default_config',
    'DatabaseManager',
    'insert_data',
    'insert_raw_data'
]

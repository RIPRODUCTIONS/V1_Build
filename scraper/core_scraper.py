import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import Dict, List
import aiohttp
from concurrent.futures import ThreadPoolExecutor

async def scrape_data(url: str, selectors: Dict[str, str]) -> Dict[str, str]:
    """
    Navigates to the given URL using Playwright, waits for a specific element,
    extracts data using BeautifulSoup based on selectors, and returns a dict of scraped data.

    Args:
        url (str): The URL to scrape.
        selectors (Dict[str, str]): A dictionary where keys are field names and values are CSS selectors.

    Returns:
        Dict[str, str]: Scraped data.
    """
    data = {}
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Wait for a key element to be visible (use the first selector as an example)
            first_selector = next(iter(selectors.values()))
            await page.wait_for_selector(first_selector, timeout=10000)

            # Get page content and parse with BeautifulSoup
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')

            # Extract data
            for field, selector in selectors.items():
                element = soup.select_one(selector)
                data[field] = element.text.strip() if element else "Not found"

            await browser.close()
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        for field in selectors:
            data[field] = "Error"

    return data

async def scrape_data_with_pagination(url: str, selectors: Dict[str, str], next_page_selector: str = None) -> List[Dict[str, str]]:
    """
    Expanded to handle pagination: Detects and clicks 'next page' button, recursively scrapes until no more pages.

    Args:
        url (str): Starting URL.
        selectors (Dict[str, str]): Field selectors.
        next_page_selector (str, optional): CSS selector for the 'next page' link/button.

    Returns:
        List[Dict[str, str]]: All scraped data from all pages.
    """
    all_data = []
    current_url = url
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(current_url, wait_until="domcontentloaded", timeout=30000)

            while True:
                # Wait for content
                first_selector = next(iter(selectors.values()))
                await page.wait_for_selector(first_selector, timeout=10000)

                # Parse and extract
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                page_data = {}
                for field, selector in selectors.items():
                    element = soup.select_one(selector)
                    page_data[field] = element.text.strip() if element else "Not found"
                all_data.append(page_data)

                # Check for next page
                if next_page_selector:
                    next_button = await page.query_selector(next_page_selector)
                    if next_button and await next_button.is_enabled():
                        await next_button.click()
                        await page.wait_for_load_state("domcontentloaded", timeout=10000)
                    else:
                        break
                else:
                    break

            await browser.close()
    except Exception as e:
        print(f"Error during pagination on {url}: {e}")

    return all_data

async def run_scraper(urls: List[str], selectors: Dict[str, str], next_page_selector: str = None, max_concurrent: int = 5) -> List[List[Dict[str, str]]]:
    """
    Runs scrape_data concurrently on a list of URLs using asyncio, limiting concurrent connections.

    Args:
        urls (List[str]): List of URLs to scrape.
        selectors (Dict[str, str]): Field selectors.
        next_page_selector (str, optional): For pagination.
        max_concurrent (int): Max simultaneous scrapes (default: 5).

    Returns:
        List[List[Dict[str, str]]]: Aggregated results from all URLs.
    """
    all_results = []
    semaphore = asyncio.Semaphore(max_concurrent)

    async def bounded_scrape(url):
        async with semaphore:
            return await scrape_data_with_pagination(url, selectors, next_page_selector)

    tasks = [bounded_scrape(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if not isinstance(result, Exception):
            all_results.append(result)

    return all_results

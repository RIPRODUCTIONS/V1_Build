#!/usr/bin/env python3
"""
Main scraper script for the modular web scraper system.
Can be run directly or as a Docker container entry point.
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Add the scraper directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config_loader import create_default_config, load_config
from core_scraper import run_scraper
from load_data import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main function for the scraper"""
    parser = argparse.ArgumentParser(description='Modular Web Scraper')
    parser.add_argument('--urls', nargs='+', help='URLs to scrape')
    parser.add_argument('--urls-file', help='File containing URLs (one per line)')
    parser.add_argument('--selectors', help='JSON string of CSS selectors')
    parser.add_argument('--selectors-file', help='File containing CSS selectors in JSON format')
    parser.add_argument('--next-page-selector', help='CSS selector for next page button')
    parser.add_argument('--max-concurrent', type=int, default=5, help='Maximum concurrent scrapes')
    parser.add_argument('--output', help='Output file for results (JSON)')
    parser.add_argument('--save-to-db', action='store_true', help='Save results to database')
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('--create-config', action='store_true', help='Create default configuration file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create default config if requested
    if args.create_config:
        create_default_config(args.config)
        logger.info(f"Default configuration created at {args.config}")
        return

    # Load configuration
    try:
        config = load_config(args.config)
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        logger.info("Creating default configuration...")
        create_default_config(args.config)
        config = load_config(args.config)

    # Get URLs
    urls = []
    if args.urls:
        urls = args.urls
    elif args.urls_file:
        try:
            with open(args.urls_file) as f:
                urls = [line.strip() for line in f if line.strip()]
        except Exception as e:
            logger.error(f"Failed to read URLs file: {e}")
            return 1
    else:
        logger.error("No URLs provided. Use --urls or --urls-file")
        return 1

    if not urls:
        logger.error("No valid URLs found")
        return 1

    logger.info(f"Found {len(urls)} URLs to scrape")

    # Get selectors
    selectors = {}
    if args.selectors:
        try:
            selectors = json.loads(args.selectors)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in selectors: {e}")
            return 1
    elif args.selectors_file:
        try:
            with open(args.selectors_file) as f:
                selectors = json.load(f)
        except Exception as e:
            logger.error(f"Failed to read selectors file: {e}")
            return 1
    else:
        # Use default selectors from config
        selectors = config.get('selectors', {})

    if not selectors:
        logger.error("No selectors provided. Use --selectors, --selectors-file, or configure in config.yaml")
        return 1

    logger.info(f"Using selectors: {list(selectors.keys())}")

    # Get next page selector
    next_page_selector = args.next_page_selector or config.get('next_page_selector')
    if next_page_selector:
        logger.info(f"Using next page selector: {next_page_selector}")

    # Get max concurrent setting
    max_concurrent = args.max_concurrent or config.get('max_concurrent', 5)
    logger.info(f"Maximum concurrent scrapes: {max_concurrent}")

    # Run the scraper
    try:
        logger.info("Starting scraping operation...")
        start_time = asyncio.get_event_loop().time()

        results = await run_scraper(
            urls=urls,
            selectors=selectors,
            next_page_selector=next_page_selector,
            max_concurrent=max_concurrent
        )

        execution_time = asyncio.get_event_loop().time() - start_time

        # Process results
        all_data = []
        total_pages = 0

        for page_data in results:
            if isinstance(page_data, list):
                all_data.extend(page_data)
                total_pages += 1
            else:
                all_data.append(page_data)
                total_pages += 1

        logger.info(f"Scraping completed in {execution_time:.2f} seconds")
        logger.info(f"Processed {total_pages} pages, extracted {len(all_data)} items")

        # Save to database if requested
        if args.save_to_db:
            try:
                db_manager = DatabaseManager()
                db_manager.create_tables()

                # Group data by source URL
                for url in urls:
                    url_data = [item for item in all_data if item.get('url', '').startswith(url)]
                    if url_data:
                        success = db_manager.insert_raw_data(url_data, url)
                        if success:
                            logger.info(f"Saved {len(url_data)} items from {url} to database")
                        else:
                            logger.warning(f"Failed to save data from {url} to database")

            except Exception as e:
                logger.error(f"Database operation failed: {e}")

        # Save to output file if requested
        if args.output:
            try:
                output_path = Path(args.output)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, 'w') as f:
                    json.dump({
                        'metadata': {
                            'total_urls': len(urls),
                            'total_pages': total_pages,
                            'total_items': len(all_data),
                            'execution_time': execution_time,
                            'timestamp': asyncio.get_event_loop().time()
                        },
                        'data': all_data
                    }, f, indent=2, default=str)

                logger.info(f"Results saved to {output_path}")

            except Exception as e:
                logger.error(f"Failed to save output file: {e}")

        # Print summary
        print("\n=== Scraping Summary ===")
        print(f"URLs processed: {len(urls)}")
        print(f"Pages scraped: {total_pages}")
        print(f"Items extracted: {len(all_data)}")
        print(f"Execution time: {execution_time:.2f} seconds")
        print(f"Average items per page: {len(all_data)/total_pages:.1f}" if total_pages > 0 else "No pages processed")

        if args.save_to_db:
            print("Data saved to database: Yes")
        if args.output:
            print(f"Output file: {args.output}")

        return 0

    except Exception as e:
        logger.error(f"Scraping operation failed: {e}")
        return 1

def run_example():
    """Run an example scraping operation"""
    example_urls = [
        'https://httpbin.org/html',
        'https://httpbin.org/json'
    ]

    example_selectors = {
        'title': 'h1',
        'content': 'p',
        'status': '.status'
    }

    print("Running example scraping operation...")
    print(f"URLs: {example_urls}")
    print(f"Selectors: {example_selectors}")

    # This would run the actual scraping
    # For now, just show what would happen
    print("\nExample completed (demo mode)")

if __name__ == "__main__":
    try:
        # Check if running in demo mode
        if len(sys.argv) == 1:
            print("No arguments provided. Running example...")
            run_example()
        else:
            exit_code = asyncio.run(main())
            sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

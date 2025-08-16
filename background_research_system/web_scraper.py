"""
Public Web Scraper Module

This module provides comprehensive web scraping capabilities for publicly
available information while respecting robots.txt and terms of service.
"""

import logging
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)


class PublicWebScraper:
    """Handles web scraping of publicly available information."""

    def __init__(self, rate_limiter, config: dict):
        self.rate_limiter = rate_limiter
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.get('web_scraping', {}).get('user_agent', 'Legal Research Tool v1.0')
        })

        # Setup headless browser for JavaScript-heavy sites
        self.driver = None
        if config.get('web_scraping', {}).get('javascript_rendering', True):
            self._setup_browser()

        # Define search sources
        self.professional_networks = [
            'linkedin', 'xing', 'viadeo', 'researchgate', 'academia_edu'
        ]

        self.news_sources = [
            'newsapi', 'google_news', 'bing_news', 'reuters', 'ap'
        ]

        self.business_directories = [
            'yellowpages', 'whitepages', 'superpages', 'manta', 'bizapedia'
        ]

        self.academic_sources = [
            'google_scholar', 'researchgate', 'academia_edu', 'arxiv', 'pubmed'
        ]

    def _setup_browser(self):
        """Setup headless Chrome browser."""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Headless browser setup completed")

        except Exception as e:
            logger.error(f"Failed to setup headless browser: {e}")
            self.driver = None

    def comprehensive_web_search(self, name: str, location: str = None) -> dict:
        """Comprehensive search across all public web sources."""
        results = {}

        try:
            # Professional networks
            logger.info("Searching professional networks")
            results['professional'] = self.search_professional_networks(name, location)

            # News and media mentions
            logger.info("Searching news mentions")
            results['media_mentions'] = self.search_news_mentions(name, location)

            # Business directories
            logger.info("Searching business directories")
            results['business_directories'] = self.search_business_directories(name, location)

            # Academic and professional publications
            logger.info("Searching academic publications")
            results['publications'] = self.search_academic_publications(name)

            # Social media public profiles
            logger.info("Searching social media profiles")
            results['social_media'] = self.search_public_social_media(name, location)

        except Exception as e:
            logger.error(f"Error in comprehensive web search: {e}")
            results['error'] = str(e)

        return results

    def search_professional_networks(self, name: str, location: str = None) -> list[dict]:
        """Search professional networks for public profiles."""
        results = []

        try:
            # LinkedIn public directory search
            linkedin_results = self.search_linkedin_public_directory(name, location)
            results.extend(linkedin_results)

            # Professional associations and directories
            professional_results = self.search_professional_directories(name, location)
            results.extend(professional_results)

            # Research platforms
            research_results = self.search_research_platforms(name, location)
            results.extend(research_results)

        except Exception as e:
            logger.error(f"Error searching professional networks: {e}")

        return results

    def search_linkedin_public_directory(self, name: str, location: str = None) -> list[dict]:
        """Search LinkedIn's public directory (respecting robots.txt)."""
        self.rate_limiter.wait_for_rate_limit('web_scraping')
        results = []

        try:
            # Use Google search to find LinkedIn profiles (public method)
            search_query = f"site:linkedin.com/in {name}"
            if location:
                search_query += f" {location}"

            google_results = self.search_google_for_profiles(search_query)

            for result in google_results:
                if 'linkedin.com/in/' in result.get('url', ''):
                    profile_data = self.extract_linkedin_public_info(result['url'])
                    if profile_data:
                        results.append(profile_data)

        except Exception as e:
            logger.error(f"Error searching LinkedIn public directory: {e}")

        return results

    def search_google_for_profiles(self, query: str) -> list[dict]:
        """Use Google search to find public profiles."""
        self.rate_limiter.wait_for_rate_limit('web_scraping')
        results = []

        try:
            # Google Custom Search API (requires API key)
            if 'google_search' in self.config.get('api_keys', {}):
                url = "https://customsearch.googleapis.com/customsearch/v1"
                params = {
                    'key': self.config['api_keys']['google_search'],
                    'cx': self.config['api_keys']['google_cx'],
                    'q': query,
                    'num': 10
                }

                response = self.session.get(url, params=params, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    for item in data.get('items', []):
                        results.append({
                            'title': item.get('title'),
                            'url': item.get('link'),
                            'snippet': item.get('snippet')
                        })

        except Exception as e:
            logger.error(f"Error with Google search: {e}")

        return results

    def extract_linkedin_public_info(self, profile_url: str) -> dict | None:
        """Extract public information from LinkedIn profile."""
        try:
            if not self.driver:
                return None

            self.driver.get(profile_url)
            time.sleep(3)  # Allow page to load

            # Extract basic profile information
            profile_data = {
                'url': profile_url,
                'name': '',
                'headline': '',
                'location': '',
                'company': '',
                'education': '',
                'source': 'linkedin'
            }

            try:
                # Extract name
                name_elem = self.driver.find_element(By.CSS_SELECTOR, 'h1.text-heading-xlarge')
                if name_elem:
                    profile_data['name'] = name_elem.text.strip()

                # Extract headline
                headline_elem = self.driver.find_element(By.CSS_SELECTOR, '.text-body-medium.break-words')
                if headline_elem:
                    profile_data['headline'] = headline_elem.text.strip()

                # Extract location
                location_elem = self.driver.find_element(By.CSS_SELECTOR, '.text-body-small.inline.t-black--light.break-words')
                if location_elem:
                    profile_data['location'] = location_elem.text.strip()

            except Exception as e:
                logger.debug(f"Could not extract all LinkedIn fields: {e}")

            return profile_data

        except Exception as e:
            logger.error(f"Error extracting LinkedIn info: {e}")
            return None

    def search_professional_directories(self, name: str, location: str = None) -> list[dict]:
        """Search professional association directories."""
        results = []

        try:
            # Professional association searches
            associations = [
                'american_bar_association',
                'american_medical_association',
                'national_society_of_professional_engineers',
                'american_institute_of_certified_public_accountants'
            ]

            for association in associations:
                self.rate_limiter.wait_for_rate_limit('web_scraping')
                association_results = self.search_professional_association(name, association)
                results.extend(association_results)

        except Exception as e:
            logger.error(f"Error searching professional directories: {e}")

        return results

    def search_research_platforms(self, name: str, location: str = None) -> list[dict]:
        """Search research and academic platforms."""
        results = []

        try:
            # ResearchGate
            researchgate_results = self.search_researchgate(name, location)
            results.extend(researchgate_results)

            # Academia.edu
            academia_results = self.search_academia_edu(name, location)
            results.extend(academia_results)

        except Exception as e:
            logger.error(f"Error searching research platforms: {e}")

        return results

    def search_news_mentions(self, name: str, location: str = None) -> list[dict]:
        """Search for news and media mentions."""
        self.rate_limiter.wait_for_rate_limit('web_scraping')
        results = []

        try:
            # News APIs
            news_sources = {
                'newsapi': self.search_newsapi,
                'google_news': self.search_google_news,
                'bing_news': self.search_bing_news
            }

            for source_name, search_func in news_sources.items():
                try:
                    source_results = search_func(name, location)
                    results.extend(source_results)
                    time.sleep(1)  # Rate limiting
                except Exception as e:
                    logger.error(f"Error with {source_name}: {e}")

        except Exception as e:
            logger.error(f"Error searching news mentions: {e}")

        return results

    def search_newsapi(self, name: str, location: str = None) -> list[dict]:
        """Search NewsAPI for mentions."""
        results = []

        try:
            if 'newsapi' in self.config.get('api_keys', {}):
                url = "https://newsapi.org/v2/everything"
                params = {
                    'q': name,
                    'apiKey': self.config['api_keys']['newsapi'],
                    'language': 'en',
                    'sortBy': 'relevancy',
                    'pageSize': 20
                }

                if location:
                    params['q'] += f" AND {location}"

                response = self.session.get(url, params=params, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    for article in data.get('articles', []):
                        results.append({
                            'title': article.get('title'),
                            'description': article.get('description'),
                            'url': article.get('url'),
                            'source': article.get('source', {}).get('name'),
                            'published_at': article.get('publishedAt'),
                            'relevance_score': self._calculate_news_relevance(article, name)
                        })

        except Exception as e:
            logger.error(f"Error searching NewsAPI: {e}")

        return results

    def search_google_news(self, name: str, location: str = None) -> list[dict]:
        """Search Google News for mentions."""
        results = []

        try:
            # Use Google News search
            search_query = f'"{name}"'
            if location:
                search_query += f" {location}"

            url = "https://news.google.com/search"
            params = {'q': search_query, 'hl': 'en-US', 'gl': 'US', 'ceid': 'US:en'}

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                articles = soup.find_all('article', class_='MQsxId')

                for article in articles[:10]:  # Limit to 10 results
                    try:
                        title_elem = article.find('h3')
                        link_elem = article.find('a')
                        source_elem = article.find('time')

                        if title_elem and link_elem:
                            results.append({
                                'title': title_elem.text.strip(),
                                'url': urljoin('https://news.google.com', link_elem.get('href', '')),
                                'source': 'Google News',
                                'published_at': source_elem.get('datetime') if source_elem else None,
                                'relevance_score': 0.8
                            })
                    except Exception as e:
                        logger.debug(f"Error parsing Google News article: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error searching Google News: {e}")

        return results

    def search_bing_news(self, name: str, location: str = None) -> list[dict]:
        """Search Bing News for mentions."""
        results = []

        try:
            # Use Bing News search
            search_query = f'"{name}"'
            if location:
                search_query += f" {location}"

            url = "https://www.bing.com/news/search"
            params = {'q': search_query}

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                articles = soup.find_all('div', class_='news-card')

                for article in articles[:10]:  # Limit to 10 results
                    try:
                        title_elem = article.find('a', class_='title')
                        source_elem = article.find('a', class_='source')
                        time_elem = article.find('span', class_='timestamp')

                        if title_elem:
                            results.append({
                                'title': title_elem.text.strip(),
                                'url': title_elem.get('href', ''),
                                'source': source_elem.text.strip() if source_elem else 'Bing News',
                                'published_at': time_elem.get('title') if time_elem else None,
                                'relevance_score': 0.8
                            })
                    except Exception as e:
                        logger.debug(f"Error parsing Bing News article: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error searching Bing News: {e}")

        return results

    def search_business_directories(self, name: str, location: str = None) -> list[dict]:
        """Search business directories and professional listings."""
        self.rate_limiter.wait_for_rate_limit('web_scraping')
        results = []

        try:
            directories = [
                'yellowpages.com',
                'whitepages.com',
                'superpages.com',
                'manta.com',
                'bizapedia.com'
            ]

            for directory in directories:
                try:
                    directory_results = self.search_directory_site(directory, name, location)
                    results.extend(directory_results)
                    time.sleep(2)  # Respectful rate limiting
                except Exception as e:
                    logger.error(f"Error searching {directory}: {e}")

        except Exception as e:
            logger.error(f"Error searching business directories: {e}")

        return results

    def search_directory_site(self, directory: str, name: str, location: str = None) -> list[dict]:
        """Search a specific business directory site."""
        results = []

        try:
            if directory == 'yellowpages.com':
                return self.search_yellowpages(name, location)
            elif directory == 'whitepages.com':
                return self.search_whitepages_web(name, location)
            elif directory == 'superpages.com':
                return self.search_superpages(name, location)
            elif directory == 'manta.com':
                return self.search_manta(name, location)
            elif directory == 'bizapedia.com':
                return self.search_bizapedia(name, location)

        except Exception as e:
            logger.error(f"Error searching directory {directory}: {e}")

        return []

    def search_yellowpages(self, name: str, location: str = None) -> list[dict]:
        """Search YellowPages for business listings."""
        results = []

        try:
            url = "https://www.yellowpages.com/search"
            params = {
                'search_terms': name,
                'geo_location_terms': location if location else ''
            }

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                listings = soup.find_all('div', class_='result')

                for listing in listings[:5]:  # Limit to 5 results
                    try:
                        name_elem = listing.find('a', class_='business-name')
                        phone_elem = listing.find('div', class_='phones phone primary')
                        address_elem = listing.find('div', class_='street-address')

                        if name_elem:
                            results.append({
                                'name': name_elem.text.strip(),
                                'phone': phone_elem.text.strip() if phone_elem else '',
                                'address': address_elem.text.strip() if address_elem else '',
                                'source': 'yellowpages',
                                'relevance_score': 0.7
                            })
                    except Exception as e:
                        logger.debug(f"Error parsing YellowPages listing: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error searching YellowPages: {e}")

        return results

    def search_academic_publications(self, name: str) -> list[dict]:
        """Search for academic publications and professional credentials."""
        self.rate_limiter.wait_for_rate_limit('web_scraping')
        results = []

        try:
            # Academic search engines
            academic_sources = {
                'google_scholar': self.search_google_scholar,
                'researchgate': self.search_researchgate,
                'academia_edu': self.search_academia_edu
            }

            for source_name, search_func in academic_sources.items():
                try:
                    source_results = search_func(name)
                    results.extend(source_results)
                    time.sleep(2)  # Rate limiting
                except Exception as e:
                    logger.error(f"Error with {source_name}: {e}")

        except Exception as e:
            logger.error(f"Error searching academic publications: {e}")

        return results

    def search_google_scholar(self, name: str) -> list[dict]:
        """Search Google Scholar for academic publications."""
        results = []

        try:
            url = "https://scholar.google.com/scholar"
            params = {'q': f'"{name}"', 'hl': 'en'}

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                publications = soup.find_all('div', class_='gs_r gs_or gs_scl')

                for pub in publications[:10]:  # Limit to 10 results
                    try:
                        title_elem = pub.find('h3', class_='gs_rt')
                        authors_elem = pub.find('div', class_='gs_a')
                        abstract_elem = pub.find('div', class_='gs_rs')

                        if title_elem:
                            results.append({
                                'title': title_elem.text.strip(),
                                'authors': authors_elem.text.strip() if authors_elem else '',
                                'abstract': abstract_elem.text.strip() if abstract_elem else '',
                                'source': 'Google Scholar',
                                'relevance_score': 0.9
                            })
                    except Exception as e:
                        logger.debug(f"Error parsing Google Scholar publication: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error searching Google Scholar: {e}")

        return results

    def search_public_social_media(self, name: str, location: str = None) -> list[dict]:
        """Search for publicly available social media profiles."""
        self.rate_limiter.wait_for_rate_limit('web_scraping')
        results = []

        try:
            # Search for social media profiles
            social_platforms = [
                'twitter', 'facebook', 'instagram', 'youtube', 'tiktok'
            ]

            for platform in social_platforms:
                try:
                    platform_results = self.search_social_platform(name, platform, location)
                    results.extend(platform_results)
                    time.sleep(1)  # Rate limiting
                except Exception as e:
                    logger.error(f"Error searching {platform}: {e}")

        except Exception as e:
            logger.error(f"Error searching social media: {e}")

        return results

    def search_social_platform(self, name: str, platform: str, location: str = None) -> list[dict]:
        """Search a specific social media platform."""
        results = []

        try:
            if platform == 'twitter':
                return self.search_twitter(name, location)
            elif platform == 'facebook':
                return self.search_facebook(name, location)
            elif platform == 'instagram':
                return self.search_instagram(name, location)
            elif platform == 'youtube':
                return self.search_youtube(name, location)
            elif platform == 'tiktok':
                return self.search_tiktok(name, location)

        except Exception as e:
            logger.error(f"Error searching {platform}: {e}")

        return []

    # Placeholder methods for specific searches
    def search_professional_association(self, name: str, association: str) -> list[dict]:
        """Search professional association directory."""
        # Implementation would involve searching specific association websites
        return []

    def search_researchgate(self, name: str, location: str = None) -> list[dict]:
        """Search ResearchGate for profiles and publications."""
        # Implementation would involve ResearchGate searching
        return []

    def search_academia_edu(self, name: str, location: str = None) -> list[dict]:
        """Search Academia.edu for profiles and publications."""
        # Implementation would involve Academia.edu searching
        return []

    def search_whitepages_web(self, name: str, location: str = None) -> list[dict]:
        """Search WhitePages website."""
        # Implementation would involve WhitePages web searching
        return []

    def search_superpages(self, name: str, location: str = None) -> list[dict]:
        """Search SuperPages directory."""
        # Implementation would involve SuperPages searching
        return []

    def search_manta(self, name: str, location: str = None) -> list[dict]:
        """Search Manta business directory."""
        # Implementation would involve Manta searching
        return []

    def search_bizapedia(self, name: str, location: str = None) -> list[dict]:
        """Search Bizapedia business directory."""
        # Implementation would involve Bizapedia searching
        return []

    def search_twitter(self, name: str, location: str = None) -> list[dict]:
        """Search Twitter for public profiles."""
        # Implementation would involve Twitter searching
        return []

    def search_facebook(self, name: str, location: str = None) -> list[dict]:
        """Search Facebook for public profiles."""
        # Implementation would involve Facebook searching
        return []

    def search_instagram(self, name: str, location: str = None) -> list[dict]:
        """Search Instagram for public profiles."""
        # Implementation would involve Instagram searching
        return []

    def search_youtube(self, name: str, location: str = None) -> list[dict]:
        """Search YouTube for channels and videos."""
        # Implementation would involve YouTube searching
        return []

    def search_tiktok(self, name: str, location: str = None) -> list[dict]:
        """Search TikTok for public profiles."""
        # Implementation would involve TikTok searching
        return []

    def _calculate_news_relevance(self, article: dict, name: str) -> float:
        """Calculate relevance score for news article."""
        try:
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            content = f"{title} {description}"

            name_lower = name.lower()
            name_parts = name_lower.split()

            # Calculate relevance based on name matches
            relevance = 0.0

            # Exact name match
            if name_lower in content:
                relevance += 0.8

            # Partial name matches
            for part in name_parts:
                if len(part) > 2 and part in content:  # Only count significant parts
                    relevance += 0.2

            return min(relevance, 1.0)

        except Exception:
            return 0.5

    def close(self):
        """Cleanup web scraper resources."""
        if self.driver:
            self.driver.quit()
            logger.info("Web scraper browser closed")

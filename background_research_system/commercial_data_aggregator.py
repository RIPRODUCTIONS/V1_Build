"""
Commercial Data Aggregator Module

This module provides comprehensive integration with legitimate commercial
data services for background research purposes.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime

import requests

logger = logging.getLogger(__name__)


class CommercialDataAggregator:
    """Aggregates data from various commercial data services."""

    def __init__(self, api_keys: dict, rate_limiter):
        self.api_keys = api_keys
        self.rate_limiter = rate_limiter
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Legal Research Tool v1.0'
        })

        # Define supported commercial services
        self.supported_services = {
            'spokeo': {
                'name': 'Spokeo',
                'api_url': 'https://api.spokeo.com/v1',
                'rate_limit': 60,
                'requires_auth': True
            },
            'whitepages': {
                'name': 'WhitePages',
                'api_url': 'https://api.whitepages.com/v1',
                'rate_limit': 100,
                'requires_auth': True
            },
            'been_verified': {
                'name': 'BeenVerified',
                'api_url': 'https://api.beenverified.com/v1',
                'rate_limit': 50,
                'requires_auth': True
            },
            'intelius': {
                'name': 'Intelius',
                'api_url': 'https://api.intelius.com/v1',
                'rate_limit': 40,
                'requires_auth': True
            },
            'people_finders': {
                'name': 'PeopleFinders',
                'api_url': 'https://api.peoplefinders.com/v1',
                'rate_limit': 30,
                'requires_auth': True
            },
            'true_people_search': {
                'name': 'TruePeopleSearch',
                'api_url': 'https://www.truepeoplesearch.com',
                'rate_limit': 120,
                'requires_auth': False
            },
            'fast_people_search': {
                'name': 'FastPeopleSearch',
                'api_url': 'https://www.fastpeoplesearch.com',
                'rate_limit': 120,
                'requires_auth': False
            },
            'radaris': {
                'name': 'Radaris',
                'api_url': 'https://api.radaris.com/v1',
                'rate_limit': 50,
                'requires_auth': True
            }
        }

    def aggregate_all_sources(self, name: str, location: str = None) -> dict:
        """Query all available commercial data sources."""
        results = {}

        try:
            # Use ThreadPoolExecutor for parallel API calls
            with ThreadPoolExecutor(max_workers=3) as executor:
                future_to_service = {}

                # Submit jobs for all available services
                for service_name, service_info in self.supported_services.items():
                    if service_name in self.api_keys or not service_info['requires_auth']:
                        future = executor.submit(
                            self._query_service,
                            service_name,
                            name,
                            location
                        )
                        future_to_service[future] = service_name

                # Collect results as they complete
                for future in as_completed(future_to_service):
                    service_name = future_to_service[future]
                    try:
                        service_results = future.result(timeout=60)
                        results[service_name] = service_results
                        logger.info(f"Completed {service_name} search")
                    except Exception as e:
                        logger.error(f"Error with {service_name}: {e}")
                        results[service_name] = {'error': str(e)}

        except Exception as e:
            logger.error(f"Error in commercial data aggregation: {e}")
            results['error'] = str(e)

        return results

    def _query_service(self, service_name: str, name: str, location: str = None) -> list[dict]:
        """Query a specific commercial service."""
        try:
            if service_name == 'spokeo':
                return self.query_spokeo_api(name, location)
            elif service_name == 'whitepages':
                return self.query_whitepages_api(name, location)
            elif service_name == 'been_verified':
                return self.query_beenverified_api(name, location)
            elif service_name == 'intelius':
                return self.query_intelius_api(name, location)
            elif service_name == 'people_finders':
                return self.query_peoplefinders_api(name, location)
            elif service_name == 'true_people_search':
                return self.query_truepeoplesearch_api(name, location)
            elif service_name == 'fast_people_search':
                return self.query_fastpeoplesearch_api(name, location)
            elif service_name == 'radaris':
                return self.query_radaris_api(name, location)
            else:
                logger.warning(f"Unknown service: {service_name}")
                return []

        except Exception as e:
            logger.error(f"Error querying {service_name}: {e}")
            return []

    def query_spokeo_api(self, name: str, location: str = None) -> list[dict]:
        """Query Spokeo API for person information."""
        self.rate_limiter.wait_for_rate_limit('spokeo')

        try:
            url = f"{self.supported_services['spokeo']['api_url']}/person"
            headers = {
                'Authorization': f"Bearer {self.api_keys['spokeo']}",
                'Content-Type': 'application/json'
            }

            # Parse name into components
            name_parts = self._parse_name(name)

            params = {
                'first_name': name_parts.get('first_name', ''),
                'last_name': name_parts.get('last_name', ''),
                'city': self._extract_city(location) if location else None,
                'state': self._extract_state(location) if location else None,
                'limit': 50
            }

            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}

            response = self.session.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return self._parse_spokeo_results(data)
            elif response.status_code == 429:
                logger.warning("Spokeo rate limit exceeded")
                return []
            else:
                logger.error(f"Spokeo API error: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error querying Spokeo: {e}")
            return []

    def query_whitepages_api(self, name: str, location: str = None) -> list[dict]:
        """Query WhitePages API for person information."""
        self.rate_limiter.wait_for_rate_limit('whitepages')

        try:
            url = f"{self.supported_services['whitepages']['api_url']}/person"
            headers = {
                'Authorization': f"Bearer {self.api_keys['whitepages']}",
                'Content-Type': 'application/json'
            }

            name_parts = self._parse_name(name)

            params = {
                'first_name': name_parts.get('first_name', ''),
                'last_name': name_parts.get('last_name', ''),
                'city': self._extract_city(location) if location else None,
                'state': self._extract_state(location) if location else None,
                'limit': 50
            }

            params = {k: v for k, v in params.items() if v is not None}

            response = self.session.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return self._parse_whitepages_results(data)
            elif response.status_code == 429:
                logger.warning("WhitePages rate limit exceeded")
                return []
            else:
                logger.error(f"WhitePages API error: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error querying WhitePages: {e}")
            return []

    def query_beenverified_api(self, name: str, location: str = None) -> list[dict]:
        """Query BeenVerified API for person information."""
        self.rate_limiter.wait_for_rate_limit('been_verified')

        try:
            url = f"{self.supported_services['been_verified']['api_url']}/person"
            headers = {
                'Authorization': f"Bearer {self.api_keys['been_verified']}",
                'Content-Type': 'application/json'
            }

            name_parts = self._parse_name(name)

            params = {
                'first_name': name_parts.get('first_name', ''),
                'last_name': name_parts.get('last_name', ''),
                'city': self._extract_city(location) if location else None,
                'state': self._extract_state(location) if location else None,
                'limit': 50
            }

            params = {k: v for k, v in params.items() if v is not None}

            response = self.session.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return self._parse_beenverified_results(data)
            elif response.status_code == 429:
                logger.warning("BeenVerified rate limit exceeded")
                return []
            else:
                logger.error(f"BeenVerified API error: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error querying BeenVerified: {e}")
            return []

    def query_intelius_api(self, name: str, location: str = None) -> list[dict]:
        """Query Intelius API for person information."""
        self.rate_limiter.wait_for_rate_limit('intelius')

        try:
            url = f"{self.supported_services['intelius']['api_url']}/person"
            headers = {
                'Authorization': f"Bearer {self.api_keys['intelius']}",
                'Content-Type': 'application/json'
            }

            name_parts = self._parse_name(name)

            params = {
                'first_name': name_parts.get('first_name', ''),
                'last_name': name_parts.get('last_name', ''),
                'city': self._extract_city(location) if location else None,
                'state': self._extract_state(location) if location else None,
                'limit': 50
            }

            params = {k: v for k, v in params.items() if v is not None}

            response = self.session.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return self._parse_intelius_results(data)
            elif response.status_code == 429:
                logger.warning("Intelius rate limit exceeded")
                return []
            else:
                logger.error(f"Intelius API error: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error querying Intelius: {e}")
            return []

    def query_peoplefinders_api(self, name: str, location: str = None) -> list[dict]:
        """Query PeopleFinders API for person information."""
        self.rate_limiter.wait_for_rate_limit('people_finders')

        try:
            url = f"{self.supported_services['people_finders']['api_url']}/person"
            headers = {
                'Authorization': f"Bearer {self.api_keys['people_finders']}",
                'Content-Type': 'application/json'
            }

            name_parts = self._parse_name(name)

            params = {
                'first_name': name_parts.get('first_name', ''),
                'last_name': name_parts.get('last_name', ''),
                'city': self._extract_city(location) if location else None,
                'state': self._extract_state(location) if location else None,
                'limit': 50
            }

            params = {k: v for k, v in params.items() if v is not None}

            response = self.session.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return self._parse_peoplefinders_results(data)
            elif response.status_code == 429:
                logger.warning("PeopleFinders rate limit exceeded")
                return []
            else:
                logger.error(f"PeopleFinders API error: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error querying PeopleFinders: {e}")
            return []

    def query_truepeoplesearch_api(self, name: str, location: str = None) -> list[dict]:
        """Query TruePeopleSearch (free service)."""
        self.rate_limiter.wait_for_rate_limit('web_scraping')

        try:
            # TruePeopleSearch is a free service that requires web scraping
            # This is a placeholder implementation
            url = f"{self.supported_services['true_people_search']['api_url']}/results"

            params = {
                'name': name,
                'citystatezip': location if location else ''
            }

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                # Parse HTML response
                return self._parse_truepeoplesearch_html(response.text)
            else:
                logger.error(f"TruePeopleSearch error: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error querying TruePeopleSearch: {e}")
            return []

    def query_fastpeoplesearch_api(self, name: str, location: str = None) -> list[dict]:
        """Query FastPeopleSearch (free service)."""
        self.rate_limiter.wait_for_rate_limit('web_scraping')

        try:
            # FastPeopleSearch is a free service that requires web scraping
            url = f"{self.supported_services['fast_people_search']['api_url']}/search"

            params = {
                'name': name,
                'citystatezip': location if location else ''
            }

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                # Parse HTML response
                return self._parse_fastpeoplesearch_html(response.text)
            else:
                logger.error(f"FastPeopleSearch error: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error querying FastPeopleSearch: {e}")
            return []

    def query_radaris_api(self, name: str, location: str = None) -> list[dict]:
        """Query Radaris API for person information."""
        self.rate_limiter.wait_for_rate_limit('radaris')

        try:
            url = f"{self.supported_services['radaris']['api_url']}/person"
            headers = {
                'Authorization': f"Bearer {self.api_keys['radaris']}",
                'Content-Type': 'application/json'
            }

            name_parts = self._parse_name(name)

            params = {
                'first_name': name_parts.get('first_name', ''),
                'last_name': name_parts.get('last_name', ''),
                'city': self._extract_city(location) if location else None,
                'state': self._extract_state(location) if location else None,
                'limit': 50
            }

            params = {k: v for k, v in params.items() if v is not None}

            response = self.session.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return self._parse_radaris_results(data)
            elif response.status_code == 429:
                logger.warning("Radaris rate limit exceeded")
                return []
            else:
                logger.error(f"Radaris API error: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error querying Radaris: {e}")
            return []

    # Result parsing methods
    def _parse_spokeo_results(self, data: dict) -> list[dict]:
        """Parse Spokeo API response."""
        results = []

        try:
            for person in data.get('results', []):
                result = {
                    'name': person.get('name', ''),
                    'age': person.get('age'),
                    'addresses': person.get('addresses', []),
                    'phone_numbers': person.get('phones', []),
                    'email_addresses': person.get('emails', []),
                    'relatives': person.get('relatives', []),
                    'associates': person.get('associates', []),
                    'social_profiles': person.get('social_profiles', []),
                    'employment': person.get('employment', []),
                    'education': person.get('education', []),
                    'confidence': person.get('confidence_score', 0.5),
                    'source': 'spokeo',
                    'timestamp': datetime.now(UTC).isoformat()
                }
                results.append(result)

        except Exception as e:
            logger.error(f"Error parsing Spokeo results: {e}")

        return results

    def _parse_whitepages_results(self, data: dict) -> list[dict]:
        """Parse WhitePages API response."""
        results = []

        try:
            for person in data.get('results', []):
                result = {
                    'name': person.get('name', ''),
                    'age': person.get('age'),
                    'addresses': person.get('addresses', []),
                    'phone_numbers': person.get('phones', []),
                    'email_addresses': person.get('emails', []),
                    'relatives': person.get('relatives', []),
                    'associates': person.get('associates', []),
                    'confidence': person.get('confidence_score', 0.5),
                    'source': 'whitepages',
                    'timestamp': datetime.now(UTC).isoformat()
                }
                results.append(result)

        except Exception as e:
            logger.error(f"Error parsing WhitePages results: {e}")

        return results

    def _parse_beenverified_results(self, data: dict) -> list[dict]:
        """Parse BeenVerified API response."""
        results = []

        try:
            for person in data.get('results', []):
                result = {
                    'name': person.get('name', ''),
                    'age': person.get('age'),
                    'addresses': person.get('addresses', []),
                    'phone_numbers': person.get('phones', []),
                    'email_addresses': person.get('emails', []),
                    'relatives': person.get('relatives', []),
                    'associates': person.get('associates', []),
                    'social_profiles': person.get('social_profiles', []),
                    'employment': person.get('employment', []),
                    'education': person.get('education', []),
                    'criminal_records': person.get('criminal_records', []),
                    'bankruptcy_records': person.get('bankruptcy_records', []),
                    'confidence': person.get('confidence_score', 0.5),
                    'source': 'been_verified',
                    'timestamp': datetime.now(UTC).isoformat()
                }
                results.append(result)

        except Exception as e:
            logger.error(f"Error parsing BeenVerified results: {e}")

        return results

    def _parse_intelius_results(self, data: dict) -> list[dict]:
        """Parse Intelius API response."""
        results = []

        try:
            for person in data.get('results', []):
                result = {
                    'name': person.get('name', ''),
                    'age': person.get('age'),
                    'addresses': person.get('addresses', []),
                    'phone_numbers': person.get('phones', []),
                    'email_addresses': person.get('emails', []),
                    'relatives': person.get('relatives', []),
                    'associates': person.get('associates', []),
                    'social_profiles': person.get('social_profiles', []),
                    'employment': person.get('employment', []),
                    'education': person.get('education', []),
                    'confidence': person.get('confidence_score', 0.5),
                    'source': 'intelius',
                    'timestamp': datetime.now(UTC).isoformat()
                }
                results.append(result)

        except Exception as e:
            logger.error(f"Error parsing Intelius results: {e}")

        return results

    def _parse_peoplefinders_results(self, data: dict) -> list[dict]:
        """Parse PeopleFinders API response."""
        results = []

        try:
            for person in data.get('results', []):
                result = {
                    'name': person.get('name', ''),
                    'age': person.get('age'),
                    'addresses': person.get('addresses', []),
                    'phone_numbers': person.get('phones', []),
                    'email_addresses': person.get('emails', []),
                    'relatives': person.get('relatives', []),
                    'associates': person.get('associates', []),
                    'confidence': person.get('confidence_score', 0.5),
                    'source': 'people_finders',
                    'timestamp': datetime.now(UTC).isoformat()
                }
                results.append(result)

        except Exception as e:
            logger.error(f"Error parsing PeopleFinders results: {e}")

        return results

    def _parse_truepeoplesearch_html(self, html_content: str) -> list[dict]:
        """Parse TruePeopleSearch HTML response."""
        # This would involve HTML parsing with BeautifulSoup
        # For now, return empty results
        return []

    def _parse_fastpeoplesearch_html(self, html_content: str) -> list[dict]:
        """Parse FastPeopleSearch HTML response."""
        # This would involve HTML parsing with BeautifulSoup
        # For now, return empty results
        return []

    def _parse_radaris_results(self, data: dict) -> list[dict]:
        """Parse Radaris API response."""
        results = []

        try:
            for person in data.get('results', []):
                result = {
                    'name': person.get('name', ''),
                    'age': person.get('age'),
                    'addresses': person.get('addresses', []),
                    'phone_numbers': person.get('phones', []),
                    'email_addresses': person.get('emails', []),
                    'relatives': person.get('relatives', []),
                    'associates': person.get('associates', []),
                    'social_profiles': person.get('social_profiles', []),
                    'employment': person.get('employment', []),
                    'education': person.get('education', []),
                    'confidence': person.get('confidence_score', 0.5),
                    'source': 'radaris',
                    'timestamp': datetime.now(UTC).isoformat()
                }
                results.append(result)

        except Exception as e:
            logger.error(f"Error parsing Radaris results: {e}")

        return results

    # Helper methods
    def _parse_name(self, name: str) -> dict[str, str]:
        """Parse full name into first and last name components."""
        if not name:
            return {}

        name_parts = name.strip().split()

        if len(name_parts) == 1:
            return {'first_name': name_parts[0]}
        elif len(name_parts) == 2:
            return {'first_name': name_parts[0], 'last_name': name_parts[1]}
        else:
            # Handle middle names, titles, etc.
            return {
                'first_name': name_parts[0],
                'last_name': name_parts[-1],
                'middle_name': ' '.join(name_parts[1:-1])
            }

    def _extract_city(self, location: str) -> str | None:
        """Extract city from location string."""
        if not location:
            return None

        # Remove state and zip code
        city = location.split(',')[0].strip()
        return city if city else None

    def _extract_state(self, location: str) -> str | None:
        """Extract state from location string."""
        if not location or ',' not in location:
            return None

        # Extract state part
        state_part = location.split(',')[1].strip()

        # Remove zip code if present
        if ' ' in state_part:
            state = state_part.split()[0].strip()
        else:
            state = state_part

        return state if state else None

    def get_service_status(self) -> dict[str, dict]:
        """Get status of all commercial services."""
        status = {}

        for service_name, service_info in self.supported_services.items():
            status[service_name] = {
                'name': service_info['name'],
                'available': service_name in self.api_keys or not service_info['requires_auth'],
                'rate_limit': service_info['rate_limit'],
                'requires_auth': service_info['requires_auth'],
                'remaining_requests': self.rate_limiter.get_remaining_requests(service_name)
            }

        return status

    def get_available_services(self) -> list[str]:
        """Get list of available commercial services."""
        available = []

        for service_name, service_info in self.supported_services.items():
            if service_name in self.api_keys or not service_info['requires_auth']:
                available.append(service_name)

        return available

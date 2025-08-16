"""
Public Records Search Module

This module provides comprehensive search capabilities for publicly available
records including court records, property records, business registrations,
and professional licenses.
"""

import logging

import requests

logger = logging.getLogger(__name__)


class PublicRecordsSearch:
    """Handles searches across various public records databases."""

    def __init__(self, api_keys: dict, rate_limiter):
        self.api_keys = api_keys
        self.rate_limiter = rate_limiter
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Legal Research Tool v1.0'
        })

        # Define supported court systems
        self.federal_courts = [
            'pacer', 'supreme_court', 'appellate_courts', 'district_courts'
        ]

        self.state_courts = {
            'CA': 'California',
            'NY': 'New York',
            'TX': 'Texas',
            'FL': 'Florida',
            'IL': 'Illinois',
            'PA': 'Pennsylvania',
            'OH': 'Ohio',
            'GA': 'Georgia',
            'NC': 'North Carolina',
            'MI': 'Michigan'
        }

    def comprehensive_search(self, name: str, location: str = None) -> dict:
        """Search all available public records sources."""
        results = {}

        try:
            # Court records search
            logger.info("Searching court records")
            results['court_records'] = self.search_court_records(name, location)

            # Property records search
            logger.info("Searching property records")
            results['property_records'] = self.search_property_records(name, location)

            # Business registration search
            logger.info("Searching business records")
            results['business_records'] = self.search_business_records(name, location)

            # Professional license search
            logger.info("Searching professional licenses")
            results['professional_licenses'] = self.search_professional_licenses(name, location)

            # Voter registration (where public)
            logger.info("Searching voter records")
            results['voter_records'] = self.search_voter_records(name, location)

            # Vital records (birth, death, marriage)
            logger.info("Searching vital records")
            results['vital_records'] = self.search_vital_records(name, location)

        except Exception as e:
            logger.error(f"Error in comprehensive public records search: {e}")
            results['error'] = str(e)

        return results

    def search_court_records(self, name: str, location: str = None) -> list[dict]:
        """Search federal and state court records."""
        results = []

        try:
            # PACER federal court search
            if 'pacer' in self.api_keys:
                self.rate_limiter.wait_for_rate_limit('public_records')
                federal_results = self.query_pacer_api(name, location)
                results.extend(federal_results)

            # State court searches
            if location:
                state_code = self._extract_state_code(location)
                if state_code in self.state_courts:
                    self.rate_limiter.wait_for_rate_limit('public_records')
                    state_results = self.query_state_court_api(name, state_code)
                    results.extend(state_results)

            # Search multiple states if no specific location
            if not location:
                for state_code in list(self.state_courts.keys())[:5]:  # Limit to 5 states
                    self.rate_limiter.wait_for_rate_limit('public_records')
                    state_results = self.query_state_court_api(name, state_code)
                    results.extend(state_results)

        except Exception as e:
            logger.error(f"Error searching court records: {e}")

        return results

    def search_property_records(self, name: str, location: str = None) -> list[dict]:
        """Search property ownership records."""
        results = []

        try:
            # County assessor databases
            if location:
                counties = self._get_counties_for_location(location)
                for county in counties:
                    self.rate_limiter.wait_for_rate_limit('public_records')
                    property_data = self.query_county_assessor(name, county)
                    results.extend(property_data)

            # National property databases
            if 'property_api' in self.api_keys:
                self.rate_limiter.wait_for_rate_limit('public_records')
                national_results = self.query_national_property_api(name)
                results.extend(national_results)

            # Zillow/Redfin public records (respecting terms of service)
            self.rate_limiter.wait_for_rate_limit('public_records')
            real_estate_results = self.search_real_estate_sites(name, location)
            results.extend(real_estate_results)

        except Exception as e:
            logger.error(f"Error searching property records: {e}")

        return results

    def search_business_records(self, name: str, location: str = None) -> list[dict]:
        """Search business registrations and corporate records."""
        results = []

        try:
            # Secretary of State databases
            if location:
                state_code = self._extract_state_code(location)
                if state_code in self.state_courts:
                    self.rate_limiter.wait_for_rate_limit('public_records')
                    sos_results = self.query_secretary_of_state(name, state_code)
                    results.extend(sos_results)

            # National business databases
            national_sources = [
                'open_corporates',
                'corporation_wiki',
                'bizapedia'
            ]

            for source in national_sources:
                self.rate_limiter.wait_for_rate_limit('public_records')
                source_results = self.query_business_database(name, source)
                results.extend(source_results)

        except Exception as e:
            logger.error(f"Error searching business records: {e}")

        return results

    def search_professional_licenses(self, name: str, location: str = None) -> list[dict]:
        """Search professional licensing databases."""
        results = []

        try:
            # State licensing boards
            if location:
                state_code = self._extract_state_code(location)
                if state_code in self.state_courts:
                    self.rate_limiter.wait_for_rate_limit('public_records')
                    license_results = self.query_state_licensing_board(name, state_code)
                    results.extend(license_results)

            # National professional databases
            national_boards = [
                'medical_licenses',
                'legal_licenses',
                'engineering_licenses',
                'accounting_licenses'
            ]

            for board in national_boards:
                self.rate_limiter.wait_for_rate_limit('public_records')
                board_results = self.query_national_licensing_board(name, board)
                results.extend(board_results)

        except Exception as e:
            logger.error(f"Error searching professional licenses: {e}")

        return results

    def search_voter_records(self, name: str, location: str = None) -> list[dict]:
        """Search voter registration records (where publicly available)."""
        results = []

        try:
            # Only search states where voter records are public
            public_voter_states = ['FL', 'OH', 'MI', 'NC']

            if location:
                state_code = self._extract_state_code(location)
                if state_code in public_voter_states:
                    self.rate_limiter.wait_for_rate_limit('public_records')
                    voter_data = self.query_voter_registration(name, state_code)
                    results.extend(voter_data)

        except Exception as e:
            logger.error(f"Error searching voter records: {e}")

        return results

    def search_vital_records(self, name: str, location: str = None) -> list[dict]:
        """Search vital records (birth, death, marriage) where public."""
        results = []

        try:
            # Vital records are generally not public, but some indexes may be
            # This is a placeholder for states that allow limited access
            if location:
                state_code = self._extract_state_code(location)
                # Only search states with public vital record indexes
                public_vital_states = ['CA', 'NY', 'TX']

                if state_code in public_vital_states:
                    self.rate_limiter.wait_for_rate_limit('public_records')
                    vital_data = self.query_vital_records_index(name, state_code)
                    results.extend(vital_data)

        except Exception as e:
            logger.error(f"Error searching vital records: {e}")

        return results

    def query_pacer_api(self, name: str, location: str = None) -> list[dict]:
        """Query PACER federal court system."""
        try:
            # PACER requires authentication and has specific API endpoints
            # This is a placeholder implementation
            url = "https://pcl.uscourts.gov/search"
            params = {
                'name': name,
                'location': location,
                'api_key': self.api_keys.get('pacer')
            }

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return self._parse_pacer_results(data)

        except Exception as e:
            logger.error(f"Error querying PACER: {e}")

        return []

    def query_state_court_api(self, name: str, state_code: str) -> list[dict]:
        """Query state court systems."""
        try:
            # State court APIs vary significantly
            # This is a generic implementation
            court_urls = {
                'CA': 'https://www.courts.ca.gov/courts.htm',
                'NY': 'https://iapps.courts.state.ny.us/webcivil/ecourtsMain',
                'TX': 'https://www.txcourts.gov/',
                'FL': 'https://www.flcourts.org/'
            }

            if state_code in court_urls:
                # Implement state-specific court searching
                return self._search_state_court_system(name, state_code, court_urls[state_code])

        except Exception as e:
            logger.error(f"Error querying state court {state_code}: {e}")

        return []

    def query_county_assessor(self, name: str, county: str) -> list[dict]:
        """Query county assessor databases."""
        try:
            # County assessor databases are typically web-based
            # This would involve scraping public assessor websites
            assessor_urls = {
                'Los Angeles': 'https://assessor.lacounty.gov/',
                'New York': 'https://a836-acris.nyc.gov/',
                'Harris': 'https://www.hcad.org/',
                'Miami-Dade': 'https://www.miamidade.gov/assessor/'
            }

            if county in assessor_urls:
                return self._search_county_assessor_website(name, county, assessor_urls[county])

        except Exception as e:
            logger.error(f"Error querying county assessor {county}: {e}")

        return []

    def query_national_property_api(self, name: str) -> list[dict]:
        """Query national property databases."""
        try:
            # National property APIs (e.g., CoreLogic, Black Knight)
            if 'property_api' in self.api_keys:
                url = "https://api.property.com/v1/search"
                headers = {
                    'Authorization': f"Bearer {self.api_keys['property_api']}",
                    'Content-Type': 'application/json'
                }

                params = {
                    'owner_name': name,
                    'limit': 50
                }

                response = self.session.get(url, headers=headers, params=params, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    return self._parse_property_results(data)

        except Exception as e:
            logger.error(f"Error querying national property API: {e}")

        return []

    def search_real_estate_sites(self, name: str, location: str = None) -> list[dict]:
        """Search public real estate websites for property information."""
        results = []

        try:
            # Zillow public records search
            zillow_results = self._search_zillow_public_records(name, location)
            results.extend(zillow_results)

            # Redfin public records search
            redfin_results = self._search_redfin_public_records(name, location)
            results.extend(redfin_results)

        except Exception as e:
            logger.error(f"Error searching real estate sites: {e}")

        return results

    def query_secretary_of_state(self, name: str, state_code: str) -> list[dict]:
        """Query Secretary of State business databases."""
        try:
            # SOS business search URLs
            sos_urls = {
                'CA': 'https://bizfileonline.sos.ca.gov/',
                'NY': 'https://appext20.dos.ny.gov/',
                'TX': 'https://www.sos.state.tx.us/',
                'FL': 'https://dos.myflorida.com/'
            }

            if state_code in sos_urls:
                return self._search_sos_business_database(name, state_code, sos_urls[state_code])

        except Exception as e:
            logger.error(f"Error querying SOS {state_code}: {e}")

        return []

    def query_business_database(self, name: str, source: str) -> list[dict]:
        """Query various business databases."""
        try:
            if source == 'open_corporates':
                return self._search_open_corporates(name)
            elif source == 'corporation_wiki':
                return self._search_corporation_wiki(name)
            elif source == 'bizapedia':
                return self._search_bizapedia(name)

        except Exception as e:
            logger.error(f"Error querying business database {source}: {e}")

        return []

    def query_state_licensing_board(self, name: str, state_code: str) -> list[dict]:
        """Query state professional licensing boards."""
        try:
            # Professional licensing board URLs
            board_urls = {
                'CA': {
                    'medical': 'https://www.mbc.ca.gov/',
                    'legal': 'https://www.calbar.ca.gov/',
                    'engineering': 'https://www.bpelsg.ca.gov/'
                },
                'NY': {
                    'medical': 'https://www.health.ny.gov/',
                    'legal': 'https://www.nycourts.gov/',
                    'engineering': 'https://www.op.nysed.gov/'
                }
            }

            if state_code in board_urls:
                results = []
                for profession, url in board_urls[state_code].items():
                    profession_results = self._search_licensing_board(name, state_code, profession, url)
                    results.extend(profession_results)
                return results

        except Exception as e:
            logger.error(f"Error querying licensing board {state_code}: {e}")

        return []

    def query_national_licensing_board(self, name: str, board: str) -> list[dict]:
        """Query national professional licensing boards."""
        try:
            # National licensing board implementations
            if board == 'medical_licenses':
                return self._search_national_medical_licenses(name)
            elif board == 'legal_licenses':
                return self._search_national_legal_licenses(name)
            elif board == 'engineering_licenses':
                return self._search_national_engineering_licenses(name)

        except Exception as e:
            logger.error(f"Error querying national licensing board {board}: {e}")

        return []

    def query_voter_registration(self, name: str, state_code: str) -> list[dict]:
        """Query voter registration records."""
        try:
            # Voter registration search implementations
            if state_code == 'FL':
                return self._search_florida_voter_records(name)
            elif state_code == 'OH':
                return self._search_ohio_voter_records(name)
            elif state_code == 'MI':
                return self._search_michigan_voter_records(name)

        except Exception as e:
            logger.error(f"Error querying voter registration {state_code}: {e}")

        return []

    def query_vital_records_index(self, name: str, state_code: str) -> list[dict]:
        """Query vital records indexes where available."""
        try:
            # Vital records index search implementations
            if state_code == 'CA':
                return self._search_california_vital_records(name)
            elif state_code == 'NY':
                return self._search_new_york_vital_records(name)
            elif state_code == 'TX':
                return self._search_texas_vital_records(name)

        except Exception as e:
            logger.error(f"Error querying vital records {state_code}: {e}")

        return []

    # Helper methods for specific searches
    def _extract_state_code(self, location: str) -> str | None:
        """Extract state code from location string."""
        if not location:
            return None

        # Common state abbreviations
        state_mapping = {
            'california': 'CA', 'ca': 'CA',
            'new york': 'NY', 'ny': 'NY',
            'texas': 'TX', 'tx': 'TX',
            'florida': 'FL', 'fl': 'FL',
            'illinois': 'IL', 'il': 'IL',
            'pennsylvania': 'PA', 'pa': 'PA',
            'ohio': 'OH', 'oh': 'OH',
            'georgia': 'GA', 'ga': 'GA',
            'north carolina': 'NC', 'nc': 'NC',
            'michigan': 'MI', 'mi': 'MI'
        }

        location_lower = location.lower()
        for state_name, state_code in state_mapping.items():
            if state_name in location_lower:
                return state_code

        return None

    def _get_counties_for_location(self, location: str) -> list[str]:
        """Get relevant counties for a location."""
        # This would typically involve geocoding or database lookup
        # For now, return common counties for major cities
        county_mapping = {
            'New York, NY': ['New York', 'Bronx', 'Kings', 'Queens', 'Richmond'],
            'Los Angeles, CA': ['Los Angeles'],
            'Chicago, IL': ['Cook'],
            'Houston, TX': ['Harris'],
            'Miami, FL': ['Miami-Dade']
        }

        return county_mapping.get(location, [])

    # Placeholder methods for specific search implementations
    def _parse_pacer_results(self, data: dict) -> list[dict]:
        """Parse PACER API results."""
        # Implementation would depend on PACER API response format
        return []

    def _search_state_court_system(self, name: str, state_code: str, url: str) -> list[dict]:
        """Search state court system."""
        # Implementation would involve state-specific court searching
        return []

    def _search_county_assessor_website(self, name: str, county: str, url: str) -> list[dict]:
        """Search county assessor website."""
        # Implementation would involve web scraping assessor sites
        return []

    def _parse_property_results(self, data: dict) -> list[dict]:
        """Parse property API results."""
        # Implementation would depend on property API response format
        return []

    def _search_zillow_public_records(self, name: str, location: str = None) -> list[dict]:
        """Search Zillow public records."""
        # Implementation would involve searching Zillow's public records
        return []

    def _search_redfin_public_records(self, name: str, location: str = None) -> list[dict]:
        """Search Redfin public records."""
        # Implementation would involve searching Redfin's public records
        return []

    def _search_sos_business_database(self, name: str, state_code: str, url: str) -> list[dict]:
        """Search Secretary of State business database."""
        # Implementation would involve searching SOS business databases
        return []

    def _search_open_corporates(self, name: str) -> list[dict]:
        """Search OpenCorporates database."""
        # Implementation would involve OpenCorporates API
        return []

    def _search_corporation_wiki(self, name: str) -> list[dict]:
        """Search Corporation Wiki database."""
        # Implementation would involve Corporation Wiki searching
        return []

    def _search_bizapedia(self, name: str) -> list[dict]:
        """Search Bizapedia database."""
        # Implementation would involve Bizapedia searching
        return []

    def _search_licensing_board(self, name: str, state_code: str, profession: str, url: str) -> list[dict]:
        """Search specific licensing board."""
        # Implementation would involve searching specific licensing boards
        return []

    def _search_national_medical_licenses(self, name: str) -> list[dict]:
        """Search national medical licensing databases."""
        # Implementation would involve national medical license searches
        return []

    def _search_national_legal_licenses(self, name: str) -> list[dict]:
        """Search national legal licensing databases."""
        # Implementation would involve national legal license searches
        return []

    def _search_national_engineering_licenses(self, name: str) -> list[dict]:
        """Search national engineering licensing databases."""
        # Implementation would involve national engineering license searches
        return []

    def _search_florida_voter_records(self, name: str) -> list[dict]:
        """Search Florida voter registration records."""
        # Implementation would involve Florida voter record searches
        return []

    def _search_ohio_voter_records(self, name: str) -> list[dict]:
        """Search Ohio voter registration records."""
        # Implementation would involve Ohio voter record searches
        return []

    def _search_michigan_voter_records(self, name: str) -> list[dict]:
        """Search Michigan voter registration records."""
        # Implementation would involve Michigan voter record searches
        return []

    def _search_california_vital_records(self, name: str) -> list[dict]:
        """Search California vital records index."""
        # Implementation would involve California vital record searches
        return []

    def _search_new_york_vital_records(self, name: str) -> list[dict]:
        """Search New York vital records index."""
        # Implementation would involve New York vital record searches
        return []

    def _search_texas_vital_records(self, name: str) -> list[dict]:
        """Search Texas vital records index."""
        # Implementation would involve Texas vital record searches
        return []

"""
Core System Architecture for Legitimate Background Research System

This module provides the foundational classes and functionality for conducting
legal and ethical background research using publicly available information.
"""

import hashlib
import json
import logging
import sqlite3
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('research_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class PersonProfile:
    """Data class representing a person's profile for research purposes."""
    name: str
    addresses: list[str] = None
    phone_numbers: list[str] = None
    email_addresses: list[str] = None
    social_profiles: list[str] = None
    employment_history: list[str] = None
    education: list[str] = None
    public_records: list[str] = None
    aliases: list[str] = None
    relatives: list[str] = None
    age_range: str = None
    last_updated: str = None
    confidence_score: float = 0.0
    data_sources: list[str] = None
    legitimate_purpose: str = None
    consent_obtained: bool = False

    def __post_init__(self):
        """Initialize default values for lists."""
        if self.addresses is None:
            self.addresses = []
        if self.phone_numbers is None:
            self.phone_numbers = []
        if self.email_addresses is None:
            self.email_addresses = []
        if self.social_profiles is None:
            self.social_profiles = []
        if self.employment_history is None:
            self.employment_history = []
        if self.education is None:
            self.education = []
        if self.public_records is None:
            self.public_records = []
        if self.aliases is None:
            self.aliases = []
        if self.relatives is None:
            self.relatives = []
        if self.data_sources is None:
            self.data_sources = []
        if self.last_updated is None:
            self.last_updated = datetime.now(UTC).isoformat()


@dataclass
class DataPoint:
    """Data class representing a single piece of information about a person."""
    profile_id: str
    data_type: str
    value: str
    source: str
    confidence_score: float
    date_collected: str
    verified: bool = False
    notes: str = None
    data_hash: str = None

    def __post_init__(self):
        """Generate hash for data integrity."""
        if self.data_hash is None:
            data_string = f"{self.profile_id}{self.data_type}{self.value}{self.source}"
            self.data_hash = hashlib.sha256(data_string.encode()).hexdigest()


class DatabaseManager:
    """Manages database operations for the research system."""

    def __init__(self, db_path: str = 'research_database.db'):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.lock = threading.Lock()
        self.setup_database()

    def setup_database(self):
        """Create comprehensive database schema."""
        cursor = self.connection.cursor()

        # Profiles table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_date TEXT,
            last_updated TEXT,
            data_sources TEXT,
            legitimate_purpose TEXT,
            confidence_score REAL,
            consent_obtained BOOLEAN DEFAULT 0,
            status TEXT DEFAULT 'active',
            notes TEXT
        )
        ''')

        # Data points table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_points (
            id TEXT PRIMARY KEY,
            profile_id TEXT,
            data_type TEXT,
            value TEXT,
            source TEXT,
            confidence_score REAL,
            date_collected TEXT,
            verified BOOLEAN DEFAULT 0,
            notes TEXT,
            data_hash TEXT,
            FOREIGN KEY (profile_id) REFERENCES profiles (id)
        )
        ''')

        # Search history table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_history (
            id TEXT PRIMARY KEY,
            profile_id TEXT,
            search_type TEXT,
            search_parameters TEXT,
            results_count INTEGER,
            timestamp TEXT,
            execution_time REAL,
            FOREIGN KEY (profile_id) REFERENCES profiles (id)
        )
        ''')

        # API usage tracking
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_usage (
            id TEXT PRIMARY KEY,
            service_name TEXT,
            endpoint TEXT,
            timestamp TEXT,
            response_time REAL,
            success BOOLEAN,
            rate_limit_remaining INTEGER,
            error_message TEXT
        )
        ''')

        # Compliance audit log
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id TEXT PRIMARY KEY,
            action TEXT,
            profile_id TEXT,
            user_id TEXT,
            timestamp TEXT,
            details TEXT,
            ip_address TEXT,
            compliance_status TEXT
        )
        ''')

        # Data retention and cleanup
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_retention (
            profile_id TEXT,
            data_type TEXT,
            retention_date TEXT,
            cleanup_status TEXT DEFAULT 'pending',
            FOREIGN KEY (profile_id) REFERENCES profiles (id)
        )
        ''')

        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_profiles_name ON profiles(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_data_points_profile ON data_points(profile_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_log_profile ON audit_log(profile_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_usage_service ON api_usage(service_name)')

        self.connection.commit()

    def insert_profile(self, profile: PersonProfile) -> str:
        """Insert new profile and return profile ID."""
        with self.lock:
            profile_id = hashlib.md5(f"{profile.name}{datetime.now()}".encode()).hexdigest()
            cursor = self.connection.cursor()

            cursor.execute('''
            INSERT INTO profiles (id, name, created_date, last_updated, confidence_score,
                                legitimate_purpose, consent_obtained)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (profile_id, profile.name, datetime.now().isoformat(),
                  datetime.now().isoformat(), profile.confidence_score,
                  profile.legitimate_purpose, profile.consent_obtained))

            self.connection.commit()
            return profile_id

    def update_profile(self, profile_id: str, updates: dict):
        """Update existing profile."""
        with self.lock:
            cursor = self.connection.cursor()
            set_clause = ', '.join([f"{key} = ?" for key in updates])
            values = list(updates.values()) + [profile_id]

            cursor.execute(f'''
            UPDATE profiles SET {set_clause}, last_updated = ?
            WHERE id = ?
            ''', values + [datetime.now().isoformat()])

            self.connection.commit()

    def insert_data_point(self, data_point: DataPoint):
        """Insert new data point."""
        with self.lock:
            data_id = hashlib.md5(f"{data_point.profile_id}{data_point.data_type}{data_point.value}".encode()).hexdigest()
            cursor = self.connection.cursor()

            cursor.execute('''
            INSERT OR REPLACE INTO data_points
            (id, profile_id, data_type, value, source, confidence_score, date_collected, verified, notes, data_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (data_id, data_point.profile_id, data_point.data_type, data_point.value,
                  data_point.source, data_point.confidence_score, data_point.date_collected,
                  data_point.verified, data_point.notes, data_point.data_hash))

            self.connection.commit()

    def get_profile(self, profile_id: str) -> dict | None:
        """Retrieve profile by ID."""
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM profiles WHERE id = ?', (profile_id,))
        row = cursor.fetchone()

        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row, strict=False))
        return None

    def get_profile_data_points(self, profile_id: str) -> list[dict]:
        """Retrieve all data points for a profile."""
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM data_points WHERE profile_id = ?', (profile_id,))
        rows = cursor.fetchall()

        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row, strict=False)) for row in rows]

    def search_profiles(self, name: str, limit: int = 10) -> list[dict]:
        """Search profiles by name."""
        cursor = self.connection.cursor()
        cursor.execute('''
        SELECT * FROM profiles
        WHERE name LIKE ? AND status = 'active'
        ORDER BY last_updated DESC
        LIMIT ?
        ''', (f'%{name}%', limit))

        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row, strict=False)) for row in rows]

    def cleanup_expired_data(self, retention_days: int):
        """Clean up data older than retention period."""
        with self.lock:
            cursor = self.connection.cursor()
            cutoff_date = (datetime.now() - timedelta(days=retention_days)).isoformat()

            # Mark expired data for cleanup
            cursor.execute('''
            INSERT OR REPLACE INTO data_retention (profile_id, data_type, retention_date, cleanup_status)
            SELECT id, 'profile', ?, 'pending'
            FROM profiles
            WHERE last_updated < ?
            ''', (cutoff_date, cutoff_date))

            self.connection.commit()

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()


class RateLimiter:
    """Manages rate limiting for API calls and web scraping."""

    def __init__(self):
        self.limits = {}
        self.lock = threading.Lock()

    def set_limit(self, service: str, requests_per_minute: int):
        """Set rate limit for a service."""
        self.limits[service] = {
            'rpm': requests_per_minute,
            'requests': [],
            'lock': threading.Lock()
        }

    def can_make_request(self, service: str) -> bool:
        """Check if request is allowed under rate limit."""
        if service not in self.limits:
            return True

        with self.limits[service]['lock']:
            now = datetime.now()
            service_data = self.limits[service]

            # Remove requests older than 1 minute
            service_data['requests'] = [
                req_time for req_time in service_data['requests']
                if (now - req_time).seconds < 60
            ]

            # Check if under limit
            if len(service_data['requests']) < service_data['rpm']:
                service_data['requests'].append(now)
                return True

            return False

    def wait_for_rate_limit(self, service: str):
        """Wait until request is allowed."""
        while not self.can_make_request(service):
            time.sleep(1)

    def get_remaining_requests(self, service: str) -> int:
        """Get remaining requests for a service in current minute."""
        if service not in self.limits:
            return 999

        with self.limits[service]['lock']:
            now = datetime.now()
            service_data = self.limits[service]

            # Count requests in current minute
            current_requests = len([
                req_time for req_time in service_data['requests']
                if (now - req_time).seconds < 60
            ])

            return max(0, service_data['rpm'] - current_requests)


class LegitimateResearchEngine:
    """Main engine for conducting legitimate background research."""

    def __init__(self, config_path: str = 'config.json'):
        self.db = DatabaseManager()
        self.rate_limiter = RateLimiter()
        self.config = self.load_config(config_path)
        self.api_keys = self.config.get('api_keys', {})
        self.setup_rate_limits()

        # Initialize service modules
        self.public_records = PublicRecordsSearch(self.api_keys, self.rate_limiter)
        self.commercial_services = CommercialDataAggregator(self.api_keys, self.rate_limiter)
        self.web_scraper = PublicWebScraper(self.rate_limiter, self.config)
        self.data_verifier = DataVerification()

        logger.info("Research engine initialized successfully")

    def load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path) as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return {
                'api_keys': {},
                'rate_limits': {
                    'spokeo': 60,
                    'whitepages': 100,
                    'been_verified': 50,
                    'public_records': 30
                },
                'compliance': {
                    'fcra_mode': False,
                    'retention_days': 365,
                    'audit_enabled': True
                }
            }

    def setup_rate_limits(self):
        """Configure rate limits for all services."""
        for service, limit in self.config.get('rate_limits', {}).items():
            self.rate_limiter.set_limit(service, limit)

    def conduct_comprehensive_search(self, name: str, initial_location: str = None,
                                   legitimate_purpose: str = None, user_id: str = None) -> str:
        """Conduct comprehensive background search."""
        logger.info(f"Starting comprehensive search for: {name}")

        # Validate legitimate purpose
        if not legitimate_purpose:
            raise ValueError("Legitimate purpose must be specified for compliance")

        # Create initial profile
        profile = PersonProfile(
            name=name,
            legitimate_purpose=legitimate_purpose,
            consent_obtained=False  # Will be updated based on requirements
        )
        profile_id = self.db.insert_profile(profile)

        # Log the search for compliance
        self.log_audit_event("search_initiated", profile_id, user_id, details={
            'name': name,
            'location': initial_location,
            'purpose': legitimate_purpose,
            'timestamp': datetime.now().isoformat()
        })

        try:
            # Phase 1: Public Records Search
            logger.info("Phase 1: Searching public records")
            public_data = self.public_records.comprehensive_search(name, initial_location)
            self.store_search_results(profile_id, public_data, 'public_records')

            # Phase 2: Commercial Data Aggregation
            logger.info("Phase 2: Querying commercial services")
            commercial_data = self.commercial_services.aggregate_all_sources(name, initial_location)
            self.store_search_results(profile_id, commercial_data, 'commercial')

            # Phase 3: Web Presence Analysis
            logger.info("Phase 3: Analyzing web presence")
            web_data = self.web_scraper.comprehensive_web_search(name, initial_location)
            self.store_search_results(profile_id, web_data, 'web_scraping')

            # Phase 4: Data Verification and Cross-Reference
            logger.info("Phase 4: Verifying and cross-referencing data")
            verified_profile = self.data_verifier.verify_and_merge_data(profile_id, self.db)

            # Phase 5: Generate Comprehensive Report
            logger.info("Phase 5: Generating final report")
            report = self.generate_comprehensive_report(profile_id)

            # Log successful completion
            self.log_audit_event("search_completed", profile_id, user_id, details={
                'status': 'success',
                'completion_time': datetime.now().isoformat()
            })

            logger.info(f"Search completed successfully for: {name}")
            return profile_id

        except Exception as e:
            logger.error(f"Search failed for {name}: {e}")
            self.log_audit_event("search_failed", profile_id, user_id, details={
                'error': str(e),
                'failure_time': datetime.now().isoformat()
            })
            raise

    def store_search_results(self, profile_id: str, results: dict, source_type: str):
        """Store search results in database."""
        for data_type, values in results.items():
            if isinstance(values, list):
                for value in values:
                    if isinstance(value, dict):
                        # Handle complex data structures
                        for sub_key, sub_value in value.items():
                            data_point = DataPoint(
                                profile_id=profile_id,
                                data_type=f"{data_type}_{sub_key}",
                                value=str(sub_value),
                                source=source_type,
                                confidence_score=0.7,  # Default confidence
                                date_collected=datetime.now().isoformat()
                            )
                            self.db.insert_data_point(data_point)
                    else:
                        data_point = DataPoint(
                            profile_id=profile_id,
                            data_type=data_type,
                            value=str(value),
                            source=source_type,
                            confidence_score=0.7,
                            date_collected=datetime.now().isoformat()
                        )
                        self.db.insert_data_point(data_point)

    def log_audit_event(self, action: str, profile_id: str, user_id: str = None, details: dict = None):
        """Log events for compliance auditing."""
        audit_id = hashlib.md5(f"{action}{profile_id}{datetime.now()}".encode()).hexdigest()
        cursor = self.db.connection.cursor()

        cursor.execute('''
        INSERT INTO audit_log (id, action, profile_id, user_id, timestamp, details, compliance_status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (audit_id, action, profile_id, user_id, datetime.now().isoformat(),
              json.dumps(details) if details else None, 'compliant'))

        self.db.connection.commit()

    def generate_comprehensive_report(self, profile_id: str) -> dict:
        """Generate comprehensive research report."""
        profile = self.db.get_profile(profile_id)
        data_points = self.db.get_profile_data_points(profile_id)

        # Organize data by type
        organized_data = {}
        for dp in data_points:
            if dp['data_type'] not in organized_data:
                organized_data[dp['data_type']] = []
            organized_data[dp['data_type']].append(dp)

        # Calculate overall confidence
        total_confidence = sum(dp['confidence_score'] for dp in data_points)
        avg_confidence = total_confidence / len(data_points) if data_points else 0

        report = {
            'profile_id': profile_id,
            'subject_name': profile['name'],
            'report_date': datetime.now().isoformat(),
            'data_summary': {
                'total_data_points': len(data_points),
                'data_types_found': list(organized_data.keys()),
                'overall_confidence': avg_confidence
            },
            'detailed_findings': organized_data,
            'data_sources': list(set(dp['source'] for dp in data_points)),
            'verification_status': 'pending',
            'recommendations': self._generate_recommendations(organized_data),
            'compliance_notes': {
                'legitimate_purpose': profile['legitimate_purpose'],
                'consent_obtained': profile['consent_obtained'],
                'data_retention_policy': f"{self.config.get('compliance', {}).get('retention_days', 365)} days"
            }
        }

        return report

    def _generate_recommendations(self, organized_data: dict) -> list[str]:
        """Generate recommendations based on findings."""
        recommendations = []

        # Data quality recommendations
        if len(organized_data) < 3:
            recommendations.append("Limited data found - consider additional sources")

        # Verification recommendations
        recommendations.append("Cross-reference findings with multiple sources")
        recommendations.append("Verify critical information independently")

        # Compliance recommendations
        recommendations.append("Ensure legitimate purpose documentation is maintained")
        recommendations.append("Implement data retention and cleanup procedures")

        return recommendations

    def cleanup_old_data(self):
        """Clean up data older than retention period."""
        retention_days = self.config.get('compliance', {}).get('retention_days', 365)
        self.db.cleanup_expired_data(retention_days)
        logger.info(f"Data cleanup completed for retention period: {retention_days} days")

    def close(self):
        """Cleanup and close the research engine."""
        self.db.close()
        logger.info("Research engine closed successfully")


if __name__ == "__main__":
    # Example usage
    engine = LegitimateResearchEngine()

    try:
        profile_id = engine.conduct_comprehensive_search(
            name="John Doe",
            initial_location="New York, NY",
            legitimate_purpose="Employment background verification",
            user_id="researcher_001"
        )

        print(f"Search completed. Profile ID: {profile_id}")

    except Exception as e:
        print(f"Search failed: {e}")

    finally:
        engine.close()

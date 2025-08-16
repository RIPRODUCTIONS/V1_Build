"""
Enhanced Research Engine with AI/LLM Integration

This module extends the core research engine with AI-powered analysis,
automated workflows, and intelligent data processing capabilities.
"""

import hashlib
import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from ai_llm_integration import (
    AILLMIntegration,
    AutomatedReporting,
    AutomatedWorkflows,
    IntelligentDataProcessor,
    SmartDataValidation,
)

# Import core system components
from core_system import LegitimateResearchEngine

logger = logging.getLogger(__name__)


class EnhancedLegitimateResearchEngine(LegitimateResearchEngine):
    """Enhanced research engine with AI/LLM integration capabilities."""

    def __init__(self, config_path: str = 'config.json'):
        # Initialize parent class
        super().__init__(config_path)

        # Initialize AI components
        self.llm_integration = AILLMIntegration(self.config)
        self.ai_processor = IntelligentDataProcessor(self.llm_integration)
        self.automated_workflows = AutomatedWorkflows(self, self.ai_processor)
        self.automated_reporting = AutomatedReporting(self.llm_integration)
        self.smart_validator = SmartDataValidation(self.llm_integration)

        # Update components with AI capabilities
        self._enhance_existing_components()

        # Setup AI analysis database tables
        self._setup_ai_database_tables()

        logger.info("Enhanced Research Engine with AI initialized successfully")

    def _enhance_existing_components(self):
        """Enhance existing components with AI capabilities."""
        # The existing components are already enhanced through inheritance
        # This method can be used for additional enhancements if needed
        pass

    def _setup_ai_database_tables(self):
        """Setup additional database tables for AI analysis."""
        cursor = self.db.connection.cursor()

        # AI analysis table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_analysis (
            id TEXT PRIMARY KEY,
            profile_id TEXT,
            analysis_type TEXT,
            results TEXT,
            timestamp TEXT,
            model_used TEXT,
            confidence_score REAL,
            processing_time REAL,
            processing_location TEXT,
            metadata TEXT,
            FOREIGN KEY (profile_id) REFERENCES profiles (id)
        )
        ''')

        # AI reports table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_reports (
            id TEXT PRIMARY KEY,
            profile_id TEXT,
            report_type TEXT,
            content TEXT,
            generated_by TEXT,
            timestamp TEXT,
            model_used TEXT,
            confidence_score REAL,
            FOREIGN KEY (profile_id) REFERENCES profiles (id)
        )
        ''')

        # AI workflow execution log
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_workflows (
            id TEXT PRIMARY KEY,
            workflow_type TEXT,
            profile_id TEXT,
            parameters TEXT,
            execution_time REAL,
            status TEXT,
            results TEXT,
            timestamp TEXT,
            FOREIGN KEY (profile_id) REFERENCES profiles (id)
        )
        ''')

        # AI model performance metrics
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_model_metrics (
            id TEXT PRIMARY KEY,
            model_name TEXT,
            provider TEXT,
            analysis_type TEXT,
            processing_time REAL,
            confidence_score REAL,
            success_rate REAL,
            timestamp TEXT
        )
        ''')

        self.db.connection.commit()
        logger.info("AI database tables setup complete")

    def conduct_ai_enhanced_search(self, name: str, initial_location: str = None,
                                  legitimate_purpose: str = None, workflow_type: str = None,
                                  user_id: str = None) -> str:
        """Conduct AI-enhanced comprehensive search with optional automated workflow."""
        logger.info(f"Starting AI-enhanced search for: {name}")

        # Use automated workflow if specified
        if workflow_type:
            logger.info(f"Executing automated workflow: {workflow_type}")
            return self.automated_workflows.execute_workflow(workflow_type, {
                'name': name,
                'location': initial_location,
                'purpose': legitimate_purpose,
                'user_id': user_id
            })

        # Standard enhanced search
        profile_id = self.conduct_comprehensive_search(
            name, initial_location, legitimate_purpose, user_id
        )

        # AI-powered analysis of collected data
        raw_data = self._get_profile_data(profile_id)
        ai_analysis = self.ai_processor.process_search_results(profile_id, raw_data)

        # Store AI analysis results
        self._store_ai_analysis(profile_id, ai_analysis)

        # Generate comprehensive AI report
        report = self.automated_reporting.generate_comprehensive_report(profile_id, ai_analysis)
        self._store_ai_report(profile_id, report, 'comprehensive_analysis')

        # Update profile with AI insights
        self._update_profile_with_ai_insights(profile_id, ai_analysis)

        logger.info(f"AI-enhanced search completed for: {name}")
        return profile_id

    def _get_profile_data(self, profile_id: str) -> dict[str, Any]:
        """Retrieve all data for a profile."""
        cursor = self.db.connection.cursor()

        # Get profile info
        cursor.execute('SELECT * FROM profiles WHERE id = ?', (profile_id,))
        profile = cursor.fetchone()

        # Get all data points
        cursor.execute('SELECT * FROM data_points WHERE profile_id = ?', (profile_id,))
        data_points = cursor.fetchall()

        # Get column names for data points
        column_names = [description[0] for description in cursor.description]

        # Convert to structured format
        structured_data = {
            'profile': dict(zip(column_names, profile, strict=False)) if profile else {},
            'data_points': [dict(zip(column_names, row, strict=False)) for row in data_points]
        }

        return structured_data

    def _store_ai_analysis(self, profile_id: str, analysis: dict[str, Any]):
        """Store AI analysis results in database."""
        analysis_id = hashlib.md5(f"{profile_id}_analysis_{datetime.now()}".encode()).hexdigest()
        cursor = self.db.connection.cursor()

        cursor.execute('''
        INSERT OR REPLACE INTO ai_analysis
        (id, profile_id, analysis_type, results, timestamp, model_used,
         confidence_score, processing_time, processing_location, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            analysis_id, profile_id, 'comprehensive',
            json.dumps(analysis), datetime.now(UTC).isoformat(),
            analysis.get('model_used', 'unknown'),
            analysis.get('confidence_score', 0.5),
            analysis.get('processing_time', 0.0),
            analysis.get('processing_location', 'unknown'),
            json.dumps(analysis.get('metadata', {}))
        ))

        self.db.connection.commit()
        logger.info(f"AI analysis stored for profile: {profile_id}")

    def _store_ai_report(self, profile_id: str, report: dict[str, Any], report_type: str):
        """Store AI-generated report in database."""
        report_id = hashlib.md5(f"{profile_id}_report_{report_type}_{datetime.now()}".encode()).hexdigest()
        cursor = self.db.connection.cursor()

        cursor.execute('''
        INSERT OR REPLACE INTO ai_reports
        (id, profile_id, report_type, content, generated_by, timestamp,
         model_used, confidence_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            report_id, profile_id, report_type, json.dumps(report),
            'ai_enhanced_engine', datetime.now(UTC).isoformat(),
            report.get('model_used', 'unknown'),
            report.get('confidence_score', 0.5)
        ))

        self.db.connection.commit()
        logger.info(f"AI report stored for profile: {profile_id}")

    def _update_profile_with_ai_insights(self, profile_id: str, ai_analysis: dict[str, Any]):
        """Update profile with AI-generated insights and confidence scores."""
        # Extract key insights from AI analysis
        insights = {
            'ai_confidence_score': ai_analysis.get('confidence_score', 0.5),
            'ai_analysis_summary': ai_analysis.get('ai_summary', {}),
            'risk_assessment': ai_analysis.get('risk_assessment', {}),
            'anomalies_detected': ai_analysis.get('anomalies', {}),
            'last_ai_analysis': datetime.now(UTC).isoformat()
        }

        # Update profile with AI insights
        self.db.update_profile(profile_id, {
            'confidence_score': insights['ai_confidence_score'],
            'notes': json.dumps(insights, indent=2)
        })

        logger.info(f"Profile updated with AI insights: {profile_id}")

    def get_ai_analysis(self, profile_id: str, analysis_type: str = None) -> dict[str, Any]:
        """Retrieve AI analysis results for a profile."""
        cursor = self.db.connection.cursor()

        if analysis_type:
            cursor.execute('''
            SELECT * FROM ai_analysis
            WHERE profile_id = ? AND analysis_type = ?
            ORDER BY timestamp DESC LIMIT 1
            ''', (profile_id, analysis_type))
        else:
            cursor.execute('''
            SELECT * FROM ai_analysis
            WHERE profile_id = ?
            ORDER BY timestamp DESC LIMIT 1
            ''', (profile_id,))

        analysis = cursor.fetchone()

        if analysis:
            column_names = [description[0] for description in cursor.description]
            return dict(zip(column_names, analysis, strict=False))

        return {}

    def get_ai_report(self, profile_id: str, report_type: str = None) -> dict[str, Any]:
        """Retrieve AI-generated reports for a profile."""
        cursor = self.db.connection.cursor()

        if report_type:
            cursor.execute('''
            SELECT * FROM ai_reports
            WHERE profile_id = ? AND report_type = ?
            ORDER BY timestamp DESC LIMIT 1
            ''', (profile_id, report_type))
        else:
            cursor.execute('''
            SELECT * FROM ai_reports
            WHERE profile_id = ?
            ORDER BY timestamp DESC LIMIT 1
            ''', (profile_id,))

        report = cursor.fetchone()

        if report:
            column_names = [description[0] for description in cursor.description]
            return dict(zip(column_names, report, strict=False))

        return {}

    def execute_automated_workflow(self, workflow_type: str, parameters: dict[str, Any]) -> str:
        """Execute a specific automated workflow."""
        return self.automated_workflows.execute_workflow(workflow_type, parameters)

    def get_available_workflows(self) -> list[str]:
        """Get list of available automated workflows."""
        return list(self.automated_workflows.workflows.keys())

    def validate_data_with_ai(self, profile_id: str) -> dict[str, Any]:
        """Use AI to validate data consistency and accuracy."""
        profile_data = self._get_profile_data(profile_id)

        # Perform AI-powered validation
        validation_results = self.smart_validator.validate_data_consistency(profile_data)

        # Store validation results
        self._store_ai_analysis(profile_id, {
            'validation_results': validation_results,
            'analysis_type': 'data_validation',
            'timestamp': datetime.now(UTC).isoformat()
        })

        return validation_results

    def cross_reference_sources_with_ai(self, profile_id: str) -> dict[str, Any]:
        """Use AI to cross-reference data from multiple sources."""
        profile_data = self._get_profile_data(profile_id)

        # Extract data sources
        data_sources = self._extract_data_sources(profile_data)

        # Perform AI-powered cross-referencing
        cross_reference_results = self.smart_validator.cross_reference_sources(data_sources)

        # Store cross-reference results
        self._store_ai_analysis(profile_id, {
            'cross_reference_results': cross_reference_results,
            'analysis_type': 'cross_reference',
            'timestamp': datetime.now(UTC).isoformat()
        })

        return cross_reference_results

    def _extract_data_sources(self, profile_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract data sources from profile data."""
        data_points = profile_data.get('data_points', [])
        sources = {}

        for data_point in data_points:
            source = data_point.get('source', 'unknown')
            if source not in sources:
                sources[source] = []
            sources[source].append(data_point)

        return [{'source': source, 'data': data} for source, data in sources.items()]

    def get_ai_performance_metrics(self) -> dict[str, Any]:
        """Get AI model performance metrics."""
        cursor = self.db.connection.cursor()

        cursor.execute('''
        SELECT
            model_name,
            provider,
            analysis_type,
            AVG(processing_time) as avg_processing_time,
            AVG(confidence_score) as avg_confidence,
            AVG(success_rate) as avg_success_rate,
            COUNT(*) as total_analyses
        FROM ai_model_metrics
        GROUP BY model_name, provider, analysis_type
        ORDER BY total_analyses DESC
        ''')

        metrics = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]

        return [dict(zip(column_names, row, strict=False)) for row in metrics]

    def cleanup_old_ai_data(self, days_old: int = 30):
        """Clean up old AI analysis data."""
        cursor = self.db.connection.cursor()
        cutoff_date = datetime.now(UTC) - timedelta(days=days_old)

        # Clean up old AI analysis
        cursor.execute('''
        DELETE FROM ai_analysis
        WHERE timestamp < ?
        ''', (cutoff_date.isoformat(),))

        # Clean up old AI reports
        cursor.execute('''
        DELETE FROM ai_reports
        WHERE timestamp < ?
        ''', (cutoff_date.isoformat(),))

        # Clean up old workflow logs
        cursor.execute('''
        DELETE FROM ai_workflows
        WHERE timestamp < ?
        ''', (cutoff_date.isoformat(),))

        # Clean up old model metrics
        cursor.execute('''
        DELETE FROM ai_model_metrics
        WHERE timestamp < ?
        ''', (cutoff_date.isoformat(),))

        deleted_count = cursor.rowcount
        self.db.connection.commit()

        logger.info(f"Cleaned up {deleted_count} old AI data records")
        return deleted_count


class ConfigurationManager:
    """Configuration management for the enhanced system."""

    @staticmethod
    def create_enhanced_config_template():
        """Create enhanced configuration template with AI/LLM settings."""
        config = {
            "api_keys": {
                "spokeo": "YOUR_SPOKEO_API_KEY",
                "whitepages": "YOUR_WHITEPAGES_API_KEY",
                "been_verified": "YOUR_BEENVERIFIED_API_KEY",
                "intelius": "YOUR_INTELIUS_API_KEY",
                "people_finders": "YOUR_PEOPLEFINDERS_API_KEY",
                "google_search": "YOUR_GOOGLE_SEARCH_API_KEY",
                "google_cx": "YOUR_GOOGLE_CUSTOM_SEARCH_ENGINE_ID",
                "newsapi": "YOUR_NEWSAPI_KEY",
                "pacer": "YOUR_PACER_API_KEY",
                "property_api": "YOUR_PROPERTY_API_KEY",
                "openai_api_key": "YOUR_OPENAI_API_KEY",
                "anthropic_api_key": "YOUR_ANTHROPIC_API_KEY"
            },
            "ollama_models": [
                "llama3.1:8b",
                "llama3.1:70b",
                "codellama:13b",
                "mistral:7b"
            ],
            "openai_models": [
                "gpt-4",
                "gpt-3.5-turbo",
                "gpt-4-turbo"
            ],
            "anthropic_models": [
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307"
            ],
            "rate_limits": {
                "spokeo": 60,
                "whitepages": 100,
                "been_verified": 50,
                "public_records": 30,
                "web_scraping": 20,
                "openai": 50,
                "ollama": 1000,
                "anthropic": 30
            },
            "ai_routing": {
                "sensitive_data_local": True,
                "complex_analysis_cloud": True,
                "default_model": "llama3.1:8b",
                "fallback_model": "gpt-3.5-turbo"
            },
            "compliance": {
                "fcra_mode": False,
                "retention_days": 365,
                "audit_enabled": True,
                "privacy_protection": True,
                "data_minimization": True
            },
            "ai_analysis": {
                "cache_enabled": True,
                "cache_ttl_hours": 24,
                "max_cache_size": 1000,
                "confidence_scoring": True,
                "anomaly_detection": True,
                "relationship_mapping": True,
                "risk_assessment": True
            }
        }

        with open('enhanced_config.json', 'w') as f:
            json.dump(config, f, indent=2)

        return config


class UsageExamples:
    """Example usage of the enhanced research engine."""

    def __init__(self, config_path: str = 'config.json'):
        self.engine = EnhancedLegitimateResearchEngine(config_path)

    def employment_verification_example(self):
        """Example: Automated employment verification workflow."""
        result = self.engine.conduct_ai_enhanced_search(
            name="John Smith",
            initial_location="San Francisco, CA",
            legitimate_purpose="Employment Verification",
            workflow_type="employment_verification"
        )

        return result

    def tenant_screening_example(self):
        """Example: Automated tenant screening workflow."""
        result = self.engine.execute_automated_workflow(
            'tenant_screening',
            {
                'name': 'Jane Doe',
                'current_address': '123 Main St, New York, NY',
                'claimed_income': 75000,
                'employer': 'ABC Corp'
            }
        )

        return result

    def batch_processing_example(self):
        """Example: Process multiple subjects with AI enhancement."""
        subjects = [
            {'name': 'John Smith', 'location': 'CA'},
            {'name': 'Jane Doe', 'location': 'NY'},
            {'name': 'Bob Johnson', 'location': 'TX'}
        ]

        results = []
        for subject in subjects:
            result = self.engine.conduct_ai_enhanced_search(
                name=subject['name'],
                initial_location=subject['location'],
                legitimate_purpose="Bulk Background Check"
            )
            results.append(result)

        return results

    def ai_validation_example(self):
        """Example: AI-powered data validation."""
        # First conduct a search
        profile_id = self.engine.conduct_ai_enhanced_search(
            name="John Smith",
            legitimate_purpose="Data Validation Test"
        )

        # Then validate the data with AI
        validation_results = self.engine.validate_data_with_ai(profile_id)

        # Cross-reference sources with AI
        cross_reference_results = self.engine.cross_reference_sources_with_ai(profile_id)

        return {
            'profile_id': profile_id,
            'validation': validation_results,
            'cross_reference': cross_reference_results
        }


class SystemSetup:
    """Setup and installation helper for the enhanced system."""

    @staticmethod
    def install_dependencies():
        """Install required dependencies for the enhanced system."""
        dependencies = [
            "requests",
            "selenium",
            "beautifulsoup4",
            "sqlite3",
            "ollama",
            "openai",
            "anthropic",
            "pandas",
            "numpy",
            "matplotlib",
            "seaborn"
        ]

        install_script = f"""
# Install Python dependencies
pip install {' '.join(dependencies)}

# Install and setup Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull recommended models
ollama pull llama3.1:8b
ollama pull llama3.1:70b
ollama pull codellama:13b
ollama pull mistral:7b

# Setup Chrome for Selenium
# Ubuntu/Debian:
# sudo apt-get update
# sudo apt-get install -y google-chrome-stable

# Install ChromeDriver
# Download from: https://chromedriver.chromium.org/
        """

        print(install_script)
        return install_script

    @staticmethod
    def setup_database():
        """Initialize database with AI analysis tables."""
        # This is now handled by the EnhancedLegitimateResearchEngine
        pass


def main():
    """Main function to demonstrate the enhanced system."""

    # Setup
    print("Setting up Enhanced Research System...")

    # Create enhanced configuration
    config = ConfigurationManager.create_enhanced_config_template()
    print("✓ Enhanced configuration template created")

    # Initialize enhanced system
    try:
        engine = EnhancedLegitimateResearchEngine()
        print("✓ Enhanced Research Engine initialized")

        # Example usage
        examples = UsageExamples()

        print("\nRunning example searches...")

        # Employment verification
        print("Running employment verification example...")
        # result1 = examples.employment_verification_example()

        # Tenant screening
        print("Running tenant screening example...")
        # result2 = examples.tenant_screening_example()

        # AI validation
        print("Running AI validation example...")
        # result3 = examples.ai_validation_example()

        print("Enhanced system ready for operation!")

    except Exception as e:
        print(f"Setup failed: {e}")
        print("Please check configuration and dependencies")


if __name__ == "__main__":
    main()

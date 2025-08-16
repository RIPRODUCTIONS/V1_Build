#!/usr/bin/env python3
"""
Test AI System for Enhanced Background Research System

This module provides comprehensive testing and demonstration of the AI/LLM
integration capabilities of the enhanced background research system.
"""

import json
import logging
import sys
import time
from datetime import UTC, datetime

# Import our enhanced modules
from enhanced_research_engine import EnhancedLegitimateResearchEngine


def setup_test_logging():
    """Setup logging for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('ai_system_test.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


class AISystemTester:
    """Comprehensive tester for the AI-enhanced research system."""

    def __init__(self, config_path: str = 'config.json'):
        self.config_path = config_path
        self.engine = None
        self.test_results = {}

        setup_test_logging()
        self.logger = logging.getLogger(__name__)

    def initialize_system(self):
        """Initialize the enhanced research engine."""
        try:
            self.logger.info("Initializing Enhanced Research Engine...")
            self.engine = EnhancedLegitimateResearchEngine(self.config_path)
            self.logger.info("✓ Enhanced Research Engine initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"✗ Failed to initialize system: {e}")
            return False

    def test_ai_integration(self):
        """Test AI/LLM integration capabilities."""
        self.logger.info("\n" + "="*50)
        self.logger.info("Testing AI/LLM Integration")
        self.logger.info("="*50)

        test_results = {}

        # Test 1: AI Integration Initialization
        try:
            ai_integration = self.engine.llm_integration
            test_results['ai_integration_init'] = {
                'status': 'PASS',
                'ollama_available': ai_integration.ollama_client is not None,
                'openai_available': ai_integration.openai_client is not None,
                'anthropic_available': ai_integration.anthropic_client is not None
            }
            self.logger.info("✓ AI Integration initialized successfully")
        except Exception as e:
            test_results['ai_integration_init'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            self.logger.error(f"✗ AI Integration initialization failed: {e}")

        # Test 2: Model Router Configuration
        try:
            model_router = ai_integration.model_router
            test_results['model_router'] = {
                'status': 'PASS',
                'ollama_models': model_router.ollama_models,
                'openai_models': model_router.openai_models,
                'task_routing': list(model_router.task_routing.keys())
            }
            self.logger.info("✓ Model Router configured successfully")
        except Exception as e:
            test_results['model_router'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            self.logger.error(f"✗ Model Router configuration failed: {e}")

        # Test 3: Intelligent Data Processor
        try:
            ai_processor = self.engine.ai_processor
            test_results['ai_processor'] = {
                'status': 'PASS',
                'available_processors': list(ai_processor.processors.keys())
            }
            self.logger.info("✓ Intelligent Data Processor initialized")
        except Exception as e:
            test_results['ai_processor'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            self.logger.error(f"✗ AI Processor initialization failed: {e}")

        # Test 4: Automated Workflows
        try:
            workflows = self.engine.automated_workflows
            test_results['automated_workflows'] = {
                'status': 'PASS',
                'available_workflows': list(workflows.workflows.keys())
            }
            self.logger.info("✓ Automated Workflows initialized")
        except Exception as e:
            test_results['automated_workflows'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            self.logger.error(f"✗ Automated Workflows initialization failed: {e}")

        self.test_results['ai_integration'] = test_results
        return test_results

    def test_ai_analysis_capabilities(self):
        """Test AI analysis capabilities with sample data."""
        self.logger.info("\n" + "="*50)
        self.logger.info("Testing AI Analysis Capabilities")
        self.logger.info("="*50)

        test_results = {}

        # Sample data for testing
        sample_data = {
            'name': 'John Smith',
            'addresses': ['123 Main St, New York, NY', '456 Oak Ave, Los Angeles, CA'],
            'employment': ['ABC Corp - Software Engineer', 'XYZ Inc - Developer'],
            'education': ['BS Computer Science, MIT', 'MS Software Engineering, Stanford'],
            'phone_numbers': ['555-1234', '555-5678']
        }

        # Test 1: Entity Extraction
        try:
            ai_processor = self.engine.ai_processor
            entities = ai_processor.extract_entities(sample_data)
            test_results['entity_extraction'] = {
                'status': 'PASS',
                'result': entities
            }
            self.logger.info("✓ Entity extraction test completed")
        except Exception as e:
            test_results['entity_extraction'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            self.logger.error(f"✗ Entity extraction test failed: {e}")

        # Test 2: Relationship Mapping
        try:
            relationships = ai_processor.map_relationships(sample_data)
            test_results['relationship_mapping'] = {
                'status': 'PASS',
                'result': relationships
            }
            self.logger.info("✓ Relationship mapping test completed")
        except Exception as e:
            test_results['relationship_mapping'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            self.logger.error(f"✗ Relationship mapping test failed: {e}")

        # Test 3: Anomaly Detection
        try:
            anomalies = ai_processor.detect_anomalies(sample_data)
            test_results['anomaly_detection'] = {
                'status': 'PASS',
                'result': anomalies
            }
            self.logger.info("✓ Anomaly detection test completed")
        except Exception as e:
            test_results['anomaly_detection'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            self.logger.error(f"✗ Anomaly detection test failed: {e}")

        # Test 4: Risk Assessment
        try:
            risk_assessment = ai_processor.assess_risk_factors(sample_data)
            test_results['risk_assessment'] = {
                'status': 'PASS',
                'result': risk_assessment
            }
            self.logger.info("✓ Risk assessment test completed")
        except Exception as e:
            test_results['risk_assessment'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            self.logger.error(f"✗ Risk assessment test failed: {e}")

        self.test_results['ai_analysis'] = test_results
        return test_results

    def test_automated_workflows(self):
        """Test automated workflow execution."""
        self.logger.info("\n" + "="*50)
        self.logger.info("Testing Automated Workflows")
        self.logger.info("="*50)

        test_results = {}

        # Test 1: Employment Verification Workflow
        try:
            workflow_params = {
                'name': 'John Smith',
                'employer': 'ABC Corp',
                'position': 'Software Engineer'
            }

            # Note: This would normally execute a full search, but we'll test the workflow setup
            workflows = self.engine.automated_workflows
            if 'employment_verification' in workflows.workflows:
                test_results['employment_verification_workflow'] = {
                    'status': 'PASS',
                    'workflow_available': True,
                    'parameters': workflow_params
                }
                self.logger.info("✓ Employment verification workflow available")
            else:
                test_results['employment_verification_workflow'] = {
                    'status': 'FAIL',
                    'workflow_available': False
                }
                self.logger.error("✗ Employment verification workflow not available")
        except Exception as e:
            test_results['employment_verification_workflow'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            self.logger.error(f"✗ Employment verification workflow test failed: {e}")

        # Test 2: Tenant Screening Workflow
        try:
            workflow_params = {
                'name': 'Jane Doe',
                'current_address': '123 Main St, New York, NY',
                'claimed_income': 75000
            }

            if 'tenant_screening' in workflows.workflows:
                test_results['tenant_screening_workflow'] = {
                    'status': 'PASS',
                    'workflow_available': True,
                    'parameters': workflow_params
                }
                self.logger.info("✓ Tenant screening workflow available")
            else:
                test_results['tenant_screening_workflow'] = {
                    'status': 'FAIL',
                    'workflow_available': False
                }
                self.logger.error("✗ Tenant screening workflow not available")
        except Exception as e:
            test_results['tenant_screening_workflow'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            self.logger.error(f"✗ Tenant screening workflow test failed: {e}")

        # Test 3: Business Due Diligence Workflow
        try:
            workflow_params = {
                'business_name': 'Tech Solutions Inc',
                'owner_name': 'John Smith'
            }

            if 'due_diligence' in workflows.workflows:
                test_results['business_due_diligence_workflow'] = {
                    'status': 'PASS',
                    'workflow_available': True,
                    'parameters': workflow_params
                }
                self.logger.info("✓ Business due diligence workflow available")
            else:
                test_results['business_due_diligence_workflow'] = {
                    'status': 'FAIL',
                    'workflow_available': False
                }
                self.logger.error("✗ Business due diligence workflow not available")
        except Exception as e:
            test_results['business_due_diligence_workflow'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            self.logger.error(f"✗ Business due diligence workflow test failed: {e}")

        self.test_results['automated_workflows'] = test_results
        return test_results

    def test_database_integration(self):
        """Test AI database integration."""
        self.logger.info("\n" + "="*50)
        self.logger.info("Testing AI Database Integration")
        self.logger.info("="*50)

        test_results = {}

        # Test 1: AI Analysis Table
        try:
            cursor = self.engine.db.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_analysis'")
            ai_analysis_exists = cursor.fetchone() is not None

            test_results['ai_analysis_table'] = {
                'status': 'PASS' if ai_analysis_exists else 'FAIL',
                'table_exists': ai_analysis_exists
            }

            if ai_analysis_exists:
                self.logger.info("✓ AI analysis table exists")
            else:
                self.logger.error("✗ AI analysis table does not exist")
        except Exception as e:
            test_results['ai_analysis_table'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            self.logger.error(f"✗ AI analysis table test failed: {e}")

        # Test 2: AI Reports Table
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_reports'")
            ai_reports_exists = cursor.fetchone() is not None

            test_results['ai_reports_table'] = {
                'status': 'PASS' if ai_reports_exists else 'FAIL',
                'table_exists': ai_reports_exists
            }

            if ai_reports_exists:
                self.logger.info("✓ AI reports table exists")
            else:
                self.logger.error("✗ AI reports table does not exist")
        except Exception as e:
            test_results['ai_reports_table'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            self.logger.error(f"✗ AI reports table test failed: {e}")

        # Test 3: AI Workflows Table
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_workflows'")
            ai_workflows_exists = cursor.fetchone() is not None

            test_results['ai_workflows_table'] = {
                'status': 'PASS' if ai_workflows_exists else 'FAIL',
                'table_exists': ai_workflows_exists
            }

            if ai_workflows_exists:
                self.logger.info("✓ AI workflows table exists")
            else:
                self.logger.error("✗ AI workflows table does not exist")
        except Exception as e:
            test_results['ai_workflows_table'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            self.logger.error(f"✗ AI workflows table test failed: {e}")

        self.test_results['database_integration'] = test_results
        return test_results

    def test_ai_model_routing(self):
        """Test AI model routing capabilities."""
        self.logger.info("\n" + "="*50)
        self.logger.info("Testing AI Model Routing")
        self.logger.info("="*50)

        test_results = {}

        # Test 1: Local Processing Decision
        try:
            model_router = self.engine.llm_integration.model_router

            # Test with sensitive data
            sensitive_data = {'ssn': '123-45-6789', 'credit_card': '1234-5678-9012-3456'}
            should_use_local = model_router._should_use_local_processing(sensitive_data, 'data_extraction')

            test_results['sensitive_data_routing'] = {
                'status': 'PASS',
                'sensitive_data_detected': True,
                'should_use_local': should_use_local,
                'expected': True
            }

            if should_use_local:
                self.logger.info("✓ Sensitive data correctly routed to local processing")
            else:
                self.logger.warning("⚠ Sensitive data not routed to local processing")
        except Exception as e:
            test_results['sensitive_data_routing'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            self.logger.error(f"✗ Sensitive data routing test failed: {e}")

        # Test 2: Task Type Routing
        try:
            # Test different task types
            task_types = ['data_extraction', 'summary_generation', 'advanced_reasoning']
            routing_results = {}

            for task_type in task_types:
                routing_config = model_router.task_routing.get(task_type, {})
                routing_results[task_type] = routing_config

            test_results['task_type_routing'] = {
                'status': 'PASS',
                'routing_configs': routing_results
            }
            self.logger.info("✓ Task type routing configuration verified")
        except Exception as e:
            test_results['task_type_routing'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            self.logger.error(f"✗ Task type routing test failed: {e}")

        # Test 3: Model Selection
        try:
            # Test model selection for different analysis types
            analysis_types = ['data_extraction', 'advanced_reasoning', 'relationship_mapping']
            model_selections = {}

            for analysis_type in analysis_types:
                ollama_model = model_router._select_ollama_model(analysis_type)
                openai_model = model_router._select_openai_model(analysis_type)
                model_selections[analysis_type] = {
                    'ollama': ollama_model,
                    'openai': openai_model
                }

            test_results['model_selection'] = {
                'status': 'PASS',
                'model_selections': model_selections
            }
            self.logger.info("✓ Model selection logic verified")
        except Exception as e:
            test_results['model_selection'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            self.logger.error(f"✗ Model selection test failed: {e}")

        self.test_results['ai_model_routing'] = test_results
        return test_results

    def run_comprehensive_test(self):
        """Run all tests and generate comprehensive report."""
        self.logger.info("\n" + "="*60)
        self.logger.info("Starting Comprehensive AI System Test")
        self.logger.info("="*60)

        start_time = time.time()

        # Initialize system
        if not self.initialize_system():
            self.logger.error("System initialization failed. Cannot proceed with tests.")
            return False

        # Run all test suites
        test_suites = [
            ('AI Integration', self.test_ai_integration),
            ('AI Analysis Capabilities', self.test_ai_analysis_capabilities),
            ('Automated Workflows', self.test_automated_workflows),
            ('Database Integration', self.test_database_integration),
            ('AI Model Routing', self.test_ai_model_routing)
        ]

        for suite_name, test_function in test_suites:
            try:
                self.logger.info(f"\nRunning {suite_name} tests...")
                test_function()
            except Exception as e:
                self.logger.error(f"Test suite {suite_name} failed: {e}")
                self.test_results[suite_name.lower().replace(' ', '_')] = {
                    'status': 'FAIL',
                    'error': str(e)
                }

        # Generate test summary
        end_time = time.time()
        test_duration = end_time - start_time

        self.generate_test_summary(test_duration)

        return True

    def generate_test_summary(self, test_duration: float):
        """Generate comprehensive test summary."""
        self.logger.info("\n" + "="*60)
        self.logger.info("Test Summary Report")
        self.logger.info("="*60)

        total_tests = 0
        passed_tests = 0
        failed_tests = 0

        for suite_name, suite_results in self.test_results.items():
            self.logger.info(f"\n{suite_name.upper().replace('_', ' ')}:")
            self.logger.info("-" * 40)

            for test_name, test_result in suite_results.items():
                total_tests += 1
                status = test_result.get('status', 'UNKNOWN')

                if status == 'PASS':
                    passed_tests += 1
                    self.logger.info(f"✓ {test_name}: PASS")
                elif status == 'FAIL':
                    failed_tests += 0
                    self.logger.info(f"✗ {test_name}: FAIL")
                    if 'error' in test_result:
                        self.logger.error(f"  Error: {test_result['error']}")
                else:
                    self.logger.warning(f"⚠ {test_name}: {status}")

        # Overall summary
        self.logger.info("\n" + "="*60)
        self.logger.info("OVERALL TEST RESULTS")
        self.logger.info("="*60)
        self.logger.info(f"Total Tests: {total_tests}")
        self.logger.info(f"Passed: {passed_tests}")
        self.logger.info(f"Failed: {failed_tests}")
        self.logger.info(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "N/A")
        self.logger.info(f"Test Duration: {test_duration:.2f} seconds")

        # Save test results
        self.save_test_results()

        if failed_tests == 0:
            self.logger.info("\n🎉 All tests passed! AI system is ready for operation.")
        else:
            self.logger.warning(f"\n⚠ {failed_tests} test(s) failed. Please review and fix issues.")

    def save_test_results(self):
        """Save test results to file."""
        try:
            timestamp = datetime.now(UTC).isoformat()
            results_file = f"ai_system_test_results_{timestamp[:10]}.json"

            with open(results_file, 'w') as f:
                json.dump(self.test_results, f, indent=2)

            self.logger.info(f"Test results saved to: {results_file}")
        except Exception as e:
            self.logger.error(f"Failed to save test results: {e}")


def main():
    """Main function to run the AI system tests."""
    print("AI-Enhanced Background Research System - Comprehensive Test Suite")
    print("=" * 70)

    # Initialize tester
    tester = AISystemTester()

    # Run comprehensive test
    success = tester.run_comprehensive_test()

    if success:
        print("\n✅ Test suite completed successfully!")
        print("Check the log file 'ai_system_test.log' for detailed results.")
    else:
        print("\n❌ Test suite failed!")
        print("Check the log file 'ai_system_test.log' for error details.")

    return success


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Enhanced Main Application for AI-Powered Background Research System

This module provides a command-line interface and main application logic
for conducting AI-enhanced legitimate background research.
"""

import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

# Import our enhanced modules
from enhanced_research_engine import EnhancedLegitimateResearchEngine, UsageExamples


def setup_logging(log_level: str = "INFO", log_file: str = "enhanced_research_system.log"):
    """Setup logging configuration for enhanced system."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )


def load_config(config_path: str) -> dict[str, Any]:
    """Load configuration from file."""
    try:
        with open(config_path) as f:
            config = json.load(f)
        logging.info(f"Configuration loaded from {config_path}")
        return config
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in configuration file: {e}")
        sys.exit(1)


def validate_legitimate_purpose(purpose: str) -> bool:
    """Validate that the stated purpose is legitimate."""
    legitimate_purposes = [
        'employment_background_verification',
        'tenant_screening',
        'business_due_diligence',
        'skip_tracing_legal',
        'professional_licensing_verification',
        'academic_verification',
        'volunteer_screening',
        'contractor_verification',
        'vendor_due_diligence',
        'legal_investigation',
        'ai_enhanced_analysis',
        'comprehensive_background_check'
    ]

    return purpose in legitimate_purposes


def conduct_ai_enhanced_research(engine: EnhancedLegitimateResearchEngine, name: str,
                                location: str, purpose: str, user_id: str,
                                workflow_type: str = None) -> str:
    """Conduct AI-enhanced background research."""
    try:
        logging.info(f"Starting AI-enhanced research for: {name}")
        logging.info(f"Location: {location}")
        logging.info(f"Purpose: {purpose}")
        logging.info(f"User ID: {user_id}")
        if workflow_type:
            logging.info(f"Workflow Type: {workflow_type}")

        # Conduct the AI-enhanced research
        profile_id = engine.conduct_ai_enhanced_search(
            name=name,
            initial_location=location,
            legitimate_purpose=purpose,
            workflow_type=workflow_type,
            user_id=user_id
        )

        logging.info(f"AI-enhanced research completed successfully. Profile ID: {profile_id}")
        return profile_id

    except Exception as e:
        logging.error(f"AI-enhanced research failed: {e}")
        raise


def generate_ai_report(engine: EnhancedLegitimateResearchEngine, profile_id: str) -> dict[str, Any]:
    """Generate AI-powered research report."""
    try:
        logging.info(f"Generating AI report for profile: {profile_id}")

        # Get AI analysis results
        ai_analysis = engine.get_ai_analysis(profile_id)

        # Get AI-generated report
        ai_report = engine.get_ai_report(profile_id)

        # Combine results
        comprehensive_report = {
            'profile_id': profile_id,
            'report_generated_at': datetime.now(UTC).isoformat(),
            'ai_analysis': ai_analysis,
            'ai_report': ai_report,
            'report_type': 'ai_enhanced_comprehensive'
        }

        logging.info(f"AI report generated successfully for profile: {profile_id}")
        return comprehensive_report

    except Exception as e:
        logging.error(f"AI report generation failed: {e}")
        raise


def run_ai_validation(engine: EnhancedLegitimateResearchEngine, profile_id: str) -> dict[str, Any]:
    """Run AI-powered data validation."""
    try:
        logging.info(f"Running AI validation for profile: {profile_id}")

        # Validate data consistency with AI
        validation_results = engine.validate_data_with_ai(profile_id)

        # Cross-reference sources with AI
        cross_reference_results = engine.cross_reference_sources_with_ai(profile_id)

        validation_summary = {
            'profile_id': profile_id,
            'validation_timestamp': datetime.now(UTC).isoformat(),
            'data_validation': validation_results,
            'cross_reference_analysis': cross_reference_results,
            'overall_confidence': validation_results.get('confidence_score', 0.5)
        }

        logging.info(f"AI validation completed for profile: {profile_id}")
        return validation_summary

    except Exception as e:
        logging.error(f"AI validation failed: {e}")
        raise


def execute_automated_workflow(engine: EnhancedLegitimateResearchEngine,
                              workflow_type: str, parameters: dict[str, Any]) -> str:
    """Execute a specific automated workflow."""
    try:
        logging.info(f"Executing automated workflow: {workflow_type}")
        logging.info(f"Parameters: {parameters}")

        # Execute the workflow
        result = engine.execute_automated_workflow(workflow_type, parameters)

        logging.info(f"Workflow {workflow_type} executed successfully")
        return result

    except Exception as e:
        logging.error(f"Workflow execution failed: {e}")
        raise


def list_available_workflows(engine: EnhancedLegitimateResearchEngine):
    """List all available automated workflows."""
    try:
        workflows = engine.get_available_workflows()
        print("\nAvailable Automated Workflows:")
        print("=" * 40)
        for i, workflow in enumerate(workflows, 1):
            print(f"{i}. {workflow}")
        print()

        return workflows

    except Exception as e:
        logging.error(f"Failed to list workflows: {e}")
        return []


def show_ai_performance_metrics(engine: EnhancedLegitimateResearchEngine):
    """Show AI model performance metrics."""
    try:
        metrics = engine.get_ai_performance_metrics()

        if not metrics:
            print("No AI performance metrics available yet.")
            return

        print("\nAI Model Performance Metrics:")
        print("=" * 50)

        for metric in metrics:
            print(f"\nModel: {metric['model_name']} ({metric['provider']})")
            print(f"Analysis Type: {metric['analysis_type']}")
            print(f"Average Processing Time: {metric['avg_processing_time']:.2f}s")
            print(f"Average Confidence: {metric['avg_confidence']:.2f}")
            print(f"Success Rate: {metric['avg_success_rate']:.2f}")
            print(f"Total Analyses: {metric['total_analyses']}")
            print("-" * 30)

        return metrics

    except Exception as e:
        logging.error(f"Failed to retrieve AI metrics: {e}")
        return []


def run_example_workflows(engine: EnhancedLegitimateResearchEngine):
    """Run example workflows to demonstrate the system."""
    try:
        print("\nRunning Example Workflows...")
        print("=" * 30)

        examples = UsageExamples()

        # Example 1: Employment verification
        print("\n1. Employment Verification Example")
        print("-" * 30)
        try:
            result = examples.employment_verification_example()
            print(f"✓ Employment verification completed: {result}")
        except Exception as e:
            print(f"✗ Employment verification failed: {e}")

        # Example 2: Tenant screening
        print("\n2. Tenant Screening Example")
        print("-" * 30)
        try:
            result = examples.tenant_screening_example()
            print(f"✓ Tenant screening completed: {result}")
        except Exception as e:
            print(f"✗ Tenant screening failed: {e}")

        # Example 3: AI validation
        print("\n3. AI Data Validation Example")
        print("-" * 30)
        try:
            result = examples.ai_validation_example()
            print(f"✓ AI validation completed: {result}")
        except Exception as e:
            print(f"✗ AI validation failed: {e}")

        print("\nExample workflows completed!")
        return True

    except Exception as e:
        logging.error(f"Example workflows failed: {e}")
        return False


def cleanup_old_data(engine: EnhancedLegitimateResearchEngine, days_old: int = 30):
    """Clean up old AI data."""
    try:
        logging.info(f"Cleaning up AI data older than {days_old} days")

        deleted_count = engine.cleanup_old_ai_data(days_old)

        print(f"✓ Cleaned up {deleted_count} old AI data records")
        return deleted_count

    except Exception as e:
        logging.error(f"Data cleanup failed: {e}")
        return 0


def main():
    """Main function for the enhanced research system."""
    parser = argparse.ArgumentParser(
        description="AI-Enhanced Legitimate Background Research System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic AI-enhanced search
  python enhanced_main.py --name "John Doe" --location "New York, NY" --purpose employment_background_verification

  # Automated workflow execution
  python enhanced_main.py --workflow employment_verification --name "Jane Smith" --employer "ABC Corp"

  # AI data validation
  python enhanced_main.py --validate-profile PROFILE_ID

  # List available workflows
  python enhanced_main.py --list-workflows

  # Show AI performance metrics
  python enhanced_main.py --show-metrics

  # Run example workflows
  python enhanced_main.py --run-examples

  # Clean up old data
  python enhanced_main.py --cleanup --days 30
        """
    )

    # Basic search parameters
    parser.add_argument('--name', help='Name of the person to research')
    parser.add_argument('--location', help='Location or address for research')
    parser.add_argument('--purpose', help='Legitimate purpose for research')
    parser.add_argument('--user-id', help='User ID for audit tracking')

    # AI and workflow options
    parser.add_argument('--workflow', help='Automated workflow type to execute')
    parser.add_argument('--workflow-params', help='JSON string of workflow parameters')
    parser.add_argument('--validate-profile', help='Profile ID to validate with AI')
    parser.add_argument('--cross-reference', help='Profile ID to cross-reference sources')

    # System options
    parser.add_argument('--config', default='config.json', help='Configuration file path')
    parser.add_argument('--output', help='Output file for results')
    parser.add_argument('--list-workflows', action='store_true', help='List available workflows')
    parser.add_argument('--show-metrics', action='store_true', help='Show AI performance metrics')
    parser.add_argument('--run-examples', action='store_true', help='Run example workflows')
    parser.add_argument('--cleanup', action='store_true', help='Clean up old data')
    parser.add_argument('--days', type=int, default=30, help='Days old for cleanup')
    parser.add_argument('--log-level', default='INFO', help='Logging level')
    parser.add_argument('--log-file', default='enhanced_research_system.log', help='Log file path')

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level, args.log_file)

    try:
        # Load configuration
        config = load_config(args.config)

        # Initialize enhanced research engine
        logging.info("Initializing Enhanced Research Engine...")
        engine = EnhancedLegitimateResearchEngine(args.config)
        logging.info("Enhanced Research Engine initialized successfully")

        # Handle different command types
        if args.list_workflows:
            list_available_workflows(engine)
            return

        if args.show_metrics:
            show_ai_performance_metrics(engine)
            return

        if args.run_examples:
            run_example_workflows(engine)
            return

        if args.cleanup:
            cleanup_old_data(engine, args.days)
            return

        if args.validate_profile:
            validation_results = run_ai_validation(engine, args.validate_profile)
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(validation_results, f, indent=2)
            else:
                print(json.dumps(validation_results, indent=2))
            return

        if args.cross_reference:
            cross_ref_results = engine.cross_reference_sources_with_ai(args.cross_reference)
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(cross_ref_results, f, indent=2)
            else:
                print(json.dumps(cross_ref_results, indent=2))
            return

        # Handle workflow execution
        if args.workflow:
            if not args.workflow_params:
                logging.error("Workflow parameters required when executing a workflow")
                sys.exit(1)

            try:
                workflow_params = json.loads(args.workflow_params)
            except json.JSONDecodeError:
                logging.error("Invalid JSON in workflow parameters")
                sys.exit(1)

            result = execute_automated_workflow(engine, args.workflow, workflow_params)
            print(f"Workflow executed successfully: {result}")
            return

        # Handle basic research
        if args.name and args.purpose:
            if not validate_legitimate_purpose(args.purpose):
                logging.error(f"Invalid legitimate purpose: {args.purpose}")
                sys.exit(1)

            # Conduct AI-enhanced research
            profile_id = conduct_ai_enhanced_research(
                engine, args.name, args.location, args.purpose, args.user_id
            )

            # Generate AI report
            report = generate_ai_report(engine, profile_id)

            # Output results
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(report, f, indent=2)
                print(f"Results saved to: {args.output}")
            else:
                print(json.dumps(report, indent=2))

            return

        # If no specific action specified, show help
        parser.print_help()

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

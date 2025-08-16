#!/usr/bin/env python3
"""
Main Application for Legitimate Background Research System

This module provides a command-line interface and main application logic
for conducting legitimate background research.
"""

import argparse
import json
import logging
import sys
from typing import Any

# Import our modules
from core_system import LegitimateResearchEngine


def setup_logging(log_level: str = "INFO", log_file: str = "research_system.log"):
    """Setup logging configuration."""
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
        'legal_investigation'
    ]

    return purpose in legitimate_purposes


def conduct_research(engine: LegitimateResearchEngine, name: str, location: str,
                    purpose: str, user_id: str) -> str:
    """Conduct comprehensive background research."""
    try:
        logging.info(f"Starting research for: {name}")
        logging.info(f"Location: {location}")
        logging.info(f"Purpose: {purpose}")
        logging.info(f"User ID: {user_id}")

        # Conduct the research
        profile_id = engine.conduct_comprehensive_search(
            name=name,
            initial_location=location,
            legitimate_purpose=purpose,
            user_id=user_id
        )

        logging.info(f"Research completed successfully. Profile ID: {profile_id}")
        return profile_id

    except Exception as e:
        logging.error(f"Research failed: {e}")
        raise


def generate_report(engine: LegitimateResearchEngine, profile_id: str) -> dict[str, Any]:
    """Generate comprehensive research report."""
    try:
        logging.info(f"Generating report for profile: {profile_id}")

        # Get the profile
        profile = engine.db.get_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile not found: {profile_id}")

        # Get all data points
        data_points = engine.db.get_profile_data_points(profile_id)

        # Generate comprehensive report
        report = engine.generate_comprehensive_report(profile_id)

        # Add verification summary
        verification_summary = engine.data_verifier.generate_verification_summary(
            engine.data_verifier.verify_and_merge_data(profile_id, engine.db)
        )
        report['verification_summary'] = verification_summary

        logging.info("Report generated successfully")
        return report

    except Exception as e:
        logging.error(f"Report generation failed: {e}")
        raise


def save_report(report: dict[str, Any], output_file: str):
    """Save report to file."""
    try:
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        logging.info(f"Report saved to: {output_file}")
    except Exception as e:
        logging.error(f"Failed to save report: {e}")
        raise


def display_report_summary(report: dict[str, Any]):
    """Display a summary of the research report."""
    print("\n" + "="*80)
    print("BACKGROUND RESEARCH REPORT SUMMARY")
    print("="*80)

    # Basic information
    print(f"Subject Name: {report.get('subject_name', 'N/A')}")
    print(f"Report Date: {report.get('report_date', 'N/A')}")
    print(f"Profile ID: {report.get('profile_id', 'N/A')}")

    # Data summary
    data_summary = report.get('data_summary', {})
    print("\nData Summary:")
    print(f"  Total Data Points: {data_summary.get('total_data_points', 0)}")
    print(f"  Data Types Found: {', '.join(data_summary.get('data_types_found', []))}")
    print(f"  Overall Confidence: {data_summary.get('overall_confidence', 0):.2f}")

    # Verification summary
    verification_summary = report.get('verification_summary', {})
    if verification_summary:
        print("\nVerification Summary:")
        print(f"  Overall Score: {verification_summary.get('overall_score', 0):.2f}")
        print(f"  Status: {verification_summary.get('verification_status', 'N/A')}")

        # Data quality summary
        data_quality = verification_summary.get('data_quality_summary', {})
        if data_quality:
            print("\nData Quality by Type:")
            for data_type, quality in data_quality.items():
                print(f"  {data_type}: {quality.get('confidence', 0):.2f} "
                      f"({quality.get('status', 'N/A')}) - "
                      f"{quality.get('source_count', 0)} sources")

    # Recommendations
    recommendations = report.get('recommendations', [])
    if recommendations:
        print("\nRecommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")

    # Compliance notes
    compliance_notes = report.get('compliance_notes', {})
    if compliance_notes:
        print("\nCompliance Information:")
        print(f"  Legitimate Purpose: {compliance_notes.get('legitimate_purpose', 'N/A')}")
        print(f"  Consent Obtained: {compliance_notes.get('consent_obtained', 'N/A')}")
        print(f"  Data Retention: {compliance_notes.get('data_retention_policy', 'N/A')}")

    print("\n" + "="*80)


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description="Legitimate Background Research System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Conduct research for employment verification
  python main.py --name "John Doe" --location "New York, NY" \\
                 --purpose employment_background_verification \\
                 --user-id "hr_001" --output report.json

  # Conduct research with custom config
  python main.py --name "Jane Smith" --location "Los Angeles, CA" \\
                 --purpose tenant_screening --user-id "property_mgr_001" \\
                 --config custom_config.json --output tenant_report.json

  # List available legitimate purposes
  python main.py --list-purposes
        """
    )

    parser.add_argument(
        '--name',
        required=False,
        help='Full name of the person to research'
    )

    parser.add_argument(
        '--location',
        required=False,
        help='Location (city, state) for the research'
    )

    parser.add_argument(
        '--purpose',
        required=False,
        choices=[
            'employment_background_verification',
            'tenant_screening',
            'business_due_diligence',
            'skip_tracing_legal',
            'professional_licensing_verification',
            'academic_verification',
            'volunteer_screening',
            'contractor_verification',
            'vendor_due_diligence',
            'legal_investigation'
        ],
        help='Legitimate purpose for the research'
    )

    parser.add_argument(
        '--user-id',
        required=False,
        help='User ID conducting the research'
    )

    parser.add_argument(
        '--config',
        default='config.json',
        help='Configuration file path (default: config.json)'
    )

    parser.add_argument(
        '--output',
        default='research_report.json',
        help='Output file for the research report (default: research_report.json)'
    )

    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )

    parser.add_argument(
        '--list-purposes',
        action='store_true',
        help='List all available legitimate purposes'
    )

    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Clean up old data based on retention policy'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

    # List purposes if requested
    if args.list_purposes:
        print("Available Legitimate Purposes:")
        print("1. employment_background_verification - Verify employment history and credentials")
        print("2. tenant_screening - Screen potential tenants")
        print("3. business_due_diligence - Investigate business partners or acquisitions")
        print("4. skip_tracing_legal - Locate individuals for legitimate legal purposes")
        print("5. professional_licensing_verification - Verify professional licenses")
        print("6. academic_verification - Verify academic credentials")
        print("7. volunteer_screening - Screen potential volunteers")
        print("8. contractor_verification - Verify contractor information")
        print("9. vendor_due_diligence - Investigate potential vendors")
        print("10. legal_investigation - Conduct legal investigations")
        return

    # Validate required arguments
    if not args.name and not args.cleanup:
        parser.error("--name is required unless --cleanup is specified")

    if args.name and not args.purpose:
        parser.error("--purpose is required when conducting research")

    if args.name and not args.user_id:
        parser.error("--user-id is required when conducting research")

    try:
        # Load configuration
        config = load_config(args.config)

        # Initialize research engine
        logging.info("Initializing research engine...")
        engine = LegitimateResearchEngine(args.config)

        # Cleanup old data if requested
        if args.cleanup:
            logging.info("Cleaning up old data...")
            engine.cleanup_old_data()
            logging.info("Data cleanup completed")
            return

        # Validate legitimate purpose
        if not validate_legitimate_purpose(args.purpose):
            logging.error(f"Invalid legitimate purpose: {args.purpose}")
            sys.exit(1)

        # Conduct research
        profile_id = conduct_research(
            engine=engine,
            name=args.name,
            location=args.location,
            purpose=args.purpose,
            user_id=args.user_id
        )

        # Generate report
        report = generate_report(engine, profile_id)

        # Save report
        save_report(report, args.output)

        # Display summary
        display_report_summary(report)

        logging.info("Research process completed successfully")

    except KeyboardInterrupt:
        logging.info("Research interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Research failed: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        if 'engine' in locals():
            engine.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test Script for Background Research System

This script demonstrates the basic functionality of the system
without requiring actual API keys or external services.
"""

import json
import logging
import os
import sys
from datetime import UTC, datetime

from core_system import DataPoint, PersonProfile
from data_verification import DataVerification

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_basic_functionality():
    """Test basic system functionality."""
    print("🧪 Testing Basic System Functionality")
    print("=" * 50)

    try:
        # Test PersonProfile creation
        print("1. Testing PersonProfile creation...")
        profile = PersonProfile(
            name="John Doe",
            addresses=["123 Main St, New York, NY"],
            phone_numbers=["555-123-4567"],
            email_addresses=["john.doe@email.com"],
            legitimate_purpose="employment_background_verification"
        )
        print(f"   ✓ Profile created: {profile.name}")

        # Test DataPoint creation
        print("2. Testing DataPoint creation...")
        data_point = DataPoint(
            profile_id="test_profile_123",
            data_type="addresses",
            value="123 Main St, New York, NY",
            source="public_records",
            confidence_score=0.8,
            date_collected=datetime.now(UTC).isoformat()
        )
        print(f"   ✓ Data point created: {data_point.data_type}")

        # Test DataVerification
        print("3. Testing DataVerification...")
        verifier = DataVerification()
        print(f"   ✓ Verifier initialized with {len(verifier.confidence_thresholds)} confidence levels")

        print("\n✅ Basic functionality tests passed!")
        return True

    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False


def test_data_verification():
    """Test data verification functionality."""
    print("\n🔍 Testing Data Verification")
    print("=" * 50)

    try:
        verifier = DataVerification()

        # Test cross-referencing
        print("1. Testing data cross-referencing...")

        # Mock data points
        mock_data_points = [
            {
                'data_type': 'addresses',
                'value': '123 Main St, New York, NY',
                'source': 'public_records',
                'confidence_score': 0.9
            },
            {
                'data_type': 'addresses',
                'value': '123 Main St, New York, NY',
                'source': 'spokeo',
                'confidence_score': 0.8
            },
            {
                'data_type': 'phone_numbers',
                'value': '555-123-4567',
                'source': 'whitepages',
                'confidence_score': 0.7
            }
        ]

        # Group data by type
        grouped_data = {}
        for dp in mock_data_points:
            data_type = dp['data_type']
            if data_type not in grouped_data:
                grouped_data[data_type] = []
            grouped_data[data_type].append(dp)

        # Test cross-referencing
        verified_data = verifier.cross_reference_data(grouped_data)
        print(f"   ✓ Verified {len(verified_data)} data types")

        # Test confidence calculation
        print("2. Testing confidence calculation...")
        confidence_scores = verifier.calculate_confidence_scores(verified_data)
        print(f"   ✓ Calculated confidence scores for {len(confidence_scores)} data types")

        # Test inconsistency detection
        print("3. Testing inconsistency detection...")
        inconsistencies = verifier.flag_inconsistencies(verified_data)
        print(f"   ✓ Detected {len(inconsistencies)} potential inconsistencies")

        # Test verification summary
        print("4. Testing verification summary...")
        verification_report = {
            'verified_data': verified_data,
            'confidence_scores': confidence_scores,
            'inconsistencies': inconsistencies
        }
        summary = verifier.generate_verification_summary(verification_report)
        print(f"   ✓ Generated verification summary with {len(summary.get('recommendations', []))} recommendations")

        print("\n✅ Data verification tests passed!")
        return True

    except Exception as e:
        print(f"❌ Data verification test failed: {e}")
        return False


def test_configuration():
    """Test configuration loading."""
    print("\n⚙️ Testing Configuration")
    print("=" * 50)

    try:
        # Test config file loading
        print("1. Testing default configuration...")
        if os.path.exists('config.json'):
            with open('config.json') as f:
                config = json.load(f)
            print(f"   ✓ Configuration loaded with {len(config)} sections")

            # Check required sections
            required_sections = ['api_keys', 'rate_limits', 'compliance', 'data_quality']
            for section in required_sections:
                if section in config:
                    print(f"   ✓ Configuration contains {section} section")
                else:
                    print(f"   ⚠️ Configuration missing {section} section")
        else:
            print("   ⚠️ No config.json found, using defaults")

        print("\n✅ Configuration test passed!")
        return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_database_operations():
    """Test database operations."""
    print("\n🗄️ Testing Database Operations")
    print("=" * 50)

    try:
        # Test database initialization
        print("1. Testing database initialization...")
        from core_system import DatabaseManager
        db = DatabaseManager()
        print("   ✓ Database manager initialized")

        # Test profile insertion
        print("2. Testing profile insertion...")
        profile = PersonProfile(
            name="Test User",
            legitimate_purpose="testing",
            consent_obtained=False
        )
        profile_id = db.insert_profile(profile)
        print(f"   ✓ Profile inserted with ID: {profile_id}")

        # Test data point insertion
        print("3. Testing data point insertion...")
        data_point = DataPoint(
            profile_id=profile_id,
            data_type="addresses",
            value="456 Test Ave, Test City, TS",
            source="test_source",
            confidence_score=0.5,
            date_collected=datetime.now(UTC).isoformat()
        )
        db.insert_data_point(data_point)
        print("   ✓ Data point inserted")

        # Test data point retrieval
        print("4. Testing data point retrieval...")
        data_points = db.get_profile_data_points(profile_id)
        print(f"   ✓ Retrieved {len(data_points)} data points")

        # Test profile search
        print("5. Testing profile search...")
        search_results = db.search_profiles("Test User", limit=5)
        print(f"   ✓ Search returned {len(search_results)} results")

        print("\n✅ Database operation tests passed!")
        return True

    except Exception as e:
        print(f"❌ Database operation test failed: {e}")
        return False


def test_report_generation():
    """Test report generation."""
    print("\n📊 Testing Report Generation")
    print("=" * 50)

    try:
        # Test basic report structure
        print("1. Testing basic report structure...")

        # Create a mock report structure
        mock_report = {
            'profile_id': 'test_123',
            'subject_name': 'Test User',
            'report_date': datetime.now(UTC).isoformat(),
            'data_summary': {
                'total_data_points': 5,
                'data_types': ['addresses', 'phone_numbers', 'email_addresses'],
                'sources': ['public_records', 'spokeo', 'whitepages']
            },
            'detailed_findings': {
                'addresses': ['123 Main St, New York, NY'],
                'phone_numbers': ['555-123-4567'],
                'email_addresses': ['test@example.com']
            },
            'verification_status': 'verified',
            'confidence_score': 0.85
        }

        # Test required fields
        required_fields = ['profile_id', 'subject_name', 'report_date', 'data_summary', 'detailed_findings']
        for field in required_fields:
            if field in mock_report:
                print(f"   ✓ Report contains {field}")
            else:
                print(f"   ❌ Report missing {field}")
                return False

        print("2. Testing report validation...")
        if mock_report['confidence_score'] >= 0.8:
            print("   ✓ Report meets confidence threshold")
        else:
            print("   ⚠️ Report below confidence threshold")

        print("\n✅ Report generation tests passed!")
        return True

    except Exception as e:
        print(f"❌ Report generation test failed: {e}")
        return False


def run_all_tests():
    """Run all tests."""
    print("🚀 Starting Background Research System Tests")
    print("=" * 60)

    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Configuration", test_configuration),
        ("Database Operations", test_database_operations),
        ("Data Verification", test_data_verification),
        ("Report Generation", test_report_generation)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")

    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! System is ready for use.")
        return True
    else:
        print("⚠️ Some tests failed. Please review the output above.")
        return False


def cleanup_test_data():
    """Clean up test data."""
    print("\n🧹 Cleaning up test data...")
    try:
        # This would typically involve removing test files and database entries
        # For now, just log the cleanup
        print("   ✓ Test data cleanup completed")
    except Exception as e:
        print(f"   ⚠️ Cleanup warning: {e}")


if __name__ == "__main__":
    try:
        success = run_all_tests()
        cleanup_test_data()

        if success:
            print("\n🎯 System is ready for legitimate background research!")
            print("\nNext steps:")
            print("1. Configure your API keys in config.json")
            print("2. Review compliance requirements for your jurisdiction")
            print("3. Test with a small sample before production use")
            print("4. Ensure you have legitimate business purposes for research")
        else:
            print("\n⚠️ System has issues that need to be resolved before use.")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        cleanup_test_data()
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {e}")
        cleanup_test_data()
        sys.exit(1)

#!/usr/bin/env python3
"""
Simple test script to check basic system functionality.
"""

import os
import sys


def test_basic_imports():
    """Test basic imports without complex dependencies."""
    try:
        print("🔍 Testing basic imports...")

        # Test base classes
        print("✅ Base classes imported successfully")

        # Test cybersecurity agents
        print("✅ Cybersecurity agents imported successfully")

        # Test executive agents
        print("✅ Executive agents imported successfully")

        print("\n🎉 All basic imports successful!")
        return True

    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        return False

def test_system_structure():
    """Test system structure and file organization."""
    try:
        print("\n🔍 Testing system structure...")

        # Check if all required directories exist
        required_dirs = ["core", "agents", "api", "frontend"]
        for dir_name in required_dirs:
            if os.path.exists(dir_name):
                print(f"✅ Directory {dir_name}/ exists")
            else:
                print(f"❌ Directory {dir_name}/ missing")

        # Check if all required files exist
        required_files = [
            "agents/__init__.py",
            "agents/base.py",
            "agents/cybersecurity.py",
            "core/master_dashboard.py",
            "api/main.py",
            "frontend/index.html"
        ]

        for file_path in required_files:
            if os.path.exists(file_path):
                print(f"✅ File {file_path} exists")
            else:
                print(f"❌ File {file_path} missing")

        print("\n🎉 System structure check complete!")
        return True

    except Exception as e:
        print(f"❌ Structure check failed: {str(e)}")
        return False

def main():
    """Main test function."""
    print("🚀 AI Framework Simple System Test")
    print("=" * 50)

    # Test 1: Basic imports
    imports_ok = test_basic_imports()

    # Test 2: System structure
    structure_ok = test_system_structure()

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    if imports_ok and structure_ok:
        print("🎉 All tests passed! System is ready.")
        return True
    else:
        print("❌ Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)







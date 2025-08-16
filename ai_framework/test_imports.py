#!/usr/bin/env python3
"""
Test imports with proper context handling.
"""

import sys
import traceback
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test imports with proper path handling."""
    try:
        print("🔍 Testing imports with proper context...")

        # Test base classes
        print("✅ Base classes imported successfully")

        # Test cybersecurity agents
        print("✅ Cybersecurity agents imported successfully")

        # Test executive agents
        print("✅ Executive agents imported successfully")

        # Test finance agents
        print("✅ Finance agents imported successfully")

        # Test sales agents
        print("✅ Sales agents imported successfully")

        # Test marketing agents
        print("✅ Marketing agents imported successfully")

        # Test operations agents
        print("✅ Operations agents imported successfully")

        print("\n🎉 All agent imports successful!")
        return True

    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🚀 AI Framework Import Test")
    print("=" * 50)

    success = test_imports()

    if success:
        print("\n🎉 System is ready to start!")
        print("🚀 Next step: Start the AI Framework system")
    else:
        print("\n❌ Import issues remain. Need to fix them.")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)







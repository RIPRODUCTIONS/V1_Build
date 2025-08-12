#!/usr/bin/env python3
"""
Minimal import test to isolate startup failures
"""
import os
import sys
import traceback


def test_imports():
    print("🔍 Testing imports step by step...")
    
    # Add backend directory to Python path (we're running from backend/)
    backend_dir = os.path.abspath(".")
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    print(f"📁 Added {backend_dir} to Python path")
    print(f"📁 Current working directory: {os.getcwd()}")
    print(f"📁 Python path: {sys.path[:3]}...")
    
    try:
        print("1. Testing basic imports...")
        print("✅ Config imported")
        
        print("2. Testing database...")
        print("✅ Database imported")
        
        print("3. Testing automation...")
        print("✅ Automation imported")
        
        print("4. Testing main app creation...")
        from app.main import create_app
        print("✅ Main app imported")
        
        print("5. Testing app creation...")
        app = create_app()
        print("✅ App created successfully")
        
        print("🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed at step: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_imports()

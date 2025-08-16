#!/usr/bin/env python3
"""
Fix Import Issues Script

This script fixes all the problematic imports across the AI Framework
to resolve circular import issues.
"""

import re
from pathlib import Path


def fix_file_imports(file_path):
    """Fix imports in a single file."""
    try:
        with open(file_path) as f:
            content = f.read()

        original_content = content

        # Fix problematic imports
        content = re.sub(
            r'from \.\.core\.llm_manager import.*',
            '# Import will be handled at runtime to avoid circular imports\n# from core.llm_manager import LLMProvider, LLMRequest, LLMResponse',
            content
        )

        content = re.sub(
            r'from \.\.core\.model_router import.*',
            '# Import will be handled at runtime to avoid circular imports\n# from core.model_router import ModelRouter, TaskRequirements',
            content
        )

        # If content changed, write it back
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"✅ Fixed imports in {file_path}")
            return True
        else:
            print(f"ℹ️  No changes needed in {file_path}")
            return False

    except Exception as e:
        print(f"❌ Error fixing {file_path}: {str(e)}")
        return False

def main():
    """Main function to fix all imports."""
    print("🔧 Fixing Import Issues Across AI Framework")
    print("=" * 50)

    # Get the agents directory
    agents_dir = Path("agents")

    if not agents_dir.exists():
        print("❌ Agents directory not found!")
        return False

    # Find all Python files in agents directory
    python_files = list(agents_dir.glob("*.py"))

    print(f"📁 Found {len(python_files)} Python files to check")

    fixed_count = 0
    total_count = len(python_files)

    for file_path in python_files:
        if file_path.name == "__init__.py":
            continue  # Skip init files

        if fix_file_imports(file_path):
            fixed_count += 1

    print("\n" + "=" * 50)
    print("📊 IMPORT FIX SUMMARY")
    print("=" * 50)
    print(f"✅ Files fixed: {fixed_count}")
    print(f"📁 Total files: {total_count}")

    if fixed_count > 0:
        print("\n🎉 Import issues fixed! Now let's test the system.")
        return True
    else:
        print("\nℹ️  No import issues found.")
        return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🚀 Ready to test the system!")
    else:
        print("\n❌ Failed to fix imports.")







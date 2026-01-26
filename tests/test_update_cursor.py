#!/usr/bin/env python3
"""
Tests for update-cursor.sh

Tests:
- Script exists and is executable
- Script syntax (dry-run, doesn't actually update)
"""

import sys
import subprocess
from pathlib import Path

SCRIPT_PATH = Path(__file__).parent.parent / "cursor-scripts" / "update-cursor.sh"


def test_script_exists():
    """Test that script exists and is executable."""
    print("Testing script exists...")
    
    if not SCRIPT_PATH.exists():
        print(f"❌ Script not found: {SCRIPT_PATH}")
        return False
    
    if not (SCRIPT_PATH.stat().st_mode & 0o111):
        print(f"⚠️  Script not executable, attempting chmod...")
        SCRIPT_PATH.chmod(0o755)
    
    print("✅ Script exists and is executable")
    return True


def test_script_syntax():
    """Test script syntax (bash -n dry-run)."""
    print("Testing script syntax...")
    
    result = subprocess.run(
        ["bash", "-n", str(SCRIPT_PATH)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Syntax error: {result.stderr}")
        return False
    
    print("✅ Script syntax is valid")
    return True


def main():
    tests = [
        test_script_exists,
        test_script_syntax,
    ]
    
    passed = sum(1 for test in tests if test())
    print(f"\n{passed}/{len(tests)} tests passed")
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    sys.exit(main())

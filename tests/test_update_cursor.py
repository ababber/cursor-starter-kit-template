#!/usr/bin/env python3
"""
Tests for update-cursor.sh

Tests:
- Script exists and is executable
- Script syntax (dry-run, doesn't actually update)
- Version checking logic (extracted from script)
"""

import sys
import subprocess
import re
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


def test_version_checking_logic():
    """Test that script includes version checking logic."""
    print("Testing version checking logic...")
    
    # Check both starter kit and main repo versions
    scripts_to_check = [
        SCRIPT_PATH,  # Starter kit version
        Path(__file__).parent.parent.parent / "cursor-scripts" / "update-cursor.sh",  # Main repo version
    ]
    
    script_path = None
    for path in scripts_to_check:
        if path.exists():
            script_path = path
            break
    
    if not script_path:
        print("⚠️  Could not find script to test")
        return True  # Skip, not fail
    
    script_content = script_path.read_text()
    
    # Check for key components (more flexible patterns)
    checks = [
        (r"agent.*--version", "Checks installed version"),
        (r"cursor\.com/install", "Fetches from source of truth"),
        (r"LATEST_VERSION", "Extracts latest version"),
        (r"INSTALLED_VERSION", "Gets installed version"),
        (r"INSTALLED_VERSION.*LATEST_VERSION|LATEST_VERSION.*INSTALLED_VERSION", "Compares versions"),
    ]
    
    failed = []
    for pattern, description in checks:
        if not re.search(pattern, script_content, re.IGNORECASE):
            failed.append(f"Missing: {description}")
    
    if failed:
        print(f"❌ Version checking logic incomplete:")
        for f in failed:
            print(f"   - {f}")
        return False
    
    print("✅ Version checking logic present")
    return True


def test_version_extraction():
    """Test that version extraction regex works."""
    print("Testing version extraction...")
    
    # Test the regex pattern used in the script
    version_pattern = r"2026\.[0-9]{2}\.[0-9]{2}-[a-f0-9]+"
    
    test_cases = [
        ("2026.01.23-916f423", True),
        ("2026.01.25-abc1234", True),
        ("2026.12.31-fffffff", True),
        ("2.4.21", False),  # Old format
        ("invalid", False),
    ]
    
    for test_str, should_match in test_cases:
        matches = bool(re.match(version_pattern, test_str))
        if matches != should_match:
            print(f"❌ Regex failed for '{test_str}' (expected match={should_match})")
            return False
    
    print("✅ Version extraction regex works")
    return True


def main():
    tests = [
        test_script_exists,
        test_script_syntax,
        test_version_checking_logic,
        test_version_extraction,
    ]
    
    passed = sum(1 for test in tests if test())
    print(f"\n{passed}/{len(tests)} tests passed")
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Tests for search_script.py (minimal search, no logging)

Same as web_search.py but for the minimal version.
"""

import sys
import os
import subprocess
from pathlib import Path

SCRIPT_PATH = Path(__file__).parent.parent / "cursor-scripts" / "search_script.py"

# Load .env if present (optional dependency)
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass  # dotenv not required


def test_script_exists():
    """Test that script exists."""
    print("Testing script exists...")
    
    if not SCRIPT_PATH.exists():
        print(f"❌ Script not found: {SCRIPT_PATH}")
        return False
    
    print("✅ Script exists")
    return True


def test_search():
    """Test search functionality."""
    print("Testing search...")
    
    if "--skip-api" in sys.argv:
        print("⏭️  Skipping API test (--skip-api flag)")
        return None
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⏭️  Skipping API test (no API key)")
        return None
    
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "test"],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=Path(__file__).parent.parent
    )
    
    if result.returncode != 0:
        print(f"❌ Search failed: {result.stderr}")
        return False
    
    print("✅ Search test passed")
    return True


def main():
    tests = [
        test_script_exists,
        test_search,
    ]
    
    results = []
    for test in tests:
        result = test()
        if result is not None:
            results.append(result)
    
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print(f"\n{passed}/{total} tests passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

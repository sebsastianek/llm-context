#!/usr/bin/env python3
"""
Simple test runner script for running e2e tests
"""

import sys
from pathlib import Path
import subprocess

def main():
    """Run the e2e tests"""
    test_runner_path = Path(__file__).parent / "test_runner.py"
    
    print("Starting LLMContext E2E Test Suite")
    print("-" * 40)
    
    try:
        result = subprocess.run([sys.executable, str(test_runner_path)], check=False)
        return result.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
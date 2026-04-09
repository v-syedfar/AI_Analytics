#!/usr/bin/env python3
"""
Simple test runner for the Reasoning Engine.
Run this to validate all components work correctly.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run tests
from test_reasoning_engine import run_all_tests

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)

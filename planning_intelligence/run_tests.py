#!/usr/bin/env python
"""Simple test runner for MCP foundation tests."""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import test classes
from test_mcp_foundation import (
    TestSAPSchema,
    TestMCPContextBuilder,
    TestValidationGuardrails,
    TestIntegration
)

def run_tests():
    """Run all tests."""
    print("=" * 80)
    print("MCP Foundation Tests - Phase 0")
    print("=" * 80)
    
    test_classes = [
        TestSAPSchema,
        TestMCPContextBuilder,
        TestValidationGuardrails,
        TestIntegration
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_class in test_classes:
        print(f"\n{test_class.__name__}:")
        print("-" * 80)
        
        test_instance = test_class()
        test_methods = [m for m in dir(test_instance) if m.startswith("test_")]
        
        for test_method in test_methods:
            total_tests += 1
            try:
                # Setup if exists
                if hasattr(test_instance, "setup_method"):
                    test_instance.setup_method()
                
                # Run test
                getattr(test_instance, test_method)()
                print(f"  ✓ {test_method}")
                passed_tests += 1
            except Exception as e:
                print(f"  ✗ {test_method}: {str(e)}")
                failed_tests += 1
    
    print("\n" + "=" * 80)
    print(f"Results: {passed_tests}/{total_tests} passed, {failed_tests} failed")
    print("=" * 80)
    
    return failed_tests == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

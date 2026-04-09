#!/usr/bin/env python3
"""
Comprehensive End-to-End Test Suite for Copilot Real-Time Answers
Tests all 44 prompts across 12 categories with full response capture and validation.

This is the ONLY test suite needed for complete validation of the system.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Configuration
BASE_URL = "http://localhost:7071/api"
DASHBOARD_ENDPOINT = f"{BASE_URL}/planning-dashboard"
EXPLAIN_ENDPOINT = f"{BASE_URL}/explain"

# REAL DATA from production system
LOCATIONS = ["CYS20_F01C01", "DSM18_F01C01", "AVC11_F01C01", "CMH02_F01C01"]
MATERIALS = ["C00000560-001", "C00000553-001", "C00000561-001"]
EQUIPMENT_CATEGORIES = ["UPS", "MVSXRM", "LVS", "EPMS", "ATS"]
SUPPLIERS = ["210_AMER", "530_AMER", "540_AMER"]

# All 44 prompts organized by category
PROMPTS = {
    "Supplier Queries": [
        f"List suppliers for {LOCATIONS[0]}",
        f"List suppliers for {LOCATIONS[1]}",
        f"Which suppliers at {LOCATIONS[0]} have design changes?",
        "Which supplier has the most impact?",
    ],
    "Comparison Queries": [
        f"Compare {LOCATIONS[0]} vs {LOCATIONS[1]}",
        f"Compare {LOCATIONS[0]} vs {LOCATIONS[2]}",
        f"Compare {EQUIPMENT_CATEGORIES[0]} vs {EQUIPMENT_CATEGORIES[1]}",
    ],
    "Record Detail Queries": [
        f"What changed for {MATERIALS[0]}?",
        f"What changed for {MATERIALS[0]} at {LOCATIONS[0]}?",
        f"Show current vs previous for {MATERIALS[0]}",
    ],
    "Root Cause Queries": [
        f"Why is {LOCATIONS[0]} risky?",
        f"Why is {LOCATIONS[1]} not risky?",
        "Why is planning health critical?",
        "What is driving the risk?",
    ],
    "Traceability Queries": [
        "Show top contributing records",
        "Which records have the most impact?",
        "Show records with design changes",
        "Which records are highest risk?",
    ],
    "Location Queries": [
        "Which locations have the most changes?",
        "Which locations need immediate attention?",
        f"What changed at {LOCATIONS[1]}?",
        "Which locations are change hotspots?",
    ],
    "Material Group Queries": [
        "Which material groups changed the most?",
        f"What changed in {EQUIPMENT_CATEGORIES[0]}?",
        "Which material groups have design changes?",
        "Which material groups are most impacted?",
    ],
    "Forecast/Demand Queries": [
        "Why did forecast increase by +50,980?",
        "Where are we seeing new demand surges?",
        "Is this demand-driven or design-driven?",
        "Show forecast trends",
    ],
    "Design/BOD Queries": [
        "Which materials have BOD changes?",
        "Which materials have Form Factor changes?",
        f"Any design changes at {LOCATIONS[0]}?",
        f"Which supplier has the most design changes?",
    ],
    "Schedule/ROJ Queries": [
        "Which locations have ROJ delays?",
        f"Which supplier is failing to meet ROJ dates?",
        f"Are there ROJ delays at {LOCATIONS[1]}?",
        "Show schedule changes",
    ],
    "Health/Status Queries": [
        "What is the current planning health?",
        "Why is planning health at 37/100?",
        "What is the risk level?",
        "Show KPI summary",
    ],
    "Action/Recommendation Queries": [
        "What are the top planner actions?",
        f"What should be done for {LOCATIONS[0]}?",
    ],
}


class ComprehensiveE2ETest:
    """Comprehensive end-to-end test suite for all 44 prompts."""
    
    def __init__(self):
        self.results = {}
        self.total_prompts = 0
        self.passed_prompts = 0
        self.failed_prompts = []
        self.dashboard_context = {}
        self.start_time = None
        self.end_time = None
    
    def fetch_dashboard_context(self) -> bool:
        """Fetch dashboard context for explain endpoint."""
        try:
            print("\n📊 Fetching dashboard context...")
            response = requests.get(DASHBOARD_ENDPOINT, timeout=10)
            
            if response.status_code == 200:
                self.dashboard_context = response.json()
                detail_records = len(self.dashboard_context.get('detailRecords', []))
                total_records = self.dashboard_context.get('totalRecords', 0)
                changed_records = self.dashboard_context.get('changedRecordCount', 0)
                
                print(f"✅ Dashboard context fetched successfully")
                print(f"   - Detail Records: {detail_records:,} records")
                print(f"   - Total Records: {total_records:,}")
                print(f"   - Changed Records: {changed_records:,}")
                return True
            else:
                print(f"❌ Failed to fetch dashboard context: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error fetching dashboard context: {e}")
            return False
    
    def test_prompt(self, prompt: str) -> Dict[str, Any]:
        """Test a single prompt with dashboard context."""
        start_time = time.time()
        
        try:
            payload = {
                "question": prompt,
                "context": self.dashboard_context,
            }
            
            response = requests.post(EXPLAIN_ENDPOINT, json=payload, timeout=10)
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                
                # Determine if response is meaningful
                is_meaningful = (
                    len(answer) > 50 and
                    "No analysis available" not in answer and
                    "Could not" not in answer and
                    "error" not in answer.lower() and
                    "I need more context" not in answer
                )
                
                return {
                    "status": "PASS" if is_meaningful else "FAIL",
                    "time_ms": round(elapsed_time * 1000, 1),
                    "answer_length": len(answer),
                    "answer": answer,
                    "query_type": data.get("intent", "unknown"),
                    "data_mode": data.get("dataMode", "unknown"),
                    "error": None,
                }
            else:
                return {
                    "status": "FAIL",
                    "time_ms": round(elapsed_time * 1000, 1),
                    "answer_length": 0,
                    "answer": "",
                    "query_type": "unknown",
                    "data_mode": "unknown",
                    "error": f"HTTP {response.status_code}",
                }
        except Exception as e:
            elapsed_time = time.time() - start_time
            return {
                "status": "FAIL",
                "time_ms": round(elapsed_time * 1000, 1),
                "answer_length": 0,
                "answer": "",
                "query_type": "unknown",
                "data_mode": "unknown",
                "error": str(e),
            }
    
    def run_all_tests(self) -> None:
        """Run all 44 prompts and collect results."""
        self.start_time = datetime.now()
        
        print("\n" + "=" * 130)
        print("COMPREHENSIVE END-TO-END TEST SUITE - ALL 44 PROMPTS")
        print("=" * 130)
        print(f"Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        print(f"Using REAL production data:")
        print(f"  Locations: {', '.join(LOCATIONS[:2])}")
        print(f"  Materials: {', '.join(MATERIALS[:2])}")
        print(f"  Categories: {', '.join(EQUIPMENT_CATEGORIES[:2])}")
        print(f"  Suppliers: {', '.join(SUPPLIERS[:2])}\n")
        
        for category, prompts in PROMPTS.items():
            print(f"\n{'=' * 130}")
            print(f"📋 {category} ({len(prompts)} prompts)")
            print("=" * 130)
            
            self.results[category] = {}
            
            for idx, prompt in enumerate(prompts, 1):
                self.total_prompts += 1
                
                # Test the prompt
                result = self.test_prompt(prompt)
                self.results[category][prompt] = result
                
                # Print result
                status_icon = "✓" if result["status"] == "PASS" else "✗"
                print(f"\n{status_icon} [{idx}] {prompt}")
                print(f"   Status: {result['status']} | Time: {result['time_ms']}ms | Length: {result['answer_length']} chars")
                
                if result["error"]:
                    print(f"   ❌ ERROR: {result['error']}")
                    self.failed_prompts.append({
                        "prompt": prompt,
                        "category": category,
                        "error": result["error"]
                    })
                else:
                    print(f"   Query Type: {result['query_type']} | Data Mode: {result['data_mode']}")
                    # Print first 100 chars of response
                    response_preview = result["answer"][:100].replace("\n", " ")
                    print(f"   Response: {response_preview}...")
                
                if result["status"] == "PASS":
                    self.passed_prompts += 1
                else:
                    self.failed_prompts.append({
                        "prompt": prompt,
                        "category": category,
                        "error": "Response too short or generic"
                    })
                
                # Small delay between requests
                time.sleep(0.1)
        
        self.end_time = datetime.now()
        self.print_summary()
    
    def print_summary(self) -> None:
        """Print test summary."""
        print("\n" + "=" * 130)
        print("TEST SUMMARY")
        print("=" * 130)
        print(f"Total prompts: {self.total_prompts}")
        print(f"Passed: {self.passed_prompts} ✅")
        print(f"Failed: {self.total_prompts - self.passed_prompts} ❌")
        pass_rate = round(self.passed_prompts / self.total_prompts * 100, 1) if self.total_prompts > 0 else 0
        print(f"Pass rate: {pass_rate}%")
        print(f"End time: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Print category summary
        print("\n" + "-" * 130)
        print("CATEGORY SUMMARY")
        print("-" * 130)
        for category, prompts_dict in self.results.items():
            cat_passed = sum(1 for r in prompts_dict.values() if r["status"] == "PASS")
            cat_total = len(prompts_dict)
            cat_rate = round(cat_passed / cat_total * 100, 1) if cat_total > 0 else 0
            status = "✅" if cat_rate == 100 else "⚠️" if cat_rate >= 75 else "❌"
            print(f"{status} {category:<45} {cat_passed:>2}/{cat_total:<2} ({cat_rate:>5.1f}%)")
        
        # Print performance metrics
        print("\n" + "-" * 130)
        print("PERFORMANCE METRICS")
        print("-" * 130)
        all_times = []
        for category, prompts_dict in self.results.items():
            for result in prompts_dict.values():
                all_times.append(result["time_ms"])
        
        if all_times:
            avg_time = sum(all_times) / len(all_times)
            min_time = min(all_times)
            max_time = max(all_times)
            print(f"Average Response Time: {avg_time:.1f}ms")
            print(f"Min Response Time: {min_time:.1f}ms")
            print(f"Max Response Time: {max_time:.1f}ms")
            print(f"Total Test Duration: {(self.end_time - self.start_time).total_seconds():.1f}s")
    
    def print_failures(self) -> None:
        """Print detailed failure information."""
        if not self.failed_prompts:
            print("\n✅ All tests passed! No failures to report.")
            return
        
        print("\n" + "=" * 130)
        print("FAILED PROMPTS - DETAILED ANALYSIS")
        print("=" * 130)
        
        for idx, failure in enumerate(self.failed_prompts, 1):
            print(f"\n❌ [{idx}] {failure['prompt']}")
            print(f"   Category: {failure['category']}")
            print(f"   Issue: {failure['error']}")
    
    def save_results(self, filename: str = "test_results_comprehensive_e2e.json") -> None:
        """Save test results to JSON file."""
        clean_results = {}
        for category, prompts_dict in self.results.items():
            clean_results[category] = {}
            for prompt, result in prompts_dict.items():
                clean_results[category][prompt] = result
        
        output = {
            "total": self.total_prompts,
            "passed": self.passed_prompts,
            "failed": self.total_prompts - self.passed_prompts,
            "pass_rate": round(self.passed_prompts / self.total_prompts * 100, 1) if self.total_prompts > 0 else 0,
            "timestamp": datetime.now().isoformat(),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "results": clean_results,
            "failed_prompts": self.failed_prompts,
        }
        
        with open(filename, "w") as f:
            json.dump(output, f, indent=2)
        
        print(f"\n✅ Test results saved to {filename}")
    
    def generate_report(self, filename: str = "test_report_comprehensive_e2e.txt") -> None:
        """Generate comprehensive test report."""
        report = []
        report.append("=" * 130)
        report.append("COMPREHENSIVE END-TO-END TEST REPORT")
        report.append("=" * 130)
        report.append(f"Test Date: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Prompts: {self.total_prompts}")
        report.append(f"Passed: {self.passed_prompts} ✅")
        report.append(f"Failed: {self.total_prompts - self.passed_prompts} ❌")
        pass_rate = round(self.passed_prompts / self.total_prompts * 100, 1) if self.total_prompts > 0 else 0
        report.append(f"Pass Rate: {pass_rate}%")
        report.append("")
        report.append("CATEGORY BREAKDOWN:")
        report.append("-" * 130)
        
        for category, prompts_dict in self.results.items():
            cat_passed = sum(1 for r in prompts_dict.values() if r["status"] == "PASS")
            cat_total = len(prompts_dict)
            cat_rate = round(cat_passed / cat_total * 100, 1) if cat_total > 0 else 0
            status = "✅" if cat_rate == 100 else "⚠️" if cat_rate >= 75 else "❌"
            report.append(f"{status} {category:<45} {cat_passed:>2}/{cat_total:<2} ({cat_rate:>5.1f}%)")
        
        report.append("")
        report.append("CONCLUSION:")
        report.append("-" * 130)
        if pass_rate >= 95:
            report.append("✅ EXCELLENT - All tests passing with high success rate")
        elif pass_rate >= 90:
            report.append("✅ GOOD - Most tests passing, minor issues to address")
        elif pass_rate >= 75:
            report.append("⚠️ ACCEPTABLE - Some tests failing, improvements needed")
        else:
            report.append("❌ NEEDS WORK - Significant failures, review required")
        
        report.append("=" * 130)
        
        with open(filename, "w") as f:
            f.write("\n".join(report))
        
        print(f"✅ Test report saved to {filename}")


def main():
    """Main test execution."""
    print("\n🚀 Starting Comprehensive End-to-End Test Suite...")
    print("Make sure backend is running on http://localhost:7071")
    print("Make sure data is loaded via /api/daily-refresh\n")
    
    try:
        # Initialize test suite
        test_suite = ComprehensiveE2ETest()
        
        # Fetch dashboard context
        if not test_suite.fetch_dashboard_context():
            print("\n⚠️ WARNING: Could not fetch dashboard context")
            print("Continuing with empty context...\n")
        
        # Run all tests
        test_suite.run_all_tests()
        
        # Print failures
        test_suite.print_failures()
        
        # Save results
        test_suite.save_results()
        
        # Generate report
        test_suite.generate_report()
        
        # Exit with appropriate code
        exit(0 if test_suite.passed_prompts / test_suite.total_prompts >= 0.9 else 1)
        
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        print("Make sure the backend is running on http://localhost:7071")
        exit(1)


if __name__ == "__main__":
    main()

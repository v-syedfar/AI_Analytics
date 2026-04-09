"""
Performance validation for Copilot Real-Time Answers.
Measures response times and validates against targets.
"""

import time
import json
from typing import Dict, List, Tuple
from function_app import (
    _extract_scope,
    _determine_answer_mode,
    _compute_scoped_metrics,
    _generate_comparison_answer,
    _generate_root_cause_answer,
    _generate_why_not_answer,
    _generate_traceability_answer,
    _generate_answer_from_context,
    _classify_question,
)

# Performance targets (milliseconds)
PERFORMANCE_TARGETS = {
    "scope_extraction": 5,
    "answer_mode_determination": 5,
    "scoped_metrics_computation": 100,
    "answer_generation": 50,
    "total_response_time": 500,
}


class PerformanceValidator:
    """Validates performance of Copilot Real-Time Answers."""

    def __init__(self):
        self.results = {}
        self.passed = 0
        self.failed = 0

    def measure_scope_extraction(self, questions: List[str]) -> Dict:
        """Measure scope extraction performance."""
        times = []
        for question in questions:
            start = time.perf_counter()
            _extract_scope(question)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        max_time = max(times)
        target = PERFORMANCE_TARGETS["scope_extraction"]

        result = {
            "operation": "Scope Extraction",
            "count": len(questions),
            "avg_time_ms": round(avg_time, 3),
            "max_time_ms": round(max_time, 3),
            "target_ms": target,
            "passed": avg_time < target,
        }

        self.results["scope_extraction"] = result
        if result["passed"]:
            self.passed += 1
        else:
            self.failed += 1

        return result

    def measure_answer_mode_determination(self, query_types: List[Tuple[str, str]]) -> Dict:
        """Measure answer mode determination performance."""
        times = []
        for query_type, scope_type in query_types:
            start = time.perf_counter()
            _determine_answer_mode(query_type, scope_type)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        max_time = max(times)
        target = PERFORMANCE_TARGETS["answer_mode_determination"]

        result = {
            "operation": "Answer Mode Determination",
            "count": len(query_types),
            "avg_time_ms": round(avg_time, 3),
            "max_time_ms": round(max_time, 3),
            "target_ms": target,
            "passed": avg_time < target,
        }

        self.results["answer_mode_determination"] = result
        if result["passed"]:
            self.passed += 1
        else:
            self.failed += 1

        return result

    def measure_scoped_metrics_computation(self, detail_records: List[Dict], scopes: List[Tuple[str, str]]) -> Dict:
        """Measure scoped metrics computation performance."""
        times = []
        for scope_type, scope_value in scopes:
            start = time.perf_counter()
            _compute_scoped_metrics(detail_records, scope_type, scope_value)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        max_time = max(times)
        target = PERFORMANCE_TARGETS["scoped_metrics_computation"]

        result = {
            "operation": "Scoped Metrics Computation",
            "record_count": len(detail_records),
            "scope_count": len(scopes),
            "avg_time_ms": round(avg_time, 3),
            "max_time_ms": round(max_time, 3),
            "target_ms": target,
            "passed": avg_time < target,
        }

        self.results["scoped_metrics_computation"] = result
        if result["passed"]:
            self.passed += 1
        else:
            self.failed += 1

        return result

    def measure_answer_generation(self, questions: List[str], context: Dict) -> Dict:
        """Measure answer generation performance."""
        times = []
        for question in questions:
            start = time.perf_counter()
            _generate_answer_from_context(question, context)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        max_time = max(times)
        target = PERFORMANCE_TARGETS["answer_generation"]

        result = {
            "operation": "Answer Generation",
            "count": len(questions),
            "avg_time_ms": round(avg_time, 3),
            "max_time_ms": round(max_time, 3),
            "target_ms": target,
            "passed": avg_time < target,
        }

        self.results["answer_generation"] = result
        if result["passed"]:
            self.passed += 1
        else:
            self.failed += 1

        return result

    def measure_total_response_time(self, questions: List[str], context: Dict) -> Dict:
        """Measure total response time for full pipeline."""
        times = []
        for question in questions:
            start = time.perf_counter()
            scope_type, scope_value = _extract_scope(question)
            query_type = _classify_question(question)
            answer_mode = _determine_answer_mode(query_type, scope_type)
            if answer_mode == "investigate":
                scoped_metrics = _compute_scoped_metrics(
                    context.get("detailRecords", []),
                    scope_type,
                    scope_value
                )
            else:
                scoped_metrics = None
            answer = _generate_answer_from_context(
                question, context, answer_mode, scope_type, scope_value, scoped_metrics
            )
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        max_time = max(times)
        target = PERFORMANCE_TARGETS["total_response_time"]

        result = {
            "operation": "Total Response Time",
            "count": len(questions),
            "avg_time_ms": round(avg_time, 3),
            "max_time_ms": round(max_time, 3),
            "target_ms": target,
            "passed": avg_time < target,
        }

        self.results["total_response_time"] = result
        if result["passed"]:
            self.passed += 1
        else:
            self.failed += 1

        return result

    def print_report(self):
        """Print performance validation report."""
        print("\n" + "=" * 80)
        print("COPILOT REAL-TIME ANSWERS - PERFORMANCE VALIDATION REPORT")
        print("=" * 80)

        for operation, result in self.results.items():
            status = "✓ PASS" if result["passed"] else "✗ FAIL"
            print(f"\n{status} | {result['operation']}")
            print(f"  Average: {result['avg_time_ms']}ms (Target: {result['target_ms']}ms)")
            print(f"  Maximum: {result['max_time_ms']}ms")

        print("\n" + "=" * 80)
        print(f"SUMMARY: {self.passed} passed, {self.failed} failed")
        print("=" * 80 + "\n")

        return self.failed == 0


def run_performance_validation():
    """Run complete performance validation."""
    # Sample data
    sample_detail_records = [
        {
            "locationId": f"LOC{i:03d}",
            "supplier": f"SUP{i % 10:03d}",
            "materialGroup": ["Electronics", "Mechanical", "Hydraulic"][i % 3],
            "materialId": f"MAT{i:05d}",
            "changed": i % 2 == 0,
            "qtyChanged": i % 3 == 0,
            "supplierChanged": i % 4 == 0,
            "designChanged": i % 5 == 0,
            "scheduleChanged": i % 6 == 0,
            "qtyDelta": (i - 50) * 100,
            "changeType": ["Qty Increase", "Qty Decrease", "Design Change", "Supplier Change"][i % 4],
            "riskLevel": ["High Risk", "Medium Risk", "Low Risk"][i % 3],
        }
        for i in range(1000)
    ]

    sample_context = {
        "detailRecords": sample_detail_records,
        "planningHealth": 65,
        "changedRecordCount": 350,
        "totalRecords": 1000,
        "aiInsight": "Design changes are driving risk",
        "rootCause": "Supplier changed design specs",
        "recommendedActions": ["Review design changes", "Monitor supplier"],
    }

    sample_questions = [
        "Compare LOC001 vs LOC002",
        "Why is LOC001 risky?",
        "Why is LOC999 not risky?",
        "Show top contributing records",
        "What is the planning health?",
        "Which supplier has design changes?",
        "What should the planner do next?",
    ]

    sample_query_types = [
        ("comparison", "location"),
        ("root_cause", "location"),
        ("why_not", "location"),
        ("traceability", None),
        ("summary", None),
        ("risk", None),
        ("action", None),
    ]

    sample_scopes = [
        ("location", "LOC001"),
        ("location", "LOC002"),
        ("supplier", "SUP001"),
        ("material_group", "Electronics"),
        ("material_id", "MAT00001"),
        (None, None),
    ]

    # Run validation
    validator = PerformanceValidator()

    print("\nRunning performance validation...")
    print(f"Sample size: {len(sample_detail_records)} records")

    validator.measure_scope_extraction(sample_questions)
    validator.measure_answer_mode_determination(sample_query_types)
    validator.measure_scoped_metrics_computation(sample_detail_records, sample_scopes)
    validator.measure_answer_generation(sample_questions, sample_context)
    validator.measure_total_response_time(sample_questions, sample_context)

    # Print report
    all_passed = validator.print_report()

    return all_passed


if __name__ == "__main__":
    success = run_performance_validation()
    exit(0 if success else 1)

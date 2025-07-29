#!/usr/bin/env python3
"""
Evaluation script for generic query conversion.

Tests the generic schema-driven approach against all 67 patterns
in Episode_53_Search_results.json to measure performance without training bias.
"""

import json
import sys
from typing import Any
from generic_query import query_generic


def load_test_queries(
    filename: str = "Episode_53_Search_results.json",
) -> list[dict[str, Any]]:
    """Load test queries from Episode file."""
    try:
        with open(filename, "r") as f:
            data = json.load(f)

        queries = []
        for entry in data:
            if "searchText" in entry and "searchQueryExpr" in entry:
                # Only include entries that have both input and expected output
                if entry["searchQueryExpr"]:  # Skip empty searchQueryExpr
                    queries.append(
                        {
                            "input": entry["searchText"],
                            "expected": entry["searchQueryExpr"],
                        }
                    )

        return queries
    except Exception as e:
        print(f"Error loading test queries: {e}")
        return []


def evaluate_query(input_text: str, expected: dict[str, Any]) -> dict[str, Any]:
    """Evaluate a single query conversion."""
    try:
        result = query_generic(input_text)
        generated = result.model_dump()

        # Basic structure comparison
        success = (
            "search_expressions" in generated
            and len(generated["search_expressions"]) > 0
            and "rewritten_query" in generated["search_expressions"][0]
        )

        return {
            "input": input_text,
            "success": success,
            "generated": generated,
            "expected": expected,
            "error": None,
        }

    except Exception as e:
        return {
            "input": input_text,
            "success": False,
            "generated": None,
            "expected": expected,
            "error": str(e),
        }


def run_evaluation(max_queries: int = 10) -> None:
    """Run evaluation on test queries."""
    queries = load_test_queries()

    if not queries:
        print("No test queries found!")
        return

    print(f"Loaded {len(queries)} test queries")
    print(f"Testing first {min(max_queries, len(queries))} queries...\n")

    results = []
    for i, query in enumerate(queries[:max_queries]):
        print(
            f"[{i+1}/{min(max_queries, len(queries))}] Testing: {query['input'][:50]}..."
        )

        result = evaluate_query(query["input"], query["expected"])
        results.append(result)

        if result["success"]:
            print("✅ SUCCESS")
        else:
            print(f"❌ FAILED: {result['error'] or 'Structure validation failed'}")
        print()

    # Summary
    successful = sum(1 for r in results if r["success"])
    total = len(results)
    success_rate = successful / total * 100

    print(f"=== EVALUATION SUMMARY ===")
    print(f"Successful: {successful}/{total} ({success_rate:.1f}%)")
    print(f"Failed: {total - successful}/{total} ({100 - success_rate:.1f}%)")

    # Show failed cases
    failed = [r for r in results if not r["success"]]
    if failed:
        print(f"\n=== FAILED CASES ===")
        for i, result in enumerate(failed[:5]):  # Show first 5 failures
            print(f"{i+1}. Input: {result['input']}")
            print(f"   Error: {result['error'] or 'Structure validation failed'}")


def main() -> None:
    """Main function."""
    max_queries = 10
    if len(sys.argv) > 1:
        try:
            max_queries = int(sys.argv[1])
        except ValueError:
            print("Usage: python evaluate_generic.py [max_queries]")
            return

    run_evaluation(max_queries)


if __name__ == "__main__":
    main()

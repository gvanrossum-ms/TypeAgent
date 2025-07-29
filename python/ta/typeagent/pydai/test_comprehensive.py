#!/usr/bin/env python3

import json

from query import query


def test_comprehensive_queries() -> None:
    """Test various types of queries to ensure the prompt works well."""

    test_cases = [
        # List all X queries (should use entity_search_terms)
        {
            "query": "List all books",
            "expected_entity_type": "book",
            "expected_name": "*",
            "expected_search_terms": [],
        },
        {
            "query": "Find all movies",
            "expected_entity_type": "movie",
            "expected_name": "*",
            "expected_search_terms": [],
        },
        {
            "query": "Show me all people",
            "expected_entity_type": "person",
            "expected_name": "*",
            "expected_search_terms": [],
        },
        # Topic-based queries (should use search_terms)
        {
            "query": "Tell me about artificial intelligence",
            "expected_search_terms": ["artificial intelligence"],
            "should_have_entity_terms": False,
        },
        # Mixed queries
        {
            "query": "Books about science",
            "expected_entity_type": "book",
            "expected_search_terms": ["science"],
        },
    ]

    for i, test_case in enumerate(test_cases):
        print(f"\n--- Test {i+1}: '{test_case['query']}' ---")

        try:
            result = query(test_case["query"])
            search_expr = result.search_expressions[0]
            filter_obj = search_expr.filters[0]

            print(f"Rewritten query: {search_expr.rewritten_query}")

            # Check entity search terms
            if "expected_entity_type" in test_case:
                if filter_obj.entity_search_terms:
                    entity_term = filter_obj.entity_search_terms[0]
                    print(
                        f"✓ Entity type: {entity_term.type} (expected: {test_case['expected_entity_type']})"
                    )
                    if "expected_name" in test_case:
                        print(
                            f"✓ Entity name: {entity_term.name} (expected: {test_case['expected_name']})"
                        )
                else:
                    print("✗ No entity search terms found")

            # Check search terms
            if "expected_search_terms" in test_case:
                print(
                    f"✓ Search terms: {filter_obj.search_terms} (expected: {test_case['expected_search_terms']})"
                )

            # Check if should NOT have entity terms
            if test_case.get("should_have_entity_terms") == False:
                if not filter_obj.entity_search_terms:
                    print("✓ Correctly has no entity search terms")
                else:
                    print("✗ Unexpectedly has entity search terms")

        except Exception as e:
            print(f"✗ Error: {e}")


def extract_search_expressions_json(result):
    """Extract just the search_expressions part to match your desired format."""
    return {
        "searchExpressions": [
            {
                "rewrittenQuery": expr.rewritten_query,
                "filters": [
                    {
                        "entitySearchTerms": (
                            [
                                {
                                    "name": term.name,
                                    "isNamePronoun": term.is_name_pronoun,
                                    "type": term.type,
                                }
                                for term in (filter_obj.entity_search_terms or [])
                            ]
                            if filter_obj.entity_search_terms
                            else []
                        ),
                        "searchTerms": filter_obj.search_terms or [],
                    }
                    for filter_obj in expr.filters
                ],
            }
            for expr in result.search_expressions
        ]
    }


if __name__ == "__main__":
    print("=== Comprehensive Query Testing ===")
    test_comprehensive_queries()

    print("\n\n=== 'List all books' in your desired JSON format ===")
    result = query("List all books")
    formatted_result = extract_search_expressions_json(result)

    print("Formatted result:")
    print(json.dumps(formatted_result, indent=4))

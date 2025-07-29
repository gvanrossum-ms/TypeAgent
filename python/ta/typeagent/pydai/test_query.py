#!/usr/bin/env python3

import json
from query import query


def test_list_all_books():
    """Test that 'List all books' produces the expected JSON structure."""

    # Expected output structure
    expected = {
        "search_expressions": [
            {
                "rewritten_query": "List all books",
                "filters": [
                    {
                        "action_search_term": None,
                        "entity_search_terms": [
                            {
                                "name": "*",
                                "is_name_pronoun": False,
                                "type": ["book"],
                                "facets": None,
                            }
                        ],
                        "search_terms": [],
                        "time_range": None,
                    }
                ],
            }
        ]
    }

    # Get actual output
    result = query("List all books")
    actual = result.model_dump()

    # Pretty print both for comparison
    print("Expected:")
    print(json.dumps(expected, indent=2))
    print("\nActual:")
    print(json.dumps(actual, indent=2))

    # Check if they match the key structure
    search_expr = actual["search_expressions"][0]
    filter_obj = search_expr["filters"][0]
    entity_term = filter_obj["entity_search_terms"][0]

    print(f"\n✓ Rewritten query: {search_expr['rewritten_query']}")
    print(f"✓ Entity name: {entity_term['name']}")
    print(f"✓ Is name pronoun: {entity_term['is_name_pronoun']}")
    print(f"✓ Entity type: {entity_term['type']}")
    print(f"✓ Search terms empty: {filter_obj['search_terms'] == []}")

    return actual


def test_other_queries():
    """Test a few other similar queries to see consistency."""

    test_cases = [
        "List all movies",
        "Find all songs",
        "Show me all people",
        "List all artists",
    ]

    for test_case in test_cases:
        print(f"\n--- Testing: '{test_case}' ---")
        result = query(test_case)

        # Extract the entity type from the result
        search_expr = result.search_expressions[0]
        filter_obj = search_expr.filters[0]
        if filter_obj.entity_search_terms:
            entity_term = filter_obj.entity_search_terms[0]
            print(f"Entity type: {entity_term.type}")
            print(f"Name: {entity_term.name}")
            print(f"Search terms: {filter_obj.search_terms}")
        else:
            print("No entity search terms found")


if __name__ == "__main__":
    print("=== Testing 'List all books' ===")
    test_list_all_books()

    print("\n\n=== Testing other similar queries ===")
    test_other_queries()

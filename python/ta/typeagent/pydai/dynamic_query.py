#!/usr/bin/env python3
"""
Pattern-based query conversion using training examples from a dataset.
This approach scales to hundreds of patterns without bloating the prompt.
"""

import json

from query import make_agent
from search_query_schema import SearchQuery


# Sample training patterns - in practice, load from a JSON file
TRAINING_PATTERNS = [
    {
        "input": "List all books",
        "output": {
            "entity_search_terms": [
                {"name": "*", "is_name_pronoun": False, "type": ["book"]}
            ],
            "search_terms": [],
        },
    },
    {
        "input": "Find all movies",
        "output": {
            "entity_search_terms": [
                {"name": "*", "is_name_pronoun": False, "type": ["movie"]}
            ],
            "search_terms": [],
        },
    },
    {
        "input": "Books by Tolkien",
        "output": {
            "entity_search_terms": [
                {"name": "Tolkien", "type": ["person"]},
                {"name": "*", "type": ["book"]},
            ],
            "search_terms": [],
        },
    },
    {
        "input": "What did Einstein say about relativity?",
        "output": {
            "action_search_term": {
                "actor_entities": [{"name": "Einstein", "type": ["person"]}],
                "action_verbs": {"words": ["say"], "tense": "Past"},
            },
            "search_terms": ["relativity"],
        },
    },
    # Add your 60+ patterns here...
]


def find_similar_patterns(
    query: str, patterns: list[dict], num_examples: int = 3
) -> list[dict]:
    """Find the most similar training patterns to use as examples."""
    # Simple similarity - in practice, use embedding similarity or fuzzy matching
    query_lower = query.lower()

    scored_patterns = []
    for pattern in patterns:
        input_lower = pattern["input"].lower()

        # Simple word overlap scoring
        query_words = set(query_lower.split())
        pattern_words = set(input_lower.split())
        overlap = len(query_words & pattern_words)

        # Boost score for structural similarities
        if any(word in query_lower for word in ["list", "find", "all"]) and any(
            word in input_lower for word in ["list", "find", "all"]
        ):
            overlap += 2

        scored_patterns.append((overlap, pattern))

    # Return top N most similar patterns
    scored_patterns.sort(reverse=True, key=lambda x: x[0])
    return [pattern for _, pattern in scored_patterns[:num_examples]]


def query_with_dynamic_examples(
    question: str, patterns: list[dict] | None = None
) -> SearchQuery:
    """Query using dynamically selected training examples."""
    if patterns is None:
        patterns = TRAINING_PATTERNS

    # Find relevant examples
    similar_patterns = find_similar_patterns(question, patterns, num_examples=3)

    # Build few-shot examples
    examples_text = ""
    for pattern in similar_patterns:
        examples_text += f"INPUT: \"{pattern['input']}\"\n"
        examples_text += f"OUTPUT: {json.dumps(pattern['output'])}\n\n"

    agent = make_agent()

    prompt = f"""Convert user questions to SearchQuery format using these similar examples:

{examples_text}

Follow the patterns shown above. Key guidelines:
- "List/find all X" → entity_search_terms with name="*", type=[X]
- Named entities → use actual names with types
- Actions → use action_search_term structure
- Topics → use search_terms
- Always include rewritten_query

Question: {question}"""

    print("Generated prompt:")
    print(prompt)
    print("-" * 50)

    result = agent.run_sync(prompt)

    print(f"Used examples: {[p['input'] for p in similar_patterns]}")
    print(result.usage())
    return result.output


if __name__ == "__main__":
    # Test with dynamic examples
    test_queries = [
        "List all books",
        "Find all artists",
        "Movies by Spielberg",
        "What did Newton discover?",
    ]

    for query in test_queries:
        print(f"\n=== Query: '{query}' ===")
        result = query_with_dynamic_examples(query)
        print(f"Result: {result}")

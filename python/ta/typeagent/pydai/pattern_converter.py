#!/usr/bin/env python3
"""
Scalable query conversion using external training data and pattern matching.
"""

import json
import os

from query import make_agent
from search_query_schema import SearchQuery


class PatternBasedQueryConverter:
    def __init__(self, patterns_file: str = "training_patterns.json") -> None:
        self.patterns_file = patterns_file
        self.patterns = self._load_patterns()
        self.agent = make_agent()

    def _load_patterns(self) -> list[dict]:
        """Load training patterns from JSON file."""
        if os.path.exists(self.patterns_file):
            with open(self.patterns_file, "r") as f:
                data = json.load(f)
                return data.get("patterns", [])
        return []

    def _find_similar_patterns(self, query: str, max_examples: int = 3) -> list[dict]:
        """Find patterns similar to the input query."""
        query_lower = query.lower()
        scored_patterns = []

        for pattern in self.patterns:
            input_lower = pattern["input"].lower()
            score = 0

            # Word overlap
            query_words = set(query_lower.split())
            pattern_words = set(input_lower.split())
            score += len(query_words & pattern_words)

            # Category-specific boosting
            category = pattern.get("category", "")
            if "list" in query_lower and category == "list_all":
                score += 5
            elif (
                any(word in query_lower for word in ["by", "from", "created"])
                and category == "entity_by_creator"
            ):
                score += 5
            elif (
                any(word in query_lower for word in ["what", "did", "say", "do"])
                and category == "action_query"
            ):
                score += 5
            elif (
                any(word in query_lower for word in ["about", "tell", "explain"])
                and category == "topic_search"
            ):
                score += 5

            scored_patterns.append((score, pattern))

        # Sort by score and return top patterns
        scored_patterns.sort(reverse=True, key=lambda x: x[0])
        return [pattern for _, pattern in scored_patterns[:max_examples]]

    def convert_query(self, question: str) -> SearchQuery:
        """Convert question to SearchQuery using pattern matching."""
        similar_patterns = self._find_similar_patterns(question)

        if not similar_patterns:
            # Fallback to basic prompt if no patterns found
            return self._basic_conversion(question)

        # Build examples from similar patterns
        examples_text = "Here are similar examples:\n\n"
        for pattern in similar_patterns:
            examples_text += f"INPUT: \"{pattern['input']}\"\n"
            examples_text += f"OUTPUT: {json.dumps(pattern['output'], indent=2)}\n\n"

        prompt = f"""{examples_text}

Based on the patterns above, convert this question to SearchQuery format:

Question: {question}

Follow the same structural patterns as the examples. Ensure proper field names and types."""

        result = self.agent.run_sync(prompt)
        print(f"Used {len(similar_patterns)} example patterns")
        print(result.usage())
        return result.output

    def _basic_conversion(self, question: str) -> SearchQuery:
        """Fallback conversion when no patterns match."""
        result = self.agent.run_sync(
            f"Convert this question to SearchQuery format: {question}"
        )
        print("Used fallback conversion (no patterns matched)")
        print(result.usage())
        return result.output

    def add_pattern(
        self, input_text: str, expected_output: dict, category: str = "custom"
    ) -> None:
        """Add a new pattern to the training data."""
        new_pattern = {
            "category": category,
            "input": input_text,
            "output": expected_output,
        }

        self.patterns.append(new_pattern)

        # Save back to file
        data = {"patterns": self.patterns}
        with open(self.patterns_file, "w") as f:
            json.dump(data, f, indent=2)

        print(f"Added new pattern: '{input_text}' -> {category}")


# Usage example
if __name__ == "__main__":
    converter = PatternBasedQueryConverter()

    test_queries = [
        "List all books",
        "Find all songs",
        "Movies by Christopher Nolan",
        "What did Shakespeare write?",
        "Tell me about quantum physics",
    ]

    for query in test_queries:
        print(f"\n=== Query: '{query}' ===")
        result = converter.convert_query(query)
        print(f"Result type: {type(result).__name__}")
        if hasattr(result, "search_expressions"):
            print(f"Number of expressions: {len(result.search_expressions)}")

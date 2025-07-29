#!/usr/bin/env python3
"""
RECOMMENDED APPROACH: Scalable Query Conversion

This approach can handle 60+ patterns efficiently by:
1. Using external training data (JSON file)
2. Dynamic pattern selection based on similarity
3. Few-shot learning with relevant examples
4. Fallback mechanisms for unknown patterns
5. Easy pattern addition and maintenance
"""

import json
import os
import sys

from colorama import Fore

from query import make_agent
from search_query_schema import SearchQuery


class ScalableQueryConverter:
    """
    A scalable query converter that uses pattern matching and few-shot learning.

    Benefits:
    - Handles 60+ patterns without prompt bloat
    - Easy to add new patterns via JSON file
    - Automatic similarity-based example selection
    - Maintains consistent output format
    - Fast inference with cached examples
    """

    def __init__(self, patterns_file: str = "Episode_53_Search_results.json") -> None:
        self.patterns_file = patterns_file
        self.patterns = self._load_patterns()
        self.agent = make_agent()
        self._pattern_cache: dict[str, list[dict]] = {}  # Cache for performance

    def _load_patterns(self) -> list[dict]:
        """Load and validate training patterns."""
        if not os.path.exists(self.patterns_file):
            print(
                f"Warning: Episode file {self.patterns_file} not found. Using minimal defaults."
            )
            return self._get_minimal_patterns()

        try:
            with open(self.patterns_file, "r") as f:
                data = json.load(f)

                # Convert from Episode_53 format to our internal format
                patterns = []
                for entry in data:
                    if "searchText" in entry and "searchQueryExpr" in entry:
                        pattern = {
                            "category": "extracted",
                            "input": entry["searchText"],
                            "output": entry["searchQueryExpr"],
                        }
                        patterns.append(pattern)

                print(
                    f"Loaded {len(patterns)} training patterns from {self.patterns_file}"
                )
                return patterns
        except Exception as e:
            print(
                f"Error loading patterns from {self.patterns_file}: {e}. Using minimal defaults."
            )
            return self._get_minimal_patterns()

    def _get_minimal_patterns(self) -> list[dict]:
        """Minimal pattern set for when external file is unavailable."""
        return [
            {
                "category": "list_all",
                "input": "List all books",
                "output_template": {
                    "entity_search_terms": [
                        {"name": "*", "is_name_pronoun": False, "type": ["book"]}
                    ],
                    "search_terms": [],
                },
            }
        ]

    def _calculate_similarity(self, query: str, pattern: dict) -> float:
        """Calculate similarity score between query and pattern."""
        query_lower = query.lower()
        pattern_input = pattern["input"].lower()

        # Word overlap scoring
        query_words = set(query_lower.split())
        pattern_words = set(pattern_input.split())
        word_overlap = len(query_words & pattern_words) / max(len(query_words), 1)

        # Pattern-specific boosts
        category_boost = 0.0
        category = pattern.get("category", "")

        if category == "list_all" and any(
            word in query_lower for word in ["list", "find", "all", "show"]
        ):
            category_boost = 0.5
        elif category == "entity_by_creator" and any(
            word in query_lower for word in ["by", "from", "written", "created"]
        ):
            category_boost = 0.5
        elif category == "action_query" and any(
            word in query_lower for word in ["what", "did", "say", "do", "tell"]
        ):
            category_boost = 0.5
        elif category == "topic_search" and any(
            word in query_lower for word in ["about", "explain", "discuss"]
        ):
            category_boost = 0.5

        return word_overlap + category_boost

    def _select_examples(self, query: str, max_examples: int = 3) -> list[dict]:
        """Select the best example patterns for the given query."""
        if query in self._pattern_cache:
            return self._pattern_cache[query]

        scored_patterns = [
            (self._calculate_similarity(query, pattern), pattern)
            for pattern in self.patterns
        ]

        # Sort by similarity and take top examples
        scored_patterns.sort(reverse=True, key=lambda x: x[0])
        selected = [pattern for _, pattern in scored_patterns[:max_examples]]

        # Cache the result
        self._pattern_cache[query] = selected
        return selected

    def convert(self, question: str) -> SearchQuery:
        """Convert question to SearchQuery using intelligent pattern matching."""
        # Select relevant examples
        examples = self._select_examples(question)

        if not examples:
            return self._fallback_conversion(question)

        # Build prompt with selected examples
        examples_text = "Convert based on these similar patterns:\n\n"
        for example in examples:
            examples_text += f"INPUT: \"{example['input']}\"\n"
            if "output" in example:
                examples_text += f"OUTPUT: {json.dumps(example['output'])}\n\n"
            elif "output_template" in example:
                examples_text += (
                    f"OUTPUT PATTERN: {json.dumps(example['output_template'])}\n\n"
                )

        prompt = f"""{examples_text}

Follow the same patterns above. Key rules:
- Always include rewritten_query field
- Use entity_search_terms for tangible entities (people, books, movies, etc.)
- Use search_terms for abstract concepts/topics
- Use action_search_term for action-based queries
- Set appropriate types and names

Convert this question: {question}"""

        print(Fore.YELLOW + prompt + Fore.RESET)
        result = self.agent.run_sync(prompt)
        print(f"Used {len(examples)} example patterns for conversion")
        print(result.usage())
        return result.output

    def _fallback_conversion(self, question: str) -> SearchQuery:
        """Simple fallback when no patterns match."""
        prompt = f"""Convert this question to SearchQuery format with proper structure.
        
Question: {question}

Use entity_search_terms for concrete entities, search_terms for topics, and include rewritten_query."""

        result = self.agent.run_sync(prompt)
        print("Used fallback conversion")
        print(result.usage())
        return result.output

    def add_training_example(
        self, input_text: str, expected_output: dict, category: str = "custom"
    ) -> None:
        """Add new training example to improve future conversions."""
        new_pattern = {
            "category": category,
            "input": input_text,
            "output": expected_output,
        }

        self.patterns.append(new_pattern)

        # Clear cache since patterns changed
        self._pattern_cache.clear()

        # Optionally save to file
        try:
            data = {"patterns": self.patterns}
            with open(self.patterns_file, "w") as f:
                json.dump(data, f, indent=2)
            print(f"Added and saved new pattern: '{input_text}'")
        except Exception as e:
            print(f"Added pattern to memory but couldn't save to file: {e}")


def query_scalable(question: str) -> SearchQuery:
    """Drop-in replacement for your original query function."""
    converter = ScalableQueryConverter()
    return converter.convert(question)


def main() -> None:
    """Main function to test the scalable query converter."""
    # Get query from command line argument or use default
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "List all books"

    # Demonstration
    converter = ScalableQueryConverter()

    # Test the query
    print(f"=== Testing '{query}' ===")
    result = converter.convert(query)

    # Extract just the search_expressions for comparison with your desired format
    search_exprs = result.model_dump()["search_expressions"]
    formatted = {"searchExpressions": search_exprs}

    print("Formatted result:")
    print(json.dumps(formatted, indent=2))


if __name__ == "__main__":
    main()

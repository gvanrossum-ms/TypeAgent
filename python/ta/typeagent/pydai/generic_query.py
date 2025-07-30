#!/usr/bin/env python3
"""
Generic Query Conversion using Schema-Driven Approach

This approach relies entirely on the Pydantic schema descriptions to guide
the LLM, similar to TypeChat. No dynamic examples or few-shot learning.
The schema descriptions in search_query_schema.py provide all the guidance needed.
"""

import asyncio
import json
import sys
from os import getenv

from dotenv import load_dotenv
from httpx import get
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.azure import AzureProvider

from typeagent.aitools.auth import get_shared_token_provider

from .search_query_schema import SearchQuery


def make_agent() -> Agent[None, SearchQuery]:
    """Create agent with schema-driven approach."""
    api_key = getenv("AZURE_OPENAI_API_KEY")
    if api_key == "identity":
        token_provider = get_shared_token_provider()
        api_key = token_provider.get_token()

    model = OpenAIModel(
        "gpt-4o",
        provider=AzureProvider(
            azure_endpoint=getenv("AZURE_OPENAI_ENDPOINT"),
            api_version="2024-08-01-preview",
            api_key=api_key,
        ),
    )

    return Agent(model, output_type=SearchQuery)


async def query_generic(question: str) -> SearchQuery:
    """
    Convert question to SearchQuery using pure schema-driven approach.
    No examples, no few-shot learning - just the schema descriptions.
    """
    agent = make_agent()

    prompt = f"""\
Convert the user's natural language question into a structured SearchQuery.
Follow the schema documentation exactly.

REQUIRED STRUCTURES:
- EntityTerm: {{"name": "...", "is_name_pronoun": false, "type": ["book"], "facets": null}}
- VerbsTerm: {{"words": ["mention"], "tense": "Past"}}
- time_range structure: {{"start_date": {{"date": {{"day": 1, "month": 5, "year": 2023}}, "time": {{"hour": 0, "minute": 0, "seconds": 0}}}}}}

FIELD USAGE:
- entity_search_terms: tangible things (people, places, books, etc.)
- search_terms: abstract concepts not covered by entities/actions
- action_search_term: when asking about actions/interactions
- facets: for entity properties like [{{"facet_name": "publication_year", "facet_value": "2008"}}]

TIME RANGE RULE:
time_range is ONLY for message timestamps, NOT content attributes!
- USE: "first 15 minutes", "messages between 2-3pm"
- DON'T USE: "published in 2008" (use entity facets instead)

User question: {question}\
"""

    retries = 3
    for i in range(retries):
        try:
            result = await agent.run(prompt)
            # print(result.usage())
            return result.output
        except Exception as e:
            print(f"### Attempt {i + 1} failed: {e}")
            if i + 1 == retries:
                raise


def main() -> None:
    """Main function to test the generic query converter."""
    # Get query from command line argument or use default
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "List all books"

    print(f"# Testing '{query}' (Generic Schema-Driven) #")
    result = asyncio.run(query_generic(query))

    # Format for comparison
    search_exprs = result.model_dump()["search_expressions"]
    formatted = {"searchExpressions": search_exprs}

    print("## Formatted result ##")
    print(json.dumps(formatted, indent=2))


if __name__ == "__main__":
    load_dotenv("../../ts/.env")
    main()

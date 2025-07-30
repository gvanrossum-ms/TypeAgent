#!/usr/bin/env python3
"""
Generic Query Conversion using Schem- time_range structure: {{"start_date": {{"date": {{"day": 1, "month": 5, "year": 2023}}, "time": {{"hour": 0, "minute": 0, "seconds": 0}}}}, "stop_date": {{"date": {{"day": 1, "month": 5, "year": 2023}}, "time": {{"hour": 0, "minute": 15, "seconds": 0}}}}}}-Driven Approach

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

CRITICAL RULES:
1. Set rewritten_query to the original question with minor corrections (fix typos, remove "please")
   but NEVER omit meaningful phrases or time references!
2. For time ranges like "first 15 minutes", ALWAYS include BOTH start_date AND stop_date!

REQUIRED STRUCTURES:
- EntityTerm: {{"name": "...", "is_name_pronoun": false, "type": ["book"], "facets": null}}
- VerbsTerm: {{"words": ["mention"], "tense": "Past"}}
- ActionTerm: {{"action_verbs": {{"words": ["referenced"], "tense": "Past"}},
              "actor_entities": "*", "target_entities": [entity], "is_informational": false}}
- time_range: {{"start_date": {{"date": {{"day": 1, "month": 4, "year": 2020}},
                                "time": {{"hour": 9, "minute": 0, "seconds": 0}}}},
                 "stop_date": {{"date": {{"day": 1, "month": 4, "year": 2020}},
                                "time": {{"hour": 9, "minute": 30, "seconds": 0}}}}}}

FIELD USAGE:
- entity_search_terms: tangible things (people, places, books, etc.)
- search_terms: abstract concepts not covered by entities/actions
- action_search_term: when asking about actions/interactions
- facets: for entity properties like [{{"facet_name": "publication_year", "facet_value": "2008"}}]

ENTITY NAME RULES:
- Use name="*" when asking for "all books", "all movies", etc. to match any entity of that type
- Use specific names like "Asimov", "Harry Potter" for particular entities

ACTION PATTERNS:
- "What did X say about Y?" → action_verbs: ["say"], actor_entities: [X], target_entities: [Y]
- "Summarize X's thoughts to Y?" → action_verbs: ["summarize", "explain", "say"], actor_entities: [X], target_entities: [Y]
- "Who was that X we talked about?" → entity_search_terms: [EntityTerm(name="*", type=["person"])], search_terms: ["X"]
- "How did X get referenced?" → action_verbs: ["referenced"], actor_entities: "*", target_entities: [X]
- "Who mentioned X?" → action_verbs: ["mentioned"], actor_entities: "*", target_entities: [X]

IMPORTANT: Questions like "How did X get [verb]?" should use action_search_term with the verb!

TIME RANGE RULE:
time_range is ONLY for message timestamps, NOT content attributes!
- For relative times like "first 15 minutes", use the start of the CONVERSATION TIME RANGE as the reference.
- USE: "first 15 minutes", "messages between 2-3pm"
- DON'T USE: "published in 2008" (use entity facets instead)

User question: {question}\
"""

    # print(prompt)
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

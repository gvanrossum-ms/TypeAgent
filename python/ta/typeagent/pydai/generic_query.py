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

IMPORTANT STRUCTURE NOTES:
- action_verbs must have "words" (array of strings) and "tense" fields
- actor_entities can be a list of EntityTerm objects OR the string "*"
- EntityTerm objects must have "name", "is_name_pronoun", and optionally "type" and "facets"

CORE PRINCIPLES:
1. Use entity_search_terms for specific, tangible people, places, institutions, or things
2. Use search_terms for abstract concepts, topics, or terms that don't fit ActionTerms or EntityTerms
3. Use action_search_term for queries about actions, interactions, or what someone said/did
4. Set rewritten_query to the user's original question
5. Resolve references like 'it', 'that', 'them' to make expressions standalone

ENTITY GUIDELINES:
- name: "*" means match any entity of that type
- type: specific types like 'book', 'movie', 'person', 'animal' (NOT generic like 'object')
- is_name_pronoun: true for pronouns like 'we', 'I', 'you'
- facets: for properties like color(blue), profession(writer)

ACTION GUIDELINES:
- Use when asking what someone said, did, or interactions between entities
- actor_entities: who performed the action (can be "*" for any actor, or list of EntityTerm)
- target_entities: recipient of the action (always a list of EntityTerm or null)
- action_verbs: MUST have "words" array and "tense" ("Past", "Present", "Future")
- is_informational: true when asking for info about entities, false for actions/interactions

SEARCH TERMS GUIDELINES:
- For abstract concepts, topics that aren't tangible entities
- Don't use noisy terms like 'topic', 'subject', 'discussion'
- Use empty array for summaries

TIME RANGE GUIDELINES:
IMPORTANT: time_range filters ONLY the timestamps of messages/conversations, NOT content attributes!

USE time_range for:
- Message timing: "first 15 minutes", "last hour", "between 2-3pm", "messages from yesterday"
- Conversation periods: "during the meeting", "in the morning session"
- When you want to limit WHICH messages to search in based on when they were sent

DO NOT use time_range for:
- Content attributes: "published in 2008", "written in the 1990s", "released last year"
- Entity properties: "books from 2008", "movies made in the 80s", "songs from 2020"
- Instead use entity facets like: publication_date(2008), year(2008), release_year(2008)

For relative times like "first X minutes", assume it starts from the beginning of the conversation/session
- Use the base date 2023-05-01 00:00:00 as the reference point for relative times
- time_range structure must use exact field names: "start_date", "stop_date", "date", "time", "day", "month", "year", "hour", "minute", "seconds"

Examples of CORRECT time_range usage:
  * "first 15 minutes" → start_date: 2023-05-01 00:00:00, stop_date: 2023-05-01 00:15:00
  * "messages between 2-3pm" → start_date: 2023-05-01 14:00:00, stop_date: 2023-05-01 15:00:00

Examples of INCORRECT time_range usage (use entity facets instead):
  * "novels published in 2008" → EntityTerm with facets: [{{"facet_name": "publication_year", "facet_value": "2008"}}]
  * "books written in the 1990s" → EntityTerm with facets: [{{"facet_name": "decade", "facet_value": "1990s"}}]

EXACT required structure (use these exact values for "first 15 minutes"):
  time_range: {{
    "start_date": {{
      "date": {{ "day": 1, "month": 5, "year": 2023 }},
      "time": {{ "hour": 0, "minute": 0, "seconds": 0 }}
    }},
    "stop_date": {{
      "date": {{ "day": 1, "month": 5, "year": 2023 }},
      "time": {{ "hour": 0, "minute": 15, "seconds": 0 }}
    }}
  }}

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

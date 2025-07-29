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

    prompt = f"""Convert to SearchQuery format:

Key fields:
- entity_search_terms: tangible entities (people, books, movies, places)
  - name: entity name or "*" for any
  - is_name_pronoun: boolean (required)
  - type: array like ["book"], ["person"], ["movie"] (required)
- search_terms: abstract topics/concepts (array)
- action_search_term: for actions/speech
  - action_verbs: object with "words" (array) and "tense" (string)
  - actor_entities: who did the action
- rewritten_query: copy original question

ONLY IF user request explicitly asks for time ranges,
THEN use the CONVERSATION TIME RANGE: "07:00 to 08:00"

Question: {question}"""

    for i in range(3):
        try:
            result = await agent.run(prompt)
            # print(result.usage())
            return result.output
        except Exception as e:
            print(f"### Attempt {i + 1} failed: {e}")
            if i == 2:
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

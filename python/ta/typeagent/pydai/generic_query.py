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
from pydantic_ai import Agent, NativeOutput, ToolOutput
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.azure import AzureProvider

import typechat

from typeagent.aitools.auth import get_shared_token_provider

from .prompts import BIG_PROMPT
from .search_query_schema import SearchQuery


def make_agent() -> Agent[None, SearchQuery]:
    """Create agent with schema-driven approach."""
    if openai_api_key := getenv("OPENAI_API_KEY"):
        model = OpenAIModel("gpt-4o")
        Wrapper = NativeOutput

    elif azure_openai_api_key := getenv("AZURE_OPENAI_API_KEY"):
        if azure_openai_api_key == "identity":
            token_provider = get_shared_token_provider()
            azure_openai_api_key = token_provider.get_token()
        model = OpenAIModel(
            "gpt-4o",
            provider=AzureProvider(
                azure_endpoint=getenv("AZURE_OPENAI_ENDPOINT"),
                api_version="2024-08-01-preview",
                api_key=azure_openai_api_key,
            ),
        )
        Wrapper = ToolOutput

    else:
        raise RuntimeError(
            "Neither OPENAI_API_KEY nor AZURE_OPENAI_API_KEY was provided."
        )

    return Agent(model, output_type=Wrapper(SearchQuery, strict=True), retries=2)


async def query_generic(
    question: str, prompt_preamble: list[typechat.PromptSection] | None = None
) -> SearchQuery:
    """Convert question to SearchQuery using an LLM."""
    agent = make_agent()

    texts = []
    if prompt_preamble:
        for section in prompt_preamble:
            texts.append(section["content"])
    texts.append(question)
    prompt = " ".join(texts)

    # print(prompt)
    retries = 1
    for i in reversed(range(retries)):
        try:
            result = await agent.run(prompt)
            print(result.usage())
            return result.output
        except Exception as e:
            if retries > 1:
                print(f"### Attempt {retries - i}/{retries} failed: {e}")
            if i == 0:
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

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import asyncio
import datetime
import json
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv

from typeagent.knowpro.convutils import get_time_range_prompt_section_for_conversation
from typeagent.knowpro.interfaces import IConversation, IMessage, kplib
from typeagent.pydai.generic_query import query_generic


@dataclass
class MockMessage(IMessage):
    id: str
    timestamp: str | None = None
    text: str | None = None
    text_embedding: list[float] | None = None
    text_from: str | None = None

    # Implement abstract properties/methods from IMessage and IKnowledgeSource
    text_chunks: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: Any = None
    deletion_info: Any = None

    def get_knowledge(self) -> kplib.KnowledgeResponse:
        return kplib.KnowledgeResponse(
            entities=[], actions=[], inverse_actions=[], topics=[]
        )


@dataclass
class MockConversation(IConversation):
    # Override messages with Any to avoid IMessageCollection issue in test
    messages: Any = field(default_factory=list)

    # Implement abstract properties from IConversation
    name_tag: str = "mock_conversation"
    tags: list[str] = field(default_factory=list)
    semantic_refs: Any = None
    semantic_ref_index: Any = None
    secondary_indexes: Any = None


async def main():
    """
    Tests the time range interpretation of the LLM.
    """
    load_dotenv("../../ts/.env")

    # 1. Create a mock conversation from 7am to 8am
    start_time = datetime.datetime(2025, 7, 30, 7, 0, 0)
    end_time = datetime.datetime(2025, 7, 30, 8, 0, 0)

    conversation = MockConversation(
        messages=[
            MockMessage(id="1", timestamp=start_time.isoformat()),
            MockMessage(id="2", timestamp=end_time.isoformat()),
        ]
    )

    # 2. Generate the time range prompt section
    time_range_prompt = get_time_range_prompt_section_for_conversation(conversation)
    prompt_text = ""
    if time_range_prompt:
        prompt_text = time_range_prompt["content"]

    # 3. Ask a question about the first 15 minutes
    question = "what happened in the first 15 minutes?"
    full_query = f"{prompt_text}\n{question}"

    print("--- Sending Query to LLM ---")
    print(full_query)
    print("----------------------------")

    # 4. Get the result from the LLM
    result = await query_generic(full_query)

    # 5. Print the result
    search_exprs = result.model_dump()["search_expressions"]
    formatted = {"searchExpressions": search_exprs}

    print("\n--- LLM Generated SearchQuery ---")
    print(json.dumps(formatted, indent=2))
    print("---------------------------------")


if __name__ == "__main__":
    asyncio.run(main())

from os import getenv

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.azure import AzureProvider

from typeagent.aitools.auth import AzureTokenProvider

from search_query_schema import SearchQuery

load_dotenv(".env")


def make_agent() -> Agent[None, SearchQuery]:
    api_key = getenv("AZURE_OPENAI_API_KEY")
    if api_key == "identity":
        token_provider = AzureTokenProvider()
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


agent = make_agent()


def query(question: str) -> SearchQuery:
    # Core pattern-based examples for few-shot learning
    examples = """
INPUT: "List all books"
OUTPUT: entity_search_terms=[{name:"*", is_name_pronoun:false, type:["book"]}], search_terms:[]

INPUT: "Find movies by Spielberg" 
OUTPUT: entity_search_terms=[{name:"Spielberg", type:["person"]}, {name:"*", type:["movie"]}], search_terms:[]

INPUT: "What did John say about AI?"
OUTPUT: action_search_term={actor_entities:[{name:"John", type:["person"]}], action_verbs:{words:["say"], tense:"Past"}}, search_terms:["AI"]

INPUT: "Tell me about machine learning"
OUTPUT: search_terms:["machine learning"], entity_search_terms:[]
"""

    result = agent.run_sync(
        f"""Convert user questions to SearchQuery format. Learn from these patterns:

{examples}

Key principles:
1. "List/find all X" → entity_search_terms with name="*" and type=[X]
2. Named entities → use actual names with appropriate types
3. Actions/verbs → use action_search_term with proper structure
4. Abstract topics → use search_terms
5. Always set rewritten_query to user's original text

Question: {question}"""
    )
    print(result.usage())
    return result.output


example_text = """\
List all books.
"""


if __name__ == "__main__":
    response = query(example_text)
    print(repr(response))

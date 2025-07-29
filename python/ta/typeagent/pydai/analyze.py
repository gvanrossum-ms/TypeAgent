import os

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.azure import AzureProvider

from typeagent.aitools.auth import AzureTokenProvider

from kplib import KnowledgeResponse

load_dotenv(".env")


def make_agent() -> Agent[None, KnowledgeResponse]:
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if api_key == "identity":
        token_provider = AzureTokenProvider()
        api_key = token_provider.get_token()

    model = OpenAIModel(
        "gpt-4o",
        provider=AzureProvider(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version="2024-08-01-preview",
            api_key=api_key,
        ),
    )

    return Agent(model, output_type=KnowledgeResponse)


agent = make_agent()


def analyze(question: str) -> KnowledgeResponse:
    result = agent.run_sync(
        f"Analyze the input looking for actions, concrete entities, and topics: {question}",
    )
    print(result.usage())
    return result.output


example_text = """\
ADRIAN TCHAIKOVSKY: So, I studied psychology, and I studied zoology.
And I kind of came out of university yet somewhat disillusioned by both.
The – there were things I – basically, there were things I wanted to learn,
and they were not the things the courses were necessarily teaching.  
 
So, I was very interested in animal behavior.
And there were some really interesting psychology lectures on that,
but very few of them. And at the time,
the – the dominant paradigm for animal behavior
was based on the work of a chap called Skinner.
And it was very much animals are kind of robots, and they didn’t think,
and they don’t have emotions,
which is obviously a very convenient thing to think
if you’re then going to run experiments on them.  
 
And in zoology, I very much wanted to learn about insects and arachnids,
and all the things I was interested in.
And we got precisely one lecture on that, and it was how to kill them,
which was not really what I felt I’d signed up for.  
 
So, I sort of – I came out of out of university with a fairly,
fairly dismal degree, and no real interest in pushing that sort of
academic side of things further.
Whereupon I ended up, through a series of bizarre chances,
with a career in law, mostly because I got a job as a legal secretary,
because my writing had given me a high typing speed.
And it basically comes down to that, something as ridiculous as that,
then just kind of paid the rent for the next 10 years or so until the,
well, 10-15 years or so until the writing finally took off. 
"""


if __name__ == "__main__":
    response = analyze(example_text)
    print(repr(response))

from fastmcp import Client
from google.genai import types
from mcp.shared.context import RequestContext
from fastmcp.client.sampling import SamplingMessage, SamplingParams

import asyncio
from google import genai

google_client = genai.Client(api_key="AIzaSyAf8NARQmskJOPz4QJtGBNZbE1lS3H-CV8")

async def basic_sampling_handler(
    messages: list[SamplingMessage],
    params: SamplingParams,
) -> str:
    conversation = ""
    for message in messages:
        conversation += message.content.text + "\n"

    system_prompt = params.systemPrompt or "You are a helpful assistant."

    response = google_client.models.generate_content(
        model="gemma-3-27b-it",
        contents=system_prompt+"\n"+conversation
    )
    tmp = response.text.replace("```","").replace("json","")
    return tmp


async def my_progress_handler(
    progress: float,
    total: float | None,
    message: str | None
) -> None:
    if total is not None:
        percentage = (progress / total) * 100
        print(f"Progress: {percentage:.1f}% \n - {message or ''} \n")
    else:
        print(f"Progress: {progress} \n - {message or ''} \n")

client = Client(
    "http://127.0.0.1:9000/mcp",
    progress_handler=my_progress_handler,
)

client2 = Client(
    "http://127.0.0.1:9001/mcp",
    sampling_handler=basic_sampling_handler
)


async def call_tool():
    async with client:
        result = await client.call_tool("search")
        print(result)


async def call_tool_2():
    async with client2:
        result = await client2.call_tool("predict",{"news":"news"})
        print(result)

asyncio.run(call_tool_2())
from openai import AsyncOpenAI
from .config import settings

client = AsyncOpenAI(base_url=settings.VLLM_URL, api_key="internal")


async def generate(data):
    response = await client.chat.completions.create(
        model=settings.MODEL,
        messages=data.messages,
        temperature=data.temperature,
        max_tokens=data.max_tokens,
    )

    return {"model": settings.MODEL, "output": response.choices[0].message.content}


async def stream(data):

    result = await client.chat.completions.create(
        model=settings.MODEL, messages=data.messages, stream=True,
        temperature=data.temperature, max_tokens=data.max_tokens
    )

    async for chunk in result:
        token = chunk.choices[0].delta.content

        if token:
            yield token

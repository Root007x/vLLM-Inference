import asyncio
from openai import AsyncOpenAI
from fastapi import HTTPException
from .config import settings

client = AsyncOpenAI(base_url=settings.VLLM_URL, api_key="internal", timeout=120)

_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)


def check_concurrency():
    if _semaphore.locked():
        raise HTTPException(status_code=503, detail="Server busy, try again later")


async def generate(data):
    check_concurrency()

    async with _semaphore:
        response = await client.chat.completions.create(
            model=settings.MODEL,
            messages=data.messages,
            temperature=data.temperature,
            max_tokens=data.max_tokens,
        )

    return {"model": settings.MODEL, "output": response.choices[0].message.content}


async def stream(data):

    async with _semaphore:
        result = await client.chat.completions.create(
            model=settings.MODEL,
            messages=data.messages,
            stream=True,
            temperature=data.temperature,
            max_tokens=data.max_tokens,
        )

        async for chunk in result:
            token = chunk.choices[0].delta.content

            if token:
                yield token

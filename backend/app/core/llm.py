from openai import AsyncOpenAI
from app.core.config import get_settings

settings = get_settings()

client = AsyncOpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url
)

async def call_llm(prompt: str, system_prompt: str = "You are a helpful assistant.", temperature: float = 0.7) -> str:
    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature
    )
    return response.choices[0].message.content
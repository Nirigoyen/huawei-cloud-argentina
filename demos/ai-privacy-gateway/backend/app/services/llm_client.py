import httpx

from app.config import settings


async def call_llm(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {settings.LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.LLM_MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        url = settings.LLM_API_URL.rstrip("/")
        if not url.endswith("/chat/completions"):
            url = f"{url}/chat/completions"

        response = await client.post(
            url,
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

    return data["choices"][0]["message"]["content"]

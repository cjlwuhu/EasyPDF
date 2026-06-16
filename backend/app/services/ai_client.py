import httpx

from app.core.config import settings


class AIClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str | None = None):
        self.api_key = api_key if api_key is not None else settings.api_key
        self.base_url = (base_url if base_url is not None else settings.base_url).rstrip("/")
        self.model = model if model is not None else settings.model_name

    async def complete(self, prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("API key is not configured")
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a precise academic translation assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

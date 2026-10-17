"""OpenAI-compatible Crusoe client. Never log headers, keys, or raw errors."""
import asyncio
import json
import os
import httpx


class InferenceError(RuntimeError):
    def __init__(self, message, status_code=None, retry_after=2):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = min(max(float(retry_after), 1), 30)


class Crusoe:
    def __init__(self):
        self.key = os.getenv("CRUSOE_API_KEY", "")
        self.base = os.getenv("CRUSOE_BASE_URL", "https://api.inference.crusoecloud.com/v1").rstrip("/")
        if self.base != "https://api.inference.crusoecloud.com/v1":
            raise ValueError("Crusoe endpoint must use the approved HTTPS host")
        self.model = os.getenv("CRUSOE_MODEL", "")

    async def models(self) -> list[str]:
        if not self.key:
            raise InferenceError("CRUSOE_API_KEY is not configured")
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(self.base + "/models", headers={"Authorization": "Bearer " + self.key})
        if response.status_code != 200:
            raise InferenceError("Crusoe model discovery HTTP " + str(response.status_code))
        return [x["id"] for x in response.json().get("data", [])]

    async def verify(self) -> dict:
        available = await self.models()
        if not self.model:
            preferred = ("nvidia/Nemotron-3.5-Lightning-30B-A3B", "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B")
            self.model = next((m for m in preferred if m in available),
                              next((m for m in available if "nemotron" in m.lower()), ""))
        if not self.model or self.model not in available:
            raise InferenceError("Select an available Nemotron model with CRUSOE_MODEL")
        for attempt in range(3):
            try:
                result = await self.json("Return a JSON object with connectivity set to ok.",
                                         {"purpose": "connectivity verification"})
                break
            except InferenceError as exc:
                if exc.status_code != 429 or attempt == 2:
                    raise
                await asyncio.sleep(exc.retry_after)
        if result.get("connectivity") != "ok":
            raise InferenceError("Crusoe JSON connectivity response failed validation")
        return {"provider": "Crusoe Managed Inference", "model": self.model, "json_verified": True}

    async def json(self, instruction: str, context: dict) -> dict:
        if not self.key or not self.model:
            raise InferenceError("Crusoe credentials/model not configured; run connectivity verification")
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(self.base + "/chat/completions",
                headers={"Authorization": "Bearer " + self.key},
                json={"model": self.model, "temperature": 0.1, "max_tokens": 4096,
                      "response_format": {"type": "json_object"},
                      "messages": [{"role": "system", "content": instruction},
                                   {"role": "user", "content": json.dumps(context, default=str)}]})
        if response.status_code != 200:
            try:
                delay = float(response.headers.get("retry-after", "15" if response.status_code == 429 else "2"))
            except ValueError:
                delay = 15
            raise InferenceError("Crusoe inference HTTP " + str(response.status_code), response.status_code, delay)
        try:
            content = response.json()["choices"][0]["message"]["content"]
            result = json.loads(content)
            if not isinstance(result, dict):
                raise ValueError()
            return result
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise InferenceError("Invalid structured Crusoe response") from exc

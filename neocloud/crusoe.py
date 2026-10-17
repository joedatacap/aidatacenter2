"""OpenAI-compatible Crusoe client. Never log headers, keys, or raw errors."""
import json
import os
import httpx


class InferenceError(RuntimeError):
    pass


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
            self.model = next((m for m in available if "nemotron" in m.lower()), "")
        if not self.model or self.model not in available:
            raise InferenceError("Select an available Nemotron model with CRUSOE_MODEL")
        result = await self.json("Return a JSON object with connectivity set to ok.",
                                 {"purpose": "connectivity verification"})
        if result.get("connectivity") != "ok":
            raise InferenceError("Crusoe JSON connectivity response failed validation")
        return {"provider": "Crusoe Managed Inference", "model": self.model, "json_verified": True}

    async def json(self, instruction: str, context: dict) -> dict:
        if not self.key or not self.model:
            raise InferenceError("Crusoe credentials/model not configured; run connectivity verification")
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(self.base + "/chat/completions",
                headers={"Authorization": "Bearer " + self.key},
                json={"model": self.model, "temperature": 0.1, "max_tokens": 2200,
                      "response_format": {"type": "json_object"},
                      "messages": [{"role": "system", "content": instruction},
                                   {"role": "user", "content": json.dumps(context, default=str)}]})
        if response.status_code != 200:
            raise InferenceError("Crusoe inference HTTP " + str(response.status_code))
        try:
            content = response.json()["choices"][0]["message"]["content"]
            result = json.loads(content)
            if not isinstance(result, dict):
                raise ValueError()
            return result
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise InferenceError("Invalid structured Crusoe response") from exc

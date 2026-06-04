from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse, urlunparse


class OllamaClient:
    def __init__(self, url: str, model: str, timeout: int = 60, retries: int = 2) -> None:
        self.url = url
        self.model = model
        self.timeout = timeout
        self.retries = retries

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        payload_chat = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }

        payload_generate = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "stream": False,
        }

        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                return self._post_chat(payload_chat)
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code == 404:
                    try:
                        return self._post_generate(payload_generate)
                    except Exception as fallback_exc:  # noqa: BLE001
                        last_error = fallback_exc
                if attempt < self.retries:
                    time.sleep(0.6)
            except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(0.6)

        raise RuntimeError(f"No se pudo obtener respuesta de Ollama: {last_error}")

    def _post_chat(self, payload: dict) -> str:
        request = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            content = response.read().decode("utf-8")
            parsed = json.loads(content)
            return str(parsed["message"]["content"])

    def _post_generate(self, payload: dict) -> str:
        parsed_url = urlparse(self.url)
        generate_path = parsed_url.path.replace("/api/chat", "/api/generate")
        if generate_path == parsed_url.path:
            generate_path = "/api/generate"
        generate_url = urlunparse(parsed_url._replace(path=generate_path))

        request = urllib.request.Request(
            generate_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            content = response.read().decode("utf-8")
            parsed = json.loads(content)
            return str(parsed["response"])

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AISettings:
    enabled: bool = True
    url: str = "http://192.168.1.7:11434/api/chat"
    model: str = "gemma4:e2b"
    timeout: int = 60
    retries: int = 2
    min_confidence_apply: str = "alta"
    max_cases: int = 30

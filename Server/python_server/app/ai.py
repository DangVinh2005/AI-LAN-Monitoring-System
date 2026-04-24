from __future__ import annotations

import json
import os
from typing import Dict, Any

import httpx

from .models import AIAnalyzeInput, AIAnalyzeResult

# Cho phép cấu hình qua biến môi trường để dễ test / deploy
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3")
AI_USE_OLLAMA = os.getenv("AI_USE_OLLAMA", "false").lower() in ("1", "true", "yes")
AI_CPM_BLOCK = int(os.getenv("AI_CPM_BLOCK", "1000"))
AI_CPM_WARN = int(os.getenv("AI_CPM_WARN", "300"))


ANALYZE_PROMPT = (
    "You are an on-prem security and ops assistant. "
    "Given recent client metrics, decide one of allow/warn/block. "
    "Respond ONLY as minified JSON with keys: client_id, status, reason. "
    "Be conservative; use block if connections_per_min is a large spike above normal.\n\n"
    "INPUT:\n{input_json}"
)


def _cheap_rule(payload: AIAnalyzeInput) -> AIAnalyzeResult:
    """Rule rẻ tiền cho môi trường test hoặc fallback khi Ollama lỗi"""
    cpm = float(payload.connections_per_min or 0)
    if cpm >= AI_CPM_BLOCK:
        return AIAnalyzeResult(
            client_id=payload.client_id,
            status="block",
            reason=f"Connections per minute too high ({cpm} >= {AI_CPM_BLOCK})",
        )
    if cpm >= AI_CPM_WARN:
        return AIAnalyzeResult(
            client_id=payload.client_id,
            status="warn",
            reason=f"Connections per minute elevated ({cpm} >= {AI_CPM_WARN})",
        )
    return AIAnalyzeResult(
        client_id=payload.client_id,
        status="allow",
        reason="Traffic within normal range",
    )


def analyze_behavior(payload: AIAnalyzeInput) -> AIAnalyzeResult:
    """
    Phân tích hành vi client (synchronous version for backward compatibility).

    - Nếu AI_USE_OLLAMA=false (mặc định cho môi trường test):
      dùng rule đơn giản dựa vào connections_per_min để ra allow/warn/block.
    - Nếu AI_USE_OLLAMA=true: gọi Ollama với timeout ngắn; khi lỗi thì rơi
      về rule đơn giản để không làm nghẽn request /metrics.
    """
    # Mặc định: ưu tiên rule nhanh, chỉ gọi Ollama khi thật sự bật
    if not AI_USE_OLLAMA:
        return _cheap_rule(payload)

    body = {
        "model": MODEL_NAME,
        "prompt": ANALYZE_PROMPT.format(input_json=payload.model_dump_json()),
        "stream": False,
    }
    try:
        # timeout ngắn hơn cho realtime; nếu fail sẽ fallback rule
        import requests
        res = requests.post(OLLAMA_URL, json=body, timeout=8)
        res.raise_for_status()
        data: Dict[str, Any] = res.json()
        # Ollama returns { response: "..." }
        text = str(data.get("response", "")).strip()
        obj = json.loads(text)
        return AIAnalyzeResult(**obj)
    except Exception:
        # Bất kỳ lỗi nào (network / parse / model) đều rơi về rule đơn giản
        return _cheap_rule(payload)


async def analyze_behavior_async(payload: AIAnalyzeInput) -> AIAnalyzeResult:
    """
    Async version of analyze_behavior - uses httpx for better performance.
    """
    # Mặc định: ưu tiên rule nhanh, chỉ gọi Ollama khi thật sự bật
    if not AI_USE_OLLAMA:
        return _cheap_rule(payload)

    body = {
        "model": MODEL_NAME,
        "prompt": ANALYZE_PROMPT.format(input_json=payload.model_dump_json()),
        "stream": False,
    }
    try:
        # Use async httpx for better performance
        async with httpx.AsyncClient(timeout=httpx.Timeout(8.0, connect=2.0)) as client:
            res = await client.post(OLLAMA_URL, json=body)
            res.raise_for_status()
            data: Dict[str, Any] = res.json()
            # Ollama returns { response: "..." }
            text = str(data.get("response", "")).strip()
            obj = json.loads(text)
            return AIAnalyzeResult(**obj)
    except Exception:
        # Bất kỳ lỗi nào (network / parse / model) đều rơi về rule đơn giản
        return _cheap_rule(payload)


"""Minimal/ OpenAI-compatible mock endpoint to test the chat flow end-to-end.

Multi-turn: 1st call -> wren_query tool call; 2nd -> render_chart; 3rd -> final text.
Non-streaming (the test uses streaming=False on ChatOpenAI).
Run: .venv/bin/uvicorn mock_openai:app --port 5050
"""
from __future__ import annotations

import json
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()


def _tool_call(name: str, args: dict) -> JSONResponse:
    return JSONResponse(
        {
            "id": str(uuid.uuid4()),
            "object": "chat.completion",
            "model": "mock",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {"id": "call_" + uuid.uuid4().hex[:8], "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ],
            "usage": {},
        }
    )


def _text(content: str) -> JSONResponse:
    return JSONResponse(
        {
            "id": str(uuid.uuid4()),
            "object": "chat.completion",
            "model": "mock",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
            "usage": {},
        }
    )


@app.post("/v1/chat/completions")
async def completions(req: Request):
    body = await req.json()
    messages = body.get("messages", [])
    has_tool_result = any(m.get("role") == "tool" for m in messages)
    has_render = any(
        m.get("role") == "assistant"
        and any(tc.get("function", {}).get("name") == "render_chart" for tc in (m.get("tool_calls") or []))
        for m in messages
    )

    if not has_tool_result:
        return _tool_call("wren_query", {"sql": "SELECT status, count(*) AS n FROM orders GROUP BY status", "limit": 10})
    if not has_render:
        spec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "mark": "bar",
            "encoding": {"x": {"field": "status", "type": "nominal"}, "y": {"field": "n", "type": "quantitative"}},
            "data": {"values": [{"status": "completed", "n": 6}, {"status": "cancelled", "n": 1}, {"status": "pending", "n": 1}]},
        }
        return _tool_call("render_chart", {"spec": json.dumps(spec), "title": "Orders by status"})
    return _text("There are 6 completed, 1 cancelled, and 1 pending order. Completed orders dominate.")


@app.post("/v1/embeddings")
async def embeddings(req: Request):
    return JSONResponse({"object": "list", "data": [{"object": "embedding", "index": 0, "embedding": [0.0] * 4}], "model": "mock", "usage": {}})

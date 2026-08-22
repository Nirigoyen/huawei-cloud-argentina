"""End-to-end chat flow test against the mock OpenAI endpoint.

Run: .venv/bin/uvicorn mock_openai:app --port 5050  (in another shell)
then: .venv/bin/python test_chat_flow.py
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

os.environ["WREN_HOME"] = str(Path(__file__).parent / ".wren")

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from wren_langchain import WrenToolkit

from app.agents.chat_agent import EXTRA_PROMPT, render_chart, stream_chat

PROJECT = Path(__file__).parent / "wren_projects" / "verify"


async def main() -> None:
    tk = WrenToolkit.from_project(str(PROJECT), profile="verify")
    model = ChatOpenAI(model="gpt-4o-mini", base_url="http://localhost:5050/v1", api_key="x", streaming=False, temperature=0)
    agent = create_agent(model=model, tools=tk.get_tools() + [render_chart], system_prompt=tk.system_prompt() + "\n\n" + EXTRA_PROMPT)

    seen: dict[str, int] = {}
    async for ev in stream_chat(agent, [HumanMessage(content="How many orders are there by status?")]):
        t = ev.get("type")
        seen[t] = seen.get(t, 0) + 1
        if t == "token":
            print("token:", ev.get("content", ""), end="", flush=True)
        else:
            print(f"\n[{t}]", str(ev.get("content", ""))[:200])

    print("\n\n=== event counts:", seen)
    assert seen.get("data", 0) >= 1, "expected at least one data event"
    assert seen.get("chart", 0) >= 1, "expected at least one chart event"
    assert seen.get("token", 0) >= 1, "expected at least one token event"
    assert seen.get("done", 0) == 1, "expected a done event"
    print("=== CHAT FLOW OK ===")


if __name__ == "__main__":
    asyncio.run(main())

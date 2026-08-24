"""Debug: print all astream_events to see exact event shapes."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

os.environ["WREN_HOME"] = str(Path(__file__).parent / ".wren")

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from wren_langchain import WrenToolkit

from app.agents.chat_agent import EXTRA_PROMPT, render_chart

PROJECT = Path(__file__).parent / "wren_projects" / "verify"


async def main() -> None:
    tk = WrenToolkit.from_project(str(PROJECT), profile="verify")
    model = ChatOpenAI(
        model="gpt-4o-mini",
        base_url="http://localhost:5050/v1",
        api_key="x",
        streaming=False,
        temperature=0,
    )
    agent = create_agent(
        model=model,
        tools=tk.get_tools() + [render_chart],
        system_prompt=tk.system_prompt() + "\n\n" + EXTRA_PROMPT,
    )

    async for ev in agent.astream_events(
        {"messages": [HumanMessage(content="How many orders by status?")]}, version="v2"
    ):
        kind = ev.get("event")
        name = ev.get("name", "")
        data = ev.get("data") or {}
        if kind in (
            "on_tool_start",
            "on_tool_end",
            "on_chat_model_start",
            "on_chat_model_stream",
            "on_chat_model_end",
        ):
            out = data.get("output")
            out_repr = repr(out)[:300] if out is not None else "None"
            print(f"{kind:25s} name={name:20s} data_keys={list(data.keys())} output={out_repr}")


asyncio.run(main())

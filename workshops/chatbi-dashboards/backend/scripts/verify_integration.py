"""Early verification: wren toolkit + ChatOpenAI(base_url) + create_agent integration.

De-risks the core integration before building the app on top.
Run: .venv/bin/python verify_integration.py
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path

# Ensure WREN_HOME points at our per-app profiles dir.
os.environ["WREN_HOME"] = str(Path(__file__).parent / ".wren")

PROJECT = Path(__file__).parent / "wren_projects" / "verify"


def run(cmd: list[str], cwd: Path) -> str:
    print(f"\n$ {' '.join(cmd)}  (cwd={cwd})")
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    print(r.stdout[-2000:] if r.stdout else "(no stdout)")
    if r.returncode != 0:
        print("STDERR:", r.stderr[-2000:])
        raise SystemExit(f"command failed: {' '.join(cmd)}")
    return r.stdout


async def main() -> None:
    # 1. Build the wren project (YAML -> target/mdl.json)
    wren = str(Path(sys.executable).parent / "wren")
    run([wren, "context", "build"], cwd=PROJECT)
    assert (PROJECT / "target" / "mdl.json").exists(), "target/mdl.json not produced"
    print("✓ wren context build -> target/mdl.json")

    # 2. Toolkit
    from wren_langchain import WrenToolkit

    toolkit = WrenToolkit.from_project(str(PROJECT), profile="verify")
    tools = toolkit.get_tools()
    tool_names = [t.name for t in tools]
    print(f"✓ WrenToolkit.from_project, tools: {tool_names}")
    assert "wren_query" in tool_names and "wren_dry_plan" in tool_names

    tools_by_name = {t.name: t for t in tools}

    # 3. wren_list_models
    res = tools_by_name["wren_list_models"].invoke({})
    print(f"✓ wren_list_models -> {str(res)[:300]}")

    # 4. wren_dry_plan (no DB needed)
    res = tools_by_name["wren_dry_plan"].invoke(
        {"sql": "SELECT count(*) AS n FROM orders"}
    )
    print(f"✓ wren_dry_plan -> {str(res)[:400]}")

    # 5. wren_query (hits postgres)
    res = tools_by_name["wren_query"].invoke(
        {"sql": "SELECT status, count(*) AS n FROM orders GROUP BY status", "limit": 10}
    )
    print(f"✓ wren_query -> {str(res)[:500]}")

    # 6. ChatOpenAI(base_url) construction (no real call)
    from langchain_openai import ChatOpenAI

    chat_model = ChatOpenAI(
        model="gpt-4o-mini",
        base_url="http://localhost:8000/v1",  # placeholder; not called here
        api_key="placeholder",
        temperature=0,
    )
    print(f"✓ ChatOpenAI(base_url=...) constructed: {type(chat_model).__name__}")

    # 7. create_agent construction
    try:
        from langchain.agents import create_agent

        agent = create_agent(
            model=chat_model,
            tools=tools,
            system_prompt=toolkit.system_prompt(),
        )
        print(f"✓ langchain.agents.create_agent constructed: {type(agent).__name__}")
    except ImportError as e:
        print(
            f"  langchain.agents.create_agent not available ({e}), trying langgraph..."
        )
        from langgraph.prebuilt import create_react_agent

        agent = create_react_agent(
            model=chat_model, tools=tools, prompt=toolkit.system_prompt()
        )
        print(f"✓ langgraph.create_react_agent constructed: {type(agent).__name__}")

    print("\n=== ALL CHECKS PASSED ===")


if __name__ == "__main__":
    asyncio.run(main())

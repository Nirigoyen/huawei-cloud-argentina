"""Build the Wren + LLM chat agent and stream its events as SSE dicts."""
from __future__ import annotations

import ast
import json
import re
from collections.abc import AsyncIterator
from pathlib import Path
from threading import Lock

from langchain.tools import tool

from app.config import settings
from app.wren.project import get_toolkit

EXTRA_PROMPT = """\
You are a BI assistant in a dashboard-building workshop. Participants ask questions in plain \
language about the connected database.

The semantic models and their columns are listed above in "Available models". Do NOT call \
wren_list_models — the models are already in your context.

For each question:
1. Write SQL against the Wren SEMANTIC models (not raw tables). Call wren_dry_plan to verify \
it expands.
2. Call wren_query to execute and get rows.
3. Answer in clear, concise plain language — surface the key numbers and a short insight.
4. If the results are visualizable, call render_chart with a Vega-Lite spec as a JSON string. \
IMPORTANT: OMIT the "data" field from the spec — the system automatically injects the rows \
from your last wren_query. Specify only mark, encoding, and title. Pick the right mark: \
bar for comparisons, line for trends over time, arc/pie for part-of-whole, point for correlations, \
area for cumulative. Add clear titles and axis labels. If not chartable, skip render_chart.

Always use Wren model names from the Available models section, never raw table names.
"""


@tool
def render_chart(spec: str, title: str = "") -> str:
    """Render a Vega-Lite chart. `spec` is a JSON string of a complete Vega-Lite spec,
    including "data":{"values":[...]} built from the rows returned by wren_query.
    Call this AFTER wren_query, once you have the data."""
    # No-op: the spec is intercepted from the tool call args in the stream.
    return f"Chart '{title}' queued."


_agent_cache: dict[str, object] = {}
_agent_lock = Lock()


def build_agent(project_path: Path, profile: str):
    """Build (and cache) the chat agent for a workshop project."""
    from langchain.agents import create_agent
    from langchain_openai import ChatOpenAI

    key = str(Path(project_path).resolve())
    with _agent_lock:
        if key in _agent_cache:
            return _agent_cache[key]

    chat_model = ChatOpenAI(
        model=settings.openai_model,
        base_url=settings.openai_base_url,
        api_key=settings.openai_api_key,
        temperature=0,
        streaming=settings.openai_streaming,
    )
    toolkit = get_toolkit(project_path, profile)
    tools = toolkit.get_tools() + [render_chart]

    # Embed the model list in the system prompt so the LLM doesn't waste a
    # round-trip calling wren_list_models, and drop the tool from the agent.
    lm_tool = next((t for t in tools if t.name == "wren_list_models"), None)
    models_block = ""
    if lm_tool:
        try:
            r = lm_tool.invoke({})
            models_block = (r.get("content") if isinstance(r, dict) else str(r)) or ""
        except Exception:
            models_block = ""
    tools = [t for t in tools if t.name != "wren_list_models"]

    system_prompt = toolkit.system_prompt()
    if models_block:
        system_prompt += "\n\n## Available models\n\n" + models_block
    system_prompt += "\n\n" + EXTRA_PROMPT
    agent = create_agent(model=chat_model, tools=tools, system_prompt=system_prompt)

    with _agent_lock:
        _agent_cache[key] = agent
    return agent


def invalidate_agent(project_path: Path) -> None:
    key = str(Path(project_path).resolve())
    with _agent_lock:
        _agent_cache.pop(key, None)


async def stream_chat(agent, messages: list) -> AsyncIterator[dict]:
    """Run the agent and yield SSE event dicts.

    Events: {type: thinking|token|sql|data|chart|done|error, ...}

    The agent makes several LLM calls: the ones preceding a tool call are
    *reasoning* (emitted as ``thinking``), and the final call — the one not
    followed by any tool — is the *answer* (emitted as ``token``). We can't
    tell which is which while streaming, so we buffer per LLM run: on
    ``on_tool_start`` the buffered text was reasoning (flush as ``thinking``);
    whatever remains at the end was the answer (flush as ``token``).
    """
    tool_inputs: dict[str, dict] = {}
    llm_buffer: dict[str, list[str]] = {}
    streamed_runs: set[str] = set()
    last_rows: list[dict] | None = None
    try:
        async for ev in agent.astream_events({"messages": messages}, version="v2"):
            kind = ev.get("event")
            name = ev.get("name", "")
            data = ev.get("data") or {}
            run_id = ev.get("run_id", "")

            if kind == "on_tool_start":
                # LLM output that preceded a tool call is reasoning, not the answer.
                for toks in llm_buffer.values():
                    if toks:
                        yield {"type": "thinking", "content": "".join(toks)}
                llm_buffer.clear()
                inp = data.get("input")
                if isinstance(inp, dict):
                    tool_inputs[run_id] = inp

            elif kind == "on_chat_model_stream":
                chunk = data.get("chunk")
                content = getattr(chunk, "content", None) if chunk else None
                if content:
                    streamed_runs.add(run_id)
                    llm_buffer.setdefault(run_id, []).append(content)

            elif kind == "on_chat_model_end":
                # Non-streaming models emit the full content here (no stream chunks).
                if run_id not in streamed_runs:
                    out = data.get("output")
                    content = getattr(out, "content", None) if out else None
                    if content:
                        llm_buffer.setdefault(run_id, []).append(content)

            elif kind == "on_tool_end":
                out = data.get("output")
                # `out` is typically a ToolMessage whose .content is a JSON string
                # of the tool's return envelope; fall back to dict if already parsed.
                payload = None
                if isinstance(out, dict):
                    payload = out
                else:
                    raw = getattr(out, "content", None)
                    if isinstance(raw, str):
                        try:
                            payload = json.loads(raw)
                        except json.JSONDecodeError:
                            # Some ToolMessages stringify the dict via repr()
                            # (Python single-quoted, True/False) instead of
                            # JSON.  Decimal/datetime values render as
                            # function calls (Decimal('...')) which
                            # literal_eval can't parse — strip them to plain
                            # strings first.
                            try:
                                cleaned = re.sub(
                                    r"Decimal\('([^']*)'\)", r"'\1'", raw
                                )
                                payload = ast.literal_eval(cleaned)
                            except (ValueError, SyntaxError):
                                payload = None
                    elif isinstance(raw, dict):
                        payload = raw
                if name == "wren_dry_plan" and isinstance(payload, dict):
                    dialect = (payload.get("data") or {}).get("dialect_sql")
                    if dialect:
                        yield {"type": "sql", "content": dialect}
                elif name == "wren_query" and isinstance(payload, dict):
                    d = payload.get("data") or {}
                    rows = d.get("rows")
                    if isinstance(rows, list) and rows:
                        last_rows = rows
                    yield {
                        "type": "data",
                        "content": {
                            "columns": d.get("columns"),
                            "rows": d.get("rows"),
                            "row_count": d.get("row_count"),
                        },
                    }
                elif name == "render_chart":
                    inp = tool_inputs.get(run_id, {})
                    raw_spec = inp.get("spec")
                    if isinstance(raw_spec, str):
                        try:
                            spec = json.loads(raw_spec)
                        except json.JSONDecodeError:
                            spec = None
                    elif isinstance(raw_spec, dict):
                        spec = raw_spec
                    else:
                        spec = None
                    if spec:
                        # Ensure the spec carries its title so the chart renders it
                        # and the frontend can use it as the dashboard item name.
                        chart_title = inp.get("title", "")
                        if chart_title and not spec.get("title"):
                            spec = {**spec, "title": chart_title}
                        # Inject the last wren_query rows server-side so the
                        # LLM doesn't have to emit them as output tokens.
                        if not spec.get("data") and last_rows:
                            spec = {**spec, "data": {"values": last_rows}}
                        yield {"type": "chart", "content": spec, "title": chart_title}

        # LLM output not followed by any tool call is the final answer.
        for toks in llm_buffer.values():
            if toks:
                yield {"type": "token", "content": "".join(toks)}
        yield {"type": "done"}
    except Exception as e:  # noqa: BLE001
        yield {"type": "error", "content": str(e)}

"""Crush adapter — Charm's TUI coding agent (ex-OpenCode)."""

from adapters.base import BaseAdapter


class Adapter(BaseAdapter):
    name = "crush"
    command_template = 'crush {prompt}'

    def prepare(self, container_id: str, model_config: dict) -> None:
        """Configure Crush with MaaS as OpenAI-compatible provider."""
        api_key = model_config.get("env_vars", {}).get("OPENAI_API_KEY", "")
        self._run_exec(
            container_id,
            f"crush provider add openai-compat "
            "--base-url https://api.modelarts-maas.com/openai/v1 "
            f"--api-key {api_key} || true",
        )

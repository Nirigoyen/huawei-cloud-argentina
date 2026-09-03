"""OpenHands adapter — autonomous coding agent (ex-OpenDevin)."""

from adapters.base import BaseAdapter


class Adapter(BaseAdapter):
    name = "openhands"
    command_template = (
        "python -m openhands.core.headless "
        "--task {prompt} --workspace /workspace "
        "--model openai/{model_id}"
    )

    def prepare(self, container_id: str, model_config: dict) -> None:
        """Write OpenHands config.toml with MaaS LLM settings."""
        api_key = model_config.get("env_vars", {}).get("OPENAI_API_KEY", "")
        model_id = model_config.get("model_id", "")
        config_content = (
            "[core]\n"
            'workspace_base = "/workspace"\n\n'
            "[llm]\n"
            f'model = "openai/{model_id}"\n'
            f'api_key = "{api_key}"\n'
            'base_url = "https://api.modelarts-maas.com/openai/v1"\n'
        )
        self._run_exec(
            container_id,
            f"mkdir -p ~/.openhands && cat > ~/.openhands/config.toml << 'HEREDOC'\n{config_content}HEREDOC",
        )

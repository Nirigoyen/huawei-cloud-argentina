"""Goose adapter — Block's general-purpose AI agent."""

from adapters.base import BaseAdapter


class Adapter(BaseAdapter):
    name = "goose"
    command_template = 'goose session --with-extension developer {prompt}'

    def prepare(self, container_id: str, model_config: dict) -> None:
        """Configure Goose with MaaS provider."""
        api_key = model_config.get("env_vars", {}).get("OPENAI_API_KEY", "")
        model_id = model_config.get("model_id", "")
        config_content = (
            "GOOSE_PROVIDER: openai\n"
            f"GOOSE_MODEL: {model_id}\n"
            f"OPENAI_API_KEY: {api_key}\n"
            "OPENAI_API_BASE: https://api.modelarts-maas.com/openai/v1\n"
        )
        self._run_exec(
            container_id,
            f"mkdir -p ~/.config/goose && cat > ~/.config/goose/config.yaml << 'HEREDOC'\n{config_content}HEREDOC",
        )

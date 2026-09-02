"""DeepSeek Harness (dsh) adapter — plugin-based coding agent."""

from adapters.base import BaseAdapter


class Adapter(BaseAdapter):
    name = "dsh"
    command_template = "dsh exec {prompt}"

    def prepare(self, container_id: str, model_config: dict) -> None:
        """Write dsh settings.yaml with MaaS provider."""
        api_key = model_config.get("env_vars", {}).get("OPENAI_API_KEY", "")
        model_id = model_config.get("model_id", "")
        config_content = (
            "provider:\n"
            "  name: openai\n"
            "  base_url: https://api.modelarts-maas.com/openai/v1\n"
            f"  api_key: {api_key}\n"
            f"model: {model_id}\n"
        )
        self._run_exec(
            container_id,
            f"mkdir -p ~/.dsh && cat > ~/.dsh/settings.yaml << 'HEREDOC'\n{config_content}HEREDOC",
        )

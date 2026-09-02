"""Trae Agent adapter — ByteDance's research coding agent."""

from adapters.base import BaseAdapter


class Adapter(BaseAdapter):
    name = "trae_agent"
    command_template = "trae run --prompt {prompt} --model {model_id}"

    def prepare(self, container_id: str, model_config: dict) -> None:
        """Write Trae config.yaml with MaaS settings."""
        api_key = model_config.get("env_vars", {}).get("OPENAI_API_KEY", "")
        model_id = model_config.get("model_id", "")
        config_content = (
            "provider: openai\n"
            f"model: {model_id}\n"
            "api_base: https://api.modelarts-maas.com/openai/v1\n"
            f"api_key: {api_key}\n"
        )
        self._run_exec(
            container_id,
            f"mkdir -p ~/.trae && cat > ~/.trae/config.yaml << 'HEREDOC'\n{config_content}HEREDOC",
        )

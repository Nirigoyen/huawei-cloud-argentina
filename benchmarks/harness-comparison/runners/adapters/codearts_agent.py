"""CodeArts Agent adapter — Huawei Cloud's native coding agent."""

from adapters.base import BaseAdapter


class Adapter(BaseAdapter):
    name = "codearts_agent"
    command_template = "codearts agent run --prompt {prompt} --model {model_id}"

    def prepare(self, container_id: str, model_config: dict) -> None:
        """Write CodeArts config inside the container."""
        api_key = model_config.get("env_vars", {}).get("HUAWEI_MAAS_API_KEY", "")
        config_content = (
            "endpoint: https://api.modelarts-maas.com/openai/v1\n"
            f"api_key: {api_key}\n"
            "region: cn-east-3\n"
            f"model: {model_config.get('model_id', '')}\n"
        )
        self._run_exec(
            container_id,
            f"mkdir -p ~/.codearts && cat > ~/.codearts/agent.yaml << 'HEREDOC'\n{config_content}HEREDOC",
        )

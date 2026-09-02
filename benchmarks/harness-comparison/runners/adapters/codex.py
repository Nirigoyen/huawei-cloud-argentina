"""Codex CLI adapter — OpenAI's CLI coding agent."""

from adapters.base import BaseAdapter


class Adapter(BaseAdapter):
    name = "codex"
    command_template = "codex exec {prompt}"

    def prepare(self, container_id: str, model_config: dict) -> None:
        """Write Codex config.toml with MaaS provider."""
        api_key = model_config.get("env_vars", {}).get("OPENAI_API_KEY", "")
        model_id = model_config.get("model_id", "")
        config_content = (
            'model_provider = "maas"\n'
            f'model = "{model_id}"\n\n'
            '[model_providers.maas]\n'
            'name = "Huawei MaaS"\n'
            'base_url = "https://api.modelarts-maas.com/openai/v1"\n'
            f'env_key = "OPENAI_API_KEY"\n'
        )
        self._run_exec(
            container_id,
            f"mkdir -p ~/.codex && cat > ~/.codex/config.toml << 'HEREDOC'\n{config_content}HEREDOC",
        )

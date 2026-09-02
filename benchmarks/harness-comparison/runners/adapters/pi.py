"""Pi adapter — earendil-works new-gen CLI coding agent."""

from adapters.base import BaseAdapter


class Adapter(BaseAdapter):
    name = "pi"
    command_template = 'pi {prompt}'

    def prepare(self, container_id: str, model_config: dict) -> None:
        """Configure Pi with MaaS as OpenAI-compatible provider."""
        api_key = model_config.get("env_vars", {}).get("OPENAI_API_KEY", "")
        self._run_exec(
            container_id,
            f"pi provider config --name openai "
            "--base-url https://api.modelarts-maas.com/openai/v1 "
            f"--api-key {api_key} || true",
        )

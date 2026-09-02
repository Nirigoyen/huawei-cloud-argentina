"""SWE-agent adapter — Princeton's software engineering agent."""

from adapters.base import BaseAdapter


class Adapter(BaseAdapter):
    name = "swe_agent"
    command_template = "python -m sweagent.run --instances_config /workspace/.swe_instances.yaml"

    def prepare(self, container_id: str, model_config: dict) -> None:
        """Write SWE-agent instances config and model config."""
        api_key = model_config.get("env_vars", {}).get("OPENAI_API_KEY", "")
        model_id = model_config.get("model_id", "")
        prompt = model_config.get("prompt", "")

        instances_content = (
            "instances:\n"
            f"  - id: task\n"
            f"    text: '{prompt}'\n"
            "    workspace: /workspace\n"
        )
        agent_config = (
            "agent:\n"
            "  model:\n"
            f"    name: openai/{model_id}\n"
            "    api_base: https://api.modelarts-maas.com/openai/v1\n"
            f"    api_key: {api_key}\n"
        )
        self._run_exec(
            container_id,
            f"cat > /workspace/.swe_instances.yaml << 'HEREDOC'\n{instances_content}HEREDOC",
        )
        self._run_exec(
            container_id,
            f"mkdir -p ~/.swe_agent && cat > ~/.swe_agent/config.yaml << 'HEREDOC'\n{agent_config}HEREDOC",
        )

    def build_command(self, prompt: str, model_config: dict) -> str:
        """SWE-agent uses a config file, not inline prompt."""
        model_config = {**model_config, "prompt": prompt}
        return self.command_template

"""Aider adapter — CLI coding assistant that works with git repos."""

from adapters.base import BaseAdapter


class Adapter(BaseAdapter):
    name = "aider"
    command_template = (
        "aider --model openai/{model_id} "
        "--no-auto-commits --yes-always "
        "--encoding utf-8 {prompt}"
    )

    def prepare(self, container_id: str, model_config: dict) -> None:
        """Aider needs a git repo to track changes."""
        self._run_exec(container_id, "git init && git add -A && git commit -m init")

    def extract_output(self, container_id: str) -> list[str]:
        """Aider tracks changes via git."""
        result = self._run_exec(container_id, "git diff --name-only HEAD")
        if result.returncode != 0:
            return []
        return [f.strip() for f in result.stdout.strip().splitlines() if f.strip()]

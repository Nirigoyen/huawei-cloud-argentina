"""Claude Code adapter — Anthropic's CLI coding agent."""

from adapters.base import BaseAdapter


class Adapter(BaseAdapter):
    name = "claude_code"
    command_template = 'claude --print {prompt}'

    def extract_output(self, container_id: str) -> list[str]:
        """Check for files modified since container start."""
        result = self._run_exec(
            container_id,
            "find /workspace -type f -newer /workspace/.benchmark_marker "
            "-not -path '*/.git/*' -not -path '*/__pycache__/*' "
            "| sed 's|/workspace/||' | sort",
        )
        if result.returncode != 0:
            return super().extract_output(container_id)
        return [f.strip() for f in result.stdout.strip().splitlines() if f.strip()]

"""Base adapter class for harness adapters."""

from __future__ import annotations

import logging
import shlex
import subprocess

log = logging.getLogger(__name__)


class BaseAdapter:
    """Base class for all harness adapters.

    Each adapter knows how to invoke a specific AI coding harness inside a
    Docker container and how to extract the files it produced or modified.
    """

    name: str = ""
    command_template: str = ""

    def build_command(self, prompt: str, model_config: dict) -> str:
        """Build the shell command to invoke the harness."""
        return self.command_template.format(
            prompt=shlex.quote(prompt),
            model_id=model_config.get("model_id", ""),
            model=model_config.get("model_id", ""),
            temperature=model_config.get("temperature", 0.7),
            max_tokens=model_config.get("max_tokens", 8192),
            config=model_config.get("config_path", ""),
        )

    def prepare(self, container_id: str, model_config: dict) -> None:
        """Optional setup before invoke. Override in subclasses."""
        pass

    def invoke(self, prompt: str, container_id: str, model_config: dict) -> dict:
        """Run the harness inside the container.

        Returns {stdout, stderr, exit_code, output_files}.
        """
        self.prepare(container_id, model_config)

        cmd = self.build_command(prompt, model_config)
        env_vars = model_config.get("env_vars", {})
        timeout = model_config.get("timeout_seconds", 600)

        docker_cmd = ["docker", "exec", "-w", "/workspace"]
        for k, v in env_vars.items():
            docker_cmd.extend(["-e", f"{k}={v}"])
        docker_cmd.extend([container_id, "bash", "-c", cmd])

        log.info("[%s] running: %s", self.name, cmd)
        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output_files = self.extract_output(container_id)
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "output_files": output_files,
            }
        except subprocess.TimeoutExpired:
            log.warning("[%s] timed out after %ds", self.name, timeout)
            return {
                "stdout": "",
                "stderr": f"Timeout after {timeout}s",
                "exit_code": -1,
                "output_files": [],
            }
        except Exception as e:
            log.error("[%s] invoke failed: %s", self.name, e)
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "output_files": [],
            }

    def extract_output(self, container_id: str) -> list[str]:
        """Extract generated/modified files from the container.

        Default: list all files in /workspace excluding VCS/cache dirs.
        """
        result = self._run_exec(
            container_id,
            "find /workspace -type f "
            "-not -path '*/.git/*' "
            "-not -path '*/__pycache__/*' "
            "-not -path '*/node_modules/*' "
            "-not -name '*.pyc' "
            "| sed 's|/workspace/||' | sort",
        )
        if result.returncode != 0:
            return []
        return [f.strip() for f in result.stdout.strip().splitlines() if f.strip()]

    def _run_exec(
        self, container_id: str, cmd: str, timeout: int = 30
    ) -> subprocess.CompletedProcess:
        """Helper: run a command via docker exec in /workspace."""
        return subprocess.run(
            ["docker", "exec", "-w", "/workspace", container_id, "bash", "-c", cmd],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

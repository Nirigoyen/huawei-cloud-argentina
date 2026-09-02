"""GitHub Copilot CLI adapter."""

from adapters.base import BaseAdapter


class Adapter(BaseAdapter):
    name = "copilot_cli"
    command_template = 'gh copilot suggest {prompt} -t shell'

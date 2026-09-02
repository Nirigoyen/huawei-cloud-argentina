import os

import pytest
import yaml


def test_tasks_main_exists():
    assert os.path.exists("roles/harden/tasks/main.yml")


def test_handlers_main_exists():
    assert os.path.exists("roles/harden/handlers/main.yml")


def test_defaults_main_exists():
    assert os.path.exists("roles/harden/defaults/main.yml")


def test_meta_main_exists():
    assert os.path.exists("roles/harden/meta/main.yml")


def test_tasks_valid_yaml():
    with open("roles/harden/tasks/main.yml") as f:
        tasks = yaml.safe_load(f)
    assert isinstance(tasks, list)
    assert len(tasks) > 0


def test_tasks_update_packages():
    with open("roles/harden/tasks/main.yml") as f:
        content = f.read()
    assert "apt" in content or "yum" in content or "package" in content, \
        "Must update packages"


def test_tasks_firewall():
    with open("roles/harden/tasks/main.yml") as f:
        content = f.read()
    assert "ufw" in content, "Must configure UFW firewall"


def test_tasks_ssh_hardening():
    with open("roles/harden/tasks/main.yml") as f:
        content = f.read()
    assert "PermitRootLogin" in content, "Must disable root SSH login"
    assert "PasswordAuthentication" in content, "Must disable password auth"
    assert "2222" in content, "Must set SSH port to 2222"


def test_tasks_fail2ban():
    with open("roles/harden/tasks/main.yml") as f:
        content = f.read()
    assert "fail2ban" in content, "Must install fail2ban"


def test_tasks_remove_packages():
    with open("roles/harden/tasks/main.yml") as f:
        content = f.read()
    assert "telnet" in content, "Must remove telnet"
    assert "absent" in content, "Must use state absent for removal"


def test_tasks_file_permissions():
    with open("roles/harden/tasks/main.yml") as f:
        content = f.read()
    assert "/etc/shadow" in content, "Must set shadow file permissions"
    assert "/etc/passwd" in content, "Must set passwd file permissions"


def test_handlers_valid():
    with open("roles/harden/handlers/main.yml") as f:
        handlers = yaml.safe_load(f)
    assert isinstance(handlers, list)
    handler_names = [h.get("name", "") for h in handlers]
    assert any("ssh" in n.lower() or "sshd" in n.lower() for n in handler_names), \
        "Must have SSH restart handler"


def test_defaults_valid():
    with open("roles/harden/defaults/main.yml") as f:
        defaults = yaml.safe_load(f)
    assert isinstance(defaults, dict)
    assert "ssh_port" in defaults
    assert defaults["ssh_port"] == 2222
    assert "allowed_ports" in defaults
    assert "fail2ban_maxretry" in defaults


def test_meta_valid():
    with open("roles/harden/meta/main.yml") as f:
        meta = yaml.safe_load(f)
    assert isinstance(meta, dict)
    assert "author" in meta.get("galaxy_info", {}) or "author" in str(meta)

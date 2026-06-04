"""
bedrock_access_check.py
Run this BEFORE the lab to confirm which models your AWS account can invoke.
Usage: python3 bedrock_access_check.py

For each Claude model, automatically tries both:
  anthropic.claude-...   (direct model ID)
  us.anthropic.claude-... (cross-region inference prefix)
and reports which one works so you know exactly what to put in your code.
"""

import boto3, json, sys

REGION = "us-east-1"
client = boto3.client("bedrock-runtime", region_name=REGION)


# ── Test functions ─────────────────────────────────────────────────────────

def _converse_once(model_id: str) -> tuple[bool, str]:
    resp = client.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": "Reply with one word: OK"}]}],
    )
    reply = resp["output"]["message"]["content"][0]["text"].strip()
    return True, f'replied: "{reply}"'


def test_converse(model_id: str) -> tuple[bool, str, str]:
    """
    Returns (ok, detail, working_id).
    For Claude models, tries bare ID first, then us.* prefix if that fails.
    """
    # Try the given ID first
    try:
        ok, detail = _converse_once(model_id)
        return ok, detail, model_id
    except Exception as e1:
        err1 = _classify_error(e1)

    # If it failed and doesn't already have us. prefix, retry with us. prefix
    if not model_id.startswith("us."):
        us_id = "us." + model_id
        try:
            ok, detail = _converse_once(us_id)
            return ok, f'{detail}  [works with us.* prefix: {us_id}]', us_id
        except Exception as e2:
            err2 = _classify_error(e2)
            # Return the more informative of the two errors
            return False, f'bare: {err1} | us.*: {err2}', model_id

    return False, err1, model_id


def test_embed(model_id: str) -> tuple[bool, str, str]:
    try:
        body = json.dumps({"inputText": "Sigma DataTech compliance test"})
        resp = client.invoke_model(modelId=model_id, body=body)
        result = json.loads(resp["body"].read())
        dims = len(result.get("embedding", []))
        return True, f"{dims}-dim vector returned", model_id
    except Exception as e:
        return False, _classify_error(e), model_id


def test_embed_cohere(model_id: str) -> tuple[bool, str, str]:
    try:
        body = json.dumps({
            "texts": ["Sigma DataTech compliance test"],
            "input_type": "search_document",
        })
        resp = client.invoke_model(modelId=model_id, body=body)
        result = json.loads(resp["body"].read())
        dims = len(result.get("embeddings", [[]])[0])
        return True, f"{dims}-dim vector returned", model_id
    except Exception as e:
        return False, _classify_error(e), model_id


def _classify_error(e: Exception) -> str:
    name = type(e).__name__
    msg  = str(e)
    if "AccessDenied" in name or "AccessDenied" in msg:
        return "Access denied — check IAM bedrock:InvokeModel permission"
    if "ResourceNotFound" in name or "ResourceNotFound" in msg:
        return "Model ID not found in this region"
    if "Could not connect" in msg or "EndpointResolution" in msg:
        return "Connection error — check region/network"
    if "throttl" in msg.lower():
        return "Throttled — wait and retry"
    return msg[:120]


# ── Model list ─────────────────────────────────────────────────────────────

MODELS = [
    # Claude — script auto-tries both bare and us.* prefix for each
    {
        "label":    "Claude Sonnet 4.6 (latest)",
        "id":       "anthropic.claude-sonnet-4-6",
        "type":     "converse",
        "critical": False,
    },
    {
        "label":    "Claude Sonnet 4.5",
        "id":       "anthropic.claude-sonnet-4-5-20250929-v1:0",
        "type":     "converse",
        "critical": False,
    },
    {
        "label":    "Claude Haiku 4.5 (recommended for student labs)",
        "id":       "anthropic.claude-haiku-4-5-20251001-v1:0",
        "type":     "converse",
        "critical": False,
    },
    # Nova — Amazon's own models
    {
        "label":    "Nova Pro",
        "id":       "amazon.nova-pro-v1:0",
        "type":     "converse",
        "critical": False,
    },
    {
        "label":    "Nova Lite (known to work on UPI accounts)",
        "id":       "us.amazon.nova-lite-v1:0",
        "type":     "converse",
        "critical": False,
    },
    {
        "label":    "Nova Micro (cheapest fallback)",
        "id":       "us.amazon.nova-micro-v1:0",
        "type":     "converse",
        "critical": False,
    },
    # Embeddings
    {
        "label":    "Titan Embed Text v2 (Day 4 FAISS lab)",
        "id":       "amazon.titan-embed-text-v2:0",
        "type":     "embed",
        "critical": True,
    },
    {
        "label":    "Titan Embed Text v1 (fallback)",
        "id":       "amazon.titan-embed-text-v1:0",
        "type":     "embed",
        "critical": False,
    },
    {
        "label":    "Cohere Embed English v3 (fallback)",
        "id":       "cohere.embed-english-v3",
        "type":     "embed-cohere",
        "critical": False,
    },
]


# ── Run tests ──────────────────────────────────────────────────────────────

print()
print("=" * 70)
print("  Bedrock Access Check — Sigma Intelligence Bootcamp")
print(f"  Region: {REGION}  |  Auto-tries us.* prefix for Claude models")
print("=" * 70)

results = []  # (label, original_id, working_id, critical, ok, detail)

for m in MODELS:
    sys.stdout.write(f"  Testing {m['label']} ... ")
    sys.stdout.flush()

    if m["type"] == "converse":
        ok, detail, working_id = test_converse(m["id"])
    elif m["type"] == "embed":
        ok, detail, working_id = test_embed(m["id"])
    else:
        ok, detail, working_id = test_embed_cohere(m["id"])

    status = "✅ PASS" if ok else "❌ FAIL"
    print(f"{status}  →  {detail}")
    results.append((m["label"], m["id"], working_id, m["critical"], ok, detail))


# ── Summary ────────────────────────────────────────────────────────────────

print()
print("=" * 70)
print("  SUMMARY")
print("=" * 70)

all_critical_ok = all(ok for *_, critical, ok, _ in results if critical)

print()
print("  TEXT GENERATION:")
for label, orig_id, working_id, critical, ok, detail in results:
    if "Embed" not in label and "embed" not in label:
        icon = "✅" if ok else "❌"
        id_note = f"  → use: {working_id}" if ok and working_id != orig_id else ""
        print(f"    {icon}  {label}{id_note}")

print()
print("  EMBEDDINGS:")
for label, orig_id, working_id, critical, ok, detail in results:
    if "Embed" in label or "embed" in label:
        tag  = " [REQUIRED — Day 4 lab]" if critical else ""
        icon = "✅" if ok else "❌"
        print(f"    {icon}  {label}{tag}")

# Working model IDs to copy-paste
working_text = [(label, working_id) for label, _, working_id, _, ok, _ in results
                if ok and "Embed" not in label and "embed" not in label]
if working_text:
    print()
    print("  WORKING MODEL IDs (copy-paste ready for your code):")
    for label, wid in working_text:
        print(f"    {wid:<55}  # {label}")

print()
if all_critical_ok:
    print("  🟢 ALL REQUIRED MODELS ACCESSIBLE — Day 4 lab is ready to run.")
else:
    print("  🔴 REQUIRED EMBEDDING MODEL FAILED — use a fallback:")
    print()

    embed_fallbacks = [(label, wid) for label, _, wid, _, ok, _ in results
                       if ("Embed" in label or "embed" in label) and ok]
    if embed_fallbacks:
        fb_label, fb_id = embed_fallbacks[0]
        print(f"  Bedrock fallback available: {fb_id}")
        print(f"  In indexer.py change model_id to: '{fb_id}'")
    else:
        print("  No Bedrock embedding model accessible. Use a local fallback:")
        print()
        print("  OPTION 1 — Ollama nomic-embed-text (students have Ollama from Day 1):")
        print("    ollama pull nomic-embed-text")
        print("    In indexer.py replace BedrockEmbeddings with:")
        print("      from langchain_community.embeddings import OllamaEmbeddings")
        print("      embeddings = OllamaEmbeddings(model='nomic-embed-text')")
        print()
        print("  OPTION 2 — HuggingFace all-MiniLM-L6-v2 (90 MB, no Ollama needed):")
        print("    pip install sentence-transformers --break-system-packages")
        print("    In indexer.py replace BedrockEmbeddings with:")
        print("      from langchain_community.embeddings import HuggingFaceEmbeddings")
        print("      embeddings = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')")

print()

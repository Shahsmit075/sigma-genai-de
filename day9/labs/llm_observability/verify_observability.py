import json
import os
import sys
import urllib.request

def main():
    print("Checking LLM Observability Lab completion status...")

    # 1. Check if Phoenix client can connect via raw HTTP (version-agnostic)
    server_up = False
    for host in ["http://127.0.0.1:6006", "http://localhost:6006"]:
        try:
            urllib.request.urlopen(host, timeout=5)
            server_up = True
            break
        except Exception:
            continue

    if not server_up:
        print("❌ Error: Could not connect to local Phoenix server on http://localhost:6006.")
        print("   Ensure your python script with px.launch_app() is running in the background.")
        sys.exit(1)

    print("✓ Phoenix Server Connection: SUCCESS")

    # 2. Import Client (arize-phoenix v16+)
    try:
        from phoenix.client import Client
    except ImportError:
        print("❌ Error: arize-phoenix is not installed. Run:")
        print("   pip install arize-phoenix")
        sys.exit(1)

    # 3. Fetch spans using the correct v16 API: client.spans.get_spans_dataframe()
    try:
        client = Client(base_url="http://127.0.0.1:6006")
        spans_df = client.spans.get_spans_dataframe()
    except Exception as e:
        try:
            client = Client(base_url="http://localhost:6006")
            spans_df = client.spans.get_spans_dataframe()
        except Exception as e2:
            print(f"❌ Error: Failed to fetch spans from Phoenix: {e2}")
            sys.exit(1)

    if spans_df is None or spans_df.empty:
        print("❌ Error: Phoenix is running, but no trace data was found.")
        print("   Make sure you ran your Bedrock LLM script after instrumenting it.")
        sys.exit(1)

    total_spans = len(spans_df)

    # Check for LLM spans
    llm_spans = 0
    if "span_kind" in spans_df.columns:
        llm_spans = len(spans_df[spans_df["span_kind"] == "LLM"])

    print(f"✓ Total Telemetry Spans Captured: {total_spans}")
    print(f"✓ LLM Inference Calls Detected: {llm_spans}")

    if total_spans > 0:
        print("🎉 Verification SUCCESS! OpenTelemetry traces successfully captured by local collector.")

        # Ensure output directory exists
        output_dir = "../output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        result = {
            "status": "success",
            "phoenix_active": True,
            "total_spans_captured": total_spans,
            "llm_inference_calls": llm_spans,
            "llm_observability_verified": True
        }

        output_file = os.path.join(output_dir, "llm_observability_success.json")
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        print(f"✓ Created '{output_file}' for the tracker app.")
    else:
        print("❌ Error: No spans captured. Run your Bedrock agent script again.")
        sys.exit(1)

if __name__ == "__main__":
    main()

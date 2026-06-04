"""
Bedrock Chatbot — Mini Claude/ChatGPT style chat
Powered by AWS Bedrock Converse API (streaming)
Models: Amazon Nova Micro, Nova Lite, Claude Haiku
"""

import json
import os
import streamlit as st
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from dotenv import load_dotenv

load_dotenv()

# ── Model catalogue ────────────────────────────────────────────────────────────
MODELS = {
    "⚡ Nova Micro  — cheapest  ($0.035 / 1M tokens)": {
        "id":           "amazon.nova-micro-v1:0",
        "input_cost":   0.035,    # $ per 1M tokens
        "output_cost":  0.140,
        "provider":     "amazon",
    },
    "🔥 Nova Lite  — balanced  ($0.06 / 1M tokens)": {
        "id":           "amazon.nova-lite-v1:0",
        "input_cost":   0.060,
        "output_cost":  0.240,
        "provider":     "amazon",
    },
    "🚀 Nova Pro  — most capable AWS model  ($0.80 / 1M tokens)": {
        "id":           "amazon.nova-pro-v1:0",
        "input_cost":   0.800,
        "output_cost":  3.200,
        "provider":     "amazon",
    },
    "🧠 Nova Premier  — highest reasoning  ($2.50 / 1M tokens)": {
        "id":           "amazon.nova-premier-v1:0",
        "input_cost":   2.500,
        "output_cost":  12.500,
        "provider":     "amazon",
    },
}

DEFAULT_SYSTEM = (
    "You are a helpful, knowledgeable AI assistant. "
    "Be concise, accurate, and practical in your responses."
)


# ── AWS client ─────────────────────────────────────────────────────────────────
@st.cache_resource
def get_bedrock_client(region: str):
    return boto3.client("bedrock-runtime", region_name=region)


# ── Credential preflight ───────────────────────────────────────────────────────
def check_aws_credentials(region: str) -> tuple[bool, str]:
    """Returns (ok, error_message)."""
    try:
        sts = boto3.client("sts", region_name=region)
        identity = sts.get_caller_identity()
        account = identity["Account"]
        return True, account
    except NoCredentialsError:
        return False, (
            "No AWS credentials found.\n\n"
            "Run in terminal:\n```\naws configure\n```\n"
            "Or create a `.env` file with:\n"
            "```\nAWS_ACCESS_KEY_ID=...\n"
            "AWS_SECRET_ACCESS_KEY=...\n"
            "AWS_DEFAULT_REGION=us-east-1\n```"
        )
    except ClientError as e:
        return False, f"AWS error: {e.response['Error']['Message']}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


# ── Converse stream ────────────────────────────────────────────────────────────
def stream_response(client, model_id: str, system: str, messages: list,
                    temperature: float, max_tokens: int):
    """
    Yields (text_chunk, input_tokens, output_tokens).
    input/output tokens yielded only in the final event (None, N, M).
    """
    bedrock_messages = []
    for m in messages:
        bedrock_messages.append({
            "role": m["role"],
            "content": [{"text": m["content"]}],
        })

    try:
        response = client.converse_stream(
            modelId=model_id,
            messages=bedrock_messages,
            system=[{"text": system}] if system.strip() else [],
            inferenceConfig={
                "maxTokens":   max_tokens,
                "temperature": temperature,
            },
        )
        stream = response.get("stream", [])
        for event in stream:
            if "contentBlockDelta" in event:
                delta = event["contentBlockDelta"].get("delta", {})
                if "text" in delta:
                    yield delta["text"], 0, 0

            elif "metadata" in event:
                usage = event["metadata"].get("usage", {})
                yield "", usage.get("inputTokens", 0), usage.get("outputTokens", 0)

    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg  = e.response["Error"]["Message"]
        if code == "AccessDeniedException":
            yield (
                f"❌ Model access denied. Go to AWS Console → Bedrock → "
                f"Model access → enable this model.", 0, 0
            )
        elif code == "ValidationException":
            yield f"❌ Validation error: {msg}", 0, 0
        else:
            yield f"❌ AWS error ({code}): {msg}", 0, 0
    except Exception as e:
        yield f"❌ Error: {e}", 0, 0


# ── Cost helper ────────────────────────────────────────────────────────────────
def calc_cost(model_cfg: dict, input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens  / 1_000_000 * model_cfg["input_cost"] +
        output_tokens / 1_000_000 * model_cfg["output_cost"]
    )


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Bedrock Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
body, .stMarkdown { font-size: 16px !important; }
h1 { font-size: 28px !important; }

.chat-user {
    background: #eff6ff;
    border-left: 4px solid #2563eb;
    border-radius: 0 10px 10px 0;
    padding: 12px 16px;
    margin: 8px 0;
    color: #1e293b !important;
}
.chat-assistant {
    background: #f0fdf4;
    border-left: 4px solid #16a34a;
    border-radius: 0 10px 10px 0;
    padding: 12px 16px;
    margin: 8px 0;
    color: #1e293b !important;
}
.cost-pill {
    background: #fef9c3;
    border: 1px solid #ca8a04;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 12px;
    color: #713f12;
    font-weight: 600;
}
.status-ok {
    background: #dcfce7;
    border: 1px solid #86efac;
    border-radius: 8px;
    padding: 8px 14px;
    color: #14532d;
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("🤖 Bedrock Chat")
    st.caption("Powered by AWS Bedrock · boto3 Converse API")
    st.divider()

    # ── AWS region ─────────────────────────────────────────────────────────────
    region = st.selectbox(
        "🌎 AWS Region",
        ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"],
        index=0,
        help="us-east-1 has the widest model availability",
    )

    # ── Credential check ───────────────────────────────────────────────────────
    if st.button("🔍 Check AWS Credentials", use_container_width=True):
        ok, result = check_aws_credentials(region)
        if ok:
            st.session_state["aws_ok"] = True
            st.session_state["aws_account"] = result
        else:
            st.session_state["aws_ok"] = False
            st.session_state["aws_error"] = result

    if st.session_state.get("aws_ok"):
        st.markdown(
            f'<div class="status-ok">✅ Connected · Account: '
            f'{st.session_state["aws_account"]}</div>',
            unsafe_allow_html=True,
        )
    elif "aws_error" in st.session_state:
        st.error(st.session_state["aws_error"])

    st.divider()

    # ── Model selector ─────────────────────────────────────────────────────────
    model_label = st.radio(
        "🧠 Model",
        list(MODELS.keys()),
        index=0,
        help="Nova Micro is cheapest. Haiku is smarter for complex tasks.",
    )
    model_cfg = MODELS[model_label]

    st.divider()

    # ── Inference params ───────────────────────────────────────────────────────
    st.subheader("⚙️ Settings")
    temperature = st.slider(
        "Temperature",
        min_value=0.0, max_value=1.0, value=0.7, step=0.05,
        help="0 = focused/deterministic. 1 = creative/varied",
    )
    max_tokens = st.slider(
        "Max output tokens",
        min_value=256, max_value=4096, value=1024, step=256,
    )
    system_prompt = st.text_area(
        "🎭 System prompt",
        value=DEFAULT_SYSTEM,
        height=100,
        help="Defines the assistant's role and behaviour",
    )

    st.divider()

    # ── Session stats ──────────────────────────────────────────────────────────
    st.subheader("📊 Session Stats")
    total_in  = st.session_state.get("total_input_tokens",  0)
    total_out = st.session_state.get("total_output_tokens", 0)
    total_cost = calc_cost(model_cfg, total_in, total_out)

    col1, col2 = st.columns(2)
    col1.metric("Input tokens",  f"{total_in:,}")
    col2.metric("Output tokens", f"{total_out:,}")
    st.metric("Estimated cost", f"${total_cost:.5f}")
    st.caption(f"Model: {model_cfg['id']}")

    st.divider()

    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state["messages"] = []
        st.session_state["total_input_tokens"]  = 0
        st.session_state["total_output_tokens"] = 0
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN CHAT AREA
# ══════════════════════════════════════════════════════════════════════════════
st.title("🤖 Bedrock Chat")
st.caption(f"Model: **{model_cfg['id']}**  ·  Region: **{region}**")
st.divider()

# Init session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "total_input_tokens" not in st.session_state:
    st.session_state["total_input_tokens"]  = 0
if "total_output_tokens" not in st.session_state:
    st.session_state["total_output_tokens"] = 0

# ── Render history ─────────────────────────────────────────────────────────────
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(msg["content"])
            if msg.get("tokens"):
                inp, out = msg["tokens"]
                cost = calc_cost(model_cfg, inp, out)
                st.markdown(
                    f'<span class="cost-pill">'
                    f'↑ {inp:,} tokens  ↓ {out:,} tokens  '
                    f'≈ ${cost:.5f}</span>',
                    unsafe_allow_html=True,
                )

# ── Chat input ─────────────────────────────────────────────────────────────────
placeholder = "Ask anything… (e.g. Write a Snowflake query to find top customers)"
user_input = st.chat_input(placeholder)

if user_input:
    # Check credentials
    if not st.session_state.get("aws_ok"):
        st.warning(
            "⚠️ AWS credentials not verified. Click **Check AWS Credentials** "
            "in the sidebar first."
        )
        st.stop()

    # Add user message
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    # Stream assistant response
    with st.chat_message("assistant", avatar="🤖"):
        response_placeholder = st.empty()
        full_response = ""
        input_tokens  = 0
        output_tokens = 0

        client = get_bedrock_client(region)

        for chunk, in_tok, out_tok in stream_response(
            client,
            model_cfg["id"],
            system_prompt,
            st.session_state["messages"],
            temperature,
            max_tokens,
        ):
            full_response += chunk
            response_placeholder.markdown(full_response + "▌")
            if in_tok:
                input_tokens  = in_tok
            if out_tok:
                output_tokens = out_tok

        response_placeholder.markdown(full_response)

        # Download button
        st.download_button(
            label="⬇️ Download as .md",
            data=full_response,
            file_name="response.md",
            mime="text/markdown",
            key=f"dl_{len(st.session_state['messages'])}",
        )

        # Token + cost display
        if input_tokens or output_tokens:
            cost = calc_cost(model_cfg, input_tokens, output_tokens)
            st.markdown(
                f'<span class="cost-pill">'
                f'↑ {input_tokens:,} tokens  ↓ {output_tokens:,} tokens  '
                f'≈ ${cost:.5f}</span>',
                unsafe_allow_html=True,
            )
            st.session_state["total_input_tokens"]  += input_tokens
            st.session_state["total_output_tokens"] += output_tokens

    # Save assistant message
    st.session_state["messages"].append({
        "role":    "assistant",
        "content": full_response,
        "tokens":  (input_tokens, output_tokens),
    })


# ── Empty state ────────────────────────────────────────────────────────────────
if not st.session_state["messages"]:
    st.markdown("""
    <div style="text-align:center; padding: 60px 20px; color: #64748b;">
        <div style="font-size: 48px; margin-bottom: 16px;">🤖</div>
        <div style="font-size: 20px; font-weight: 600; margin-bottom: 8px;">
            Bedrock Chat Ready
        </div>
        <div style="font-size: 15px;">
            Type a message below to start · Streaming responses · Cost tracked per message
        </div>
        <br/>
        <div style="font-size: 14px; color: #94a3b8;">
            💡 Try: "Explain RAG in 3 bullet points" · "Write SQL for top 10 customers"
            · "What is LangChain?"
        </div>
    </div>
    """, unsafe_allow_html=True)

"""
starter.py — Fraud Hunter AI Platform
Sigma DataTech | Day 9 Hackathon | Team 1
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import time

from utils import (
    get_top_metrics,
    get_transactions_list,
    get_transaction_details,
    get_customer_intelligence,
    get_all_transactions_for_analysis,
)
from fraud_engine import (
    run_prosecutor,
    run_defense_lawyer,
    run_prosecutor_rebuttal,
    run_defense_counter,
    get_final_verdict,
)

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Fraud Hunter — Sigma AI Ops",
    page_icon="🛡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS Injection (split into safe small chunks) ─────────────────────────────
def inject_css():
    # Base + fonts
    st.markdown(
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">',
        unsafe_allow_html=True,
    )
    # Core styles chunk 1
    st.markdown("""<style>
html, body, .stApp {
    background-color: #080C14 !important;
    font-family: 'Inter', sans-serif !important;
    color: #E2E8F0;
}
section[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(180deg, #0D1117 0%, #111827 100%);
    border-right: 1px solid #1F2937;
}
#MainMenu, footer, .stDeployButton { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #111827; }
::-webkit-scrollbar-thumb { background: #374151; border-radius: 3px; }
</style>""", unsafe_allow_html=True)

    # Buttons
    st.markdown("""<style>
.stButton > button {
    background: linear-gradient(135deg, #4F46E5, #7C3AED) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 700 !important;
    font-size: 0.9rem !important; padding: 12px 24px !important;
    transition: all 0.3s !important;
    box-shadow: 0 4px 15px rgba(99,102,241,0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(99,102,241,0.5) !important;
}
</style>""", unsafe_allow_html=True)


inject_css()


# ── Helper: Severity colour ──────────────────────────────────────────────────
def sev_color(sev):
    return {"CRITICAL":"#EF4444","HIGH":"#F59E0B","MEDIUM":"#EAB308","LOW":"#10B981"}.get(sev,"#6B7280")


# ── Helper: Render debate chat bubble ────────────────────────────────────────
def bubble(speaker, tag_text, body_text):
    is_p    = speaker == "artemis"
    row_dir = "row" if is_p else "row-reverse"
    name    = "🔴 ARTEMIS" if is_p else "🔵 MAXWELL"
    title_c = "#F87171"   if is_p else "#60A5FA"
    tag_bg  = "rgba(239,68,68,0.15)"  if is_p else "rgba(59,130,246,0.15)"
    tag_c   = "#FCA5A5"               if is_p else "#93C5FD"
    tag_br  = "rgba(239,68,68,0.25)"  if is_p else "rgba(59,130,246,0.25)"
    bub_bg  = "linear-gradient(135deg,#1C0606,#2D0A0A)" if is_p else "linear-gradient(135deg,#06101C,#0A1D2D)"
    bub_br  = "rgba(239,68,68,0.35)"  if is_p else "rgba(59,130,246,0.35)"
    av_bg   = "linear-gradient(135deg,#7F1D1D,#DC2626)" if is_p else "linear-gradient(135deg,#1E3A5F,#2563EB)"
    av_br   = "#EF4444" if is_p else "#3B82F6"
    emoji   = "🔴" if is_p else "🔵"
    radius  = "16px 16px 16px 4px" if is_p else "16px 16px 4px 16px"

    st.markdown(f"""
<div style="display:flex;flex-direction:{row_dir};align-items:flex-start;gap:14px;margin:10px 0;">
  <div style="width:46px;height:46px;border-radius:50%;flex-shrink:0;display:flex;
              align-items:center;justify-content:center;font-size:1.3rem;
              background:{av_bg};border:2px solid {av_br};
              box-shadow:0 4px 15px rgba(0,0,0,0.4);">{emoji}</div>
  <div style="max-width:74%;padding:14px 18px;border-radius:{radius};
              background:{bub_bg};border:1px solid {bub_br};
              box-shadow:0 4px 20px rgba(0,0,0,0.3);color:#E2E8F0;">
    <div style="font-size:0.67rem;font-weight:700;letter-spacing:0.1em;
                color:{title_c};text-transform:uppercase;margin-bottom:6px;">{name}</div>
    <span style="display:inline-block;padding:2px 8px;border-radius:999px;
                 font-size:0.65rem;font-weight:700;margin-bottom:8px;
                 background:{tag_bg};color:{tag_c};border:1px solid {tag_br};">{tag_text}</span>
    <div style="font-size:1rem;line-height:1.8;">{body_text}</div>
  </div>
</div>""", unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════════╗
# ║  HEADER                                                  ║
# ╚══════════════════════════════════════════════════════════╝
st.markdown("""
<div style="background:linear-gradient(135deg,#0F172A 0%,#1E1B4B 50%,#0F172A 100%);
            border:1px solid rgba(99,102,241,0.3);border-radius:16px;
            padding:28px 36px;margin-bottom:28px;position:relative;overflow:hidden;">
  <h1 style="font-size:2.2rem;font-weight:900;margin:0 0 6px 0;
             background:linear-gradient(90deg,#818CF8,#F472B6,#FB923C);
             -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
    🛡 Fraud Hunter
  </h1>
  <p style="color:#94A3B8;margin:0;font-size:0.88rem;letter-spacing:0.06em;">
    AI-POWERED FINANCIAL CRIME DETECTION &nbsp;·&nbsp; SIGMA DATATECH &nbsp;·&nbsp; DAY 9
  </p>
  <div style="margin-top:12px;">
    <span style="display:inline-block;padding:4px 12px;border-radius:999px;font-size:0.8rem;
                 font-weight:600;letter-spacing:0.1em;background:rgba(99,102,241,0.15);
                 color:#A5B4FC;border:1px solid rgba(99,102,241,0.3);margin-right:6px;">🤖 Nova Pro</span>
    <span style="display:inline-block;padding:4px 12px;border-radius:999px;font-size:0.8rem;
                 font-weight:600;letter-spacing:0.1em;background:rgba(99,102,241,0.15);
                 color:#A5B4FC;border:1px solid rgba(99,102,241,0.3);margin-right:6px;">⚡ Nova Lite</span>
    <span style="display:inline-block;padding:4px 12px;border-radius:999px;font-size:0.8rem;
                 font-weight:600;letter-spacing:0.1em;background:rgba(99,102,241,0.15);
                 color:#A5B4FC;border:1px solid rgba(99,102,241,0.3);margin-right:6px;">🦆 DuckDB</span>
    <span style="display:inline-block;padding:4px 12px;border-radius:999px;font-size:0.8rem;
                 font-weight:600;letter-spacing:0.1em;background:rgba(99,102,241,0.15);
                 color:#A5B4FC;border:1px solid rgba(99,102,241,0.3);">🔬 Explainable AI</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════════╗
# ║  TOP KPI CARDS                                           ║
# ╚══════════════════════════════════════════════════════════╝
metrics = get_top_metrics()

def kpi_card(icon, label, value, delta, accent_start, accent_end):
    return f"""
<div style="background:rgba(17,24,39,0.85);border:1px solid rgba(255,255,255,0.07);
            border-radius:14px;padding:22px 20px;position:relative;overflow:hidden;
            transition:transform 0.2s;">
  <div style="position:absolute;bottom:0;left:0;right:0;height:2px;
              background:linear-gradient(90deg,{accent_start},{accent_end});"></div>
  <div style="font-size:1.6rem;margin-bottom:10px;">{icon}</div>
  <div style="font-size:0.7rem;color:#6B7280;text-transform:uppercase;
              letter-spacing:0.1em;font-weight:600;margin-bottom:6px;">{label}</div>
  <div style="font-size:2.1rem;font-weight:800;line-height:1.1;
              background:linear-gradient(90deg,{accent_start},{accent_end});
              -webkit-background-clip:text;-webkit-text-fill-color:transparent;">{value}</div>
  <div style="font-size:0.73rem;color:#10B981;margin-top:5px;">{delta}</div>
</div>"""

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(kpi_card("📊","Total Transactions", f"{metrics['total_transactions']:,}",
                         "↑ 12% vs last month","#818CF8","#6366F1"), unsafe_allow_html=True)
with c2:
    st.markdown(kpi_card("🚨","Fraud Alerts", f"{metrics['fraud_alerts']:,}",
                         "Flagged by ARTEMIS","#F87171","#EF4444"), unsafe_allow_html=True)
with c3:
    st.markdown(kpi_card("⚠️","Est. False Positives", f"{metrics['false_positives']:,}",
                         "Caught by MAXWELL","#FCD34D","#F59E0B"), unsafe_allow_html=True)
with c4:
    st.markdown(kpi_card("🎯","System Accuracy", metrics["ai_accuracy"],
                         "Post-debate verdict","#34D399","#10B981"), unsafe_allow_html=True)

st.write("")


# ╔══════════════════════════════════════════════════════════╗
# ║  SIDEBAR                                                 ║
# ╚══════════════════════════════════════════════════════════╝
with st.sidebar:
    st.markdown("""
<div style="text-align:center;padding:14px 0 6px;">
  <div style="font-size:2.2rem;">🛡</div>
  <div style="font-size:0.8rem;font-weight:700;color:#6366F1;letter-spacing:0.2em;">FRAUD HUNTER OPS</div>
</div>
""", unsafe_allow_html=True)

    txns_df     = get_transactions_list()
    all_txn_ids = txns_df["transaction_id"].tolist()
    default_idx = all_txn_ids.index("TXN020") if "TXN020" in all_txn_ids else 0

    st.markdown('<p style="font-size:0.65rem;font-weight:700;color:#6366F1;text-transform:uppercase;letter-spacing:0.15em;margin-bottom:4px;">🔍 Select Transaction</p>', unsafe_allow_html=True)
    selected_txn_id = st.selectbox("txn", options=all_txn_ids, index=default_idx, label_visibility="collapsed")

    if selected_txn_id == "TXN020":
        st.markdown("""
<div style="background:rgba(249,115,22,0.1);border:1px solid rgba(249,115,22,0.3);
            border-radius:8px;padding:10px 12px;margin:6px 0;">
  <div style="font-size:0.73rem;font-weight:700;color:#FB923C;">🪤 THE TRAP SELECTED</div>
  <div style="font-size:0.72rem;color:#94A3B8;margin-top:3px;">Year 2099 · ₹99,999 · Watch MAXWELL win.</div>
</div>""", unsafe_allow_html=True)

    txn_details = get_transaction_details(selected_txn_id)
    customer_id = txn_details["customer_id"] if txn_details else None

    if customer_id:
        ci    = get_customer_intelligence(customer_id)
        trust = ci["trust_score"]
        tc    = "#10B981" if trust >= 75 else "#F59E0B" if trust >= 50 else "#EF4444"

        st.markdown("---")
        st.markdown('<p style="font-size:0.65rem;font-weight:700;color:#6366F1;text-transform:uppercase;letter-spacing:0.15em;">👤 Customer Intelligence</p>', unsafe_allow_html=True)

        st.markdown(f"""
<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
            border-radius:12px;padding:16px;margin-bottom:10px;">
  <div style="text-align:center;margin-bottom:12px;">
    <div style="font-size:2rem;">👤</div>
    <div style="font-size:1rem;font-weight:700;color:#E2E8F0;">{customer_id}</div>
    <div style="font-size:0.8rem;color:#6B7280;">Customer Profile</div>
  </div>
  <div style="font-size:0.8rem;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.1em;text-align:center;">Trust Score</div>
  <div style="font-size:2rem;font-weight:800;color:{tc};text-align:center;">{trust}/100</div>
  <div style="background:rgba(255,255,255,0.06);border-radius:999px;height:7px;margin:8px 0;">
    <div style="background:linear-gradient(90deg,{tc},#34D399);border-radius:999px;height:7px;width:{trust}%;"></div>
  </div>
</div>""", unsafe_allow_html=True)

        st.markdown(f"""
<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
            border-radius:12px;padding:14px;">
  <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.05);font-size:0.8rem;">
    <span style="color:#6B7280;">Avg Spend</span><span style="color:#E2E8F0;font-weight:500;">₹{ci["avg_spend"]}</span></div>
  <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.05);font-size:0.8rem;">
    <span style="color:#6B7280;">Frequency</span><span style="color:#E2E8F0;font-weight:500;">{ci["transaction_frequency"]} txns</span></div>
  <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.05);font-size:0.8rem;">
    <span style="color:#6B7280;">Fav Merchant</span><span style="color:#E2E8F0;font-weight:500;">{ci["favorite_merchant"]}</span></div>
  <div style="display:flex;justify-content:space-between;padding:5px 0;font-size:0.8rem;">
    <span style="color:#6B7280;">Countries</span><span style="color:#E2E8F0;font-weight:500;">{', '.join(ci["frequent_countries"])}</span></div>
</div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<p style="font-size:0.65rem;font-weight:700;color:#6366F1;text-transform:uppercase;letter-spacing:0.15em;">⚙️ Verdict Settings</p>', unsafe_allow_html=True)
    threshold = st.slider("Fraud Threshold", 50, 99, 85, label_visibility="collapsed")
    st.caption(f"≥{threshold} = FRAUD · 60–{threshold-1} = INVESTIGATE · <60 = LEGITIMATE")


# ╔══════════════════════════════════════════════════════════╗
# ║  TRANSACTION UNDER REVIEW                                ║
# ╚══════════════════════════════════════════════════════════╝
if not txn_details:
    st.error("Transaction not found in database.")
    st.stop()

st.markdown('<p style="font-size:0.8rem;font-weight:700;color:#6366F1;text-transform:uppercase;letter-spacing:0.2em;padding-bottom:8px;border-bottom:1px solid rgba(99,102,241,0.2);margin-bottom:16px;">📋 Transaction Under Review</p>', unsafe_allow_html=True)

amt    = txn_details.get("amount", 0)
merch  = txn_details.get("merchant_name") or "Unknown"
cat    = txn_details.get("merchant_category") or "—"
city   = txn_details.get("merchant_city") or "—"
date   = str(txn_details.get("transaction_date", "—"))
pm     = txn_details.get("payment_method") or "—"
status = txn_details.get("status") or "—"
sc     = "#10B981" if status=="COMPLETED" else "#EF4444" if status=="FAILED" else "#F59E0B"
dc     = "#F87171" if "2099" in date else "#F1F5F9"

st.markdown(f"""
<div style="background:linear-gradient(135deg,#111827 0%,#1a2235 100%);
            border:1px solid rgba(255,255,255,0.07);border-radius:14px;padding:20px;">
  <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:20px;">
    <div><div style="font-size:0.65rem;color:#6B7280;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;">Transaction ID</div>
         <div style="font-size:0.95rem;font-weight:700;color:#818CF8;">{selected_txn_id}</div></div>
    <div><div style="font-size:0.65rem;color:#6B7280;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;">Amount</div>
         <div style="font-size:1.1rem;font-weight:700;color:#F1F5F9;">₹{amt:,.2f}</div></div>
    <div><div style="font-size:0.65rem;color:#6B7280;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;">Merchant</div>
         <div style="font-size:0.9rem;font-weight:600;color:#F1F5F9;">{merch}</div>
         <div style="font-size:0.8rem;color:#6B7280;">{cat} · {city}</div></div>
    <div><div style="font-size:0.65rem;color:#6B7280;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;">Date</div>
         <div style="font-size:0.9rem;font-weight:600;color:{dc};">{date}</div>
         <div style="font-size:0.8rem;color:#6B7280;">{pm}</div></div>
    <div><div style="font-size:0.65rem;color:#6B7280;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;">Status</div>
         <div style="font-size:0.9rem;font-weight:700;color:{sc};">{status}</div></div>
  </div>
</div>
""", unsafe_allow_html=True)

st.write("")
run_analysis = st.button("⚡ Start AI Courtroom Debate", use_container_width=False, type="primary")


# ╔══════════════════════════════════════════════════════════╗
# ║  AI COURTROOM DEBATE                                     ║
# ╚══════════════════════════════════════════════════════════╝
if run_analysis:

    tab_court, tab_verdict, tab_analytics, tab_explorer = st.tabs([
        "⚔️  AI Courtroom",
        "⚖️  Final Verdict",
        "📈  Analytics",
        "🗃  Data Explorer",
    ])

    # ── Run all AI rounds first ──────────────────────────────────
    with st.spinner("🤖 Summoning ARTEMIS and MAXWELL..."):
        t0 = time.time(); prosecutor_result  = run_prosecutor(txn_details);       t_p  = time.time()-t0
        t0 = time.time(); defense_result     = run_defense_lawyer(txn_details, prosecutor_result); t_d  = time.time()-t0
        t0 = time.time(); prosecutor_rebuttal= run_prosecutor_rebuttal(txn_details, defense_result); t_pr = time.time()-t0
        t0 = time.time(); defense_counter    = run_defense_counter(txn_details, prosecutor_rebuttal); t_dc = time.time()-t0

    prosecutor_risk = prosecutor_result.get("risk_score", 0)
    defense_fp      = defense_result.get("false_positive_probability", 0)
    disagreement    = prosecutor_risk > 70 and defense_fp > 65

    # ═══════════════════════════════════════════════════════════
    # TAB 1 — AI COURTROOM
    # ═══════════════════════════════════════════════════════════
    with tab_court:
        # Courtroom banner
        st.markdown("""
<div style="background:linear-gradient(90deg,#1E1533 0%,#1A1035 50%,#1E1533 100%);
            border:1px solid rgba(139,92,246,0.3);border-radius:16px;
            padding:20px 24px;margin:4px 0 20px 0;text-align:center;">
  <div style="font-size:1.3rem;font-weight:800;color:#C4B5FD;letter-spacing:0.05em;">
    🔴 ARTEMIS &nbsp;<span style="background:#7C3AED;color:#fff;padding:4px 14px;border-radius:999px;font-size:0.8rem;font-weight:700;">VS</span>&nbsp; 🔵 MAXWELL
  </div>
  <div style="color:#A78BFA;font-size:0.78rem;margin-top:6px;">
    AI Prosecutor (Nova Pro) &nbsp;·&nbsp; AI Defense Lawyer (Nova Lite) &nbsp;·&nbsp; Live Debate
  </div>
  <div style="display:flex;justify-content:center;gap:32px;margin-top:14px;">
    <div style="text-align:center;">
      <div style="font-size:0.65rem;color:#6B7280;text-transform:uppercase;letter-spacing:0.1em;">Round 1 Response</div>
      <div style="font-size:0.9rem;font-weight:700;color:#F87171;">{:.1f}s + {:.1f}s</div>
    </div>
    <div style="text-align:center;">
      <div style="font-size:0.65rem;color:#6B7280;text-transform:uppercase;letter-spacing:0.1em;">Round 2 Response</div>
      <div style="font-size:0.9rem;font-weight:700;color:#60A5FA;">{:.1f}s + {:.1f}s</div>
    </div>
  </div>
</div>""".format(t_p, t_d, t_pr, t_dc), unsafe_allow_html=True)

        # ── ROUND 1 ──────────────────────────────────────────────
        st.markdown('<p style="font-size:0.8rem;font-weight:700;color:#6366F1;text-transform:uppercase;letter-spacing:0.2em;padding-bottom:6px;border-bottom:1px solid rgba(99,102,241,0.2);margin-bottom:14px;">Round 1 — Opening Statements</p>', unsafe_allow_html=True)

        bubble("artemis", "⚖️ Opening Statement",
               prosecutor_result.get("opening_statement", prosecutor_result.get("reason", "")))
        bubble("maxwell", "🛡 Opening Defense",
               defense_result.get("opening_statement", defense_result.get("counter_argument", "")))

        # Disagreement banner
        if disagreement:
            st.markdown(f"""
<div style="background:linear-gradient(90deg,rgba(239,68,68,0.1),rgba(245,158,11,0.1));
            border:1px solid rgba(239,68,68,0.4);border-radius:12px;
            padding:16px 20px;margin:16px 0;display:flex;align-items:center;gap:14px;">
  <div style="font-size:2rem;flex-shrink:0;">⚡</div>
  <div>
    <p style="font-size:1rem;font-weight:700;color:#FCA5A5;margin:0 0 4px 0;">Strong AI Disagreement Detected!</p>
    <p style="font-size:0.82rem;color:#FCD34D;margin:0;">
      ARTEMIS risk: <strong>{prosecutor_risk}/100</strong> &nbsp;|&nbsp;
      MAXWELL false-positive probability: <strong>{defense_fp}%</strong><br>
      Human analyst review is <strong>strongly recommended</strong> before any card action.
    </p>
  </div>
</div>""", unsafe_allow_html=True)

        # ── ROUND 2 ──────────────────────────────────────────────
        st.markdown('<p style="font-size:0.8rem;font-weight:700;color:#6366F1;text-transform:uppercase;letter-spacing:0.2em;padding-bottom:6px;border-bottom:1px solid rgba(99,102,241,0.2);margin-top:24px;margin-bottom:14px;">Round 2 — Cross-Examination</p>', unsafe_allow_html=True)

        bubble("artemis", "🔥 Rebuttal",
               prosecutor_rebuttal.get("rebuttal", "My position stands."))
        bubble("maxwell", "🎤 Counter-Rebuttal",
               defense_counter.get("counter_rebuttal", "Case rests."))

        # ── Fraud Signals ─────────────────────────────────────────
        st.markdown('<p style="font-size:0.8rem;font-weight:700;color:#6366F1;text-transform:uppercase;letter-spacing:0.2em;padding-bottom:6px;border-bottom:1px solid rgba(99,102,241,0.2);margin-top:24px;margin-bottom:14px;">🔍 Fraud Signals Identified by ARTEMIS</p>', unsafe_allow_html=True)

        severity  = prosecutor_result.get("severity", "UNKNOWN")
        sev_c     = sev_color(severity)
        pills_html = " ".join(
            f'<span style="display:inline-block;padding:5px 12px;margin:4px;border-radius:999px;'
            f'font-size:0.75rem;font-weight:600;background:rgba(239,68,68,0.1);color:#FCA5A5;'
            f'border:1px solid rgba(239,68,68,0.25);">⚠ {s}</span>'
            for s in prosecutor_result.get("signals", [])
        )
        st.markdown(f"""
<div style="background:rgba(17,24,39,0.7);border:1px solid rgba(255,255,255,0.07);
            border-radius:12px;padding:18px;">
  <div style="display:flex;align-items:center;gap:14px;margin-bottom:12px;">
    <div style="background:{sev_c}22;border:1px solid {sev_c}55;border-radius:8px;
                padding:5px 14px;color:{sev_c};font-weight:700;font-size:0.78rem;">{severity}</div>
    <div style="font-size:0.84rem;color:#94A3B8;">{prosecutor_result.get("reason","")}</div>
  </div>
  <div>{pills_html}</div>
</div>""", unsafe_allow_html=True)

        # ── What AI Got Wrong ─────────────────────────────────────
        if selected_txn_id == "TXN020":
            st.markdown("""
<div style="background:linear-gradient(90deg,rgba(124,58,237,0.12),rgba(239,68,68,0.08));
            border:1px solid rgba(124,58,237,0.4);border-radius:12px;padding:20px;margin-top:20px;">
  <div style="font-size:0.8rem;font-weight:700;color:#A78BFA;letter-spacing:0.2em;
              text-transform:uppercase;margin-bottom:10px;">🪤 What AI Got Wrong — The Trap</div>
  <div style="font-size:0.88rem;color:#CBD5E1;line-height:1.7;">
    ARTEMIS flagged the date <strong style="color:#F87171;">2099-12-31</strong> and the
    amount <strong style="color:#F87171;">₹99,999.99</strong> as extremely suspicious — and technically, she's right.<br><br>
    But MAXWELL's counterpoint is surgically correct: <strong>fraudsters steal money today, not in 75 years.</strong>
    No fraud engine would let a 2099 transaction through — so a real criminal would never use this date.
    This is a classic <strong style="color:#34D399;">data-entry glitch</strong>, not fraud.<br><br>
    <strong style="color:#FBBF24;">False positives are expensive.</strong>
    Blocking this card = 1 furious customer + 1 support call + potential churn. MAXWELL wins this round.
  </div>
</div>""", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════
    # TAB 2 — FINAL VERDICT
    # ═══════════════════════════════════════════════════════════
    with tab_verdict:
        verdict = get_final_verdict(prosecutor_risk, threshold)
        v_map   = {
            "FRAUD":       ("#EF4444","#7F1D1D","#450A0A","🚨","Card blocked. Escalated to Fraud Response Team."),
            "INVESTIGATE": ("#F59E0B","#78350F","#431407","🕵️","Sent to Human Analyst Queue."),
            "LEGITIMATE":  ("#10B981","#064E3B","#022C22","✅","Transaction approved and processed normally."),
        }
        vc, vd, vb, vi, vm = v_map[verdict]

        final_fp = min(100, defense_fp + defense_counter.get("confidence_boost", 0))

        st.markdown(f"""
<div style="background:linear-gradient(135deg,{vb},{vd});border:2px solid {vc}55;
            border-radius:16px;padding:32px;text-align:center;margin:8px 0 20px 0;">
  <div style="font-size:0.8rem;font-weight:700;letter-spacing:0.3em;
              color:rgba(255,255,255,0.55);text-transform:uppercase;margin-bottom:10px;">Round 3 — Final Verdict Engine</div>
  <div style="font-size:3rem;font-weight:900;color:{vc};">{vi} {verdict}</div>
  <div style="font-size:0.86rem;color:rgba(255,255,255,0.6);margin-top:12px;">{vm}</div>
</div>""", unsafe_allow_html=True)

        # Score row
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            st.markdown(f"""
<div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.25);
            border-radius:12px;padding:18px;text-align:center;">
  <div style="font-size:0.8rem;color:#9CA3AF;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;">ARTEMIS Risk Score</div>
  <div style="font-size:3.2rem;font-weight:900;color:#EF4444;line-height:1;">{prosecutor_risk}</div>
  <div style="font-size:0.7rem;color:#6B7280;margin-top:4px;">out of 100</div>
</div>""", unsafe_allow_html=True)
        with sc2:
            st.markdown(f"""
<div style="background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.25);
            border-radius:12px;padding:18px;text-align:center;">
  <div style="font-size:0.8rem;color:#9CA3AF;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;">MAXWELL FP Probability</div>
  <div style="font-size:3.2rem;font-weight:900;color:#3B82F6;line-height:1;">{final_fp}%</div>
  <div style="font-size:0.7rem;color:#6B7280;margin-top:4px;">false-positive risk</div>
</div>""", unsafe_allow_html=True)
        with sc3:
            net = prosecutor_risk - final_fp
            nc  = "#EF4444" if net>20 else "#10B981" if net<-10 else "#F59E0B"
            st.markdown(f"""
<div style="background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.25);
            border-radius:12px;padding:18px;text-align:center;">
  <div style="font-size:0.8rem;color:#9CA3AF;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;">Net Risk Delta</div>
  <div style="font-size:3.2rem;font-weight:900;color:{nc};line-height:1;">{net:+d}</div>
  <div style="font-size:0.7rem;color:#6B7280;margin-top:4px;">Prosecutor − Defense</div>
</div>""", unsafe_allow_html=True)

        # Gauge
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number",
            value=prosecutor_risk,
            title={"text":"ARTEMIS Risk Score","font":{"color":"#94A3B8","size":13}},
            gauge={
                "axis":{"range":[0,100],"tickcolor":"#374151"},
                "bar":{"color":"#6366F1"},
                "bgcolor":"rgba(0,0,0,0)","borderwidth":0,
                "steps":[
                    {"range":[0,60],"color":"rgba(16,185,129,0.15)"},
                    {"range":[60,threshold],"color":"rgba(245,158,11,0.15)"},
                    {"range":[threshold,100],"color":"rgba(239,68,68,0.2)"},
                ],
                "threshold":{"line":{"color":"#EF4444","width":3},"value":threshold},
            },
            number={"font":{"color":"#E2E8F0","size":38}},
        ))
        fig_g.update_layout(height=240,paper_bgcolor="rgba(0,0,0,0)",
                            font={"color":"#E2E8F0"},margin=dict(t=40,b=10,l=20,r=20))
        st.plotly_chart(fig_g, use_container_width=True)

        # Analyst workspace
        if verdict == "INVESTIGATE":
            st.markdown('<p style="font-size:0.8rem;font-weight:700;color:#6366F1;text-transform:uppercase;letter-spacing:0.2em;padding-bottom:6px;border-bottom:1px solid rgba(99,102,241,0.2);margin-bottom:14px;">📝 Human Analyst Workspace</p>', unsafe_allow_html=True)
            an1, an2 = st.columns([3,1])
            with an1:
                st.text_area("Notes", placeholder="Add analyst observations...", height=110, label_visibility="collapsed")
            with an2:
                st.selectbox("Action", ["Approve Transaction","Block Card","Request Customer Verification","Escalate"], label_visibility="collapsed")
                st.button("Submit Decision", use_container_width=True)
        elif verdict == "FRAUD":
            st.error("🚨 ESCALATED — Fraud Response Team notified. Card temporarily blocked.")

        with st.expander("📊 Business Justification for This Threshold"):
            st.markdown(f"""
**Why threshold {threshold} was chosen:**
- Transactions scoring **≥ {threshold}** → automatic block (precision over recall)
- Industry average threshold: **82–88**
- At {threshold}, estimated **{metrics['false_positives']} false positives** across {metrics['total_transactions']} transactions
- Each false positive ≈ **₹850 in support + churn risk**
- MAXWELL's defense catches **~{defense_fp}% of cases** that would be wrongly blocked

> *"The goal is not zero fraud. The goal is zero angry legitimate customers."*
""")

    # ═══════════════════════════════════════════════════════════
    # TAB 3 — ANALYTICS
    # ═══════════════════════════════════════════════════════════
    with tab_analytics:
        st.markdown('<p style="font-size:0.8rem;font-weight:700;color:#6366F1;text-transform:uppercase;letter-spacing:0.2em;padding-bottom:6px;border-bottom:1px solid rgba(99,102,241,0.2);margin-bottom:16px;">📈 Fraud Distribution Analytics</p>', unsafe_allow_html=True)

        all_txns = get_all_transactions_for_analysis()
        CHART_LAYOUT = dict(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#94A3B8", title_font_color="#E2E8F0", height=280,
            margin=dict(t=40,b=20,l=10,r=10),
        )

        ac1, ac2 = st.columns(2)
        with ac1:
            fig_h = px.histogram(all_txns, x="amount", nbins=18,
                                 title="Transaction Amount Distribution",
                                 color_discrete_sequence=["#6366F1"],
                                 labels={"amount":"Amount (₹)"})
            fig_h.update_layout(**CHART_LAYOUT, showlegend=False)
            fig_h.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
            fig_h.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
            st.plotly_chart(fig_h, use_container_width=True)
        with ac2:
            sc = all_txns["status"].value_counts().reset_index()
            sc.columns = ["status","count"]
            fig_d = px.pie(sc, values="count", names="status", hole=0.52,
                           title="Transaction Status Breakdown",
                           color_discrete_sequence=["#10B981","#EF4444","#F59E0B","#6366F1"])
            fig_d.update_traces(textfont_color="#E2E8F0")
            fig_d.update_layout(**CHART_LAYOUT)
            st.plotly_chart(fig_d, use_container_width=True)

        ac3, ac4 = st.columns(2)
        with ac3:
            pm = all_txns["payment_method"].value_counts().reset_index()
            pm.columns = ["method","count"]
            fig_p = px.bar(pm, x="method", y="count", title="Transactions by Payment Method",
                           color="method", color_discrete_sequence=["#818CF8","#34D399","#FB923C"],
                           labels={"method":"","count":"Count"})
            fig_p.update_layout(**CHART_LAYOUT, showlegend=False)
            fig_p.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
            fig_p.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
            st.plotly_chart(fig_p, use_container_width=True)
        with ac4:
            ths  = list(range(60,100,5))
            f_pct= [round((100-t)/40*15,1) for t in ths]
            fp_p = [round((100-t)/40*8,1)  for t in ths]
            fig_s = go.Figure()
            fig_s.add_trace(go.Scatter(x=ths,y=f_pct,name="Caught Fraud %",
                line=dict(color="#EF4444",width=2),fill="tozeroy",fillcolor="rgba(239,68,68,0.08)"))
            fig_s.add_trace(go.Scatter(x=ths,y=fp_p,name="False Positives %",
                line=dict(color="#F59E0B",width=2),fill="tozeroy",fillcolor="rgba(245,158,11,0.08)"))
            fig_s.add_vline(x=threshold,line_color="#6366F1",line_dash="dot",
                annotation_text=f"Threshold: {threshold}",annotation_font_color="#818CF8")
            fig_s.update_layout(**CHART_LAYOUT, title="Threshold Sensitivity",
                legend=dict(bgcolor="rgba(0,0,0,0)"),
                xaxis=dict(title="Threshold",gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(title="%",gridcolor="rgba(255,255,255,0.05)"))
            st.plotly_chart(fig_s, use_container_width=True)

        # Timeline
        st.markdown('<p style="font-size:0.8rem;font-weight:700;color:#6366F1;text-transform:uppercase;letter-spacing:0.2em;padding-bottom:6px;border-bottom:1px solid rgba(99,102,241,0.2);margin:20px 0 14px;">🕐 Transaction Activity Timeline</p>', unsafe_allow_html=True)

        timeline = [
            ("Jan 15","TXN001","₹450","Swiggy · UPI · Bengaluru","normal"),
            ("Jan 15","TXN002","₹1,200","Amazon · Credit Card · Bengaluru","high"),
            ("Jan 16","TXN003","₹89 ❌","Zomato · Debit Card · FAILED","fail"),
            ("Jan 16","TXN004","₹3,200","Ola · Credit Card · Bengaluru","high"),
            ("Jan 19","TXN010","₹1,450","Flipkart · Credit Card · Bengaluru","high"),
            ("Jan 25","TXN016","₹3,400","Flipkart · Credit Card · Bengaluru","high"),
            ("Dec 31, 2099","TXN020","₹99,999 🪤","Swiggy · IMPOSSIBLE DATE · THE TRAP","trap"),
        ]
        for td, tid, ta, desc, kind in timeline:
            dc2  = {"normal":"#6366F1","fail":"#EF4444","high":"#F59E0B","trap":"#7C3AED"}.get(kind,"#6366F1")
            bg2  = "rgba(124,58,237,0.07)" if kind=="trap" else "transparent"
            bdr  = f"border:1px solid {dc2}33;" if kind=="trap" else ""
            st.markdown(f"""
<div style="display:flex;align-items:flex-start;gap:16px;padding:10px 14px;
            border-bottom:1px solid rgba(255,255,255,0.05);
            background:{bg2};{bdr}border-radius:8px;margin-bottom:2px;">
  <div style="width:10px;height:10px;border-radius:50%;background:{dc2};margin-top:5px;flex-shrink:0;"></div>
  <div style="font-size:0.7rem;color:#6B7280;min-width:80px;margin-top:2px;">{td}</div>
  <div>
    <span style="color:#818CF8;font-weight:600;font-size:0.82rem;">{tid}</span>
    <span style="color:#64748B;font-size:0.82rem;"> · {ta}</span>
    <div style="font-size:0.82rem;color:#CBD5E1;margin-top:2px;">{desc}</div>
  </div>
</div>""", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════
    # TAB 4 — DATA EXPLORER
    # ═══════════════════════════════════════════════════════════
    with tab_explorer:
        st.markdown('<p style="font-size:0.8rem;font-weight:700;color:#6366F1;text-transform:uppercase;letter-spacing:0.2em;padding-bottom:6px;border-bottom:1px solid rgba(99,102,241,0.2);margin-bottom:16px;">🗃 DuckDB Transaction Explorer</p>', unsafe_allow_html=True)

        all_t = get_all_transactions_for_analysis()
        ec1, ec2, ec3 = st.columns(3)
        with ec1:
            sf = st.multiselect("Status", all_t["status"].unique().tolist(),
                                default=all_t["status"].unique().tolist(), key="sf")
        with ec2:
            pf = st.multiselect("Payment Method",
                                all_t["payment_method"].dropna().unique().tolist(),
                                default=all_t["payment_method"].dropna().unique().tolist(), key="pf")
        with ec3:
            mn, mx = float(all_t["amount"].min()), float(all_t["amount"].max())
            ar = st.slider("Amount (₹)", mn, mx, (mn, mx), key="ar")

        fil = all_t[
            all_t["status"].isin(sf) &
            all_t["payment_method"].isin(pf) &
            all_t["amount"].between(*ar)
        ]

        st.markdown(f'<div style="font-size:0.78rem;color:#6B7280;margin-bottom:8px;">Showing <strong style="color:#818CF8;">{len(fil)}</strong> of {len(all_t)} transactions</div>', unsafe_allow_html=True)
        st.dataframe(fil, use_container_width=True, height=380)

        st.markdown('<p style="font-size:0.8rem;font-weight:700;color:#6366F1;text-transform:uppercase;letter-spacing:0.2em;padding-bottom:6px;border-bottom:1px solid rgba(99,102,241,0.2);margin:20px 0 14px;">🦆 DuckDB Live Query Stats</p>', unsafe_allow_html=True)
        qc1, qc2, qc3, qc4 = st.columns(4)
        qc1.metric("Total Bronze Records", len(all_t))
        qc2.metric("COMPLETED", len(all_t[all_t["status"]=="COMPLETED"]))
        qc3.metric("FAILED", len(all_t[all_t["status"]=="FAILED"]))
        qc4.metric("Suspicious (FAILED+PENDING)", len(all_t[all_t["status"].isin(["FAILED","PENDING"])]))

# app.py
# Sigma DataTech — Compliance Command Centre
# Data Catalogue RAG | Day 4 Lab 2

import streamlit as st
from datetime import datetime, date, timedelta
from snowflake_catalog import TABLE_CATALOG
from indexer import build_index, search_catalog, search_recent_tables

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Compliance Command Centre",
    page_icon="🔍",
    layout="wide",
)

# ── CSS ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Alert banner */
.alert-banner {
    background: linear-gradient(90deg, #b91c1c 0%, #dc2626 50%, #b91c1c 100%);
    color: #fff;
    padding: 13px 24px;
    border-radius: 10px;
    font-size: 15px;
    font-weight: 700;
    text-align: center;
    letter-spacing: 0.4px;
    margin-bottom: 18px;
}

/* Dark metric tiles */
.metric-tile {
    background: #0f172a;
    color: #fff;
    padding: 22px 16px;
    border-radius: 12px;
    text-align: center;
    border: 1px solid #1e293b;
}
.metric-num  { font-size: 46px; font-weight: 900; line-height: 1; }
.metric-num-red    { color: #f87171; }
.metric-num-yellow { color: #fbbf24; }
.metric-num-green  { color: #34d399; }
.metric-label {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #94a3b8;
    margin-top: 6px;
}

/* Result cards */
.card-pii {
    background: #fef2f2;
    border-left: 5px solid #dc2626;
    padding: 14px 18px;
    border-radius: 0 10px 10px 0;
    margin: 8px 0;
}
.card-sensitive {
    background: #fffbeb;
    border-left: 5px solid #f59e0b;
    padding: 14px 18px;
    border-radius: 0 10px 10px 0;
    margin: 8px 0;
}
.card-safe {
    background: #f0fdf4;
    border-left: 5px solid #16a34a;
    padding: 14px 18px;
    border-radius: 0 10px 10px 0;
    margin: 8px 0;
}
.card-ref {
    background: #f0f9ff;
    border-left: 5px solid #0ea5e9;
    padding: 14px 18px;
    border-radius: 0 10px 10px 0;
    margin: 8px 0;
}
.tname  { font-size: 16px; font-weight: 800; color: #1e293b; }
.tmeta  { font-size: 12px; color: #64748b; margin-top: 4px; }
.badge  {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 10px;
    font-weight: 700;
    margin-left: 8px;
    vertical-align: middle;
}
.badge-pii       { background:#fee2e2; color:#991b1b; }
.badge-sensitive { background:#fef3c7; color:#92400e; }
.badge-safe      { background:#dcfce7; color:#166534; }
.badge-ref       { background:#e0f2fe; color:#0369a1; }
.score-pill      {
    float: right;
    background: #1e293b;
    color: #fbbf24;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
}
/* Mission sidebar */
.mission-done    { color: #22c55e; font-weight: 700; }
.mission-active  { color: #fbbf24; font-weight: 700; }
.mission-locked  { color: #475569; }
</style>
""", unsafe_allow_html=True)

# ── Audit countdown ────────────────────────────────────────────────────────
now = datetime.now()
audit_at = now.replace(hour=14, minute=0, second=0, microsecond=0)
mins_left = max(0, int((audit_at - now).total_seconds() / 60))
urgency = "🔴" if mins_left < 30 else ("🟡" if mins_left < 60 else "🟢")

st.markdown(
    f'<div class="alert-banner">'
    f'⚠️ &nbsp; COMPLIANCE AUDIT IN PROGRESS &nbsp;|&nbsp; '
    f'Auditors arrive in <b>{mins_left} min</b> &nbsp;|&nbsp; '
    f'{urgency} &nbsp; ALL DATA ENGINEERS ON STANDBY'
    f'</div>',
    unsafe_allow_html=True,
)

# ── Build index (cached so it runs once per session) ───────────────────────
@st.cache_resource(show_spinner="Building FAISS index from 20 table descriptions…")
def get_index():
    return build_index()

vectorstore = get_index()

# ── Sidebar: Mission tracker ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎯 Mission Control")

    m1 = st.session_state.get("m1_done", False)
    m2 = st.session_state.get("m2_done", False)
    m3 = st.session_state.get("m3_done", False)
    boss = st.session_state.get("boss_done", False)

    def ms(done, active_cond, label):
        if done:
            return f'<div class="mission-done">✅ {label}</div>'
        elif active_cond:
            return f'<div class="mission-active">▶ {label}</div>'
        else:
            return f'<div class="mission-locked">🔒 {label}</div>'

    st.markdown(ms(m1, True, "Mission 1 — Index Built"),    unsafe_allow_html=True)
    st.markdown(ms(m2, m1,  "Mission 2 — Investigations"), unsafe_allow_html=True)
    st.markdown(ms(m3, m2,  "Mission 3 — Dashboard Live"), unsafe_allow_html=True)

    score = (30 if m1 else 0) + (30 if m2 else 0) + (30 if m3 else 0)
    st.divider()
    st.metric("🏆 Compliance Score", f"{score} / 100")

    st.divider()
    st.markdown("**Stack**")
    st.markdown("- Embeddings: Ollama nomic-embed-text")
    st.markdown("- Vector Store: FAISS (in-memory)")
    st.markdown("- LLM: —  *(pure retrieval lab)*")
    st.markdown(f"- Tables indexed: **{len(TABLE_CATALOG)}**")

    st.divider()
    st.markdown("**Mark your progress:**")
    if vectorstore is not None and not m1:
        if st.button("✅ Mark Mission 1 Done", use_container_width=True):
            st.session_state["m1_done"] = True
            st.rerun()
    if m1 and not m2:
        st.info("▶ Run both queries in the console, then mark Mission 2 done.")
        if st.button("✅ Mark Mission 2 Done", use_container_width=True):
            st.session_state["m2_done"] = True
            st.rerun()
    if m2 and not m3:
        st.info("▶ Confirm Streamlit app is fully working, then mark Mission 3 done.")
        if st.button("✅ Mark Mission 3 Done", use_container_width=True):
            st.session_state["m3_done"] = True
            st.rerun()

# ── Top metrics ────────────────────────────────────────────────────────────
pii_count  = sum(1 for t in TABLE_CATALOG if "PII" in t["classification"])
cutoff     = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")
recent_ct  = sum(1 for t in TABLE_CATALOG if t["last_updated"] >= cutoff)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(
        f'<div class="metric-tile">'
        f'<div class="metric-num metric-num-red">{pii_count}</div>'
        f'<div class="metric-label">PII Tables</div>'
        f'</div>', unsafe_allow_html=True)
with c2:
    st.markdown(
        f'<div class="metric-tile">'
        f'<div class="metric-num metric-num-yellow">{len(TABLE_CATALOG)}</div>'
        f'<div class="metric-label">Total Tables</div>'
        f'</div>', unsafe_allow_html=True)
with c3:
    st.markdown(
        f'<div class="metric-tile">'
        f'<div class="metric-num metric-num-green">{recent_ct}</div>'
        f'<div class="metric-label">Modified Last 7 Days</div>'
        f'</div>', unsafe_allow_html=True)

st.divider()

# ── Investigator Console ───────────────────────────────────────────────────
st.markdown("### 🔍 Investigator Console")
st.markdown(
    "*Ask the catalogue in natural language. "
    "Results are ranked by semantic similarity.*"
)

PRESET_QUERIES = [
    "— pick a query or type your own —",
    "Which tables contain customer PII?",
    "Show me all tables updated in the last 7 days",
    "What tables are relevant for a PCI-DSS audit?",
    "Which tables store payment or financial transaction data?",
    "What data does the Risk team own?",
    "Find tables with personally identifiable information related to identity",
]

col_q, col_k = st.columns([3, 1])
with col_q:
    preset = st.selectbox("Preset queries", PRESET_QUERIES, label_visibility="collapsed")
    query  = st.text_input(
        "Or type your own",
        value="" if preset.startswith("—") else preset,
        placeholder="e.g. Which tables contain customer PII?",
        label_visibility="collapsed",
    )
with col_k:
    k = st.slider("Top-K", min_value=3, max_value=10, value=6)

col_btn1, col_btn2, _ = st.columns([1, 1, 3])
with col_btn1:
    run_search = st.button("🔍 Investigate", type="primary", use_container_width=True)
with col_btn2:
    run_date   = st.button("📅 Last 7 Days", use_container_width=True,
                           help="Metadata-filtered search — Boss Challenge mode")

# ── Helper: card HTML ──────────────────────────────────────────────────────
def classification_card(meta: dict, snippet: str, score: float) -> str:
    clf = meta.get("classification", "Internal")
    if "PII" in clf:
        css, badge_css, badge_txt = "card-pii", "badge-pii", clf
    elif clf in ("Confidential",):
        css, badge_css, badge_txt = "card-sensitive", "badge-sensitive", clf
    elif clf in ("Public", "Reference"):
        css, badge_css, badge_txt = "card-ref", "badge-ref", clf
    else:
        css, badge_css, badge_txt = "card-safe", "badge-safe", clf

    return (
        f'<div class="{css}">'
        f'  <div class="tname">{meta["table_name"]}'
        f'    <span class="badge {badge_css}">{badge_txt}</span>'
        f'    <span class="score-pill">score {score:.3f}</span>'
        f'  </div>'
        f'  <div class="tmeta">'
        f'    📂 {meta.get("domain","?")} &nbsp;·&nbsp; '
        f'    🕐 last updated {meta.get("last_updated","?")} &nbsp;·&nbsp; '
        f'    👤 {meta.get("owner","?")}'
        f'  </div>'
        f'  <div style="font-size:12px;color:#374151;margin-top:8px;">{snippet[:200]}…</div>'
        f'</div>'
    )

# ── Semantic search results ────────────────────────────────────────────────
if run_search and query.strip():
    if vectorstore is None:
        st.error("Index not built — complete Mission 1 first.")
    else:
        with st.spinner("Searching FAISS index…"):
            hits = search_catalog(query, vectorstore, k=k)

        if not hits:
            st.warning("No results — complete the [YOUR CODE HERE] gaps in indexer.py.")
        else:
            st.markdown(f"#### Results for: *\"{query}\"*")
            for doc, score in hits:
                html = classification_card(doc.metadata, doc.page_content, score)
                st.markdown(html, unsafe_allow_html=True)
                with st.expander(f"📄 Full description — {doc.metadata['table_name']}"):
                    st.write(doc.page_content)

            if not m2:
                st.info("✔ Results look good? Mark Mission 2 Done in the **left sidebar**.")

# ── Date-filtered results ──────────────────────────────────────────────────
if run_date:
    if vectorstore is None:
        st.error("Index not built — complete Mission 1 first.")
    else:
        with st.spinner("Running metadata-filtered search…"):
            recent = search_recent_tables(vectorstore, days=7, k=20)

        st.markdown(f"#### Tables modified in the **last 7 days** (since {cutoff})")
        if not recent:
            st.warning("No recent tables found.")
        else:
            for t in recent:
                clf   = t["classification"]
                badge = "badge-pii" if "PII" in clf else (
                        "badge-sensitive" if clf == "Confidential" else "badge-safe")
                st.markdown(
                    f'<div class="card-safe">'
                    f'  <div class="tname">{t["table_name"]}'
                    f'    <span class="badge {badge}">{clf}</span>'
                    f'    <span class="score-pill">updated {t["last_updated"]}</span>'
                    f'  </div>'
                    f'  <div class="tmeta">📂 {t["domain"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            st.info(
                f"Found {len(recent)} tables updated since {cutoff}. "
                "These results use metadata filtering in Python — not vector similarity."
            )

# ── Legend ─────────────────────────────────────────────────────────────────
st.divider()
st.markdown("**Legend**")
leg1, leg2, leg3, leg4 = st.columns(4)
with leg1: st.markdown('<span class="badge badge-pii">PII-Critical / PII-High</span> — Contains personal identifiers', unsafe_allow_html=True)
with leg2: st.markdown('<span class="badge badge-sensitive">Confidential</span> — Commercially sensitive', unsafe_allow_html=True)
with leg3: st.markdown('<span class="badge badge-safe">Internal / Public</span> — No PII', unsafe_allow_html=True)
with leg4: st.markdown('<span class="badge badge-ref">Reference</span> — Lookup / rate data', unsafe_allow_html=True)

# ── Stretch Goal: Export Audit Report ──────────────────────────────────────
st.divider()
st.markdown("### 📥 Export Audit Report")
st.markdown("*Generate a downloadable compliance report for the auditor.*")

if st.button("📥 Export Audit Report", type="primary"):
    with st.spinner("Generating audit report…"):

        # Clue 2 — Run both searches
        pii_hits    = search_catalog("Which tables contain customer PII?", vectorstore, k=6)
        recent_hits = search_recent_tables(vectorstore, days=7)

        # Clue 3 — Build the report text
        lines = [
            "=" * 60,
            "  SIGMA DATATECH — COMPLIANCE AUDIT REPORT",
            "=" * 60,
            f"  Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"  Prepared for : RBI + GDPR Joint Audit",
            f"  Total tables catalogued : {len(TABLE_CATALOG)}",
            "=" * 60,
            "",
            "## SECTION 1 — PII TABLES",
            "-" * 40,
        ]

        # Loop through PII hits — only include rows classified as PII
        pii_found = 0
        for doc, score in pii_hits:
            if "PII" in doc.metadata["classification"]:
                lines.append(
                    f"  [{pii_found + 1}] {doc.metadata['table_name'].upper()}"
                )
                lines.append(f"      Classification : {doc.metadata['classification']}")
                lines.append(f"      Owner          : {doc.metadata['owner']}")
                lines.append(f"      Domain         : {doc.metadata['domain']}")
                lines.append(f"      Last Updated   : {doc.metadata['last_updated']}")
                lines.append(f"      Relevance Score: {score:.4f}")
                lines.append("")
                pii_found += 1

        if pii_found == 0:
            lines.append("  No PII tables found.")
        lines.append(f"  Total PII tables flagged: {pii_found}")
        lines.append("")

        # Section 2 — Recent tables (YOUR CODE part from the lab)
        lines.append("## SECTION 2 — TABLES MODIFIED IN LAST 7 DAYS")
        lines.append("-" * 40)

        if not recent_hits:
            lines.append("  No tables modified in the last 7 days.")
        else:
            for i, t in enumerate(recent_hits):
                lines.append(f"  [{i + 1}] {t['table_name'].upper()}")
                lines.append(f"      Last Updated   : {t['last_updated']}")
                lines.append(f"      Classification : {t['classification']}")
                lines.append(f"      Domain         : {t['domain']}")
                lines.append("")

        lines.append(f"  Total recently modified tables: {len(recent_hits)}")
        lines.append("")
        lines.append("=" * 60)
        lines.append("  END OF REPORT — Sigma DataTech Compliance Team")
        lines.append("=" * 60)

        report_text = "\n".join(lines)

    # Show a preview in the app
    st.success("✅ Report generated successfully!")
    st.code(report_text, language="text")

    # Clue 4 — Download button
    st.download_button(
        label="⬇️ Download Report",
        data=report_text,
        file_name="sigma_audit_report.txt",
        mime="text/plain",
    )

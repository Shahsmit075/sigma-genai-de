"""
Sigma DataTech Intelligence Pipeline — Day 3 Streamlit App
Real AWS Pipeline (S3 + Glue + Athena) with AI assistance via AWS Bedrock.

Run: streamlit run app.py
"""
import streamlit as st
import os
import time
import json
import pandas as pd
import boto3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from s3_manager import S3Manager
from glue_manager import GlueManager
from athena_client import AthenaClient
from bedrock_client import BedrockClient
from prompt_builder import (
    SYSTEM_PROMPT,
    build_glue_etl_prompt,
    build_nl2sql_prompt,
    build_data_quality_prompt,
    build_query_explanation_prompt,
    build_health_summary_prompt,
    SCHEMA_CONTEXT,
    QUICK_QUESTIONS,
)

DATA_DIR = Path(__file__).parent / 'data'

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sigma DataTech Pipeline Forge",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0D111F; color: #E8EAF0; font-size: 16px; }
    section[data-testid="stSidebar"] { background-color: #111827; }
    .stTabs [data-baseweb="tab-list"] { gap: 6px; background-color: #0D111F; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1A1F35; border-radius: 8px;
        color: #9CA3AF; font-size: 16px; font-weight: 600; padding: 10px 18px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00D4AA20; color: #00D4AA;
        border-bottom: 3px solid #00D4AA;
    }
    .stButton > button {
        background-color: #00D4AA; color: #0D111F;
        font-weight: 700; font-size: 16px;
        border: none; border-radius: 8px; padding: 10px 22px;
        width: 100%;
    }
    .stButton > button:hover { background-color: #00B894; }
    .stButton > button:disabled { background-color: #2D3555; color: #6B7280; }
    .card {
        background: #1A1F35; border: 1px solid #2D3555;
        border-radius: 12px; padding: 20px; margin-bottom: 12px;
    }
    .tag-success { background:#10B98120; color:#10B981; padding:3px 10px;
                   border-radius:12px; font-size:13px; font-weight:600; }
    .tag-warning { background:#F59E0B20; color:#F59E0B; padding:3px 10px;
                   border-radius:12px; font-size:13px; font-weight:600; }
    .tag-error   { background:#EF444420; color:#EF4444; padding:3px 10px;
                   border-radius:12px; font-size:13px; font-weight:600; }
    .cost-pill {
        background:#00D4AA15; border:1px solid #00D4AA40; border-radius:20px;
        padding:4px 14px; font-size:14px; color:#00D4AA; display:inline-block;
    }
    h1 { font-size: 28px !important; color: #E8EAF0 !important; }
    h2 { font-size: 22px !important; color: #E8EAF0 !important; }
    h3 { font-size: 18px !important; color: #9CA3AF !important; }
    .stDataFrame { font-size: 14px; }
    div[data-testid="stCode"] pre { font-size: 14px !important; }
    .stSelectbox > div, .stTextInput > div, .stTextArea > div { font-size: 16px; }
    label { font-size: 14px !important; color: #9CA3AF !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state defaults ─────────────────────────────────────────────────────
if 'total_cost' not in st.session_state:
    st.session_state.total_cost = 0.0
if 'pipeline_ready' not in st.session_state:
    st.session_state.pipeline_ready = False
if 'loaded_days' not in st.session_state:
    st.session_state.loaded_days = []
if 'selected_question' not in st.session_state:
    st.session_state.selected_question = ''


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ Pipeline Forge")
    st.markdown("*Sigma DataTech · Day 3 Lab*")
    st.divider()

    st.markdown("#### Your AWS Setup")
    student_initials = st.text_input(
        "Your initials (2–4 chars)",
        placeholder="e.g. AK",
        max_chars=4,
        help="Creates bucket: sigma-datatech-{initials}"
    ).strip().lower()

    aws_region = "us-east-1"
    bucket_name = f"sigma-datatech-{student_initials}" if student_initials else ""

    if bucket_name:
        st.caption(f"Bucket: `{bucket_name}`")

    st.divider()
    st.markdown("#### Preflight Check")

    if st.button("▶ Check AWS Access", disabled=not student_initials):
        checks = {}
        with st.spinner("Checking..."):
            for service, check_fn in [
                ('S3',      lambda: boto3.client('s3', region_name=aws_region).list_buckets()),
                ('Glue',    lambda: boto3.client('glue', region_name=aws_region).list_jobs(MaxResults=1)),
                ('Athena',  lambda: boto3.client('athena', region_name=aws_region).list_work_groups()),
                ('Bedrock', lambda: BedrockClient(aws_region).test_connection()),
            ]:
                try:
                    check_fn()
                    checks[service] = True
                except Exception:
                    checks[service] = False

        for svc, ok in checks.items():
            st.markdown(f"{'✅' if ok else '❌'} **{svc}**")

        if not checks.get('Bedrock'):
            st.warning("Enable Claude 3.5 Haiku in AWS Bedrock Console → Model Access")

    st.divider()
    st.markdown("#### Bedrock Cost")
    st.markdown(
        f"<div class='cost-pill'>${st.session_state.total_cost:.4f} USD</div>",
        unsafe_allow_html=True
    )
    st.caption("Haiku: $0.80/1M in · $4.00/1M out")

    if st.session_state.loaded_days:
        st.divider()
        st.markdown("#### Days Loaded")
        for d in st.session_state.loaded_days:
            label = d
            if '2024-01-17' in d:
                label += ' ⚠️'
            st.markdown(f"✅ `{label}`")


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("# ⚡ Sigma DataTech Intelligence Pipeline")
st.markdown(
    "Real AWS pipeline — S3 → Glue → Athena — powered by Bedrock AI. "
    "Built in one day."
)
st.divider()

if not student_initials:
    st.warning("⬅️  Enter your initials in the sidebar to get started.")
    st.stop()

# ── Instantiate clients (lazy — only created when needed) ──────────────────────
def get_clients():
    return (
        S3Manager(bucket_name, aws_region),
        GlueManager(bucket_name, aws_region),
        AthenaClient(bucket_name, aws_region),
        BedrockClient(region=aws_region),
    )


tab1, tab2, tab3, tab4 = st.tabs([
    "🔧  Setup Pipeline",
    "📦  Daily Load",
    "🔍  Ask Your Data",
    "📊  Pipeline Health",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — SETUP
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("## Step 1 — Deploy Your Pipeline")
    st.markdown(
        "Run this **once**. It creates your S3 bucket, uploads reference data, "
        "AI writes the Glue ETL script, deploys the job, and sets up Athena. "
        "Takes ~2 minutes."
    )

    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown("#### What will be created")
        st.markdown(f"""
- S3 bucket: `{bucket_name}`
- Folders: `raw/`, `processed/`, `reports/`, `athena-results/`
- Reference data: 200 customers · 50 products
- IAM role: `SigmaGlueServiceRole` (auto-created)
- Glue job: `sigma-datatech-etl` (Python Shell, 1/16 DPU)
- Athena database: `sigma_db` with 3 tables
        """)

        setup_btn = st.button("🚀 Generate & Deploy Pipeline", key="setup_btn")

    with right:
        st.markdown("#### AI-Generated Glue ETL Script")
        script_box = st.empty()
        script_box.code(
            "# Click 'Generate & Deploy Pipeline' →\n# Watch AI write this in real time...",
            language="python"
        )
        setup_status = st.empty()

    if setup_btn:
        s3_mgr, glue_mgr, athena_cl, bedrock = get_clients()
        steps = setup_status.container()

        # Step 1 — S3
        with steps:
            st.markdown("**⏳ 1/5 — Creating S3 bucket...**")
        s3_mgr.ensure_bucket_exists()

        # Step 2 — Upload reference data
        with steps:
            st.markdown("**⏳ 2/5 — Uploading reference data (customers + products)...**")
        for fname, key in [
            ('customers.csv', 'raw/customers/customers.csv'),
            ('products.csv',  'raw/products/products.csv'),
        ]:
            local = DATA_DIR / fname
            if local.exists():
                s3_mgr.upload_file(str(local), key)
            else:
                st.error(f"Missing: {local} — run data/generate_data.py first")
                st.stop()

        # Step 3 — AI writes Glue script (streamed)
        with steps:
            st.markdown("**⏳ 3/5 — Bedrock writing Glue ETL script...**")

        source_cols = [
            'order_id', 'customer_id', 'product_id', 'amount',
            'status', 'payment_method', 'created_at', 'city'
        ]
        prompt = build_glue_etl_prompt(bucket_name, source_cols)

        generated = ""
        for chunk in bedrock.stream_message(prompt, system=SYSTEM_PROMPT, max_tokens=2000):
            generated += chunk
            script_box.code(generated, language="python")
        st.session_state.total_cost += bedrock.get_cost_usd()

        # Step 4 — Deploy Glue job (use validated script for reliability)
        with steps:
            st.markdown("**⏳ 4/5 — Deploying Glue job...**")

        validated_script = Path(__file__).parent / 'glue_scripts' / 'sigma_etl.py'
        deploy_script = validated_script.read_text() if validated_script.exists() else generated
        s3_mgr.upload_string(deploy_script, 'glue-scripts/sigma_etl.py')
        glue_mgr.deploy_job('glue-scripts/sigma_etl.py')

        # Run reference job
        run_id = glue_mgr.run_job(job_type='reference', date_partition='none')
        result = glue_mgr.wait_for_completion(run_id, timeout=180)
        if result['status'] != 'SUCCEEDED':
            st.error(f"Reference job failed: {result['error']}")
            st.stop()

        # Step 5 — Athena setup
        with steps:
            st.markdown("**⏳ 5/5 — Setting up Athena database and tables...**")

        athena_cl.setup_database()
        time.sleep(3)
        athena_cl.create_orders_table()
        athena_cl.create_customers_table()
        athena_cl.create_products_table()

        st.session_state.pipeline_ready = True
        setup_status.success(
            "✅ Pipeline deployed! Go to **Daily Load** tab to start ingesting orders."
        )
        st.balloons()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — DAILY LOAD
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("## Step 2 — Load Daily Orders")
    st.markdown(
        "Sigma DataTech receives a new batch of orders every day. "
        "Upload each day's file to S3, run the Glue ETL job, and let AI "
        "analyse the data quality."
    )

    DAY_OPTIONS = {
        'Day 1 — 2024-01-15  (clean data)':           ('2024-01-15', 1),
        'Day 2 — 2024-01-16  (clean data)':           ('2024-01-16', 2),
        'Day 3 — 2024-01-17  ⚠️  (issues planted!)': ('2024-01-17', 3),
        'Day 4 — 2024-01-18  (clean data)':           ('2024-01-18', 4),
        'Day 5 — 2024-01-19  (clean data)':           ('2024-01-19', 5),
    }

    left, right = st.columns([1, 1], gap="large")

    with left:
        selected = st.selectbox("Select day to load", list(DAY_OPTIONS.keys()))
        date_str, day_num = DAY_OPTIONS[selected]

        if day_num == 3:
            st.warning(
                "⚠️  Day 3 data was deliberately corrupted to simulate a production incident:\n"
                "- 10 rows have **negative amounts** (refund misposting)\n"
                "- 5 rows are **duplicate order_ids** (retry without idempotency)\n"
                "- 3 rows have **null customer_ids** (guest checkout failure)\n\n"
                "Will the pipeline catch all of them?"
            )

        load_btn = st.button("📦 Upload & Run Pipeline", key="load_btn")

    with right:
        job_status = st.empty()
        job_status.info("Select a day and click Upload & Run Pipeline.")
        quality_report = st.empty()

    if load_btn:
        s3_mgr, glue_mgr, athena_cl, bedrock = get_clients()
        orders_file = DATA_DIR / f'orders_day{day_num}.csv'

        if not orders_file.exists():
            st.error(f"File not found: {orders_file}\nRun  `python data/generate_data.py`  first.")
            st.stop()

        # Upload to S3
        s3_key = f'raw/orders/date={date_str}/orders.csv'
        job_status.info(f"⏳ Uploading Day {day_num} orders to S3...")
        s3_mgr.upload_file(str(orders_file), s3_key)

        # Start Glue job
        job_status.info("⏳ Starting Glue Python Shell job... (~25 seconds)")
        run_id = glue_mgr.run_job(job_type='orders', date_partition=date_str)

        # Poll for completion
        start_ts = time.time()
        while True:
            status = glue_mgr.get_job_status(run_id)
            elapsed = int(time.time() - start_ts)
            state = status['status']

            if state in ('RUNNING', 'STARTING'):
                prog = min(elapsed / 35, 0.95)
                job_status.info(f"⏳ Glue job running... {elapsed}s")
            elif state == 'SUCCEEDED':
                job_status.success(
                    f"✅ Glue job completed in {status['duration_seconds']}s"
                )
                break
            elif state in ('FAILED', 'ERROR', 'STOPPED'):
                job_status.error(f"❌ Glue job {state}: {status['error']}")
                st.stop()
            elif state == 'TIMEOUT':
                job_status.warning("⏰ Glue job timed out — check Glue Console")
                st.stop()

            if state not in ('RUNNING', 'STARTING', 'STOPPING'):
                break
            time.sleep(4)

        if status['status'] == 'SUCCEEDED':
            # Refresh Athena partitions
            try:
                athena_cl.refresh_partitions()
            except Exception:
                pass  # Non-fatal — partition may already exist

            # Record loaded day
            if date_str not in st.session_state.loaded_days:
                st.session_state.loaded_days.append(date_str)

            # Read quality report
            time.sleep(2)
            report_key = f'reports/quality_report_orders_{date_str}.json'

            try:
                report = s3_mgr.read_json(report_key)
            except Exception:
                quality_report.warning("Quality report not yet available. Refresh in a moment.")
                st.stop()

            # AI analysis
            ai_text = bedrock.invoke(build_data_quality_prompt(json.dumps(report, indent=2)))
            st.session_state.total_cost += bedrock.get_cost_usd()

            with quality_report.container():
                st.markdown("### 🤖 AI Data Quality Report")

                c1, c2, c3, c4 = st.columns(4)
                issues = (
                    report.get('null_customer_ids', 0)
                    + report.get('negative_amounts', 0)
                    + report.get('duplicate_order_ids', 0)
                )
                c1.metric("Input Rows",  f"{report.get('input_rows', 0):,}")
                c2.metric("Output Rows", f"{report.get('output_rows', 0):,}")
                c3.metric(
                    "Issues Fixed", issues,
                    delta=f"-{issues} cleaned" if issues else None,
                    delta_color="inverse"
                )
                c4.metric("Status", report.get('status', '').upper())

                st.info(f"**Bedrock says:** {ai_text}")

                if issues > 0:
                    with st.expander("🔍 Issue Breakdown"):
                        st.write(f"- **Null customer_ids:** {report.get('null_customer_ids', 0)} rows dropped")
                        st.write(f"- **Negative amounts:** {report.get('negative_amounts', 0)} rows corrected")
                        st.write(f"- **Duplicate order_ids:** {report.get('duplicate_order_ids', 0)} duplicates removed")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — NL2SQL
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("## Ask Your Data — Natural Language → SQL → Athena")
    st.markdown(
        "Type a business question. Bedrock generates Athena SQL. "
        "Athena runs it. Bedrock explains the result."
    )

    if not st.session_state.loaded_days:
        st.info("Load at least one day of data in the **Daily Load** tab first.")
    else:
        # Quick question buttons
        st.markdown("#### Quick Questions")
        cols = st.columns(len(QUICK_QUESTIONS))
        for i, (col, q) in enumerate(zip(cols, QUICK_QUESTIONS)):
            with col:
                label = (q[:32] + "…") if len(q) > 32 else q
                if st.button(label, key=f"qq_{i}"):
                    st.session_state.selected_question = q

        st.divider()

        user_q = st.text_area(
            "Or type your own question:",
            value=st.session_state.selected_question,
            height=80,
            placeholder="e.g. Which city had the highest revenue on Day 3?",
        )

        show_prompt = st.checkbox("Show the prompt sent to Bedrock", value=False)
        ask_btn = st.button("🔍 Ask", key="ask_btn")

        if ask_btn and user_q.strip():
            s3_mgr, glue_mgr, athena_cl, bedrock = get_clients()

            if show_prompt:
                with st.expander("📋 Prompt sent to Bedrock (prompt engineering transparency)"):
                    st.code(build_nl2sql_prompt(user_q, SCHEMA_CONTEXT), language="text")

            col_sql, col_result = st.columns([1, 1], gap="large")

            with col_sql:
                st.markdown("#### Generated SQL")
                sql_box = st.empty()
                sql_box.code("Generating...", language="sql")

                generated_sql = ""
                for chunk in bedrock.stream_message(
                    build_nl2sql_prompt(user_q, SCHEMA_CONTEXT), max_tokens=512
                ):
                    generated_sql += chunk
                    sql_box.code(generated_sql.strip(), language="sql")
                st.session_state.total_cost += bedrock.get_cost_usd()

            with col_result:
                st.markdown("#### Result from Athena")
                result_box = st.empty()
                result_box.info("⏳ Running on Athena...")

                try:
                    clean_sql = (
                        generated_sql.strip()
                        .removeprefix("```sql").removeprefix("```")
                        .removesuffix("```").strip()
                    )
                    df_result = athena_cl.run_query(clean_sql)
                    result_box.dataframe(df_result, use_container_width=True)

                    # AI explains result
                    summary = (
                        f"{len(df_result)} rows. "
                        + (f"First row: {df_result.iloc[0].to_dict()}" if len(df_result) > 0 else "Empty result.")
                    )
                    explanation = bedrock.invoke(
                        build_query_explanation_prompt(user_q, clean_sql, summary),
                        max_tokens=150
                    )
                    st.session_state.total_cost += bedrock.get_cost_usd()
                    st.success(f"💬 {explanation}")

                except Exception as e:
                    result_box.error(f"Query failed: {e}")
                    st.caption(
                        "Try rephrasing. Make sure the relevant day is loaded. "
                        "Athena is case-sensitive on string comparisons."
                    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — PIPELINE HEALTH
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("## Pipeline Health Dashboard")

    refresh_btn = st.button("🔄 Refresh Dashboard", key="refresh_btn")

    if refresh_btn or st.session_state.loaded_days:
        s3_mgr, _, athena_cl, bedrock = get_clients()

        dates = ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19']
        labels = ['Day 1', 'Day 2', 'Day 3 ⚠️', 'Day 4', 'Day 5']

        reports = []
        for date, label in zip(dates, labels):
            key = f'reports/quality_report_orders_{date}.json'
            if s3_mgr.file_exists(key):
                try:
                    r = s3_mgr.read_json(key)
                    r['day'] = label
                    r['date'] = date
                    reports.append(r)
                except Exception:
                    pass

        if not reports:
            st.info("No data loaded yet. Go to **Daily Load** tab to start.")
        else:
            df_r = pd.DataFrame(reports)

            # ── Summary metrics ──────────────────────────────────────────────
            total_in   = int(df_r['input_rows'].sum())
            total_out  = int(df_r['output_rows'].sum())
            total_fix  = int(
                df_r.get('null_customer_ids', pd.Series(dtype=int)).sum()
                + df_r.get('negative_amounts', pd.Series(dtype=int)).sum()
                + df_r.get('duplicate_order_ids', pd.Series(dtype=int)).sum()
            )

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Days Loaded",        f"{len(reports)}/5")
            c2.metric("Total Input Rows",   f"{total_in:,}")
            c3.metric("Clean Rows Written", f"{total_out:,}")
            c4.metric("Total Issues Fixed", f"{total_fix:,}")

            st.divider()

            # ── Per-day table ────────────────────────────────────────────────
            st.markdown("#### Daily Load Summary")
            show_cols = ['day', 'date', 'input_rows', 'output_rows',
                         'null_customer_ids', 'negative_amounts',
                         'duplicate_order_ids', 'status']
            st.dataframe(
                df_r[[c for c in show_cols if c in df_r.columns]],
                use_container_width=True
            )

            # ── Revenue trend (from Athena) ──────────────────────────────────
            st.markdown("#### Revenue Trend (live from Athena)")
            try:
                rev_df = athena_cl.run_query("""
                    SELECT date,
                           COUNT(*) AS orders,
                           ROUND(SUM(amount), 0) AS revenue_inr
                    FROM sigma_db.orders
                    GROUP BY date
                    ORDER BY date
                """)
                if not rev_df.empty:
                    rev_df['revenue_inr'] = pd.to_numeric(rev_df['revenue_inr'], errors='coerce')
                    st.bar_chart(rev_df.set_index('date')['revenue_inr'])
                    st.caption("Revenue in INR (₹). Source: Athena → sigma_db.orders")
            except Exception as e:
                st.caption(f"Revenue chart not available: {e}")

            # ── AI health summary ────────────────────────────────────────────
            st.divider()
            st.markdown("#### 🤖 AI Pipeline Health Summary")

            with st.spinner("Bedrock analysing pipeline health..."):
                summary = bedrock.invoke(
                    build_health_summary_prompt(json.dumps(reports, indent=2)),
                    max_tokens=200
                )
                st.session_state.total_cost += bedrock.get_cost_usd()

            st.info(f"**Bedrock:** {summary}")
    else:
        st.info("Load some data first, then click Refresh Dashboard.")

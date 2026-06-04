import time
import json
import io
import re
import boto3
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="QuickMart Dashboard | phoenix",
    page_icon="🛒",
    layout="wide"
)

# Color Theme injection (Slate-Emerald Luxury Dark Mode)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    /* Global typography */
    html, body, [class*="css"], .stApp { 
        font-family: 'Plus Jakarta Sans', sans-serif !important; 
        font-size: 16px !important;
        background-color: #080C14 !important;
        color: #E2E8F0 !important;
    }

    /* Heading highlights - Emerald Green */
    h1, h2, h3, h4, h5, h6 { 
        color: #10B981 !important; 
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }

    /* Tab styles */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(17, 24, 39, 0.6);
        padding: 0.5rem;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .stTabs [data-baseweb="tab"] {
        color: #94A3B8;
        font-weight: 500;
        transition: all 0.2s ease;
        padding: 0.6rem 1.2rem;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #10B981;
        background-color: rgba(255, 255, 255, 0.02);
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #10B981 !important;
        background-color: rgba(16, 185, 129, 0.1);
        border-bottom: 2px solid #10B981 !important;
        font-weight: 600;
    }

    /* Metric Layout Card */
    div[data-testid="stMetricLabel"] { 
        color: #94A3B8 !important; 
        font-weight: 600; 
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="stMetricValue"] {
        color: #34D399 !important;
        font-weight: 800 !important;
        font-size: 2.2rem !important;
        letter-spacing: -0.03em;
    }
    div[data-testid="stMetric"] {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        padding: 1.2rem !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    div[data-testid="stMetric"]:hover {
        background: rgba(15, 23, 42, 0.8) !important;
        border-color: rgba(16, 185, 129, 0.3) !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(16, 185, 129, 0.12) !important;
    }

    /* Primary and Accent Button styles */
    .stButton > button {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.6rem !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2) !important;
        transition: all 0.2s ease-in-out, transform 0.1s ease !important;
    }
    .stButton > button:hover { 
        background: linear-gradient(135deg, #34D399 0%, #059669 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.35) !important;
    }
    .stButton > button:active {
        transform: translateY(1px) !important;
    }

    /* Alerts and Warning blocks */
    div.stAlert {
        background-color: rgba(15, 23, 42, 0.6) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-left: 5px solid #10B981 !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        color: #E2E8F0 !important;
    }
    div.stAlert [data-testid="stMarkdownContainer"] p {
        color: #E2E8F0 !important;
    }

    /* Sidebar container styling */
    [data-testid="stSidebar"] { 
        background: linear-gradient(180deg, #090D16 0%, #0F172A 100%) !important; 
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    [data-testid="stSidebar"] h1 { 
        color: #10B981 !important; 
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 1.8rem !important;
        font-weight: 800 !important;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] div, [data-testid="stSidebar"] span { 
        color: #94A3B8 !important; 
    }
    
    /* Code block enhancements */
    div[data-testid="stCodeBlock"] {
        border-radius: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        background-color: #070A10 !important;
    }
    
    /* Custom divider line */
    hr {
        border-color: rgba(255, 255, 255, 0.05) !important;
    }

    /* Selectbox styling */
    div[data-baseweb="select"] {
        background-color: #0F172A !important;
        border-radius: 8px !important;
    }

    /* ── Dark-theme overrides for charts & dataframes ── */
    /* Vega-Lite / Altair chart canvases */
    .vega-embed canvas, .stVegaLiteChart canvas { background: transparent !important; }
    .vega-embed .marks { background: transparent !important; }

    /* st.bar_chart / st.line_chart wrapper */
    div[data-testid="stArrowVegaLiteChart"] > div,
    div[data-testid="stArrowVegaLiteChart"] svg {
        background: transparent !important;
    }

    /* Dataframe / st.dataframe containers */
    div[data-testid="stDataFrame"] > div,
    div[data-testid="stDataFrame"] iframe {
        background-color: rgba(15, 23, 42, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 10px !important;
    }
    /* Glide-data-grid inner canvas (Streamlit dataframe) */
    .stDataFrame canvas { background: #0B1120 !important; }

    /* st.code block inner */
    .stCodeBlock pre, .stCodeBlock code {
        background-color: #070A10 !important;
        color: #A7F3D0 !important;
    }

    /* st.text_input and st.selectbox inputs */
    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea {
        background-color: #0F172A !important;
        color: #E2E8F0 !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="input"] input:focus,
    div[data-baseweb="textarea"] textarea:focus {
        border-color: #10B981 !important;
        box-shadow: 0 0 0 2px rgba(16,185,129,0.2) !important;
    }

    /* Progress bar */
    div[role="progressbar"] > div {
        background: linear-gradient(90deg, #10B981, #34D399) !important;
    }

    /* Spinner text */
    .stSpinner > div { color: #10B981 !important; }
</style>
""", unsafe_allow_html=True)

# Sidebar Design
with st.sidebar:
    st.markdown("# 🟢 **QuickMart**")
    st.markdown("### *AI-Powered Data Pipeline*")
    st.markdown("---")
    st.write("**Region:** India")
    st.write("**Stack:** S3 → Glue → Athena → Bedrock")
    st.write("**Team:** phoenix")
    st.write("**Color:** Emerald & Mint (#10B981)")

# Constants
S3_BUCKET = "sigma-phoenix-bucket-431294761477"
GLUE_JOB = "sigma-phoenix-etl"
ATHENA_DB = "sigma_phoenix_db"
GLUE_ROLE = "SigmaGlueServiceRole"

# Boto3 clients
s3_client = boto3.client('s3', region_name='us-east-1')
glue_client = boto3.client('glue', region_name='us-east-1')
bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')

# Athena Helper Function
def run_athena_query(query, database="default"):
    athena = boto3.client('athena', region_name='us-east-1')
    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': database},
        ResultConfiguration={'OutputLocation': f's3://{S3_BUCKET}/athena-results/'}
    )
    query_execution_id = response['QueryExecutionId']
    
    while True:
        status_resp = athena.get_query_execution(QueryExecutionId=query_execution_id)
        status = status_resp['QueryExecution']['Status']['State']
        if status == 'SUCCEEDED':
            break
        elif status == 'FAILED':
            reason = status_resp['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
            raise RuntimeError(f"Athena query failed: {reason}. Query: {query}")
        elif status == 'CANCELLED':
            raise RuntimeError("Athena query was cancelled.")
        time.sleep(2)
        
    results = athena.get_query_results(QueryExecutionId=query_execution_id)
    
    metadata = results.get("ResultSet", {}).get("ResultSetMetadata", {})
    cols = [c["Label"] for c in metadata.get("ColumnInfo", [])]
    
    all_rows = results.get("ResultSet", {}).get("Rows", [])
    
    # Only skip Rows[0] if it matches column names (SELECT query header row)
    if cols and all_rows:
        first_row_data = [f.get("VarCharValue", "") for f in all_rows[0]["Data"]]
        if first_row_data == cols:
            all_rows = all_rows[1:]
            
    data = [[field.get("VarCharValue", "") for field in row["Data"]] for row in all_rows]
    if cols:
        return pd.DataFrame(data, columns=cols)
    else:
        return pd.DataFrame(data)

# Helper function to format monetary numbers
def format_dataframe_display(df):
    def format_val(val, col_name):
        if pd.isna(val) or val == "":
            return val
        col_lower = col_name.lower()
        if any(term in col_lower for term in ['amount', 'revenue', 'total_sales', 'avg_basket', 'price', 'total_revenue']):
            try:
                # Strip symbols and commas
                clean_val = str(val).replace('₹', '').replace(',', '').strip()
                if not clean_val:
                    return val
                return f"₹{int(round(float(clean_val))):,}"
            except Exception:
                return val
        return val

    formatted_df = df.copy()
    for col in formatted_df.columns:
        formatted_df[col] = formatted_df[col].apply(lambda x: format_val(x, col))
    return formatted_df

# Streamlit Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔧 Setup Pipeline", 
    "📦 Daily Load", 
    "🔍 Ask Your Data", 
    "📊 Pipeline Health", 
    "🛒 Store Intelligence"
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — 🔧 Setup Pipeline
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("## QuickMart — Pipeline Setup")
    if st.button("🚀 Deploy Pipeline", key="deploy_pipeline_btn"):
        status_placeholders = [st.empty() for _ in range(8)]
        
        # 1. Create S3 bucket if not exists
        try:
            try:
                s3_client.head_bucket(Bucket=S3_BUCKET)
            except Exception:
                s3_client.create_bucket(Bucket=S3_BUCKET)
            status_placeholders[0].success("✅ S3 bucket ready")
        except Exception as e:
            status_placeholders[0].error(f"❌ Create S3 bucket failed: {str(e)}")
            st.stop()
            
        # 2. Upload glue_scripts/etl.py
        try:
            with open('glue_scripts/etl.py', 'rb') as f:
                s3_client.put_object(Bucket=S3_BUCKET, Key='glue-scripts/etl.py', Body=f)
            status_placeholders[1].success("✅ Uploaded etl.py to S3")
        except Exception as e:
            status_placeholders[1].error(f"❌ Upload etl.py failed: {str(e)}")
            st.stop()
            
        # 3. Upload reference data
        try:
            with open('new_data/customers.csv', 'rb') as f:
                cust_data = f.read()
            s3_client.put_object(Bucket=S3_BUCKET, Key='raw/customers.csv', Body=cust_data)
            s3_client.put_object(Bucket=S3_BUCKET, Key='processed/customers/customers.csv', Body=cust_data)
            
            with open('new_data/products.csv', 'rb') as f:
                prod_data = f.read()
            s3_client.put_object(Bucket=S3_BUCKET, Key='raw/products.csv', Body=prod_data)
            s3_client.put_object(Bucket=S3_BUCKET, Key='processed/products/products.csv', Body=prod_data)
            status_placeholders[2].success("✅ Uploaded reference data to raw/ and processed/")
        except Exception as e:
            status_placeholders[2].error(f"❌ Upload reference data failed: {str(e)}")
            st.stop()
            
        # 4. Create Glue job
        try:
            try:
                glue_client.delete_job(JobName=GLUE_JOB)
            except Exception:
                pass
            glue_client.create_job(
                Name=GLUE_JOB,
                Role=GLUE_ROLE,
                Command={
                    "Name": "pythonshell",
                    "ScriptLocation": f"s3://{S3_BUCKET}/glue-scripts/etl.py",
                    "PythonVersion": "3"
                },
                GlueVersion="1.0",
                MaxCapacity=0.0625,
                MaxRetries=0,
                Timeout=10,
                ExecutionProperty={"MaxConcurrentRuns": 5},
                DefaultArguments={"--additional-python-modules": "pandas"}
            )
            status_placeholders[3].success("✅ Glue job created (Version 1.0, MaxCapacity=0.0625)")
        except Exception as e:
            status_placeholders[3].error(f"❌ Create Glue job failed: {str(e)}")
            st.stop()
            
        # 5. Create Athena DB
        try:
            run_athena_query("CREATE DATABASE IF NOT EXISTS sigma_phoenix_db", database="default")
            status_placeholders[4].success("✅ Athena database sigma_phoenix_db created")
        except Exception as e:
            status_placeholders[4].error(f"❌ Create Athena DB failed: {str(e)}")
            st.stop()
            
        # 6. Create orders table
        try:
            orders_ddl = f"""
            CREATE EXTERNAL TABLE IF NOT EXISTS {ATHENA_DB}.sigma_phoenix_orders (
                order_id STRING,
                customer_id STRING,
                product_id STRING,
                quantity INT,
                amount DOUBLE,
                status STRING,
                payment_method STRING,
                city STRING,
                created_at STRING,
                processed_at STRING,
                is_high_value STRING,
                transaction_tier STRING
            )
            PARTITIONED BY (date STRING)
            ROW FORMAT DELIMITED
            FIELDS TERMINATED BY ','
            STORED AS TEXTFILE
            LOCATION 's3://{S3_BUCKET}/processed/orders/'
            TBLPROPERTIES ('skip.header.line.count'='1')
            """
            run_athena_query(orders_ddl, database="default")
            status_placeholders[5].success("✅ Orders table created")
        except Exception as e:
            status_placeholders[5].error(f"❌ Create orders table failed: {str(e)}")
            st.stop()
            
        # 7. Create customers table
        try:
            run_athena_query(f"DROP TABLE IF EXISTS {ATHENA_DB}.sigma_phoenix_customers", database="default")
            cust_ddl = f"""
            CREATE EXTERNAL TABLE {ATHENA_DB}.sigma_phoenix_customers (
                customer_id STRING,
                name STRING,
                email STRING,
                phone STRING,
                city STRING,
                tier STRING,
                signup_date STRING
            )
            ROW FORMAT DELIMITED
            FIELDS TERMINATED BY ','
            STORED AS TEXTFILE
            LOCATION 's3://{S3_BUCKET}/processed/customers/'
            TBLPROPERTIES ('skip.header.line.count'='1')
            """
            run_athena_query(cust_ddl, database="default")
            status_placeholders[6].success("✅ Customers table created")
        except Exception as e:
            status_placeholders[6].error(f"❌ Create customers table failed: {str(e)}")
            st.stop()
            
        # 8. Create products table
        try:
            run_athena_query(f"DROP TABLE IF EXISTS {ATHENA_DB}.sigma_phoenix_products", database="default")
            prod_ddl = f"""
            CREATE EXTERNAL TABLE {ATHENA_DB}.sigma_phoenix_products (
                product_id STRING,
                name STRING,
                category STRING,
                price DOUBLE,
                stock_quantity INT,
                is_active STRING
            )
            ROW FORMAT DELIMITED
            FIELDS TERMINATED BY ','
            STORED AS TEXTFILE
            LOCATION 's3://{S3_BUCKET}/processed/products/'
            TBLPROPERTIES ('skip.header.line.count'='1')
            """
            run_athena_query(prod_ddl, database="default")
            status_placeholders[7].success("✅ Products table created")
        except Exception as e:
            status_placeholders[7].error(f"❌ Create products table failed: {str(e)}")
            st.stop()
            
        st.success("🛒 QuickMart pipeline is live! Proceed to Tab 2.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — 📦 Daily Load
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("## 📦 Daily Load")
    day_options = {
        "Day 1 — 2026-05-01": ("2026-05-01", "orders_day1.csv"),
        "Day 2 — 2026-05-02": ("2026-05-02", "orders_day2.csv"),
        "Day 3 — 2026-05-03": ("2026-05-03", "orders_day3.csv"),
        "Day 4 — 2026-05-04": ("2026-05-04", "orders_day4.csv"),
        "Day 5 — 2026-05-05": ("2026-05-05", "orders_day5.csv"),
    }
    
    selected_label = st.selectbox("Select day to process:", list(day_options.keys()))
    selected_date, selected_file = day_options[selected_label]
    st.markdown("<p style='font-size:14px; color:#aaa; margin-top:-10px;'>⚠️ Day 3 contains planted defects — run it live!</p>", unsafe_allow_html=True)
    
    if st.button(f"▶️ Run ETL for {selected_label}", key="run_etl_btn"):
        # 1. Upload CSV to S3
        with st.spinner(f"Uploading local {selected_file} to raw/orders..."):
            try:
                with open(f"new_data/{selected_file}", "rb") as f:
                    csv_data = f.read()
                s3_client.put_object(
                    Bucket=S3_BUCKET, 
                    Key=f"raw/orders/date={selected_date}/orders.csv", 
                    Body=csv_data
                )
                st.write("✅ CSV uploaded to raw zone")
            except Exception as e:
                st.error(f"Upload failed: {str(e)}")
                st.stop()
                
        # 2. Trigger Glue job
        try:
            run_response = glue_client.start_job_run(
                JobName=GLUE_JOB,
                Arguments={
                    '--bucket_name': S3_BUCKET,
                    '--date_partition': selected_date,
                    '--job_type': 'orders'
                }
            )
            job_run_id = run_response['JobRunId']
            st.write(f"🚀 Triggered Glue job: RunId={job_run_id}")
        except Exception as e:
            st.error(f"Failed to start Glue job: {str(e)}")
            st.stop()
            
        # 3. Poll Glue job status
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        job_success = False
        error_msg = ""
        for i in range(40):
            progress_bar.progress((i + 1) / 40)
            status_text.text(f"⏳ Processing grocery transactions... (Poll {i+1}/40)")
            time.sleep(3)
            
            try:
                run_status = glue_client.get_job_run(JobName=GLUE_JOB, RunId=job_run_id)['JobRun']
                state = run_status['JobRunState']
                if state == 'SUCCEEDED':
                    job_success = True
                    break
                elif state in ['FAILED', 'STOPPED', 'TIMEOUT']:
                    error_msg = run_status.get('ErrorMessage', 'Unknown Glue error')
                    break
            except Exception as e:
                error_msg = str(e)
                break
                
        progress_bar.progress(100)
        status_text.empty()
        
        if not job_success:
            st.error(f"❌ Glue job run failed: {error_msg}")
        else:
            st.success("✅ Glue job succeeded!")
            
            # 4. MSCK REPAIR TABLE
            with st.spinner("Synchronizing partitions in Athena..."):
                try:
                    run_athena_query(f"MSCK REPAIR TABLE {ATHENA_DB}.sigma_phoenix_orders", database="default")
                    st.write("✅ Partitions synchronized")
                except Exception as e:
                    st.error(f"MSCK REPAIR failed: {str(e)}")
                    st.stop()
                    
            # 5. Read quality report from S3
            try:
                report_obj = s3_client.get_object(
                    Bucket=S3_BUCKET, 
                    Key=f"reports/quality_report_{selected_date}.json"
                )
                report_data = json.loads(report_obj['Body'].read().decode('utf-8'))
                
                # Display metrics in 2 rows of 3 columns
                st.markdown("### Data Quality Metrics")
                row1_col1, row1_col2, row1_col3 = st.columns(3)
                row1_col1.metric("Input Rows", f"{report_data['input_rows']:,}")
                row1_col2.metric("Output Rows", f"{report_data['output_rows']:,}")
                row1_col3.metric("Rows Dropped", f"{report_data['rows_dropped']:,}")
                
                row2_col1, row2_col2, row2_col3 = st.columns(3)
                row2_col1.metric("Null Customer IDs", f"{report_data['null_customer_ids']:,}")
                row2_col2.metric("Negative Amounts", f"{report_data['negative_amounts']:,}")
                row2_col3.metric("Duplicate Order IDs", f"{report_data['duplicate_order_ids']:,}")
                
                # Warning and explanations if defects found
                has_defects = (report_data['null_customer_ids'] > 0 or 
                               report_data['negative_amounts'] > 0 or 
                               report_data['duplicate_order_ids'] > 0)
                
                if has_defects:
                    st.warning("⚠️ Data quality issues detected in today's grocery transactions")
                    
                    if report_data['null_customer_ids'] > 0:
                        st.markdown("- **Null Customer IDs:** Purchase record cannot be linked to loyalty accounts. Impact: breaks personalizations, coupons, and reward distributions.")
                    if report_data['negative_amounts'] > 0:
                        st.markdown("- **Negative Amounts:** Erroneous values in orders. Impact: directly reduces gross transaction amount totals (leakage) and distorts daily GMV indicators.")
                    if report_data['duplicate_order_ids'] > 0:
                        st.markdown("- **Duplicate Order IDs:** Duplicate entries. Impact: risk of charging credit/debit or UPI accounts twice for the exact same grocery basket.")
                
                # Bedrock assessment
                with st.spinner("🤖 Requesting Bedrock AI analysis..."):
                    bedrock_prompt = f"""
                    You are a retail data quality analyst at QuickMart. Analyze this pipeline report:
                    {json.dumps(report_data, indent=2)}

                    Comment on the business risk (revenue accuracy, loyalty attribution, inventory integrity) of these defects.
                    Your analysis must start with a status classification: either "STATUS: HEALTHY", "STATUS: WARNING", or "STATUS: CRITICAL".
                    Followed by a concise comment and one recommendation focused on retail/FMCG business impact.
                    Keep your entire response under 80 words.
                    """
                    
                    resp = bedrock_client.converse(
                        modelId="us.amazon.nova-lite-v1:0",
                        messages=[{"role": "user", "content": [{"text": bedrock_prompt}]}],
                        inferenceConfig={"maxTokens": 500, "temperature": 0.0}
                    )
                    analysis_text = resp["output"]["message"]["content"][0]["text"].strip()
                    
                    st.markdown("### 🤖 Bedrock Data Quality Assessment")
                    st.info(analysis_text)
                    
            except Exception as e:
                st.error(f"Error fetching quality report: {str(e)}")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — 🔍 Ask Your Data
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("## 🔍 Ask Your Data")
    st.markdown("<p style='color:#94A3B8; font-size:15px; margin-top:-8px;'>Click a quick question below or type your own business question to auto-generate Athena SQL.</p>", unsafe_allow_html=True)

    # Pre-written, verified Athena SQL for quick-question buttons
    # These bypass Bedrock entirely — guaranteed to work on the actual schema.
    QUICK_QUESTIONS = {
        "🏙️ Revenue by City": (
            "Revenue by City",
            f"""SELECT city,
       CAST(ROUND(SUM(amount)) AS BIGINT) AS total_revenue,
       COUNT(*) AS total_orders
FROM {ATHENA_DB}.sigma_phoenix_orders
GROUP BY city
ORDER BY total_revenue DESC"""
        ),
        "📅 Daily Order Trend": (
            "Daily Order Trend",
            f"""SELECT date,
       COUNT(*) AS total_orders,
       CAST(ROUND(SUM(amount)) AS BIGINT) AS daily_revenue
FROM {ATHENA_DB}.sigma_phoenix_orders
GROUP BY date
ORDER BY date"""
        ),
        "💎 High-Value Orders": (
            "High-Value Orders per Day",
            f"""SELECT date,
       COUNT(*) AS high_value_orders,
       CAST(ROUND(SUM(amount)) AS BIGINT) AS hv_revenue
FROM {ATHENA_DB}.sigma_phoenix_orders
WHERE is_high_value = 'True'
GROUP BY date
ORDER BY date"""
        ),
        "💳 Payment Methods": (
            "Payment Methods by Order Count",
            f"""SELECT payment_method,
       COUNT(*) AS order_count,
       CAST(ROUND(SUM(amount)) AS BIGINT) AS total_revenue
FROM {ATHENA_DB}.sigma_phoenix_orders
GROUP BY payment_method
ORDER BY order_count DESC"""
        ),
        "🛍️ Category Revenue": (
            "Revenue by Product Category",
            f"""SELECT p.category,
       CAST(ROUND(SUM(o.amount)) AS BIGINT) AS total_revenue,
       COUNT(*) AS total_orders
FROM {ATHENA_DB}.sigma_phoenix_orders o
JOIN {ATHENA_DB}.sigma_phoenix_products p ON o.product_id = p.product_id
GROUP BY p.category
ORDER BY total_revenue DESC"""
        ),
    }

    # Persist staged quick-question selection
    if "_qq_label" in st.session_state:
        lbl = st.session_state.pop("_qq_label")
        if lbl in QUICK_QUESTIONS:
            q_label, q_sql = QUICK_QUESTIONS[lbl]
            st.session_state["nl_question_input"] = q_label
            st.session_state["generated_sql"] = q_sql
            st.session_state["sql_question"] = q_label
            if "query_result_df" in st.session_state:
                del st.session_state["query_result_df"]

    qq_cols = st.columns(len(QUICK_QUESTIONS))
    for i, (btn_label, _) in enumerate(QUICK_QUESTIONS.items()):
        if qq_cols[i].button(btn_label, key=f"qq_{i}"):
            st.session_state["_qq_label"] = btn_label
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    user_question = st.text_input("✏️  Or ask a custom question about QuickMart sales…", key="nl_question_input")

    if user_question:
        if "sql_question" not in st.session_state or st.session_state["sql_question"] != user_question:
            with st.spinner("🤖 Generating Athena SQL..."):
                sql_prompt = f"""
                You are a senior Data Engineer at QuickMart writing PrestoDB / Athena SQL.
                Generate ONE valid Athena SQL query for: "{user_question}"

                === TABLE SCHEMAS ===
                Table alias 'o' → {ATHENA_DB}.sigma_phoenix_orders
                  Columns: order_id, customer_id, product_id, quantity, amount (DOUBLE),
                           status, payment_method, city, created_at, processed_at,
                           is_high_value, transaction_tier, date (partition key STRING)

                Table alias 'c' → {ATHENA_DB}.sigma_phoenix_customers
                  Columns: customer_id, name, email, phone, city, tier, signup_date

                Table alias 'p' → {ATHENA_DB}.sigma_phoenix_products
                  Columns: product_id, name, category, price (DOUBLE), stock_quantity, is_active

                === STRICT RULES ===
                1. Output ONLY the raw SQL — no markdown fences, no backticks, no explanation.
                2. Prefix every table with database '{ATHENA_DB}' (e.g., {ATHENA_DB}.sigma_phoenix_orders).
                3. Every column reference MUST use the alias of the table it belongs to.
                   Example: city lives in sigma_phoenix_orders → use o.city, NOT s.city or c.city unless
                   you are referencing sigma_phoenix_customers.
                4. When joining tables always use explicit ON conditions matching primary keys.
                5. Wrap every SUM/AVG of 'amount' in CAST(ROUND(...) AS BIGINT).
                6. Aggregation queries with GROUP BY → no LIMIT. Plain SELECT → LIMIT 100.
                7. Do NOT use undefined aliases. Only use: o, c, p (as declared above).
                """
                
                try:
                    resp = bedrock_client.converse(
                        modelId="us.amazon.nova-lite-v1:0",
                        messages=[{"role": "user", "content": [{"text": sql_prompt}]}],
                        inferenceConfig={"maxTokens": 500, "temperature": 0.0}
                    )
                    sql = resp["output"]["message"]["content"][0]["text"].strip()
                    
                    # Clean markdown code fences if Bedrock added them
                    if sql.startswith("```sql"):
                        sql = sql[6:]
                    elif sql.startswith("```"):
                        sql = sql[3:]
                    if sql.endswith("```"):
                        sql = sql[:-3]
                    sql = sql.strip()
                    
                    # Post-process generated SQL
                    first_word = sql.split()[0].upper() if sql.split() else ""
                    if first_word != "SELECT":
                        sql = re.sub(r'\bLIMIT\s+\d+\b', '', sql, flags=re.IGNORECASE).strip()
                        
                    st.session_state["generated_sql"] = sql
                    st.session_state["sql_question"] = user_question
                    # Clear previous results when question changes
                    if "query_result_df" in st.session_state:
                        del st.session_state["query_result_df"]
                except Exception as e:
                    st.error(f"SQL generation failed: {str(e)}")
                    st.stop()
                    
        sql = st.session_state.get("generated_sql", "")
        st.markdown("### 🗄️ Generated Athena SQL")
        st.code(sql, language="sql")
        
        if st.button("▶️ Run on Athena", key="run_athena_btn"):
            with st.spinner("⏳ Querying Athena..."):
                try:
                    df = run_athena_query(sql, database=ATHENA_DB)
                    st.session_state["query_result_df"] = df
                    st.session_state["query_result_err"] = None
                except Exception as e:
                    st.session_state["query_result_df"] = None
                    st.session_state["query_result_err"] = str(e)
                    
        if "query_result_df" in st.session_state:
            df = st.session_state["query_result_df"]
            err = st.session_state["query_result_err"]
            
            if err:
                st.error(f"❌ Athena Error: {err}")
            elif df is not None:
                st.markdown("### Query Results")
                if df.empty:
                    st.info("No rows returned.")
                else:
                    formatted_df = format_dataframe_display(df)
                    st.dataframe(formatted_df)
                    
                    # Call Bedrock to explain the result
                    with st.spinner("🤖 Explaining results..."):
                        explain_prompt = f"""
                        You are a retail data analyst at QuickMart. Review the query results:
                        {df.head(20).to_string(index=False)}
                        
                        Explain the business insight in exactly one plain-English sentence. Focus on retail insight.
                        """
                        try:
                            resp = bedrock_client.converse(
                                modelId="us.amazon.nova-lite-v1:0",
                                messages=[{"role": "user", "content": [{"text": explain_prompt}]}],
                                inferenceConfig={"maxTokens": 200, "temperature": 0.0}
                            )
                            explanation = resp["output"]["message"]["content"][0]["text"].strip()
                            st.info(f"🤖 **AI Analysis:** {explanation}")
                        except Exception as e:
                            st.error(f"Failed to generate analysis: {str(e)}")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — 📊 Pipeline Health
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown("## 📊 Pipeline Health")
    st.markdown("<p style='color:#94A3B8; font-size:15px; margin-top:-8px;'>Real-time view of your QuickMart data pipeline — orders, revenue, quality signals, and trends.</p>", unsafe_allow_html=True)

    if st.button("🔄 Load Health Dashboard", key="load_health_btn"):
        with st.spinner("⏳ Loading pipeline metrics..."):
            try:
                # Primary query — daily revenue & orders
                health_query = f"""
                SELECT date,
                       COUNT(*) AS orders,
                       CAST(ROUND(SUM(amount)) AS BIGINT) AS revenue,
                       CAST(ROUND(AVG(amount)) AS BIGINT) AS avg_basket
                FROM {ATHENA_DB}.sigma_phoenix_orders
                GROUP BY date
                ORDER BY date
                """
                df_health = run_athena_query(health_query, database=ATHENA_DB)
                st.session_state["df_health"] = df_health

                # High-value orders per day
                hv_query = f"""
                SELECT date,
                       SUM(CASE WHEN is_high_value = 'True' THEN 1 ELSE 0 END) AS high_value_orders,
                       COUNT(*) AS total_orders
                FROM {ATHENA_DB}.sigma_phoenix_orders
                GROUP BY date
                ORDER BY date
                """
                df_hv = run_athena_query(hv_query, database=ATHENA_DB)
                st.session_state["df_hv"] = df_hv

                # Order status breakdown (completed vs pending)
                status_query = f"""
                SELECT status, COUNT(*) AS order_count
                FROM {ATHENA_DB}.sigma_phoenix_orders
                GROUP BY status
                ORDER BY order_count DESC
                """
                df_status = run_athena_query(status_query, database=ATHENA_DB)
                st.session_state["df_status"] = df_status

                # Transaction tier split (BULK vs STANDARD)
                tier_query = f"""
                SELECT transaction_tier, COUNT(*) AS order_count,
                       CAST(ROUND(SUM(amount)) AS BIGINT) AS revenue
                FROM {ATHENA_DB}.sigma_phoenix_orders
                GROUP BY transaction_tier
                ORDER BY order_count DESC
                """
                df_tier = run_athena_query(tier_query, database=ATHENA_DB)
                st.session_state["df_tier"] = df_tier

            except Exception as e:
                st.error(f"Error loading health dashboard: {str(e)}")

    if "df_health" in st.session_state:
        df         = st.session_state["df_health"]
        df_hv      = st.session_state.get("df_hv", pd.DataFrame())
        df_status  = st.session_state.get("df_status", pd.DataFrame())
        df_tier    = st.session_state.get("df_tier", pd.DataFrame())

        if df.empty:
            st.info("No data found in orders table. Make sure to run the ETL in Tab 2 first.")
        else:
            df['orders']     = pd.to_numeric(df['orders'])
            df['revenue']    = pd.to_numeric(df['revenue'])
            df['avg_basket'] = pd.to_numeric(df['avg_basket'])

            total_orders   = int(df['orders'].sum())
            total_revenue  = int(df['revenue'].sum())
            days_loaded    = len(df)
            overall_avg    = int(df['avg_basket'].mean())
            total_hv       = int(df_hv['high_value_orders'].apply(pd.to_numeric).sum()) if not df_hv.empty else 0
            hv_pct         = round(total_hv / total_orders * 100, 1) if total_orders > 0 else 0

            # ── Row 1: KPI metrics ──────────────────────────────────────────
            st.markdown("### 📈 Key Pipeline Metrics")
            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("Total Orders",      f"{total_orders:,}")
            k2.metric("Total Revenue",     f"₹{total_revenue:,}")
            k3.metric("Days Loaded",       str(days_loaded))
            k4.metric("Avg Basket Value",  f"₹{overall_avg:,}")
            k5.metric("High-Value Orders", f"{total_hv:,} ({hv_pct}%)")

            st.markdown("<hr>", unsafe_allow_html=True)

            # ── Row 2: Revenue & Orders side by side ────────────────────────
            st.markdown("### 📊 Daily Revenue & Volume")
            df_indexed = df.set_index('date')
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### 💰 Daily Revenue (₹)")
                st.bar_chart(df_indexed['revenue'])
            with c2:
                st.markdown("#### 🛒 Daily Order Count")
                st.bar_chart(df_indexed['orders'])

            st.markdown("<hr>", unsafe_allow_html=True)

            # ── Row 3: Avg Basket & High-Value trend ────────────────────────
            st.markdown("### 🎯 Order Quality Signals")
            c3, c4 = st.columns(2)
            with c3:
                st.markdown("#### 📦 Avg Basket Value per Day (₹)")
                st.bar_chart(df_indexed['avg_basket'])
            with c4:
                if not df_hv.empty:
                    st.markdown("#### 💎 High-Value Orders per Day")
                    df_hv_c = df_hv.copy()
                    df_hv_c['high_value_orders'] = pd.to_numeric(df_hv_c['high_value_orders'])
                    df_hv_c = df_hv_c.set_index('date')
                    st.bar_chart(df_hv_c['high_value_orders'])

            st.markdown("<hr>", unsafe_allow_html=True)

            # ── Row 4: Status & Tier breakdown tables ───────────────────────
            st.markdown("### 🔬 Order Composition Breakdown")
            c5, c6 = st.columns(2)
            with c5:
                st.markdown("#### ✅ Order Status Distribution")
                if not df_status.empty:
                    df_status['order_count'] = pd.to_numeric(df_status['order_count'])
                    st.dataframe(format_dataframe_display(df_status), use_container_width=True)
                    # Quick inline bar
                    st.bar_chart(df_status.set_index('status')['order_count'])
            with c6:
                st.markdown("#### 📦 Transaction Tier Split (BULK vs STANDARD)")
                if not df_tier.empty:
                    df_tier['order_count'] = pd.to_numeric(df_tier['order_count'])
                    df_tier['revenue']     = pd.to_numeric(df_tier['revenue'])
                    st.dataframe(format_dataframe_display(df_tier), use_container_width=True)
                    st.bar_chart(df_tier.set_index('transaction_tier')['order_count'])

            st.markdown("<hr>", unsafe_allow_html=True)

            # ── Bedrock CTO summary ─────────────────────────────────────────
            with st.spinner("🤖 Generating executive summary..."):
                summary_prompt = f"""
                You are QuickMart's Head of Data. Write a 3-sentence executive summary of this week's grocery transaction pipeline performance for the CTO.
                Data summary:
                Total Orders: {total_orders}
                Total Revenue: ₹{total_revenue} INR
                Days loaded: {days_loaded}
                Avg basket value: ₹{overall_avg}
                High-value orders: {total_hv} ({hv_pct}%)
                Daily breakdown:
                {df[['date','orders','revenue','avg_basket']].to_string(index=False)}
                """
                try:
                    resp = bedrock_client.converse(
                        modelId="us.amazon.nova-lite-v1:0",
                        messages=[{"role": "user", "content": [{"text": summary_prompt}]}],
                        inferenceConfig={"maxTokens": 500, "temperature": 0.0}
                    )
                    summary_text = resp["output"]["message"]["content"][0]["text"].strip()
                    st.markdown("### 🤖 Executive Summary (CTO Report)")
                    st.info(summary_text)
                except Exception as e:
                    st.error(f"Failed to generate summary: {str(e)}")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 — 🛒 Store Intelligence
# ─────────────────────────────────────────────────────────────────────────────
with tab5:
    st.markdown("## 🛒 Store Intelligence")
    st.markdown("<p style='font-size:16px; color:#94A3B8; margin-top:-10px;'>FMCG Store Performance Analytics, Inventory Health, & AI Store Manager Recommendations</p>", unsafe_allow_html=True)
    
    if st.button("🔍 Load Store Intelligence", key="load_store_intel_btn"):
        with st.spinner("⏳ Loading Store Intelligence..."):
            try:
                # Query A — Category Revenue Breakdown
                query_a = f"""
                SELECT p.category,
                       CAST(ROUND(SUM(o.amount)) AS BIGINT) AS total_revenue,
                       COUNT(*) AS total_orders
                FROM {ATHENA_DB}.sigma_phoenix_orders o
                JOIN {ATHENA_DB}.sigma_phoenix_products p ON o.product_id = p.product_id
                GROUP BY p.category
                ORDER BY total_revenue DESC
                """
                df_a = run_athena_query(query_a, database=ATHENA_DB)
                st.session_state["df_intel_a"] = df_a
                
                # Query B — Payment Method Split
                query_b = f"""
                SELECT payment_method,
                       COUNT(*) AS order_count,
                       CAST(ROUND(SUM(amount)) AS BIGINT) AS revenue
                FROM {ATHENA_DB}.sigma_phoenix_orders
                GROUP BY payment_method
                ORDER BY order_count DESC
                """
                df_b = run_athena_query(query_b, database=ATHENA_DB)
                st.session_state["df_intel_b"] = df_b
                
                # Query C — Customer Tier Performance
                query_c = f"""
                SELECT c.tier,
                       COUNT(*) AS orders,
                       CAST(ROUND(AVG(o.amount)) AS BIGINT) AS avg_basket
                FROM {ATHENA_DB}.sigma_phoenix_orders o
                JOIN {ATHENA_DB}.sigma_phoenix_customers c ON o.customer_id = c.customer_id
                GROUP BY c.tier
                ORDER BY avg_basket DESC
                """
                df_c = run_athena_query(query_c, database=ATHENA_DB)
                st.session_state["df_intel_c"] = df_c

                # Query D — Top Performing Products
                query_d = f"""
                SELECT p.name, p.category, 
                       CAST(ROUND(SUM(o.amount)) AS BIGINT) AS total_revenue, 
                       SUM(o.quantity) AS units_sold
                FROM {ATHENA_DB}.sigma_phoenix_orders o
                JOIN {ATHENA_DB}.sigma_phoenix_products p ON o.product_id = p.product_id
                GROUP BY p.name, p.category
                ORDER BY total_revenue DESC
                LIMIT 5
                """
                df_d = run_athena_query(query_d, database=ATHENA_DB)
                st.session_state["df_intel_d"] = df_d

                # Query E — Low Stock Inventory Alert
                query_e = f"""
                SELECT name, category, stock_quantity, price
                FROM {ATHENA_DB}.sigma_phoenix_products
                WHERE stock_quantity < 150
                ORDER BY stock_quantity ASC
                LIMIT 5
                """
                df_e = run_athena_query(query_e, database=ATHENA_DB)
                st.session_state["df_intel_e"] = df_e

                # Query F — City Revenue Distribution
                query_f = f"""
                SELECT city, CAST(ROUND(SUM(amount)) AS BIGINT) AS total_revenue, COUNT(*) AS total_orders
                FROM {ATHENA_DB}.sigma_phoenix_orders
                GROUP BY city
                ORDER BY total_revenue DESC
                """
                df_f = run_athena_query(query_f, database=ATHENA_DB)
                st.session_state["df_intel_f"] = df_f
                
            except Exception as e:
                st.error(f"Error loading Store Intelligence: {str(e)}")

    if "df_intel_a" in st.session_state:
        df_a = st.session_state["df_intel_a"]
        df_b = st.session_state["df_intel_b"]
        df_c = st.session_state["df_intel_c"]
        df_d = st.session_state["df_intel_d"]
        df_e = st.session_state["df_intel_e"]
        df_f = st.session_state["df_intel_f"]
        
        if df_a.empty:
            st.info("No data available. Run the setup and load daily data first.")
        else:
            # Row 1: Metrics
            st.markdown("### 📈 QuickMart Store KPIs")
            col1, col2, col3 = st.columns(3)
            
            top_category = df_a.iloc[0]['category'] if not df_a.empty else "N/A"
            top_payment = df_b.iloc[0]['payment_method'] if not df_b.empty else "N/A"
            top_tier = df_c.iloc[0]['tier'] if not df_c.empty else "N/A"
            
            col1.metric("Top Performing Category", top_category)
            col2.metric("Dominant Payment Method", top_payment)
            col3.metric("Highest Basket Tier", top_tier)
            
            st.markdown("<hr>", unsafe_allow_html=True)
            
            # Row 2: Charts (Category vs City Revenue)
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.markdown("#### 📊 Category Revenue Breakdown")
                df_a_chart = df_a.copy()
                df_a_chart['total_revenue'] = pd.to_numeric(df_a_chart['total_revenue'])
                df_a_chart = df_a_chart.set_index('category')
                st.bar_chart(df_a_chart['total_revenue'])
                
            with col_chart2:
                st.markdown("#### 🌆 City Revenue Distribution")
                df_f_chart = df_f.copy()
                df_f_chart['total_revenue'] = pd.to_numeric(df_f_chart['total_revenue'])
                df_f_chart = df_f_chart.set_index('city')
                st.bar_chart(df_f_chart['total_revenue'])

            st.markdown("<hr>", unsafe_allow_html=True)

            # Row 3: Product Performance & Stock Alerts
            col_tbl1, col_tbl2 = st.columns(2)
            
            with col_tbl1:
                st.markdown("#### 🏆 Top 5 Performing SKUs")
                st.dataframe(format_dataframe_display(df_d), use_container_width=True)
                
            with col_tbl2:
                st.markdown("#### ⚠️ Low Stock Inventory Alert (<150 units)")
                st.dataframe(format_dataframe_display(df_e), use_container_width=True)

            st.markdown("<hr>", unsafe_allow_html=True)

            # Row 4: Customer Tier & Payment Method Splits
            col_split1, col_split2 = st.columns(2)
            
            with col_split1:
                st.markdown("#### 💳 Payment Method Split")
                for idx, row in df_b.head(3).iterrows():
                    pay_method = row['payment_method']
                    ord_cnt = int(row['order_count'])
                    rev = float(row['revenue'])
                    st.metric(
                        label=f"{idx+1}. {pay_method}",
                        value=f"{ord_cnt:,} orders",
                        delta=f"₹{int(round(rev)):,} total sales"
                    )
                    
            with col_split2:
                st.markdown("#### 🏆 Customer Tier Performance")
                st.dataframe(format_dataframe_display(df_c), use_container_width=True)
            
            st.markdown("<hr>", unsafe_allow_html=True)
            
            # Row 5: AI Recommendations
            with st.spinner("🤖 Generating Store Manager recommendations..."):
                rec_prompt = f"""
                You are QuickMart's retail analytics AI. Based on the category revenue, payment method split, customer tier data, top performing products, and low stock products below, give 3 bullet-point business recommendations a retail store manager could act on this week. Be specific and data-driven. Max 120 words.
                
                Category Revenue data:
                {df_a.to_string(index=False)}
                
                Payment Method Split:
                {df_b.to_string(index=False)}
                
                Customer Tier Performance:
                {df_c.to_string(index=False)}

                Top Performing Products:
                {df_d.to_string(index=False)}

                Low Stock Products:
                {df_e.to_string(index=False)}
                """
                try:
                    resp = bedrock_client.converse(
                        modelId="us.amazon.nova-lite-v1:0",
                        messages=[{"role": "user", "content": [{"text": rec_prompt}]}],
                        inferenceConfig={"maxTokens": 500, "temperature": 0.0}
                    )
                    rec_text = resp["output"]["message"]["content"][0]["text"].strip()
                    
                    st.markdown("### 🤖 AI Store Manager Recommendations")
                    st.info(rec_text)
                except Exception as e:
                    st.error(f"Failed to generate recommendations: {str(e)}")

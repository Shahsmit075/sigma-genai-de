"""
snowflake_catalog.py
Sigma Intelligence Bootcamp — Day 4

Fetches the Sigma DataTech data catalogue from your Snowflake trial account.
Students: Fill in your Snowflake credentials below, then run the setup SQL
in setup_snowflake.sql to create the catalogue tables.

This file replaces catalog_data.py — it returns the same TABLE_CATALOG list
so indexer.py works without any changes.
"""

import snowflake.connector
import re

# ── YOUR CREDENTIALS — fill these in ──────────────────────────────────────
SNOWFLAKE_CONFIG = {
    "user":      "SMITSHAH12",
    "password":  "MVkw8eX4GKpfmR6",
    "account":   "YSIBBUB-WV28708",
    "warehouse": "COMPUTE_WH",
    "database":  "SIGMA_CATALOGUE",
    "schema":    "PUBLIC",
}
# ──────────────────────────────────────────────────────────────────────────


def _parse_tag(comment: str, tag: str, default: str = "Unknown") -> str:
    """Extract [tag:value] from a COMMENT string."""
    match = re.search(rf"\[{tag}:([^\]]+)\]", comment)
    return match.group(1).strip() if match else default


def fetch_catalogue() -> list[dict]:
    """Connect to Snowflake and return TABLE_CATALOG in the same format as catalog_data.py."""
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    cur  = conn.cursor()

    cur.execute("""
        SELECT
            TABLE_NAME,
            COMMENT,
            TO_CHAR(LAST_ALTERED, 'YYYY-MM-DD') AS LAST_UPDATED,
            ROW_COUNT
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'PUBLIC'
          AND TABLE_TYPE   = 'BASE TABLE'
          AND COMMENT IS NOT NULL
          AND COMMENT != ''
        ORDER BY TABLE_NAME
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    catalogue = []
    for table_name, comment, last_updated, row_count in rows:
        catalogue.append({
            "table_name":     table_name.lower(),
            "description":    re.sub(r"\[.*?\]", "", comment).strip(),   # strip tags from embed text
            "last_updated":   last_updated or "2026-01-01",
            "classification": _parse_tag(comment, "classification", "Internal"),
            "domain":         _parse_tag(comment, "domain", "platform"),
            "owner":          _parse_tag(comment, "owner", "Platform Engineering"),
            "rows":           f"{row_count:,}" if row_count else "unknown",
        })

    return catalogue


# TABLE_CATALOG is what indexer.py imports — same interface as catalog_data.py
try:
    TABLE_CATALOG = fetch_catalogue()
    print(f"✅ Snowflake catalogue loaded — {len(TABLE_CATALOG)} tables found.")
except Exception as e:
    print(f"❌ Snowflake connection failed: {e}")
    print("   Check your credentials in snowflake_catalog.py")
    TABLE_CATALOG = []

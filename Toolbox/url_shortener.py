import hashlib
import sqlite3
import json
from datetime import datetime

import pandas as pd
import streamlit as st

DB_PATH = "urls.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS url_mappings (
            short_code TEXT PRIMARY KEY,
            original_url TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    return conn


ALLOWED_DOMAINS = (
    "kiddom.co",
    "app.kiddom.co",
    "amazonaws.com",
)


def is_allowed_url(url: str) -> bool:
    from urllib.parse import urlparse
    try:
        host = urlparse(url).netloc.lower()
        return any(host == d or host.endswith("." + d) for d in ALLOWED_DOMAINS)
    except Exception:
        return False


def make_short_code(url: str) -> str:
    digest = hashlib.sha256(url.strip().encode()).hexdigest()[:6]
    return f"kiddom-{digest}"


def save_mapping(conn, short_code: str, original_url: str):
    conn.execute(
        "INSERT OR IGNORE INTO url_mappings (short_code, original_url) VALUES (?, ?)",
        (short_code, original_url),
    )
    conn.commit()


def load_all_mappings(conn) -> pd.DataFrame:
    return pd.read_sql(
        "SELECT short_code, original_url, created_at FROM url_mappings ORDER BY created_at DESC",
        conn,
    )


st.set_page_config(page_title="Kiddom URL Shortener", page_icon="🔗", layout="centered")
st.title("🔗 Kiddom URL Shortener")
st.caption("Generate branded short codes for Kiddom content links.")

conn = get_conn()

tab1, tab2, tab3, tab4 = st.tabs(["Single URL", "Bulk CSV", "View All Mappings", "Deploy"])

# ── Tab 1: Single URL ────────────────────────────────────────────────────────
with tab1:
    url_input = st.text_input("Enter a URL to shorten", placeholder="https://app.kiddom.co/...")

    if st.button("Shorten", type="primary", key="single"):
        url = url_input.strip()
        if not url:
            st.warning("Please enter a URL.")
        elif not url.startswith(("http://", "https://")):
            st.error("URL must start with http:// or https://")
        elif not is_allowed_url(url):
            st.error("Only Kiddom platform URLs and Kiddom AWS assets are allowed.")
        else:
            code = make_short_code(url)
            save_mapping(conn, code, url)
            st.success("Short code generated!")
            st.code(code, language=None)
            st.caption(f"Original: {url}")
            st.info("Go to the **Deploy** tab to publish this link.")

# ── Tab 2: Bulk CSV ──────────────────────────────────────────────────────────
with tab2:
    uploaded = st.file_uploader("Upload a CSV file", type="csv")

    if uploaded:
        df = pd.read_csv(uploaded)
        st.write("**Preview** (first 5 rows)")
        st.dataframe(df.head(), use_container_width=True)

        url_col = st.selectbox("Which column contains the URLs?", options=df.columns.tolist())

        if st.button("Generate Short Codes", type="primary", key="bulk"):
            codes = []
            skipped = 0
            for raw in df[url_col]:
                if pd.isna(raw) or not str(raw).strip().startswith(("http://", "https://")):
                    codes.append("")
                    skipped += 1
                elif not is_allowed_url(str(raw).strip()):
                    codes.append("BLOCKED — not a Kiddom URL")
                    skipped += 1
                else:
                    url = str(raw).strip()
                    code = make_short_code(url)
                    save_mapping(conn, code, url)
                    codes.append(code)

            df["short_url"] = codes
            generated = sum(1 for c in codes if c and not c.startswith("BLOCKED"))
            st.success(f"Generated {generated} short codes. {skipped} rows skipped.")
            st.dataframe(df, use_container_width=True)

            csv_bytes = df.to_csv(index=False).encode()
            st.download_button(
                label="⬇️ Download Updated CSV",
                data=csv_bytes,
                file_name="urls_with_short_codes.csv",
                mime="text/csv",
            )
            st.info("Go to the **Deploy** tab to publish these links.")

# ── Tab 3: All Mappings ──────────────────────────────────────────────────────
with tab3:
    all_df = load_all_mappings(conn)

    if all_df.empty:
        st.info("No mappings yet. Use the Single URL or Bulk CSV tabs to get started.")
    else:
        st.write(f"**{len(all_df)} total mappings**")
        st.dataframe(all_df, use_container_width=True)

        csv_all = all_df.to_csv(index=False).encode()
        st.download_button(
            label="⬇️ Download All Mappings as CSV",
            data=csv_all,
            file_name="all_kiddom_mappings.csv",
            mime="text/csv",
        )

# ── Tab 4: Deploy ────────────────────────────────────────────────────────────
with tab4:
    st.subheader("Deploy Redirect Pages")
    st.write(
        "Export your URL mappings as `urls.json`, commit it to the repo, "
        "and the GitHub Action will automatically generate and deploy the redirect pages."
    )

    all_df = load_all_mappings(conn)

    if all_df.empty:
        st.info("No mappings to deploy yet.")
    else:
        records = all_df[["short_code", "original_url"]].to_dict(orient="records")
        json_bytes = json.dumps(records, indent=2).encode()

        st.download_button(
            label="⬇️ Download urls.json",
            data=json_bytes,
            file_name="urls.json",
            mime="application/json",
        )

        st.markdown("**After downloading:**")
        st.code(
            "# 1. Move urls.json to the data/ folder in the repo\n"
            "# 2. Commit and push:\n"
            "git add data/urls.json\n"
            'git commit -m "Update URL mappings"\n'
            "git push\n\n"
            "# GitHub Action deploys redirect pages automatically (~2 min)",
            language="bash",
        )

        st.markdown("---")
        st.caption(
            "**Coming soon:** When connected to Snowflake, this will trigger deployment automatically."
        )

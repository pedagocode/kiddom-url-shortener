import hashlib
import sqlite3
import io
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
    return pd.read_sql("SELECT short_code, original_url, created_at FROM url_mappings ORDER BY created_at DESC", conn)


st.set_page_config(page_title="Kiddom URL Shortener", page_icon="🔗", layout="centered")
st.title("🔗 Kiddom URL Shortener")
st.caption("Generate branded short codes for Kiddom content links.")

conn = get_conn()

tab1, tab2, tab3 = st.tabs(["Single URL", "Bulk CSV", "View All Mappings"])

# ── Tab 1: Single URL ────────────────────────────────────────────────────────
with tab1:
    url_input = st.text_input("Enter a URL to shorten", placeholder="https://app.kiddom.co/...")

    if st.button("Shorten", type="primary", key="single"):
        url = url_input.strip()
        if not url:
            st.warning("Please enter a URL.")
        elif not url.startswith(("http://", "https://")):
            st.error("URL must start with http:// or https://")
        else:
            code = make_short_code(url)
            save_mapping(conn, code, url)
            st.success("Short code generated!")
            st.code(code, language=None)
            st.caption(f"Original: {url}")

# ── Tab 2: Bulk CSV ──────────────────────────────────────────────────────────
with tab2:
    uploaded = st.file_uploader("Upload a CSV file", type="csv")

    if uploaded:
        df = pd.read_csv(uploaded)
        st.write("**Preview** (first 5 rows)")
        st.dataframe(df.head(), use_container_width=True)

        url_col = st.selectbox("Which column contains the URLs?", options=df.columns.tolist())

        if st.button("Generate Short Codes", type="primary", key="bulk"):
            invalid = df[url_col].dropna().apply(
                lambda u: not str(u).strip().startswith(("http://", "https://"))
            )
            if invalid.any():
                st.warning(f"{invalid.sum()} row(s) skipped — values don't look like URLs.")

            codes = []
            for raw in df[url_col]:
                if pd.isna(raw) or not str(raw).strip().startswith(("http://", "https://")):
                    codes.append("")
                else:
                    url = str(raw).strip()
                    code = make_short_code(url)
                    save_mapping(conn, code, url)
                    codes.append(code)

            df["short_url"] = codes
            st.success(f"Generated {sum(1 for c in codes if c)} short codes.")
            st.dataframe(df, use_container_width=True)

            csv_bytes = df.to_csv(index=False).encode()
            st.download_button(
                label="⬇️ Download Updated CSV",
                data=csv_bytes,
                file_name="urls_with_short_codes.csv",
                mime="text/csv",
            )

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
            label="⬇️ Download All Mappings",
            data=csv_all,
            file_name="all_kiddom_mappings.csv",
            mime="text/csv",
        )

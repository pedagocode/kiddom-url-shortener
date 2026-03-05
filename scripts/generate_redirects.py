"""
Reads data/urls.json and generates a static HTML redirect page for each mapping.
Output goes to redirect-site/{short_code}/index.html.

Swap TODO below with Snowflake query when credentials are available.
"""

import json
import os
import html

# ── Load mappings ─────────────────────────────────────────────────────────────
# TODO (Snowflake): Replace this block with:
#   import snowflake.connector
#   conn = snowflake.connector.connect(
#       account=os.environ["SNOWFLAKE_ACCOUNT"],
#       user=os.environ["SNOWFLAKE_USER"],
#       password=os.environ["SNOWFLAKE_PASSWORD"],
#       database="KIDDOM_TOOLS",
#       schema="URL_SHORTENER",
#       warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
#   )
#   cur = conn.cursor()
#   cur.execute("SELECT short_code, original_url FROM url_mappings WHERE revoked_at IS NULL")
#   mappings = [{"short_code": row[0], "original_url": row[1]} for row in cur.fetchall()]

with open("data/urls.json") as f:
    mappings = json.load(f)

# ── Generate redirect pages ───────────────────────────────────────────────────
os.makedirs("redirect-site", exist_ok=True)

for entry in mappings:
    code = entry["short_code"]
    original_url = entry["original_url"]
    safe_url = html.escape(original_url, quote=True)

    dir_path = os.path.join("redirect-site", code)
    os.makedirs(dir_path, exist_ok=True)

    with open(os.path.join(dir_path, "index.html"), "w") as f:
        f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="0; url={safe_url}">
  <title>Redirecting...</title>
  <style>
    body {{ font-family: sans-serif; display: flex; align-items: center;
           justify-content: center; height: 100vh; margin: 0; background: #f5f5f5; }}
    .box {{ text-align: center; color: #555; }}
    a {{ color: #4a90d9; }}
  </style>
</head>
<body>
  <div class="box">
    <p>Redirecting you to Kiddom content&hellip;</p>
    <p><a href="{safe_url}">Click here if you are not redirected automatically.</a></p>
  </div>
</body>
</html>
""")

print(f"Generated {len(mappings)} redirect page(s).")

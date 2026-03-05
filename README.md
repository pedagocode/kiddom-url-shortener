# Kiddom URL Shortener

A Streamlit app for generating branded short links for Kiddom content URLs. Short links are deployed as static redirect pages via GitHub Pages.

---

## How It Works

1. Paste a Kiddom URL (or load a Google Sheet of URLs)
2. Click **Shorten** — the app generates a `kiddom-xxxxxx` short code and saves it to `data/urls.json`
3. A GitHub Action automatically builds static redirect pages and deploys them to GitHub Pages
4. The short link is live within ~2 minutes

### Link format

| Setup | Short link format |
|-------|-------------------|
| Default (no custom domain) | `https://pedagocode.github.io/kiddom-url-shortener/kiddom-xxxxxx` |
| With `links.kiddom.co` CNAME | `https://links.kiddom.co/kiddom-xxxxxx` |

> The custom domain removes the `/kiddom-url-shortener/` path segment automatically.
> Once IT sets up the DNS CNAME, all links shorten to `links.kiddom.co/kiddom-xxxxxx`.

---

## Features

- **Single URL** — paste one URL, get one short link instantly
- **Google Sheet** — load a sheet, generate short codes for all URLs, download updated CSV
- **URL allowlist** — only `*.kiddom.co` and `*.amazonaws.com` URLs are accepted
- **Deterministic codes** — the same URL always produces the same short code (no duplicates)
- **Branded links** — every short code starts with `kiddom-`

---

## Setup

### 1. GitHub Personal Access Token

Required for the app to write to `data/urls.json` and trigger deployments.

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens) → **Generate new token (classic)**
2. Select scope: **`repo`**
3. Add to Streamlit secrets:

```toml
GITHUB_TOKEN = "ghp_your_token_here"
```

### 2. Enable GitHub Pages

In the repo: **Settings → Pages → Source → GitHub Actions**

This only needs to be done once. After that, every push to `data/urls.json` triggers an automatic deploy.

### 3. Custom Domain (optional, recommended)

Ask IT to add one DNS record:

```
CNAME  links.kiddom.co  ->  pedagocode.github.io
```

Then in the repo: **Settings → Pages → Custom domain** → enter `links.kiddom.co`

GitHub will provision an SSL certificate automatically. Once live, short links will be:
```
https://links.kiddom.co/kiddom-xxxxxx
```

Also update `PAGES_BASE` in `Toolbox/url_shortener.py`:
```python
PAGES_BASE = "https://links.kiddom.co"
```

---

## Running Locally

```bash
cd Toolbox
pip install -r requirements.txt
streamlit run url_shortener.py
```

> Note: The app requires a valid `GITHUB_TOKEN` in `.streamlit/secrets.toml` to function locally.

---

## Project Structure

```
Toolbox/
  url_shortener.py       # Streamlit app
  requirements.txt
data/
  urls.json              # URL mapping store (auto-updated by app)
scripts/
  generate_redirects.py  # Builds static HTML redirect pages
redirect-site/
  404.html               # Shown for expired or invalid links
.github/workflows/
  deploy-redirects.yml   # Auto-deploys on urls.json change
```

---

## Future Improvements

- Connect to Snowflake for enterprise-grade storage and access control
- Gate app access via Snowflake OAuth (Kiddom staff only)
- Link revocation and expiration
- Analytics on link clicks

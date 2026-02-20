# Kernel Fusion & CuTe DSL — Daily Research Digest

Automated daily email digest of recent research papers on kernel fusion, CuTe DSL, CUTLASS, and automated kernel writing for GPUs.

## How It Works

1. **Searches** arXiv and Semantic Scholar for recent papers using targeted queries
2. **Deduplicates** and scores results by keyword relevance
3. **Formats** a clean HTML email with the top 15 papers
4. **Sends** via Gmail API using OAuth2 refresh token
5. **Runs daily** at 7:00 AM Pacific via GitHub Actions cron

## Setup

### 1. Gmail OAuth Credentials

You need a Google Cloud project with Gmail API enabled and OAuth2 credentials:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or use an existing one)
3. Enable the **Gmail API**
4. Create **OAuth 2.0 Client ID** (Desktop app type)
5. Note the `Client ID` and `Client Secret`
6. Generate a refresh token by completing the OAuth flow with scope `https://www.googleapis.com/auth/gmail.send`

### 2. GitHub Secrets

Add these secrets to your repo (`Settings → Secrets and variables → Actions`):

| Secret | Description |
|--------|-------------|
| `GMAIL_CLIENT_ID` | Google OAuth Client ID |
| `GMAIL_CLIENT_SECRET` | Google OAuth Client Secret |
| `GMAIL_REFRESH_TOKEN` | Gmail OAuth Refresh Token |
| `RECIPIENT_EMAIL` | Email address to receive digests |

### 3. Manual Trigger

You can trigger the digest manually from the **Actions** tab → **Daily Kernel Fusion Research Digest** → **Run workflow**.

## Local Development

```bash
# Dry run (saves HTML preview instead of sending)
DRY_RUN=1 python digest.py

# Full run (requires env vars set)
GMAIL_CLIENT_ID=... GMAIL_CLIENT_SECRET=... GMAIL_REFRESH_TOKEN=... python digest.py
```

## Configuration

Edit these in `digest.py`:
- `ARXIV_QUERIES` — arXiv search queries
- `SEMANTIC_SCHOLAR_QUERIES` — Semantic Scholar search queries
- `LOOKBACK_DAYS` — How many days back to search (default: 3)

## Research Topics Covered

- Kernel fusion (horizontal/epilogue and vertical/pipeline)
- CuTe DSL & CUTLASS 4.x
- Automated/agentic kernel generation (LLM-driven)
- Tensor compilers and autotuning
- GPU architecture-specific optimizations (Hopper, Blackwell)
- Triton and related DSLs

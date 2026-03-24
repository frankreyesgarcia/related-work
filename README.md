# research-digest

Automated academic paper search and summarization tool. Searches arXiv and Semantic Scholar daily, generates structured FAT summaries using [OpenCode](https://opencode.ai) free models, and sends a digest via email.

## Quick Start

```bash
# 1. Install dependencies
bash setup.sh

# 2. Authenticate with OpenCode Zen (free)
opencode auth login
# → Select "OpenCode Zen" → create account at opencode.ai → paste API key

# 3. Configure your topic and email
nano config.yaml   # set topic and email.to
nano .env          # set SMTP credentials

# 4. Run the pipeline
./run.sh --dry-run   # test without sending email
./run.sh             # full run with email
```

## Config Reference (`config.yaml`)

| Key | Description | Default |
|-----|-------------|---------|
| `topic` | Search query for papers | `"large language models reasoning"` |
| `sources` | `[arxiv, semantic_scholar]` | both |
| `max_papers` | Max papers per run | `10` |
| `arxiv_categories` | arXiv category filters | `[cs.AI, cs.CL]` |
| `opencode_model` | Model for summarization | `opencode/minimax-2.5-free` |
| `semantic_scholar_api_key` | Optional free API key | `""` |
| `email.to` | Recipient address | — |

## Free OpenCode Zen Models

| Model | Speed | Quality |
|-------|-------|---------|
| `opencode/minimax-2.5-free` | Fast | Good (default) |
| `opencode/mimo-v2-pro-free` | Medium | Better |
| `opencode/mimo-v2-omni-free` | Medium | Better |
| `opencode/nemotron-3-super-free` | Slow | Best |

Get a free API key at [opencode.ai](https://opencode.ai).

## Output Structure

```
summaries/
├── papers_2025-01-15.json              ← raw search results
├── 2025-01-15_01_Attention_Is_All_.md  ← individual summary (paper title as H1)
├── 2025-01-15_02_Chain_of_Thought_.md
└── ...
digests/
└── digest_2025-01-15.md               ← full daily digest
logs/
└── run_2025-01-15.log
```

Each summary file follows the **FAT method** (Martin Monperrus):
- **F — Facts**: Research Goal, Main Results, Main Takeaway
- **A — Appreciation**: Strengths, Limitations, Novelty, Overall assessment
- **T — Ties**: Applicability, Inspired ideas

## Running Options

### Local (cron)

```bash
# Add to crontab: crontab -e
0 8 * * * cd /path/to/research-digest && ./run.sh >> logs/cron.log 2>&1
```

### GitHub Actions (recommended — no PC needed)

Push to GitHub and add 3 repository secrets (`Settings → Secrets → Actions`):

| Secret | Value |
|--------|-------|
| `OPENCODE_API_KEY` | Your OpenCode Zen API key |
| `SMTP_USER` | Your email address |
| `SMTP_PASS` | App password (Gmail: generate at myaccount.google.com) |

The workflow runs automatically every day at 8am UTC and commits digests back to the repo.

You can also trigger it manually from `Actions → Daily Research Digest → Run workflow`.

## SMTP Setup (Gmail)

1. Enable 2FA on your Google account
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Create an app password for "Mail"
4. Use it as `SMTP_PASS` in `.env` or GitHub secrets

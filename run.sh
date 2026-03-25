#!/bin/bash
# Master script — run manually or via cron/GitHub Actions
# Usage: ./run.sh [--dry-run] [--no-search] [--no-summarize]

set -e
cd "$(dirname "$0")"

DRY_RUN=false
NO_SEARCH=false
NO_SUMMARIZE=false

for arg in "$@"; do
  case "$arg" in
    --dry-run)      DRY_RUN=true ;;
    --no-search)    NO_SEARCH=true ;;
    --no-summarize) NO_SUMMARIZE=true ;;
  esac
done

DATE=$(date +%Y-%m-%d)
mkdir -p logs
LOG_FILE="logs/run_${DATE}.log"

log() {
  echo "$1" | tee -a "$LOG_FILE"
}

log "$(date) — Starting research digest"
log "  dry-run=${DRY_RUN}  no-search=${NO_SEARCH}  no-summarize=${NO_SUMMARIZE}"

# Load .env if present
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Step 1: Search papers
if [ "$NO_SEARCH" = false ]; then
  log "Searching for papers..."
  python3 scripts/search.py 2>&1 | tee -a "$LOG_FILE"
else
  log "Skipping search (--no-search)"
fi

# Step 2: Summarize papers
if [ "$NO_SUMMARIZE" = false ]; then
  log "Generating summaries..."
  python3 scripts/summarize.py 2>&1 | tee -a "$LOG_FILE"
else
  log "Skipping summarize (--no-summarize)"
fi

# Step 3: Send email digest
if [ "$DRY_RUN" = false ]; then
  log "Sending email digest..."
  python3 scripts/email_digest.py 2>&1 | tee -a "$LOG_FILE"
else
  log "Skipping email (--dry-run). Building digest file only..."
  python3 -c "
import sys
sys.path.insert(0, 'scripts')
from email_digest import build_digest
from datetime import datetime
digest, count = build_digest(datetime.now().strftime('%Y-%m-%d'))
print(f'  Digest built: {count} summaries')
" 2>&1 | tee -a "$LOG_FILE"
fi

log "Completed at $(date)"

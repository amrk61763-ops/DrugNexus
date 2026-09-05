#!/usr/bin/env bash
# Rewrite repository history to remove selected authors and push the result.
# Usage: bash remove-authors.sh [--yes]

set -euo pipefail

REPO_URL="https://github.com/amrk61763-ops/DrugNexus.git"
REMOVE_NAMES=( "v0" "qwen.ai[bot]" )
REMOVE_EMAILS=( "it+v0agent@vercel.com" "qwenlm-intl@service.alibaba.com" )

AUTO_YES=0
if [[ "${1-}" == "--yes" || "${1-}" == "-y" ]]; then
  AUTO_YES=1
fi

command -v git >/dev/null || { echo "git is required." >&2; exit 1; }
command -v python3 >/dev/null || { echo "python3 is required." >&2; exit 1; }
command -v git-filter-repo >/dev/null || {
  echo "git-filter-repo is required. Install it with: pip3 install --user git-filter-repo" >&2
  exit 1
}

WORKDIR="$(mktemp -d /tmp/drugnexus-clean-XXXX)"
CALLBACK_FILE=""
trap '[[ -z "$CALLBACK_FILE" ]] || rm -f "$CALLBACK_FILE"' EXIT

echo "Mirror-cloning $REPO_URL into $WORKDIR"
git clone --mirror "$REPO_URL" "$WORKDIR/DrugNexus.git"
cd "$WORKDIR/DrugNexus.git"

BACKUP_DIR="$HOME/drugnexus-backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/DrugNexus-mirror-backup-$(date +%F-%H%M%S).tgz"
tar -czf "$BACKUP_FILE" .
echo "Backup: $BACKUP_FILE"

names_py=""
for name in "${REMOVE_NAMES[@]}"; do
  names_py+="b\"${name}\", "
done
emails_py=""
for email in "${REMOVE_EMAILS[@]}"; do
  emails_py+="b\"${email}\", "
done

CALLBACK_FILE="$(mktemp /tmp/gfr-remove-authors-XXXX.py)"
cat > "$CALLBACK_FILE" <<'PY'
TARGET_NAMES = { NAMES_PLACEHOLDER }
TARGET_EMAILS = { EMAILS_PLACEHOLDER }

def commit_callback(commit):
    if (commit.author_name in TARGET_NAMES or
            commit.committer_name in TARGET_NAMES or
            commit.author_email in TARGET_EMAILS or
            commit.committer_email in TARGET_EMAILS):
        commit.skip()
PY
sed -i "s/NAMES_PLACEHOLDER/$names_py/; s/EMAILS_PLACEHOLDER/$emails_py/" "$CALLBACK_FILE"
python3 -m py_compile "$CALLBACK_FILE"

echo "Commits matching the configured authors:"
git --no-pager log --all --format='%h %an <%ae> | %cn <%ce> | %s' |
  grep -E 'v0|qwen\.ai\[bot\]|it\+v0agent@vercel\.com|qwenlm-intl@service\.alibaba\.com' || true
echo

if [[ "$AUTO_YES" -eq 0 ]]; then
  read -r -p "Type YES to rewrite history and force-push: " confirmation
  if [[ "$confirmation" != "YES" ]]; then
    echo "Aborted. No changes were pushed."
    exit 0
  fi
fi

git filter-repo --force --commit-callback "exec(open('$CALLBACK_FILE').read())"
git push --force --all origin
git push --force --tags origin

echo "Done. Rewritten history pushed. Backup: $BACKUP_FILE"

#!/bin/bash
# Git snapshot management for config versioning
# Usage: ./scripts/git_snapshot.sh [commit|auto]

PROJECT_ROOT="/Users/onur/levibot"
SNAPSHOT_DIR="${PROJECT_ROOT}/ops/config-snapshots"

cd "$PROJECT_ROOT" || exit 1

commit_snapshots() {
  local message="${1:-Config snapshot}"
  
  echo "📦 Committing config snapshots..."
  
  # Check if there are changes
  if ! git diff --quiet ops/config-snapshots/ 2>/dev/null; then
    git add ops/config-snapshots/
    git commit -m "📸 $message" -m "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "✅ Snapshots committed"
  else
    echo "ℹ️  No changes to commit"
  fi
}

auto_snapshot() {
  echo "🔄 Auto snapshot..."
  
  # Take new snapshot
  python3 scripts/snapshot_flags.py
  
  # Commit if there are new snapshots
  commit_snapshots "Automated config snapshot"
}

ACTION="${1:-auto}"

case "$ACTION" in
  commit)
    commit_snapshots "$2"
    ;;
  auto)
    auto_snapshot
    ;;
  *)
    echo "Usage: $0 [commit|auto] [message]"
    echo ""
    echo "Commands:"
    echo "  commit  - Commit existing snapshots to git"
    echo "  auto    - Take snapshot and commit"
    exit 1
    ;;
esac


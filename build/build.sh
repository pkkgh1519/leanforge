#!/usr/bin/env bash
# build.sh — regenerate both platform plugins from the single canonical source.
#
#   src/skills/        canonical, platform-neutral skills (single source of truth)
#   platform/claude/   claude-only frontmatter values + plugin.json + LICENSE
#   platform/codex/    codex-only openai.yaml + plugin.json + LICENSE
#   README.md          repo-root README (+ README_KO.md) — GitHub landing only, NOT bundled into plugins
#   claude/            generated Claude plugin   (committed; Claude installs this)
#   codex/plugin/      generated Codex plugin    (committed; Codex installs this)
#
# Root marketplace manifests (.claude-plugin/marketplace.json, .agents/plugins/
# marketplace.json) are committed repo files, not build outputs.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/src/skills"
PLAT="$ROOT/platform"

# Per-skill allowed-tools for the Claude build. These skills perform file edits,
# shell validation, and/or subagent dispatch. bash 3.2 — no assoc arrays.
claude_tools() {
  case "$1" in
    migration|ready|go|harness) echo "Read, Edit, Write, Bash, Grep, Glob, Agent, AskUserQuestion" ;;
  esac
}

# ── Claude → ./claude ───────────────────────────────────────────────────────
echo "=== build: claude ==="
rm -rf "$ROOT/claude"
mkdir -p "$ROOT/claude/.claude-plugin"
cp -R "$SRC" "$ROOT/claude/skills"
for s in ready go migration harness; do
  INJECT=$'disable-model-invocation: true\nallowed-tools: '"$(claude_tools "$s")" \
    perl -0777 -i -pe 'BEGIN{$j=$ENV{INJECT}} s/\A(---\r?\n.*?\r?\n)---\r?\n/$1$j\n---\n/s' \
    "$ROOT/claude/skills/$s/SKILL.md"
done
cp "$PLAT/claude/plugin.json" "$ROOT/claude/.claude-plugin/plugin.json"
cp "$PLAT/claude/LICENSE" "$ROOT/claude/"

# ── Codex → ./codex/plugin ──────────────────────────────────────────────────
echo "=== build: codex ==="
rm -rf "$ROOT/codex"
mkdir -p "$ROOT/codex/plugin/.codex-plugin"
cp -R "$SRC" "$ROOT/codex/plugin/skills"
cp -R "$PLAT/codex/skills/." "$ROOT/codex/plugin/skills/"   # agents/openai.yaml overlay
cp "$PLAT/codex/plugin.json" "$ROOT/codex/plugin/.codex-plugin/plugin.json"
cp "$PLAT/codex/LICENSE" "$ROOT/codex/plugin/"

find "$ROOT/claude" "$ROOT/codex" -name ".DS_Store" -delete 2>/dev/null || true
find "$ROOT/claude" "$ROOT/codex" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true

# ── consistency guard ───────────────────────────────────────────────────────
# Assert the release version invariant: all 4 plugin.json carry the same version
# AND it matches the CHANGELOG top entry. Catches the manual-edit skew at build
# time instead of leaving it for a human (or another agent) to spot.
# (git tagging belongs to the release flow — kept out here so build stays git-free.)
pj_ver() { perl -ne 'if(/"version"\s*:\s*"([^"]+)"/){print $1; last}' "$1"; }
VERS="$(pj_ver "$PLAT/claude/plugin.json")
$(pj_ver "$PLAT/codex/plugin.json")
$(pj_ver "$ROOT/claude/.claude-plugin/plugin.json")
$(pj_ver "$ROOT/codex/plugin/.codex-plugin/plugin.json")"
UNIQ="$(printf '%s\n' "$VERS" | sort -u)"
if [ "$(printf '%s\n' "$UNIQ" | grep -c .)" -ne 1 ]; then
  echo "✗ version mismatch across plugin.json:" >&2
  printf '%s\n' "$VERS" >&2
  exit 1
fi
CL_VER="$(perl -ne 'if(/^##\s+v([0-9][^\s(]*)/){print $1; last}' "$ROOT/CHANGELOG.md")"
if [ "$UNIQ" != "$CL_VER" ]; then
  echo "✗ plugin.json=v$UNIQ but CHANGELOG top=v$CL_VER" >&2
  exit 1
fi
echo "✓ version OK: v$UNIQ (4 manifests + CHANGELOG)"

# ── duplicate-reference parity guard ────────────────────────────────────────
# Three reference files are intentionally shared across skills. A skill bundles
# only its own references/, so each consumer keeps a physical copy — and a
# one-sided edit is silent drift. Assert byte-parity on the canonical source so
# the build fails fast instead of shipping two diverging copies.
#   harness-format.md     go ↔ migration
#   harness-review.md     go ↔ migration
#   foundation-format.md  go ↔ ready
parity_check() {
  if ! cmp -s "$1" "$2"; then
    echo "✗ reference drift (shared files must stay byte-identical):" >&2
    echo "    $1" >&2
    echo "    $2" >&2
    exit 1
  fi
}
parity_check "$SRC/go/references/harness-format.md"    "$SRC/migration/references/harness-format.md"
parity_check "$SRC/go/references/harness-review.md"    "$SRC/migration/references/harness-review.md"
parity_check "$SRC/go/references/foundation-format.md" "$SRC/ready/references/foundation-format.md"
echo "✓ reference parity OK: 3 shared references identical across skills"

echo "=== done → ./claude  ./codex/plugin ==="

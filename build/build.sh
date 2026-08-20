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
# shell validation, and/or subagent dispatch. Run additionally gets SendMessage for
# the bounded NEEDS_CONTEXT/BLOCKED implementer continuation. bash 3.2 — no assoc arrays.
claude_tools() {
  case "$1" in
    set|prime) echo "Read, Edit, Write, Bash, Grep, Glob, Agent, AskUserQuestion" ;;
    run|run-tdd) echo "Read, Edit, Write, Bash, Grep, Glob, Agent, SendMessage, AskUserQuestion" ;;
  esac
}

# ── Claude → ./claude ───────────────────────────────────────────────────────
echo "=== build: claude ==="
rm -rf "$ROOT/claude"
mkdir -p "$ROOT/claude/.claude-plugin"
cp -R "$SRC" "$ROOT/claude/skills"
for s in prime run set run-tdd; do
  perl -0777 -i -pe 's/\r\n/\n/g' "$ROOT/claude/skills/$s/SKILL.md"
  INJECT=$'disable-model-invocation: true\nallowed-tools: '"$(claude_tools "$s")" \
    perl -0777 -i -pe 'BEGIN{$j=$ENV{INJECT}} s/\A(---\r?\n.*?\r?\n)---\r?\n/$1$j\n---\n/s or die "failed to inject Claude frontmatter\n"' \
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
perl -0777 -i -pe 's/\r\n?/\n/g' "$ROOT/codex/plugin/skills/run/agents/openai.yaml"
cp "$PLAT/codex/plugin.json" "$ROOT/codex/plugin/.codex-plugin/plugin.json"
cp "$PLAT/codex/LICENSE" "$ROOT/codex/plugin/"

find "$ROOT/claude" "$ROOT/codex" -name ".DS_Store" -delete 2>/dev/null || true
find "$ROOT/claude" "$ROOT/codex" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true

# ── consistency guard ───────────────────────────────────────────────────────
# Assert one release version across documentation, changelog, canonical manifests,
# and generated manifests. This remains Git-free so source archives can build too.
readme_versions() {
  perl -ne '
    if ($in_fence) {
      if (/^ {0,3}(`+|~+)[ \t]*$/) {
        my $closing_fence = $1;
        if (substr($closing_fence, 0, 1) eq $fence_char
            && length($closing_fence) >= $fence_length) {
          $in_fence = 0;
        }
      }
      next;
    }
    if ($in_comment) {
      $in_comment = 0 if /-->/;
      next;
    }
    if (/^ {0,3}(`{3,}|~{3,})/) {
      $in_fence = 1;
      $fence_char = substr($1, 0, 1);
      $fence_length = length($1);
      next;
    }
    if (/<!--/) {
      $in_comment = 1 unless /<!--.*-->/;
      next;
    }
    if (!$found_heading) {
      next unless /^#{1,6}\s+/;
      $found_heading = 1;
      if (/^# Leanforge v([0-9]+(?:\.[0-9]+)*)\s*$/) {
        print "$1\n";
        next;
      }
      last;
    }
    if (/^# Leanforge v([0-9]+(?:\.[0-9]+)*)\s*$/) {
      print "$1\n";
    }
  ' "$1"
}
changelog_versions() {
  perl -ne '
    if (!$found_title) {
      next unless /^#\s+Changelog\s*$/;
      $found_title = 1;
      next;
    }
    next if /^\s*$/;
    if (/^##\s+v([0-9]+(?:\.[0-9]+)*)\s+\([^)]*\)\s*$/) {
      print "$1\n";
      next;
    }
    last;
  ' "$1"
}
pj_versions() {
  perl -0777 -ne '
    sub json_string {
      my ($text, $start) = @_;
      my ($value, $i) = ("", $start + 1);
      while ($i < length($text)) {
        my $char = substr($text, $i, 1);
        if ($char eq "\\") {
          $value .= substr($text, $i, 2);
          $i += 2;
          next;
        }
        return ($value, $i + 1) if $char eq q{"};
        $value .= $char;
        $i++;
      }
      return ($value, $i);
    }

    my ($depth, $i, $length) = (0, 0, length($_));
    while ($i < $length) {
      my $char = substr($_, $i, 1);
      if ($char eq q{"}) {
        my ($token, $next) = json_string($_, $i);
        if ($depth == 1 && $token eq "version") {
          my $value_start = $next;
          $value_start++ while substr($_, $value_start, 1) =~ /\s/;
          if (substr($_, $value_start, 1) eq ":") {
            $value_start++;
            $value_start++ while substr($_, $value_start, 1) =~ /\s/;
            if (substr($_, $value_start, 1) eq q{"}) {
              my ($version) = json_string($_, $value_start);
              print "$version\n" if $version =~ /^[0-9]+(?:\.[0-9]+)*$/;
            }
          }
        }
        $i = $next;
        next;
      }
      $depth++ if $char eq "{" || $char eq "[";
      $depth-- if $char eq "}" || $char eq "]";
      $i++;
    }
  ' "$1"
}

VERSION_LABELS=(
  "README.md"
  "README_KO.md"
  "CHANGELOG.md"
  "platform/claude/plugin.json"
  "platform/codex/plugin.json"
  "claude/.claude-plugin/plugin.json"
  "codex/plugin/.codex-plugin/plugin.json"
)
VERSION_KINDS=(
  "readme"
  "readme"
  "changelog"
  "manifest"
  "manifest"
  "manifest"
  "manifest"
)
VERSION_PATHS=(
  "$ROOT/README.md"
  "$ROOT/README_KO.md"
  "$ROOT/CHANGELOG.md"
  "$PLAT/claude/plugin.json"
  "$PLAT/codex/plugin.json"
  "$ROOT/claude/.claude-plugin/plugin.json"
  "$ROOT/codex/plugin/.codex-plugin/plugin.json"
)

VERSION_VALUES=()
VERSION_ERRORS=0
for i in "${!VERSION_LABELS[@]}"; do
  case "${VERSION_KINDS[$i]}" in
    readme) MATCHES="$(readme_versions "${VERSION_PATHS[$i]}")" ;;
    changelog) MATCHES="$(changelog_versions "${VERSION_PATHS[$i]}")" ;;
    manifest) MATCHES="$(pj_versions "${VERSION_PATHS[$i]}")" ;;
  esac

  MATCH_COUNT=0
  MATCH_VALUE=""
  while IFS= read -r version; do
    [ -n "$version" ] || continue
    MATCH_COUNT=$((MATCH_COUNT + 1))
    MATCH_VALUE="$version"
  done <<EOF
$MATCHES
EOF

  if [ "$MATCH_COUNT" -eq 0 ]; then
    echo "✗ release version missing: ${VERSION_LABELS[$i]}" >&2
    VERSION_ERRORS=1
  elif [ "$MATCH_COUNT" -gt 1 ]; then
    echo "✗ release version ambiguous: ${VERSION_LABELS[$i]} ($MATCH_COUNT matching labels)" >&2
    printf '%s\n' "$MATCHES" | sed '/^$/d; s/^/    v/' >&2
    VERSION_ERRORS=1
  else
    VERSION_VALUES[$i]="$MATCH_VALUE"
  fi
done
if [ "$VERSION_ERRORS" -ne 0 ]; then
  exit 1
fi

UNIQ="$(printf '%s\n' "${VERSION_VALUES[@]}" | sort -u)"
if [ "$(printf '%s\n' "$UNIQ" | grep -c .)" -ne 1 ]; then
  echo "✗ release version mismatch; invariant requires one identical version across:" >&2
  for i in "${!VERSION_LABELS[@]}"; do
    printf '    %s: v%s\n' "${VERSION_LABELS[$i]}" "${VERSION_VALUES[$i]}" >&2
  done
  exit 1
fi
echo "✓ version OK: v$UNIQ (README titles + CHANGELOG + 4 manifests)"

# ── duplicate-reference parity guard ────────────────────────────────────────
# Three reference files are intentionally shared across skills. A skill bundles
# only its own references/, so each consumer keeps a physical copy — and a
# one-sided edit is silent drift. Assert byte-parity on the canonical source so
# the build fails fast instead of shipping two diverging copies.
#   harness-format.md     run ↔ set
#   harness-review.md     run ↔ set
#   foundation-format.md  run ↔ prime
parity_check() {
  if ! cmp -s "$1" "$2"; then
    echo "✗ reference drift (shared files must stay byte-identical):" >&2
    echo "    $1" >&2
    echo "    $2" >&2
    exit 1
  fi
}
parity_check "$SRC/run/references/harness-format.md"    "$SRC/set/references/harness-format.md"
parity_check "$SRC/run/references/harness-review.md"    "$SRC/set/references/harness-review.md"
parity_check "$SRC/run/references/foundation-format.md" "$SRC/prime/references/foundation-format.md"
echo "✓ reference parity OK: 3 shared references identical across skills"

echo "=== done → ./claude  ./codex/plugin ==="

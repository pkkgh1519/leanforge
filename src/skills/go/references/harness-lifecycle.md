# harness-lifecycle.md — go's harness create / update / archive (force-load)

The operational rules for go's harness step: detecting first-vs-delta, generating or updating the
harness, and archiving the 3-doc. Runs **after the completion gate, before the final review**.
Load alongside `harness-format.md` (the harness spec) — this file is the *process*, that one is the
*spec*.

## First-cycle vs delta — the `status.json` marker

`.dryforge/status.json` is a **local-only marker** (it lives inside the gitignored `.dryforge/`, so
it is not committed — local is by design). Its content is one fact: `{ "initialized": true }`. It is
written at the **successful finish** of a first cycle (after the user approves the harness — see
"Archiving" below) or by `migration` on completion.

- **Marker present (`initialized: true`)** → the harness already exists → this cycle is a **delta**.
- **Marker absent** → this cycle is **first-cycle** (create the harness).

This is the whole detection rule — simple on purpose. Consequences:

- **Pre-finish failure → first-cycle on retry.** If a first cycle fails *before* the marker is
  written (during harness generation, final review, the user gate, or archiving), the marker is
  absent, so a retry re-enters **first-cycle** and regenerates. The in-progress harness files from
  the failed run are unapproved, so overwriting them is correct. The 3-doc stays active (not yet
  archived), so the retry has its sources.
- **Safety guard against clobbering.** If first-cycle is detected (no marker) **but** a harness
  structure already exists on disk (a `CLAUDE.md` with dryforge structure + a populated `docs/`) —
  e.g. a fresh clone where the committed harness is present but the local marker isn't — do **not**
  blindly overwrite it. Stop and ask the user whether to treat it as an existing harness (delta) or
  regenerate. (escalate-don't-guess; never destroy a harness you didn't just generate.)



## Interrupted-run marker — `.dryforge/run.json`

`.dryforge/run.json` is a local-only interrupted-run marker. It is not a replacement for
`.dryforge/status.json`: `status.json` still means the harness was successfully initialized, while
`run.json` records that `go` started and may need recovery if the session stops before approval or
archive completion.

Minimal schema:

```json
{
  "schemaVersion": 1,
  "status": "in_progress",
  "cycle": "first|delta",
  "activeDocs": {
    "handoffSha256": "...",
    "specSha256": "...",
    "planSha256": "..."
  },
  "baseBranch": "...",
  "featureBranch": "...",
  "baseCommit": "...",
  "lastCompletedStep": "...",
  "pendingAction": "...",
  "updatedAt": "..."
}
```

Allowed statuses: `in_progress`, `awaiting_user_approval`, `archive_in_progress`, `completed`,
`abandoned`.

Preflight decision table:

| State | Meaning | Action |
|---|---|---|
| `status.json` present | Harness already initialized | Continue as delta. Ignore a stale completed `run.json`, or clean it up after normal checks. |
| `status.json absent + run.json present` | interrupted go run, not a first cycle | Verify active 3-doc hashes and git branch/commit facts, then ask whether to resume or abandon. |
| no `status.json`, no `run.json`, handoff has Project Foundation | normal first cycle | Continue with first-cycle execution. |
| no `status.json`, no `run.json`, existing harness on disk, no Project Foundation | marker-loss or invalid delta state | Stop and ask whether to run migration or perform a user-guaranteed marker repair. |
| no marker files and no Foundation | producer-side defect | Ask the user to regenerate with `ready`. |

`run.json` is a guardrail, not a source of truth. A mismatch between `run.json.activeDocs` and the
root active 3-doc is a stop-and-ask condition. A branch or commit mismatch is also a stop-and-ask
condition. Never use `run.json` alone to delete worktrees, reset branches, overwrite docs, or mark a
run complete.

Write `run.json` only at coarse milestones and write it atomically: write a temporary file in
`.dryforge/`, then rename it into place. This keeps the preflight cheap: file existence checks, JSON
parse, active 3-doc hashes, and a small git branch/HEAD check are enough. Do not scan the whole repo or
hash the whole `docs/` tree during preflight.
## 3-doc re-read (mandatory, both modes)

Before generating/updating, **re-read `.dryforge/{handoff,spec,plan}.md`.** By this point the session
context is code-biased (you just implemented); re-reading restores the design intent so the harness
reflects the *intended* project, not just the code as written.

## First cycle — create the whole harness

Sources, in priority: the handoff's **Project Foundation** (`foundation-format.md`) → spec (design
intent) → code (implementation fact). The Foundation's richness sets the harness's richness.

- **Foundation is a first-cycle invariant — fail-fast if absent.** `ready` always writes the
  Foundation in a first cycle (`foundation-format.md`, "First-cycle precondition"). So a first-cycle
  handoff with **no Foundation section** is a **precondition violation, not a degrade case** — do
  **not** guess a Foundation from spec + code. **Stop and ask the user to regenerate the 3-doc via
  `ready`** (escalate-don't-guess). This is a one-line precondition check, not a fallback mode.

Generate to `harness-format.md`:
1. If a CLAUDE.md exists, back it up to `.dryforge/backup/`, review it critically, propose the
   disposition to the user, and rewrite only approved content.
2. The whole `docs/` structure (all files).
3. CLAUDE.md / AGENTS.md (identical content).
4. A module AGENTS.md per implemented module.

Map the Foundation to files per `foundation-format.md` (domain → business-rules; technical →
architecture + security + standards + operations; identity → the CLAUDE.md overview; future scope →
status.md's "remaining"). Future-scope content with no code yet is correct, not a hallucination.

## Delta — update only the changed scope

1. **Read all current `docs/` files first** and treat them as the existing project constraint — this
   catches non-dryforge hand-edits (there is no separate change-tracking).
2. Identify this cycle's change scope from the **3-doc task scope + the code diff**.
3. Judge which `docs/` files are affected (`harness-format.md`, "which file to touch") — your
   reasoning decides, but reviewing every relevant file is the floor.
4. Apply a **scope-limited** update; leave content outside the change scope untouched (whether
   hand-edited or written by a prior dryforge run).
5. Where this cycle must change something that already holds different content **in scope** →
   **escalate to the user** (don't silently overwrite).
6. status.md every cycle; engineering-notes.md gets non-obvious facts found while implementing;
   decisions/ gets this cycle's trade-off decisions (only if they meet the criterion); findings.md
   updated on find/resolve.
7. A new module → create its AGENTS.md **and** update the navigation tree in CLAUDE.md / AGENTS.md.

**Delta is bidirectional.** Also verify this cycle's change hasn't invalidated an existing statement
elsewhere — updating stale content matters as much as adding new content.

## Archiving the 3-doc (after user approval)

After the user approves (final user gate), **move** the active 3-doc into `.dryforge/NNN/`: copy
`.dryforge/{handoff,spec,plan}.md` into the new `.dryforge/NNN/` (sequential number: highest existing
+ 1, e.g. `001`, `002`, …) **and then delete them from the `.dryforge/` root.** Archiving is a *move,
not a copy* — after it, the root holds **no active 3-doc** (only `NNN/` archives, `status.json`,
`backup/`). This matters: if the root copies are left, the next cycle's producer finds a stale
previous-cycle 3-doc at the root and has to disambiguate + overwrite it; moving leaves a clean root so
the next producer just writes a fresh 3-doc. Then write `.dryforge/status.json`
(`{ "initialized": true }`) if not already present — the marker for the next cycle. (First cycle: the
Foundation is archived with the handoff; from the next cycle the harness carries project context, so
no Foundation is produced.)



### Idempotent archive retry

Archive must be safe to retry after interruption. Treat this as an **idempotent archive retry**:

1. Compute hashes for the root active 3-doc: `.dryforge/handoff.md`, `.dryforge/spec.md`, and
   `.dryforge/plan.md`.
2. Set `run.json.status` to `archive_in_progress` before copying.
3. If the target archive directory does not exist, create it and copy the three files.
4. If the archive directory exists and all three archived files match the root active 3-doc hashes,
   continue; this is a retry of the same archive.
5. If the archive directory exists but is incomplete, fill only the missing files from the root active
   3-doc.
6. If an archived file exists but has a **hash mismatch** with the root active 3-doc, stop and ask the
   user. Do not overwrite it and do not choose a winner.
7. If the archive is complete but the root active 3-doc has already been removed and
   `archive complete but marker missing` is the only remaining inconsistency, write
   `.dryforge/status.json` and mark `run.json` completed.
8. Delete root active 3-doc files only after the archive is complete and hash-verified.
9. Write `.dryforge/status.json` only after the archive is complete. Then mark `run.json.status` as
   `completed` or remove the completed marker after recording the result.

A partial archive with missing root active 3-doc files and an incomplete archive is a blocker: preserve
all files and ask the user. Never force-delete worktrees or branches during archive recovery; worktree
cleanup still follows the ancestor checks in `orchestration.md`.
## Re-run after a fix

If the final review triggers a fix:
- **Code changed** → re-run the completion gate (the base SHA moved).
- **Harness changed** → re-run the harness review (lenses 3–4).
- **Both changed** → re-run both.

Do not approve/archive until the re-run is green.

## Out-of-scope review finding

If the final review surfaces a code/doc mismatch in a **document region outside this cycle's change
scope**, do **not** fix it this cycle — that would break scope-limited delta. Record it in
`docs/tracking/findings.md` (with *why it can't be resolved now*) and leave it for a later cycle or
manual handling.

## Universality guard

Stack-agnostic. What a module, a contract, or a representative flow is — and which `docs/` file a
change touches — is discovered from the project at runtime, never assumed.

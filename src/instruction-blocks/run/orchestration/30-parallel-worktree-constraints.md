
## Parallel wave — dispatch constraints (safety, non-negotiable; unordered)

- **Do not pass `isolation: worktree` to implementer dispatch** — omit isolation so the
  implementer runs in place, **pinned to the pre-created absolute worktree path**, and verify
  location with `git rev-parse --show-toplevel` at the subagent's start.
- **Create worktrees serially, under `.leanforge/worktrees/`.** Each task worktree lives at
  `.leanforge/worktrees/<task-id>` — inside the gitignored `.leanforge/`, so worktrees never sprawl into
  the project tree or get tracked, and cleanup stays contained. Concurrent `git worktree add` contends
  on `.git/config.lock` → create serially. **Worktree pool:** after live-capacity admission, create or
  grow the pool only to the current `batch_size`; never provision work that cannot be dispatched. If
  capacity later grows, grow lazily. Between waves, reuse only a clean pooled worktree whose prior work
  safely landed. After the prior wave's gate/fix is green, serialize base writes through the next
  handoff and pin the current base-tip SHA. Before assigning the worktree to another task, require an
  empty `git status --porcelain`; capture its current HEAD with `git rev-parse HEAD`, require it to equal
  the previously verified `<prior-task-tip>` from the merge gate, and prove that tip landed with
  `git merge-base --is-ancestor <prior-task-tip> <current-base-tip>`, and require that the new task
  branch name is absent. Then create and switch to it from the pinned tip with
  `git checkout -b <new-task-branch> <current-base-tip>`. Immediately before dispatch, confirm the base
  ref still resolves to `<current-base-tip>`; any failed check or mismatch blocks and preserves the
  worktree, and never force-reset or overwrite it. Defer removal until after the completion gate
  passes; then clean up all eligible successful worktrees and merged task branches in one batch (not
  per-wave), after proving each landed commit is an ancestor of the base. Remove dependency-share
  symlinks, safe-remove each eligible worktree without `--force`, then delete its merged task branch
  with `git branch -d`. Preserve dirty, failed, ambiguous, stale-base, or branch-collision worktrees and
  branches as reported diagnostic recovery state. Remove the now-empty `.leanforge/worktrees/`
  directory and task scratch/temp dirs only when no diagnostic recovery state remains. **Leave no
  disposable litter** — in that case, once the run finishes (3-doc moved into `NNN/` at archiving),
  `.leanforge/` holds only `NNN/` archives, `status.json`, and `backup/` (the active 3-doc lives at the
  root only between the producer writing it and archiving). This avoids repeated create/remove cycles
  and a cluttered `.leanforge/`.
- **Task worktrees do not contain the 3-doc.** `.leanforge/` is gitignored, so a freshly-added task
  worktree has **no** `spec.md` / `plan.md` / `handoff.md`. Pass every spec slice, task contract,
  and hard gate **inline in the subagent prompt**.
- **Verify the work before merging (objective, not existence-only)** — the task branch must be
  strictly *ahead* of the base (`git rev-list base..task` non-empty) AND its diff non-empty and
  touching declared targets — checked with **three-dot** diff (`git diff base...task`).
- **Restore the orchestrator's cwd after each wave.**
- **Subagent output is bounded.**
- **Parallelism follows the live-capacity contract above; never substitute a fixed numeric range.**
- **Don't disable the build cache or daemon.** Warm it once and share across worktrees.
- **Enable incremental / caching mode at scaffold** when the project's build or verify tools
  support it but default to off. Check the tool's config or documentation during scaffold setup;
  if an incremental or cache option exists, enable it. Repeated verify runs (per-wave gates,
  completion gate) benefit from warm caches. This is the orchestrator's scaffold responsibility,
  not a per-task concern.
- **Share dependencies; don't reinstall per worktree.** Symlink/reflink external deps; relink
  workspace-internal packages to this worktree's own source. **Caveat — path-mapping monorepos:**
  per-worktree install from the warm store is the safe default; don't force symlink sharing.
  **Cleanup caveat:** a dependency-store symlink is untracked; ignore it with a **slash-less**
  pattern (`<dir>`, not `<dir>/`); remove the symlink before safe-removing the worktree.
- **Slash-less gitignore — verify at scaffold, before any worktree.** After scaffold commits,
  confirm `.gitignore` uses slash-less patterns for dependency directories (the project's dependency
  store directory, without a trailing slash). A trailing-slash pattern does not match a symlink, so
  worktree dependency symlinks get staged by `git add`. Fix this **before** creating the first
  parallel wave's worktrees — every worktree agent will otherwise hit the same papercut
  independently.
- **Worktrees isolate *files*, not *runtime*.** Shared external resources (DB, cache, queue, ports)
  are shared across all tasks. Treat mutations as dangerous; on unexpected state drift, **stop and
  escalate**.
  - **Declared shared-resource expectations** (clean-slate / state-agnostic / additive-only /
    forbidden-mutations) are honored per the producer's dependency-calc rules.
  - **Ordering / external-state deps** — `Run` honors explicit `depends` and serializes declared
    external-state writers.
  - **Name agent-created ephemeral resources deterministically.** When a task (or scaffold) spins up
    an external runtime resource that takes a name — a container, a service instance, a database
    schema, a namespace, a temp queue — derive the name from a stable identifier (project +
    task/wave id), **never a random name.** Random names leak (the orchestrator can't find them to
    clean up) and risk silent collisions across parallel tasks sharing the runtime. *What* needs a
    name is discovered from the project (stack-agnostic); the rule is deterministic-not-random, and
    tear the resource down when its task/wave completes.

# Test an exact local Codex candidate

Use this procedure when a Leanforge branch is not yet released and the test result
must be attributable to that exact branch. A checked-out repository, a matching
version label, or a repository-local skill read is not execution provenance. The
active Codex plugin copy must match the generated package digest.

The repository includes a local marketplace definition, but an isolated candidate
marketplace is safer for branch testing because it has a commit-specific source
name and a reversible cache boundary.

## Preconditions

- Windows PowerShell, Git, Bash, Python, and Codex are available.
- The Leanforge repository is clean and checked out at the exact commit under test.
- The candidate workspace is outside the Leanforge repository.
- The current active Leanforge source, enabled state, active package path, and
  package digest are recorded before any change.

From the Leanforge repository root:

```powershell
$ExpectedHead = "<exact-40-character-SHA>"
$ObservedHead = git rev-parse HEAD
if ($ObservedHead -ne $ExpectedHead) { throw "unexpected Leanforge HEAD: $ObservedHead" }
if (git status --porcelain --untracked-files=all) { throw "Leanforge worktree is not clean" }

codex plugin marketplace list
```

Use the host's plugin-list or selected-plugin readback to obtain the current active
Leanforge package path. Record its identity before replacing it:

```powershell
python tools/codex_candidate_marketplace.py digest `
  --path "<current-active-Leanforge-package-path>" `
  | Tee-Object -FilePath "$env:TEMP\leanforge-original-package.json"
```

If the host cannot provide an authoritative active path, stop with
`BLOCKED_PROVENANCE`.

## Prepare a commit-pinned local marketplace

The helper runs `bash build/build.sh`, requires the repository to remain clean,
copies `codex/plugin` into an isolated marketplace, and records the Git commit,
Git tree, source package digest, copied package digest, and commit-specific
marketplace name.

```powershell
$ShortHead = git rev-parse --short=12 HEAD
$CandidateRoot = Join-Path $env:TEMP "leanforge-candidate-$ShortHead"

python tools/codex_candidate_marketplace.py prepare `
  --repo . `
  --workspace $CandidateRoot `
  | Tee-Object -FilePath (Join-Path $CandidateRoot "prepare-result.json")

python tools/codex_candidate_marketplace.py verify-workspace `
  --workspace $CandidateRoot
```

Preparation must fail when the worktree is dirty, the build changes generated
surfaces, the workspace is inside the repository, or source and copied package
digests differ.

## Register and activate the candidate

Register the isolated marketplace root:

```powershell
codex plugin marketplace add $CandidateRoot
codex plugin marketplace list
```

Then:

1. Restart the ChatGPT desktop app or Codex host.
2. Open the Plugins Directory.
3. Select `Leanforge Candidate <short-SHA>`.
4. Install and enable its `leanforge` plugin.
5. Disable the previously active Leanforge source for the test window so that
   package selection is not ambiguous.
6. Start a new Codex conversation for the disposable test repository.

Codex installs a local plugin into its plugin cache and executes the installed
copy, not the source directory. Obtain the new active package path from the same
predeclared host readback used for the study, then verify it:

```powershell
python tools/codex_candidate_marketplace.py verify-active `
  --workspace $CandidateRoot `
  --active-path "<candidate-active-package-path>" `
  | Tee-Object -FilePath (Join-Path $CandidateRoot "active-verification.json")
```

Only a result with `"match": true` qualifies the subsequent Prime/Run session.
A version label, source checkout, response claim, marketplace listing, or package
digest without active-path binding is insufficient.

## Run the product test

Use a new chat and a disposable Git repository. In Codex CLI, open `/skills` or type `$` and select
the installed Leanforge skill; when names are unambiguous, `$prime` and `$run` explicitly mention the
skills. In the ChatGPT desktop Codex surface, use the installed plugin/skill picker or the host's
`SkillUserInput` path. Do **not** enter `/leanforge:prime` or `/leanforge:run`: Codex does not create
those plugin-defined slash commands.

Record:

- candidate commit and tree;
- candidate marketplace name;
- staged and active package digests;
- the exact skill-selection/readback method;
- host and Codex version;
- fresh-session, reload, and cache conditions;
- Prime/Run transcript and command evidence.

For the closed existing-repository golden case, explicit Prime selection is already the workflow choice.
The implementation verbs in the goal must not trigger a Prime-versus-direct mode question. When the
request plus repository evidence close every load-bearing slot, expect zero user questions and actual
`.leanforge/handoff.md`, `.leanforge/spec.md`, and `.leanforge/plan.md` files in the same invocation.
A separate decision-ownership case should still ask the one deliberately omitted load-bearing decision.

Stop rather than run the product test when active identity is mismatched or unverifiable.

## Restore the previous installation

After the test:

1. Close the candidate conversation.
2. Disable or remove the candidate plugin in the Plugins Directory.
3. Re-enable the previously active Leanforge source.
4. Remove the temporary marketplace using the exact name printed in
   `leanforge-candidate-manifest.json`:

   ```powershell
   codex plugin marketplace remove leanforge-candidate-<short-SHA>
   ```

5. Restart the desktop app or Codex host and open a new conversation.
6. Obtain the restored active package path through the same authoritative
   readback.
7. Run `digest --path` on the restored path and compare it with
   `$env:TEMP\leanforge-original-package.json`.
8. Delete `$CandidateRoot` only after the original identity and enabled state are
   restored.

A missing original identity, ambiguous active source, digest mismatch, or failed
marketplace removal is `RESTORE_FAILED`; do not report the test environment as
clean.

## Success and failure boundary

Candidate activation succeeds only when all of the following hold:

- repository HEAD equals the pinned commit;
- build completes and leaves the repository clean;
- source and staged package digests are equal;
- the commit-specific marketplace is selected;
- the active cache path is authoritatively read back;
- active and staged package digests are equal;
- the test starts in a fresh conversation;
- the original installation is restored and reverified afterward.

Use these dispositions:

- `PASS_PROVENANCE`: every condition above is proven;
- `BLOCKED_PROVENANCE`: the host exposes no authoritative active binding;
- `FAIL_PROVENANCE`: the active package differs from the pinned candidate;
- `RESTORE_FAILED`: the pre-test installation identity or enabled state is not
  restored.

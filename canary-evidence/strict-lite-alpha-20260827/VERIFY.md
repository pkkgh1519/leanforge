# Independent remote verification instructions

## Primary path: fresh clone or branch archive

Do not review a caller-provided local directory. Fetch the public remote branch directly:

```bash
git clone --branch audit/strict-lite-alpha-canary-20260827 --single-branch https://github.com/pkkgh1519/leanforge.git leanforge-canary-review
cd leanforge-canary-review
```

Verify the evidence boundary before running product checks:

```bash
base=e082b227450acf54c29f7573d2b5fabaeac4d681
git merge-base --is-ancestor "$base" HEAD
test "$(git rev-parse "$base^{tree}")" = "a7a648714c0e4a66e70735e21eb05bba8af03c17"
git diff --name-only "$base" HEAD
python -m json.tool canary-evidence/strict-lite-alpha-20260827/manifest.json >/dev/null
bash build/build.sh
git diff --exit-code -- claude codex
python -m unittest discover -s tests -v
git diff --check
git status --short
python tools/codex_candidate_marketplace.py digest --path codex/plugin
```

The candidate base commit and Git tree are hard gates. The review branch may add only:

- `.github/workflows/strict-lite-alpha-remote-review.yml`
- `canary-evidence/strict-lite-alpha-20260827/**`

Record the newly computed package digest as checkout-local evidence. Do not require it to equal the captured Windows transport digest.

## DNS or sandbox-network fallback

If the review environment cannot resolve or connect to GitHub, do not claim a direct-download pass. Use the exact-branch GitHub Actions run as the execution fallback:

1. Open `https://github.com/pkkgh1519/leanforge/actions/workflows/strict-lite-alpha-remote-review.yml`.
2. Select the run for branch `audit/strict-lite-alpha-canary-20260827` and the exact remote review commit supplied by the requester.
3. Require both `linux-source-verification` and `windows-source-verification` to pass.
4. Inspect or download both verification artifacts and record their checkout-local package digests.
5. Use the GitHub connector or browser-visible repository files to inspect the report and manifest if raw Git transport remains unavailable.
6. State explicitly that GitHub Actions, not the reviewer sandbox, executed the source verification.

## Review questions

1. Does the branch contain the declared candidate commit and Git tree as its exact base ancestor?
2. Is the branch delta restricted to the public evidence and branch-scoped workflow?
3. Do clean build, generated-source drift checks, unit tests, and whitespace checks pass on fresh remote checkouts?
4. Does the report avoid treating an operating-system working-tree digest as a universal source identity?
5. Are the Full/Lite comparability, hard-trigger routing, monotonic promotion, post-promotion verification/review, and restoration conclusions internally consistent?
6. Are local installed-host attestations clearly separated from remotely reproduced evidence?
7. Is `READY_FOR_NEXT_LITE_ITERATION` supported under the stated no-clear economic signal?

## Required response

Return a natural Korean report with this exact top-level shape:

```text
VERDICT: PASS | REQUEST_CHANGES | NOT_EVALUABLE
REMOTE_COMMIT: <sha>
BASE_COMMIT: <sha>
BASE_TREE: <sha>
DOWNLOAD: PASS | FAILED_DNS | FAILED_OTHER
ACTIONS: PASS | FAIL | NOT_USED
FINDINGS:
- <severity> <finding or NONE>
LIMITS:
- <what was not independently reproduced>
```

Do not create a pull request or merge the review branch.

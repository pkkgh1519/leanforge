# Leanforge Strict Lite α installed-host canary

## Verdict

`READY_FOR_NEXT_LITE_ITERATION`

The corrected canary passed provenance, Full control, Strict Lite α safety routing, Lite-to-Full promotion, product verification, final review, archive closure, and original-plugin restoration. The economic signal is no-clear: the arms did not capture authoritative reviewer-count, subagent-count, or elapsed-time metrics.

## Corrected prior classification

The prior `FAIL_PROVENANCE / FIX_SAFETY` result is corrected to `NOT_EVALUABLE_STALE_DIGEST_GATE`. The stopped run had treated a digest from another operating-system working tree as a universal package identity. This run used the candidate workspace manifest's environment-local staged digest.

## Candidate provenance

| Predicate | Value | Result |
| --- | --- | --- |
| Candidate commit | `e082b227450acf54c29f7573d2b5fabaeac4d681` | PASS |
| Candidate Git tree | `a7a648714c0e4a66e70735e21eb05bba8af03c17` | PASS |
| Repository clean after build | `true` | PASS |
| Windows source digest | `4943add8d1cac9f8cc4fdde378e0ff50de146a714baeaf5992e9f47135379354` | PASS |
| Windows staged digest | `4943add8d1cac9f8cc4fdde378e0ff50de146a714baeaf5992e9f47135379354` | PASS |
| Windows active candidate digest | `4943add8d1cac9f8cc4fdde378e0ff50de146a714baeaf5992e9f47135379354` | PASS |
| Source/staged/active equality | `true` | PASS |

The installed candidate binding was `leanforge@leanforge-candidate-e082b227450a`. Before restoration, `verify-active` reported top-level `match: true`, and its `active_sha256` and `expected_sha256` equaled the workspace manifest's staged digest.

The remote review must not treat a newly computed checkout digest as a universal replacement for the Windows transport digest. Remote source identity is bound by the candidate commit and Git tree above.

## Comparable arms

- Common Full/Lite warm-up commit: `b54a5bfcbdd58e3b5d2afac2294448cfee21d7fa`
- Common baseline digest excluding `.git` and the activation file: `b0814d5f2204dd38e4878f74b623fa348108ac59a4966a9a67a570913d685545`
- Full and Lite used the same repository snapshot, harness, product files, tests, and user request.
- Only the Strict Lite α activation file differed.

### Arm A — Full control

- Result: PASS
- Task commit: `ccffca500e09504ef83572de203457f9e3fcbc20`
- Feature tip: `fe59cf0cdf1fd790295d14eba98fa13433f17ae2`
- Tests: 5 passed
- Diff check: passed
- Independent final review: clear
- Final Run state: completed, clean, active 3-doc count zero, hash-verified archive

### Arm B — Strict Lite α comparison

- Result: PASS for safety routing and quality; no-clear economic signal
- The activation was present.
- The `breaking_public_contract` hard trigger correctly selected Full Assurance rather than a wrong-path Lite shortcut.
- Task commit: `046434183df32e8760198ab376454c11b66f716a`
- Feature tip: `22ac94c7758c6071114e9ba4f4261d1f5a2d525e`
- Tests: 5 passed; direct-call and documentation readback passed
- Diff check and final review: passed
- Final Run state: completed, clean, active 3-doc count zero, hash-verified archive

### Arm C — Lite-to-Full forced promotion

- Result: `PROMOTION_PASS`
- Preflight: `mode: lite`, reason `lite_eligible`, no hard triggers
- Run assurance: `startingProfile: strict_lite_alpha`, `effectiveProfile: full`, `monotonicPromotion: true`
- Promotion was recorded before the implementation worker began, and the Run never downshifted.
- Task commit/merge: `de27fcc61ad2d07a1b73e3f8c2ffda336b9e7a18` / `048783ac090bee0eb876899879ebda51535309f8`
- Durable harness commit: `7db051ad82ef0e7f9b683675ec15d2c97358cee9`
- Recovery commit/final tip: `8deb637f5342f71ac34475a3ae54379ec2e29021` / `8eeb28bdf469fae1912cdd078a5932845218064e`
- Focused tests: 3 passed; full tests: 4 passed
- Runtime smoke and `uv pip check --python python`: passed; all 96 installed packages compatible
- The first independent final review blocked incomplete public-interface documentation. Recovery verification and a fresh final-review retry passed with no findings.
- Final Run state: completed, clean, active 3-doc count zero, hash-verified archive

## Restoration

- Candidate plugin, candidate marketplace, and candidate cache: removed
- Candidate workspace: preserved locally for audit
- Original plugin: `leanforge@leanforge-study-b-7bef4b9`, version `1.9.0`, installed and enabled
- Original pre-canary and restored package digest: `c67a80ff0ded7a548057957e22e67b414d123f660ec69f6e8791eb5ab75a9113`
- The unrelated `leanforge@local-marketplaces` installation remained disabled.

## Remote-review boundary

This public branch contains the exact candidate source as its parent commit plus sanitized review evidence and a branch-scoped verification workflow. It intentionally excludes local candidate archives, plugin caches, fixture Git databases, raw host logs, credentials, and absolute user-machine paths.

A remote reviewer can independently clone the branch, verify its parent commit/tree, confirm that only the evidence surface was added, and run clean build/tests on Linux or Windows. The installed-host activation and restoration transitions cannot be re-enacted from this public branch after the candidate was removed; those remain local evidence-backed attestations and must not be presented as remotely reproduced facts.

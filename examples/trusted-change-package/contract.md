# Approved change contract summary

## Goal

Make the Adaptive Assurance host study reject A/B measurements unless each run is tied to the exact
installed package that actually executed.

## User-owned decisions

- Keep the patch research-only. Do not activate Lite or alter Prime/Run product behavior.
- Treat missing, mismatched, or redaction-destroyed execution provenance as unusable evidence.
- Preserve the current v1.9.0 product and generated-package behavior.

## Scope

- Add per-host, predeclared execution-provenance methods.
- Add per-run A/B arm, digest, binding, qualification, and exclusion fields.
- Require both arms to qualify before latency, quality, or user-burden comparison.
- Replace permissive phrase-presence checks with semantic negative mutations.

## Non-goals

- No Claude Code or Codex host integration.
- No Lite activation, workflow split, runtime router, or telemetry service.
- No product speed, token, quality, or user-burden claim.

## Acceptance

- A run cannot be qualified by waiver, manual acceptance, repository-local source reads, or an
  opposite-arm result.
- The final report exposes qualified and excluded A/B counts by host and reason.
- Focused tests, the full test suite, the build, generated-package parity, and whitespace checks pass.

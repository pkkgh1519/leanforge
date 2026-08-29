# adaptive-assurance-live-pilot.md — default-off Strict Lite alpha


The shadow record above remains advisory. A separate, internal canary may authorize only the bounded
`strict_lite` alpha profile, and only when `.leanforge/adaptive-assurance-pilot.json` exists with the
exact closed value below:

```json
{
  "schema_version": 1,
  "pilot": "strict_lite_alpha",
  "enabled": true
}
```

The file is an experiment-harness control, never a user-facing mode choice. Its absence, `enabled:
false`, malformed JSON, unknown fields, or any value mismatch means **Full Assurance** without a user
question or Prime blocker.

At each ELICIT exit, remove any stale `.leanforge/assurance-profile.json` before evaluating the
canary. Write a new profile atomically only when all of these already-grounded facts hold:

- the activation file is the exact enabled value above;
- the validated shadow snapshot is `cycle: delta`, `mode: lite`, `reasons: ["lite_eligible"]`;
- `hard_triggers`, `missing_lite_required_true`, and `violated_lite_required_false` are empty;
- `harness_sync` is `false`;
- `bounded_direct_execution` is `true`: the grounded delivery shape is one local file-diff task,
  needs no regeneration barrier, has existing sufficient targeted verification, and has no indication
  of risk above `MECHANICAL` / `NONE`.

The authoritative canary profile contains exactly:

```json
{
  "schema_version": 1,
  "contract_id": "leanforge.adaptive-assurance-live-profile",
  "profile": "strict_lite_alpha",
  "cycle": "delta",
  "reason": "lite_eligible",
  "harness_sync": false,
  "bounded_direct_execution": true
}
```

A valid profile permits exactly two omissions: Prime skips the independent intent-completeness
reviewer, and Run may skip a no-op durable-harness synchronization after proving no durable change.
Prime still writes the same 3-doc, runs the independent 3-doc gate, obtains explicit approval, and
Run keeps its existing direct route, one full completion verification, runtime smoke when applicable,
recovery, final diff check, and user-owned integration choice. A fresh independent final reviewer
remains mandatory, but its bounded Lite scope is acceptance conformance, the product diff and changed
paths, verification evidence, and promotion handling. Harness and broad cross-module lenses remain
Full-only when the profile proves they are inapplicable.

The PLAN stage must materialize exactly one task with explicit risk `MECHANICAL` or `NONE` and no
regeneration barrier. If it cannot, delete the profile, return to ELICIT, give a fresh
intent-completeness reviewer the chat session and current decision surface, close findings with the
user, regenerate affected SPEC and PLAN content, and continue in Full before the 3-doc gate. This is
an approval-preflight fallback, not a third execution path.

Any missing, invalid, stale, contradictory, newly risky, or newly uncertain fact promotes
monotonically to the existing Full Assurance flow. If Run has already begun, it halts and preserves
state, removes the profile, and returns to Prime with the original user material, ELICIT decision
surface, approved 3-doc, and new risk evidence. Prime runs the skipped review, closes findings with the
user, regenerates and independently reviews affected 3-doc content, and obtains explicit reapproval
before Run resumes in Full. Dependent work is forbidden before reapproval, and the same cycle cannot
re-enter Lite. `standard` remains an observation label, never a third live execution path. Do not
expose the selected profile or ask the user to choose one.

If a fresh Run lacks the original user material or ELICIT decision surface, it remains halted and
preserved until the user resumes the original Prime context or re-supplies the source material. The
agent must not reconstruct missing intent context from the approved 3-doc or treat the prior approval
as sufficient to resume.

This default-off alpha deliberately keeps `schema_version: 1` while extending the closed v1 shadow
shape with `bounded_direct_execution`. A v1 record that lacks the field is stale, is never accepted as
backward-compatible, and fails closed to Full with stale profile cleanup.

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
- `harness_sync` is `false`.

The authoritative canary profile contains exactly:

```json
{
  "schema_version": 1,
  "contract_id": "leanforge.adaptive-assurance-live-profile",
  "profile": "strict_lite_alpha",
  "cycle": "delta",
  "reason": "lite_eligible",
  "harness_sync": false
}
```

A valid profile permits exactly two omissions: Prime skips the independent intent-completeness
reviewer, and Run may skip a no-op durable-harness synchronization after proving no durable change.
Prime still writes the same 3-doc, runs the independent 3-doc gate, obtains explicit approval, and
Run keeps its existing direct route, full completion verification, runtime smoke when applicable,
final independent review, recovery, final diff check, and user-owned integration choice.

Any missing, invalid, stale, contradictory, newly risky, or newly uncertain fact promotes
monotonically to the existing Full Assurance flow. `standard` remains an observation label, never a
third live execution path. Do not expose the selected profile or ask the user to choose one.

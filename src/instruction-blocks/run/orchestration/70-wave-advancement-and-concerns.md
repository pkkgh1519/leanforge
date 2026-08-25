
### Advancing waves

**Sequential waves advance immediately** — no gate to wait for, so the next wave can begin as
soon as the commit is verified and regen/wiring are done.

**Parallel waves:** **by default, overlap** the next wave's provisioning (worktree creation +
dependency share) with the current wave's integration gate — begin provisioning as soon as the
merge + wiring commits land, before the gate finishes. Gates are the **largest wall-clock sink**
(verify/build/container time), so overlapping provisioning with them is a real, free speedup — do it,
don't run strictly sequentially by default. The next wave's **dispatch still waits for a green gate**,
but the worktrees and dependencies are already ready. On gate failure the provisioned worktrees
are harmless (no task work yet) — remove or reuse after the fix. Fall back to fully serial advance
only if lock contention or refresh bookkeeping makes overlap unsafe. (Intermediate per-wave gates may
also use the test runner's affected-only filter; the completion gate always runs the full set.)

**Advisory findings are recorded, never dropped.** Findings not fix-dispatched must be explicitly
marked accepted — never silently dropped.

<!-- leanforge:run-semantic:RUN-CONCERN-DISPOSITION:start -->
```json
{
  "id": "RUN-CONCERN-DISPOSITION",
  "kind": "concern_disposition",
  "definition": "Every recorded concern has exactly one correlated disposition that follows its record and carries a non-empty value from resolved, explicitly_accepted, user_accepted, promoted_to_failure, and pending. Every concern record and its disposition precede every completion or user-gate endpoint. Pending blocks completion and the user gate without entering the failure overlay. A promoted_to_failure disposition is a failure result whose runtime-owned failure overlay precedes every continuation that follows the disposition, including wave-completion output, without retroactively constraining earlier progress or routine events. On every selected route, a promoted concern may remain a terminal failure or recover through the route-neutral ordered overlay, remedial worktree, implementer continuation, post-remediation green completion full verify or valid reusable completion facts and decision, green final review, and clear verdict before an endpoint. User-owned requirement, compatibility, and safety concerns may remain pending or be promoted to failure without user acceptance, while a resolved or accepted terminal disposition must be user-owned. The failure overlay wins every overlap.",
  "constraints": [
    "Every recorded concern precedes exactly one correlated disposition with a non-empty value from the five closed dispositions.",
    "A disposition cannot precede its correlated concern record, including pending and promoted-to-failure dispositions.",
    "Every concern record and its correlated pending, promoted, resolved, or accepted disposition precede every completion or user-gate endpoint.",
    "Pending blocks completion and the user gate without entering the failure overlay; promoted-to-failure enters the runtime-owned failure overlay before every continuation that follows the disposition, including wave-completion output, while prior progress and routine events remain allowed.",
    "On direct, single-risky, parallel, and external routes alike, a promoted concern may stop terminally after the overlay; if completion or user gate follows, the route-neutral trace requires overlay, remedial worktree, implementer continuation, post-remediation green completion full verify or valid reusable completion facts and decision, green final review, and clear verdict in that order.",
    "User-owned requirement, compatibility, and safety concerns permit pending or promoted-to-failure dispositions without acceptance; resolved, explicitly accepted, or user-accepted terminal dispositions must be user-owned."
  ]
}
```
<!-- leanforge:run-semantic:RUN-CONCERN-DISPOSITION:end -->

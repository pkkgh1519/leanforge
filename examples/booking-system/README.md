# Booking system demo

This example demonstrates the minimum useful Leanforge loop for a
behavior-changing feature: `Prime` should expose hidden product decisions before
implementation, and `Run` should finish with acceptance evidence rather than a
vague done message.

This is a workflow example, not a generated app. Copy the prompt into your own
repository to see how Leanforge shapes the work.

## 1. Start with the prompt

Invoke `Leanforge:Prime` (`/leanforge:prime`), then paste the prompt body from
[prime-prompt.md](prime-prompt.md).

## 2. Decisions Prime should force or record

A good Prime result should not silently assume these decisions:

| Decision area | Why it matters |
|---|---|
| Slot ownership | Determines whether one booking consumes one slot, a service capacity unit, or a staff calendar entry. |
| Cancellation behavior | Determines whether canceling releases the slot immediately and what happens after appointment start. |
| Double-booking prevention | Determines the concurrency rule and the required verification evidence. |
| Customer identity | Determines whether booking uses accounts, email links, phone numbers, or anonymous reservations. |
| Service lifecycle | Determines what happens to existing bookings if the business changes or disables the service. |
| Timezone and clock source | Determines how availability and appointment start are interpreted. |

If the user's prompt does not answer these, Prime should either derive them from
stated intent or ask with a recommended default.

## 3. Example acceptance/evidence shape

For SDD-lite Stage 1, behavior-changing work should carry acceptance evidence
from spec to implementation review. A small booking flow might produce rows like
these:

| AC | Observable behavior | Evidence expected after Run |
|---|---|---|
| AC-1 | A customer can reserve an available future slot. | Automated test or executable check showing the slot changes from available to booked. |
| AC-2 | A second customer cannot reserve the same slot. | Test or command output proving the second booking attempt is rejected. |
| AC-3 | A customer can cancel before the appointment starts. | Test or command output showing cancellation releases or marks the slot according to the approved spec. |
| AC-4 | Cancellation after appointment start follows the approved rule. | Boundary-time test covering the approved cutoff behavior. |

The exact AC list should follow the approved spec, not this example verbatim.

## 4. Run the approved contract

After reviewing and approving the generated spec, plan, and handoff:

```text
/leanforge:run
```

A useful final Run report should include:

- files changed;
- checks run;
- acceptance evidence tied back to the relevant AC rows;
- unresolved risks or intentionally deferred scope;
- project harness updates when applicable.

## 5. What this demo should teach

Leanforge is valuable when the expensive part is not typing code, but preventing
hidden product decisions from being embedded into code without review. This demo
keeps the implementation small so the review path is visible.

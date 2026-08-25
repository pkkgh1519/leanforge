# project-design-technical.md — first-cycle DESIGN (technical decisions)

Establish the project's **technical decisions** from explicit user intent plus authoritative
repository evidence. PRESENT is for a **new, changed, or materially unresolved** load-bearing technical
choice: translate it into concrete options + trade-offs and let the user decide. Existing language,
framework, public signature, test strategy, module boundary, or convention that the current slice preserves
may be derived from the repository and must not be re-presented as a greenfield choice. The technical floor
below is what the ELICIT loop must close on the technical axis; order is gap-driven.

It is the opposite of domain design. Domain *draws out* what the user knows; technical *presents*
what the user doesn't, as options the user chooses among. The user says a generality ("I want it to
be secure") → you translate it into concrete choices ("an external auth service vs. rolling your own;
the latter needs these decisions…") → the user decides → their language narrows → repeat. A few
rounds converge a generality into this project's specific technical decision.

**Floor, not ceiling.** You know how to present technical options. This file blocks the failure modes
and lays the floor; which options to present, in what order, is your judgment.

## Failure modes and guardrails

- **Silent new decision (the core one).** Never settle a new or changed load-bearing technical
  direction without user approval. Translate a real unresolved choice into options with trade-offs and let
  the user pick. Do not manufacture that choice for an unchanged repository fact the slice preserves.
- **Over-engineering.** When a technical choice is heavier than the CALIBRATE character warrants, detect
  it and surface it to the user with your reasoning. Don't shrink it unilaterally — the user decides.
- **Stack-locking.** Don't presuppose a specific technology. When presenting options, honor the
  stack-agnostic principle: offer the *kinds* of approach and their trade-offs, not a single assumed
  stack.
- **Security generalities.** When the current project or slice has an applicable security surface,
  don't stop at "follow security best practices." Concretize new or changed auth, authorization, and audit
  decisions until the user owns them. When no security surface applies, record a concrete `N/A` instead of
  inventing a security interview.
- **No conventions established.** Entering `Run` with no conventions lets the executor invent patterns
  arbitrarily. Derive existing conventions, test strategy, and module boundaries from the repository when
  they are clear; ask the user only when a load-bearing convention must be newly chosen or changed.

## What to cover (proportional to CALIBRATE depth)

The areas a typical project's technical floor touches — **common, not a fixed catalog.** A given project
may add others (data model / migration, observability, …) or legitimately have almost nothing in one.
Cover what *this* project's character implies, not all four by rote.

- **Architecture** — components, how they communicate, data flow.
- **Security model** — auth approach, authorization model, audit scope (this project's own policy,
  not a generality).
- **Conventions** — code conventions, test strategy, module boundaries.
- **Operations** — deployment, environment, external dependencies.

Scale to the character and evidence. An established local tool may have architecture, tests, and
operations already pinned and need no confirmation beat; a greenfield or materially changing project may
need deep design. The depth comes from the actual unresolved decisions, not a fixed amount of ceremony.

## Depth floor

- Every **new or changed user-owned** technical decision is settled by user confirmation.
- Every unchanged current technical fact used by the design is backed by authoritative repository evidence.
- Every unresolved decision with a real trade-off was presented as **options + each trade-off**.
- The security model is project-specific when a security surface exists; otherwise record a reasoned `N/A`.
- **No open user-owned technical question remains.**

The ceiling is open.

## What this produces

The grounded technical shape, recorded in the handoff's Project Foundation: user-confirmed new/
changed choices plus authoritative repository-backed facts the slice preserves. `Run` uses them as design
context while implementing, and later turns them into `architecture.md` + `security.md` + `standards.md`
+ `operations.md`.

## Universality guard

Stack-agnostic. Options are presented as kinds-of-approach with trade-offs; the concrete stack is the
user's decision at runtime, never assumed or named as a rule here.

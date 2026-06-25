# Security Policy

## Supported versions

The latest released Leanforge version is the supported version for security
fixes. Older tags remain available for compatibility, but fixes are expected to
land on `main` first and then be released from there.

## Reporting a vulnerability

Please do not disclose vulnerabilities in public issues or pull requests.

Use GitHub private vulnerability reporting if it is available for this
repository. If it is not available, contact the repository owner through GitHub
and request a private coordination channel before sharing sensitive details.

Include:

- affected version or commit;
- platform surface involved, such as Claude Code, Codex, generated skill surface,
  docs, or release automation;
- reproduction steps;
- expected and actual behavior;
- security impact;
- any safe proof-of-concept artifacts.

## Scope

Security reports are especially relevant when they involve:

- unsafe filesystem writes or state migration behavior;
- accidental disclosure of local project state;
- unsafe git or worktree operations;
- prompt or skill changes that weaken approval, evidence, or recovery gates;
- supply-chain concerns in plugin packaging or release metadata.

## Response expectations

The maintainer will triage reports as availability allows. Confirmed issues
should be fixed on a private or minimal public branch when appropriate, validated
with focused tests, and released with clear notes that avoid unnecessary exploit
detail.

## Public discussion

After a fix is available, public release notes may summarize the impact and the
upgrade path. Avoid publishing sensitive reproduction detail unless disclosure is
coordinated and safe.

---
name: run-tdd
description: >
  Execute the Leanforge Run workflow with selective TDD guidance. Use when the user invokes
  run-tdd, Leanforge:Run TDD, or asks to run Leanforge:Run while automatically applying TDD to
  observable behavior changes. This is a wrapper: Leanforge:Run remains the primary execution
  authority, and TDD is subordinate verification guidance for suitable implementation tasks.
---

# Leanforge:Run TDD

## Purpose

Use this skill as a thin wrapper around `Leanforge:Run` when the user wants Leanforge execution plus automatic TDD discipline.

The original `Leanforge:Run` workflow remains authoritative. This skill only adds selective TDD guidance for implementation tasks that change observable behavior.

This wrapper is self-contained and does not require a separately installed `tdd` skill.

## Required loading order

1. Read this `SKILL.md`.
2. Read the original `Leanforge:Run` `SKILL.md` completely and follow it as the primary workflow.
3. Apply the self-contained selective TDD policy below where this skill says TDD applies.

If the original `Leanforge:Run` skill path is not obvious from available skill metadata, ask the user for the path instead of guessing.

## Precedence

Follow this priority order:

1. System, developer, sandbox, tool, and safety instructions.
2. Project-local `AGENTS.md` and repository constraints.
3. Original `Leanforge:Run` handoff/spec/plan execution workflow.
4. This wrapper's selective TDD guidance.

If TDD guidance conflicts with the original `Leanforge:Run` flow, the Leanforge handoff/spec/plan execution flow wins.

## Selective TDD policy

Apply TDD when a task changes observable behavior, such as:

- business logic
- public API behavior
- state transitions
- validation rules
- error handling
- parsing, calculation, sorting, filtering, or authorization behavior
- user-visible flows

For those tasks, use a vertical red-green-refactor loop:

1. Write one behavior-focused failing test through the public interface.
2. Confirm the test fails for the expected reason.
3. Implement the smallest change that makes that test pass.
4. Confirm the test passes.
5. Refactor only while the relevant tests remain green.
6. Repeat for the next behavior.

Tests should verify behavior through public interfaces, not private helpers, internal structure, source strings, or incidental implementation details.

When the `Prime` spec provides an Acceptance & Evidence Matrix, derive each TDD slice from the
relevant AC's observable behavior; AC evidence must be a behavior assertion through the smallest
stable public surface. File existence, source-string checks, symbol existence, skipped tests,
weakened assertions, swallowed exceptions, or tests coupled to private helpers do not count as AC
evidence.

## TDD exclusion policy

Do not force TDD for tasks that are not behavior changes, including:

- documentation-only changes
- harness or agent-instruction updates
- formatting-only changes
- file moves or renames
- mechanical import/path wiring
- simple configuration changes
- scaffolding with no user-observable behavior yet
- build or CI plumbing with no product behavior change

For non-TDD tasks, still capture the smallest meaningful verification, such as:

- build or compile command
- lint or format check
- config parse or dry run
- focused smoke check
- documented command output
- file/content inspection for documentation or harness-only changes

## Leanforge integration rule

When `Leanforge:Run` assigns work directly to the orchestrator, apply this TDD policy to
behavior-changing tasks.

When `Leanforge:Run` dispatches subagents, include TDD policy only for behavior-changing work. Do
not add it to mechanical or documentation-only prompts.

Keep Leanforge's required evidence rules intact: a task is not complete unless the appropriate verification ran and the result is captured.

## User-facing reporting

Report results according to the original `Leanforge:Run` communication rules. Do not mention internal labels or this wrapper unless the user asks how the run was controlled.

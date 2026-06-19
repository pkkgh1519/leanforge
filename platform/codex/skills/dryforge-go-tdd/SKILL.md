---
name: dryforge-go-tdd
description: >
  Execute the Dryforge go workflow with selective TDD guidance. Use when the user invokes
  dryforge-go-tdd, go-tdd, or asks to run dryforge:go while automatically applying TDD to
  observable behavior changes. This is a wrapper: dryforge:go remains the primary execution
  authority, and TDD is subordinate verification guidance for suitable implementation tasks.
---

# dryforge-go-tdd

## Purpose

Use this skill as a thin wrapper around `dryforge:go` when the user wants Dryforge execution plus automatic TDD discipline.

The original `dryforge:go` workflow remains authoritative. This skill only adds selective TDD guidance for implementation tasks that change observable behavior.

## Required loading order

1. Read this `SKILL.md`.
2. Read the original `dryforge:go` `SKILL.md` completely and follow it as the primary workflow.
3. Read the `tdd` `SKILL.md` completely and use it only as subordinate guidance where this skill says TDD applies.

If the original `dryforge:go` skill path is not obvious from available skill metadata, ask the user for the path instead of guessing.

## Precedence

Follow this priority order:

1. System, developer, sandbox, tool, and safety instructions.
2. Project-local `AGENTS.md` and repository constraints.
3. Original `dryforge:go` handoff/spec/plan execution workflow.
4. This wrapper's selective TDD guidance.
5. The standalone `tdd` skill's general advice.

If TDD guidance conflicts with the original `dryforge:go` flow, the Dryforge handoff/spec/plan execution flow wins.

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

For non-TDD tasks, still capture the smallest meaningful verification that proves the change works, such as:

- build or compile command
- lint or format check
- config parse or dry run
- focused smoke check
- documented command output
- file/content inspection for documentation or harness-only changes

## Dryforge integration rule

When `dryforge:go` assigns work directly to the orchestrator, apply this TDD policy yourself for behavior-changing tasks.

When `dryforge:go` dispatches implementation work to subagents, include the relevant TDD policy in the task prompt only for behavior-changing work. Do not add TDD instructions to mechanical or documentation-only prompts.

Keep Dryforge's required evidence rules intact: a task is not complete unless the appropriate verification ran and the result is captured.

## User-facing reporting

Report results according to the original `dryforge:go` communication rules. Do not mention internal labels or this wrapper unless the user asks how the run was controlled.
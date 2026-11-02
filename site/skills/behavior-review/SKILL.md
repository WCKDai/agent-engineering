---
name: behavior-review
description: Review a change for what it does to behavior, not how it reads. Use when reviewing a pull request or your own diff before merge, especially changes to state, retries, persisted data, RPCs or anything with more than one entry point. For who must review and how the verdict is recorded use independent-verification.
---

# Behavior review

The first question of a review is whether the change alters behavior in any way it does not intend.
Behavior includes persisted state, scheduled work, RPCs, side effects and metrics, not only return
values. Reviews reduce risk; the author, not the reviewer, owns correctness.

## Activate when

- Reviewing a pull request, or self-reviewing a diff before asking for review.
- A change adds a new code path next to an existing one that does the same job.
- A change touches retries, idempotency, queues, persistence or multi-step operations.
- A change is user-facing and reachable from more than one surface (UI, API, CLI, agent tools).

## Inputs and assumptions

- The diff, the acceptance criteria and the evidence record for the head.
- The existing code that does the same or a similar job, found by searching, not by memory.
- The list of surfaces the product exposes, from the repository's guidance if it has one.

## Outputs

- A difference list: each behavior difference from the existing equivalent code, failure-path
  case and surface, with a disposition (intended, finding, or not applicable and why).
- Findings, each with file, line, the concrete scenario that goes wrong, and a severity on Sentry's
  LOGAF scale: high (must not merge without it), medium (worth fixing) or low (nit).
- The verdict and its evidence are recorded as independent-verification defines them.

## Permissions and restrictions

Read-only on the author's branch. Reproduce a suspected bug in a separate checkout and hand back a
failing test; do not push fixes into someone else's PR unless asked. Do not block on taste; block
on risk. A test that asserts a behavior shows the author intended it, not that it is correct.

## Workflow

1. State what the change claims to do. Then find the existing code that already does the same or a
   neighboring job, and compare: every condition, setting, side effect, metric and error path the
   old code has and the new one lacks (or the reverse) is a finding until explained.
2. Walk the failure paths of each new operation: what happens if it is retried, delivered twice,
   fails midway, or succeeds but its response is lost after each step?
3. Walk every surface: each entry point, client, adapter and agent tool that can reach the
   behavior, plus the reverse operation (undo, disable, disconnect). A path that cannot be reversed
   is a defect unless intended. Record a decision for each surface, even "not supported here".
4. Check the tests with test-design's mental-revert check; a test that would still pass with the
   implementation reverted does not cover the change.
5. Check side effects, not only output: logs, database rows, queued jobs, emitted events. A clean
   UI over an error-filled log is a failure.
6. Write findings with severity and scenario, and hand the verdict to independent-verification.
   Only low (nit) findings remaining does not block approval.

## Verification

- Each finding names a file and line, a scenario and a LOGAF severity.
- Every entry in the difference list has a disposition.
- The comparison with the existing equivalent code is recorded, or its absence is stated.
- Retry, duplicate and lost-response cases were considered for each new state-changing operation.
- The surfaces list was walked and each entry has a decision.

## Failure and escalation

- The change is too large to review behavior-by-behavior: ask for a split (see pull-request-craft).
- A finding cannot be confirmed by reading: reproduce it in a separate checkout; if you cannot,
  report it as a question, not a defect.
- Author and reviewer disagree on intended behavior: escalate to the owner of the acceptance
  criteria.

## Done when

The difference list covers the existing equivalent code, every failure-path case and every
surface, each with a disposition; tests passed the mental-revert check; side effects were
inspected; and the findings went to independent-verification for the verdict.

## Sources

- Temporal, behavior-first review that compares a change with existing code doing the same job and
  questions tests that would pass with the implementation reverted:
  https://github.com/temporalio/temporal/blob/49b2e1e954022de8ab4325dd8ec482f753ba6173/.github/copilot-instructions.md
- Sentry, reviews reduce risk, the author owns correctness, the LOGAF severity scale:
  https://develop.sentry.dev/engineering-practices/code-review/
- t3code, the "hit every surface" checklist and "a one-way door is a bug":
  https://github.com/pingdotgg/t3code/blob/47f2c8d29e981c7723467efe137ee19e91df924e/AGENTS.md
- Twenty, QA that checks database effects and treats a clean UI over a dirty log as a failure:
  https://github.com/twentyhq/twenty/blob/99ac0c8ab050f8f329254a00a7e4e9b07da96cc8/.claude/skills/qa-scout/SKILL.md

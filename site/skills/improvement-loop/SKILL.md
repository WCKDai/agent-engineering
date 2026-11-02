---
name: improvement-loop
description: Improve the delivery system weekly from evidence — pick the single worst bottleneck, change one thing, measure, keep or revert. Use for the weekly engineering review, for proposing a process or tooling change, and for any change to Creed itself.
---

# Improvement loop

Once a week, read the numbers, pick the single worst bottleneck, change one thing, and measure it the
next week. Keep the change if the number moved and the evidence level held; revert it if not.
Metric definitions live in `references/metrics.md`.

## Activate when

- The weekly review is due.
- Someone proposes a process, tooling or policy change "to go faster".
- A change to Creed itself (skills, profiles, rules, tools) is proposed.

## Inputs and assumptions

- Evidence records and the forge history for the week.
- Last week's numbers and the change that was made.

## Permissions and restrictions

- One change per loop, so its effect can be attributed.
- A change that lowers the evidence level (fewer or narrower required checks) is rejected, whatever
  it saves.
- Changes to required gates or repository policy need the owner's approval.

## Workflow

1. Compute the metrics for the week with the same script and definitions as last week. Note any
   metric without data as unknown.
2. Judge last week's change: did its target metric move beyond normal variance, and did the evidence
   level hold? Keep or revert, and record why.
3. Read `eng digest` and the worst metric. Pick the single largest bottleneck.
4. Propose one change with its expected effect, how it will be measured, and its rollback.
5. Make the change as an ordinary task (work item, worktree, PR, evidence).
6. Record the before value now; the after value is next week's step 2.

## Verification

- Each loop leaves a short record: metrics, the bottleneck chosen, the change, before and after
  numbers, keep or revert.
- A Creed change carries its before/after numbers in its pull request.

## Failure and escalation

- The data is missing or too small to judge: say so and extend the measurement; do not guess.
- Two changes landed in one week: attribute nothing; separate them next week.
- A bottleneck needs a gate or policy change: bring it to the owner as a decision, with numbers.

## Done when

The week's record exists, last week's change is kept or reverted on evidence, and exactly one new
change is in flight with its before number recorded.

---
name: autopilot-readiness
description: Decide whether a repository can run with less human attention, and promote it one tier at a time. Use when proposing that agents merge or run a repository unattended, when reviewing a repository's controls before reducing supervision, or when an unattended repository misbehaves.
---

# Autopilot readiness

Supervision is reduced one repository at a time, on evidence. Each tier has to hold for a week of
recorded evidence before the next repository is promoted.

| Tier | Agents may | A human |
| --- | --- | --- |
| Attended | Propose changes and run checks | Reviews and merges every change |
| Supervised autopilot | Merge changes that pass the required gate through a merge queue | Reviews the daily `eng digest`, owns exceptions, approves releases and deploys |
| Autopilot | Plan, build, verify independently and merge within budget | Handles exceptions the digest raises, approves releases and deploys |

No tier lets an agent release or deploy without a human.

## Activate when

- Someone proposes letting agents merge or work a repository without per-change review.
- A promoted repository has a failure, a revert or an overspend.

## Inputs and assumptions

- The repository's `AGENTS.md`, CI, required checks and recent evidence records.
- A named human who owns exceptions for this repository.

## Permissions and restrictions

- Promotion is the owner's decision. This skill produces the evidence; it does not promote.
- Never relax a required check to qualify for a tier.

## Workflow

1. Check every item; each needs a link or a command result, not a claim:
   - Reproducible environment (pinned toolchain, lockfiles, documented setup).
   - `./.agents/bin/eng verify --profile full` passes on the main branch.
   - Tiered CI: `fast`, `full` and, where the code needs it, `nightly` (`verification-tiers`).
   - A merge queue or auto-merge that requires the gate.
   - A tested rollback path (revert, flag or redeploy of the previous version).
   - A spend cap (`budget.cost_cap`) and recorded cost per run.
   - Alerting: `eng digest` (or equivalent) delivered daily to the named human.
   - Independent verification for the required gate (`independent-verification`).
   - A named human for exceptions.
2. Record the result as a checklist with evidence links in the repository's work item.
3. If every item holds, propose the next tier to the owner. Promote one repository at a time.
4. After promotion, collect a week of evidence: merged changes, digest items, reverts, cost.
5. Demote on a failed rollback, an unexplained revert, an overspend or an ignored digest item.

## Verification

- The checklist has evidence for every item; a missing item means the tier is not met.
- The week after promotion shows no unhandled digest items and no gate weakened.

## Failure and escalation

- An unattended change breaks main: revert first, demote to the previous tier, then investigate.
- The digest is not being read: demote; unattended work without attention is not autopilot.

## Done when

The owner has a checklist with evidence, a tier decision, and — after a promotion — a week of
evidence that the tier holds.

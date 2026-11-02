---
name: progressive-delivery
description: Ship code dark, turn it on gradually through reviewed configuration, and back out by reverting one commit. Use when a change alters user-visible or production behavior that should not switch on for everyone at once, or when planning a rollout, a rollback or a flag removal. For release artifacts, signing and provenance use release-verifier.
---

# Progressive delivery

Deploying code and releasing behavior are separate events. Code ships dark behind a default, the
behavior turns on through a reviewed configuration change, a cohort at a time, and every step has
a revert that does not need debugging first.

## Activate when

- A feature or behavior change should reach a subset of users, tenants or regions first.
- A risky change needs a kill switch.
- A rollout percentage, segment or option is being changed.
- A flag has reached 100% and its code paths are to be removed.
- A merged change broke something and the question is revert or fix forward.

## Inputs and assumptions

- The repository's flag or option system, where defaults are registered, and where rollout
  configuration lives and is reviewed.
- How production is deployed and how a revert reaches it.
- The metric or signal that says the new behavior is healthy.

## Outputs

- A flag or option registered with an explicit safe default, and the code guarded by it.
- A rollout plan: cohorts, the hash key that assigns them, health signals, and stop conditions.
- Each rollout step as a reviewed configuration change, not a code change.
- A removal plan for the flag once fully rolled out.

## Permissions and restrictions

Changing production rollout configuration is a production change and follows the repository's
approval rule. Never change the hashing key or algorithm of a rollout in progress: it reshuffles
every cohort. Never let a long-running unit of work (a job, a session, a workflow) see a flag flip
back and forth: evaluate per stable entity, and have long-running work read the value once when it
starts and keep it until it finishes. Never ship a flag without a default. Never combine a
rollback with a fix: revert first, then fix forward in a new change.

## Workflow

1. Register the flag or option with a default that preserves current behavior. Every option has a
   default; absence of configuration must be safe.
2. Guard the smallest code path that changes. Test both states of the flag.
3. Choose the cohort key (tenant id, user id, project id). Assign cohorts with a stable hash of that
   key so that raising the percentage only adds members and never moves an existing member out.
4. Roll out through configuration review: internal users, then a small percentage, then wider.
   Write the stop condition before each step (error rate, latency, a named metric).
5. Keep each merged change one squashed, independently revertible commit. When a merged change
   breaks production, revert it first (`git revert <sha>`, message "This reverts commit <sha>.";
   in a repository that merges with merge commits, `git revert -m 1 <merge sha>`), then
   investigate.
6. After full rollout and a quiet period, remove the flag in an ordered sequence: stop reading it
   in code, then delete the configuration, then delete the registration, each as its own change.

## Verification

- Tests cover the flag on and off; the default state matches pre-change behavior.
- The cohort assignment function is deterministic for a key, and a test pins that raising the
  percentage keeps existing members in.
- Each rollout step has a reviewed configuration change and a recorded health check.
- The revert applies cleanly to the current main, checked in a throwaway worktree
  (`git worktree add <tmp> origin/main && git -C <tmp> revert --no-commit <sha>`, then remove the
  worktree), or with `git revert --no-commit <sha>` followed by `git revert --abort`.

## Failure and escalation

- No flag system exists: propose the smallest one (a typed option with a default); do not invent a
  service.
- Health signal degrades: roll back the configuration step; if code is at fault, revert the commit.
- Revert conflicts: stop and hand back to the owner with the conflicting files; do not resolve a
  production revert by guesswork.
- A flag cannot be removed because something still reads it: list the readers; removal waits.

## Done when

The behavior is behind a defaulted flag, rolled out through reviewed configuration with stable
cohorts and stated stop conditions, the change is revertible as one commit, and the flag's removal
is planned.

## Sources

- Sentry, feature flags and options with defaults, GitOps rollout configuration:
  https://github.com/getsentry/sentry/blob/c692fefae8eaee263af3491f30747bae2eb2d756/.agents/skills/feature-flags/SKILL.md,
  https://develop.sentry.dev/backend/application-domains/feature-flags/,
  https://develop.sentry.dev/backend/application-domains/options/
- Sentry, one-label reverts and revert commit format:
  https://github.com/getsentry/sentry/blob/c692fefae8eaee263af3491f30747bae2eb2d756/.github/workflows/fast-revert.yml,
  https://develop.sentry.dev/engineering-practices/commit-messages/
- Temporal, stable-hash rollout cohorts and per-key gradual changes:
  https://github.com/temporalio/temporal/blob/49b2e1e954022de8ab4325dd8ec482f753ba6173/common/dynamicconfig/rollout.go,
  https://github.com/temporalio/temporal/blob/49b2e1e954022de8ab4325dd8ec482f753ba6173/common/dynamicconfig/gradual_change.go

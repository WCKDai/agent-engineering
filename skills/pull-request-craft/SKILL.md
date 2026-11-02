---
name: pull-request-craft
description: Shape a change into a pull request a maintainer can review, revert and trust. Use when splitting work into PRs, writing a PR title, description and commits, or handling conflicts and review comments. For what the reviewer checks use behavior-review.
---

# Pull request craft

A pull request is a claim with evidence. It solves one underlying problem, says in a few lines
what changed and how it was checked, admits what was not checked, and lands as one commit that can
be reverted on its own.

## Activate when

- Opening, splitting or updating a pull request.
- Writing commit messages for a change that will be reviewed.
- A branch conflicts with its base, or review comments arrive.

## Inputs and assumptions

- The repository's contribution rules: title grammar, issue linking, branch naming, PR template,
  merge method, attribution policy and any policy on AI-assisted contributions.
- The evidence record for the head revision.
- Which parts of the repository deploy independently.

## Outputs

- One PR per underlying problem; separate PRs where parts deploy independently, landed in a stated
  order.
- A title in the repository's grammar and a short description: what changed, why, how it was
  verified (commands and results), and what could not be checked.
- Commit messages that explain why, from the user's or maintainer's point of view.

## Permissions and restrictions

Follow the target repository's attribution policy exactly: some require an AI co-author trailer,
some reject any. In this kit's own repository, its AGENTS.md and the operator's instructions govern.
Never include customer identifiers, secrets or production data in titles, descriptions, commits or
fixtures. Never resolve a merge conflict in code you do not own by guessing; stop and hand back. Do
not commit screenshots or evidence files to the repository when the project wants them uploaded to
the PR. Do not leave template placeholders in the description.

## Workflow

1. Count the underlying problems, not the issues linked. One problem per PR. Split frontend from
   backend, or any two units that do not deploy atomically, and say which lands first.
2. Read the contribution guide and the PR template before writing. Use the exact title grammar
   (for example `fix(scope): ...`) and link the issue when the repository requires it.
3. Write the description short and in plain language:
   - What changed and why, in two or three sentences.
   - Verification: the commands run and their results, with the evidence id.
   - Not verified: anything skipped, blocked or not checkable. "Tests pass" alone is not
     verification.
   - Rollback: usually "revert this commit".
   If you do not fully understand why the change works, say so.
4. Keep each commit one concern; the merged result should be one squashable, revertible commit.
5. On conflicts with the base: rebase if the repository prefers it; if the conflict is in code
   owned by someone else or its resolution is not mechanical, stop and report the files.
6. On review: answer each comment with "fixed in <sha>" or a reason. Do not mark a thread resolved
   without one.

## Verification

- The PR touches one problem; `git diff --stat` matches the description.
- The title passes the repository's title rule; required links are present; no placeholders remain.
- The description lists what was not verified, or states that nothing was skipped.
- Commit trailers follow the repository's attribution policy (check its CI rules and settings).
- The verification claimed matches the evidence record for the PR head.

## Failure and escalation

- The work turns out to solve two problems: split it before review, not after.
- The repository's policy conflicts with the operator's instructions (for example on attribution):
  stop and ask; do not pick one silently.
- A required check cannot run for the PR: say so in the description and leave the PR unmerged.

## Done when

The PR solves one problem, follows the repository's title, link and attribution rules, has a short
description with verification and its gaps, and every review comment has an answer.

## Sources

- OpenCode, title and issue rules enforced by bots, "understand why your changes work", short
  descriptions, stop on conflicts:
  https://github.com/anomalyco/opencode/blob/67139d6827af3a337c80472c33f9cb7c6c2ce500/.github/workflows/triage-pr-standards.yml,
  https://github.com/anomalyco/opencode/blob/67139d6827af3a337c80472c33f9cb7c6c2ce500/.github/pull_request_template.md,
  https://github.com/anomalyco/opencode/blob/67139d6827af3a337c80472c33f9cb7c6c2ce500/CONTRIBUTING.md
- t3code, one underlying problem per PR, verification that states what was not checked:
  https://github.com/pingdotgg/t3code/blob/47f2c8d29e981c7723467efe137ee19e91df924e/CONTRIBUTING.md,
  https://github.com/pingdotgg/t3code/blob/47f2c8d29e981c7723467efe137ee19e91df924e/.github/pull_request_template.md
- Twenty, a CI check that rejects AI attribution trailers:
  https://github.com/twentyhq/twenty/blob/99ac0c8ab050f8f329254a00a7e4e9b07da96cc8/packages/twenty-server/scripts/check-blocked-contributors.ts
- Sentry, split PRs across non-atomic deploys, no customer identifiers:
  https://github.com/getsentry/sentry/blob/c692fefae8eaee263af3491f30747bae2eb2d756/AGENTS.md
- Temporal, PR descriptions checked for empty or placeholder sections:
  https://github.com/temporalio/temporal/blob/49b2e1e954022de8ab4325dd8ec482f753ba6173/.github/workflows/check-pr-placeholders.yml

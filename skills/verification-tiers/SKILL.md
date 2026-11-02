---
name: verification-tiers
description: Choose and run the right verification profile — fast for the inner loop, full on merge, nightly for fuzzing, mutation, benchmarks and heavy suites — and record its scope. Use when deciding what to run for a change, configuring profiles, or reporting which checks a result covers.
---

# Verification tiers

Three profiles, one evidence standard. A cheaper profile covers less; it never reports more than it
ran. Anything outside the recorded scope is unverified.

| Profile | When | Runs | Budget |
| --- | --- | --- | --- |
| `fast` | Every edit loop | Changed units: format, lint, targeted tests | Seconds to a few minutes |
| `full` | Before merge | The required gate plus security scanners | The repository's CI time |
| `nightly` | Scheduled | Fuzzing, mutation testing, benchmarks, heavy geometry or integration suites | Hours, off the critical path |

## Activate when

- Choosing what to run before reporting a change.
- Configuring `commands.fast`, `commands.full` or `commands.nightly` in `.agents/engineering.json`.
- A check is too slow for the inner loop and someone proposes dropping it.

## Inputs and assumptions

- `./.agents/bin/eng impact --base origin/main` for the changed files, symbols and likely tests.
- The repository's required checks (`AGENTS.md`, CI) for the `full` profile.

## Permissions and restrictions

- Moving a check from `full` to `nightly` lowers the merge gate; that is a policy change and needs the
  repository owner's approval.
- `nightly` has no fallback: an empty nightly profile is `blocked`, never a pass.
- Do not narrow `--scope` and present the result as covering the whole change.
- Test selection fails open: if the changed files, the impact map or coverage data cannot be
  resolved, run everything. Files with global effect (test configuration, shared fixtures, settings,
  migrations, build scripts) always trigger the full suite; keep that list explicit, with a reason
  per entry.

## Workflow

1. Run `eng impact` and pick the tests it lists plus the area's own suite. To reproduce a CI
   failure, run CI's own selected test list, not a guess.
2. Inner loop: `./.agents/bin/eng verify --profile fast --scope "<crates, packages or tests run>"`.
3. Before merge: `./.agents/bin/eng verify --profile full`. This is the gate; its evidence must be
   for the revision that merges.
4. Scheduled: `./.agents/bin/eng verify --profile nightly`. Failures open a work item with an owner;
   they do not silently wait for the next night.
5. Report the profile, the scope and the evidence id. List what the profile did not cover.

## Verification

- The evidence record shows `profile`, `scope` and `duration_s`, and a verdict for exactly that scope.
- Every change that merges has `full` evidence on its merge revision.
- A `nightly` failure has a work item and an owner within one working day.

## Failure and escalation

- `fast` is too slow: measure it first (`build-performance`), then narrow by impact; do not delete
  checks.
- `full` fails on something unrelated: record it as pre-existing with evidence and escalate; do not
  merge over it without the owner's decision.
- No `nightly` profile exists for code that needs one (parsers, kernels, unsafe code): propose one.

## Done when

The result names its profile and scope, the evidence matches it, and anything not covered is listed
as unverified.

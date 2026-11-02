---
name: diff-hygiene
description: Keep a diff to what the task needs, in the repository's own idiom, with no generated drift and no new suppressions. Use before committing any code change, and when reviewing a diff for agent over-engineering. For structural changes with no behavior change use safe-refactor.
---

# Diff hygiene

Most agent-written defects are not wrong logic but extra code: a reimplemented helper, a defensive
`try`/`catch` the area never uses, a comment restating the line, a suppression that hides a warning,
a hand-edited generated file. Every line in the diff should be one a careful maintainer of that
file would have written.

## Activate when

- Before committing any change, as a self-review against the base branch.
- A diff adds helpers, wrappers, comments, casts, `try`/`catch` blocks or lint/type suppressions.
- A change touches generated code, lockfiles, translation catalogs or other pipeline-owned files.
- A check passes locally but the result may come from a cache or a stale build artifact.

## Inputs and assumptions

- The base branch (`origin/main` or the repository's default) and the full diff against it.
- The neighboring files in the directory being edited. They outrank general style advice, unless
  the repository marks them as legacy.
- The repository's lint, format, type and generate commands.

## Outputs

- A diff limited to the task, matching local idiom, with generated files regenerated, not edited.
- No new lint or type findings in touched files, and no new or broader suppression.
- A note of any repository-owned baseline (suppression count, coverage floor) that moved, and in
  which direction.

## Permissions and restrictions

Never hand-edit a generated file; change its source and regenerate. Never add or broaden a lint,
type-checker or scanner suppression without a reason in the code and the owner's review. Never
raise a baseline or suppression budget to get green; baselines only go down. Do not commit
pipeline-owned files (translation catalogs, generated clients, lockfiles from another tool) unless
the task is to change them. Do not mix formatting or refactoring into a behavior change.

## Workflow

1. Read the diff against the base (`git diff origin/main...HEAD`) as a reviewer would.
2. Remove what a maintainer would not add:
   - helpers or abstractions used once;
   - a reimplementation of a utility the codebase already has (search for it by behavior: `rg` the
     name, then the operation);
   - `try`/`catch`, null checks or casts that are abnormal for that area; validate unknown input
     once at the boundary instead;
   - comments that narrate the code; keep comments that explain a non-obvious why;
   - speculative handling of a race or edge case nobody has shown is real. If you believe it is
     real, state the failure mode and likelihood and ask before adding the complexity.
3. Generated artifacts: run the documented generate command and check that it leaves no diff
   (`<generate> && git diff --exit-code`). Commit source and output together.
4. Paired files move together: a manifest change with its lockfile, an example config with its
   schema or docs. A lone half is a defect.
5. Lint the files you touched and add no new findings. Fix pre-existing findings in a separate
   commit or PR, not inside the behavior change. Where the repository's CI requires every touched
   file to be clean (OpenCode does this for its GUI packages), make that cleanup a separate commit
   in the same PR.
6. Re-run the checks without caches before claiming a fix (clear the task cache, rebuild the
   shared package, run the type checker directly). A cached pass is not evidence for this tree.

## Verification

- `git diff --stat` lists only files the task needs; each is explainable in one sentence.
- The generate command leaves no diff; lint and type checks report no new findings in the touched files, uncached.
- No new suppression, `any`-style escape, raised baseline or edited generated file appears in the
  diff (`rg` for the repository's suppression syntax in the added lines).

## Failure and escalation

- A suppression seems necessary: add the narrowest one with a reason and flag it for review in the
  PR description; it is not auto-approvable.
- The neighboring code is the problem the rule exists to stop spreading: follow the written rule,
  not the neighbor, and say so in the PR.
- Regeneration changes files outside the task: stop; the base is out of date or the generator is
  not deterministic. Report it instead of committing the drift.

## Done when

The diff contains only what the task needs, in local idiom, with generated files regenerated,
paired files together, no new findings or suppressions, and checks re-run uncached.

## Sources

- OpenCode, anti-slop style rules, the `/rmslop` self-review command and CI that keeps touched GUI files clean:
  https://github.com/anomalyco/opencode/blob/67139d6827af3a337c80472c33f9cb7c6c2ce500/AGENTS.md,
  https://github.com/anomalyco/opencode/blob/67139d6827af3a337c80472c33f9cb7c6c2ce500/.opencode/command/rmslop.md,
  https://github.com/anomalyco/opencode/blob/67139d6827af3a337c80472c33f9cb7c6c2ce500/script/lint-changed.ts
- t3code, suppressions must state a reason and are never auto-approvable:
  https://github.com/pingdotgg/t3code/blob/47f2c8d29e981c7723467efe137ee19e91df924e/oxlint-plugin-t3code/rules/require-suppression-reason.ts,
  https://github.com/pingdotgg/t3code/blob/47f2c8d29e981c7723467efe137ee19e91df924e/.macroscope/approvability.md
- Twenty, reimplemented utilities as the most common AI defect, cache-free verification, paired
  files:
  https://github.com/twentyhq/twenty/blob/99ac0c8ab050f8f329254a00a7e4e9b07da96cc8/CLAUDE.md,
  https://github.com/twentyhq/twenty/blob/99ac0c8ab050f8f329254a00a7e4e9b07da96cc8/packages/twenty-utils/dangerfile.ts
- Temporal, regenerate in CI and fail on any diff:
  https://github.com/temporalio/temporal/blob/49b2e1e954022de8ab4325dd8ec482f753ba6173/Makefile

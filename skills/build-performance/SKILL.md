---
name: build-performance
description: Make builds and CI faster without lowering the gate. Use when compile, test or CI time is the bottleneck, when adding a compiler cache, faster linker or test runner, or when someone claims a build optimisation; every change needs before/after numbers.
---

# Build performance

Measure before changing anything, change one thing, measure again, keep the number. An optimisation
is accepted only with before/after data and no drop in what the gate checks.

## Activate when

- Builds, tests or CI runs are the bottleneck for agents or reviewers.
- Adding or tuning a compiler cache, linker, test runner, workspace layout or CI cache.
- Someone reports a build as "faster" without numbers.

## Inputs and assumptions

- The exact command, toolchain version, build profile, machine and whether the cache was warm.
- The CI workflow and its required checks.
- For a shared cache: an S3-compatible bucket (or equivalent) with separate read-only and read-write
  credentials, injected at runtime.

## Permissions and restrictions

- Only main-branch CI writes to a shared cache. Agents and pull-request builds get read-only
  credentials, so an unmerged change cannot poison what later builds trust.
- Separate cache prefixes per project and per toolchain version.
- Cache and signing credentials never enter the repository, logs or evidence.
- Removing, skipping or narrowing a required check is not a build optimisation.

## Workflow

1. Baseline: cold and warm timings with enough runs to see variance (`hyperfine`), per-crate timing
   (`cargo build --timings`), cache statistics (for example `sccache --show-stats`), CI step times.
2. Find the dominant cost: linking, a few large crates, test execution, dependency rebuilds, cache
   misses, or queueing for a runner.
3. Apply one change. Common ones for Rust:
   - a shared compiler cache with path remapping and a fixed workdir so cache keys match across
     machines; incremental compilation off in CI (`CARGO_INCREMENTAL=0`);
   - a faster linker (mold or lld);
   - a faster test runner (cargo-nextest) and change-scoped tests from `eng impact`;
   - workspace-hack or dependency-layer caching (cargo-hakari, cargo-chef) where rebuilds dominate.
4. Measure again under the same conditions. Record both numbers with the change
   (`eng verify --cache-stats <json>` keeps cache statistics in evidence).
5. Keep it only if it is faster and the gate still runs the same checks; otherwise revert.

## Verification

- Before and after numbers with run count, cold/warm state and machine are in the PR or evidence.
- The required checks before and after are the same list.
- Cache write access is limited to main-branch CI (show the credential scoping).

## Failure and escalation

- Faster but flaky: revert and investigate (`failure-investigator`).
- Cache hit rate stays low: check keys (paths, toolchain, env, `RUSTFLAGS`) before adding capacity.
- A speedup needs a gate change: stop and ask the owner; record it as a policy decision.

## Done when

The change is merged with before/after numbers, the gate is unchanged, and the numbers are kept
where the next improvement loop can read them.

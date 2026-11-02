---
name: test-design
description: Decide whether a test is worth adding, where it goes and how to make it deterministic. Use when writing, extending or reviewing tests, or when a test is slow, timing-dependent or flaky. For the red-then-green proof of a bug fix use regression-guardian; for quarantining a flaky test use failure-investigator.
---

# Test design

A test is code the project maintains forever. It earns its place by protecting an observable
contract that a credible regression would break and no existing test already guards. Agents tend
to write too many tests, at the wrong layer, held together by sleeps.

## Activate when

- Adding or extending tests for a feature or fix.
- A test needs a timeout, a retry, a sleep or a polling loop to pass.
- A suite is slow or flaky, or a review says "this test does not prove anything".
- Code reads durable state, retries requests or handles partial failure.

## Inputs and assumptions

- The repository's test layers (unit, integration, end-to-end), their commands and conventions.
- Existing tests for the area: read them before writing a new one.
- The behavior under test, stated as an observable contract.

## Outputs

- The smallest set of tests, at the lowest layer that fails on the unfixed code.
- For each new test: the contract it protects, the regression that would break it, and why no
  existing test catches that regression (in the PR description, not as a comment).
- The kind of evidence the change needs if a test is the wrong tool (see step 6).

## Permissions and restrictions

Never make a test pass by raising a timeout, adding a retry, adding `sleep`, polling, or skipping
it on one platform. Never add a seam to production code only so a test can reach it. Never assert
on wall-clock time differences. A skip needs a linked issue and a reason in the code. Do not
loosen a golden file, fixture or expected value to make a test pass; that is a behavior change.

## Workflow

1. Answer three questions before writing: which observable contract does this protect, which
   credible regression would make it fail, and why does no existing test catch it? If you cannot
   answer all three, do not add the test.
2. Extend before you add: a new row in an existing table test beats a new test. One contract has
   one owning test.
3. Place it at the lowest layer that fails on the current code. Do not test what the type system
   already guarantees, mirror mock calls back, or snapshot static markup.
4. Make it deterministic: inject the clock, seed randomness, wait on the event or condition itself,
   not on time. If the code under test waits, remove the wait from the test path, not the test.
5. For durable state, keep a corpus of real recorded states from older versions and replay them on
   every change. Keep fixtures that must be rejected too, so a check that became too permissive
   fails.
6. For failure handling, inject the fault (request failed, response lost after the work was done,
   storage call failed) and assert that the injected fault actually fired, so a refactor that
   bypasses the path fails the test instead of passing it.
7. Match evidence to the change: logic and protocol bugs get a failing test first; a purely visual
   change gets before/after captures; a server-only fix gets a test plus a short runtime transcript.
8. Ask of every new test: would it still pass if the implementation were reverted? If yes, it
   proves nothing; fix or delete it.

## Verification

- Each new test was seen failing on the code without the change (see regression-guardian).
- The test file contains no new sleeps, retries, raised timeouts or unreasoned skips (`rg` the diff).
- The suite passes repeatedly (`--repeat`/loop N times) with stable timing.
- Replay and fault-injection tests fail when their fixture or fault is removed.

## Failure and escalation

- A test is flaky: measure the failure rate over repeated runs and look for the commit that
  introduced it; do not call one green rerun proof. Quarantine only through failure-investigator.
- The only way to test is through a production seam: stop and propose a design change to the owner.
- No layer can observe the contract: state that the behavior is unverified rather than adding a
  test that asserts the implementation.

## Done when

Every new test has a stated contract and regression, sits at the lowest failing layer, is
deterministic, was seen failing before the change, and the suite contains no new timing crutches.

## Sources

- OpenCode, the three questions before adding a test and "never add production seams for tests":
  https://github.com/anomalyco/opencode/blob/67139d6827af3a337c80472c33f9cb7c6c2ce500/packages/app/AGENTS.md,
  https://github.com/anomalyco/opencode/blob/67139d6827af3a337c80472c33f9cb7c6c2ce500/.opencode/skills/unit-tests/SKILL.md
- t3code, lowest failing layer, extend before add, no sleeps or retries, evidence by kind of change:
  https://github.com/pingdotgg/t3code/blob/47f2c8d29e981c7723467efe137ee19e91df924e/AGENTS.md,
  https://github.com/pingdotgg/t3code/blob/47f2c8d29e981c7723467efe137ee19e91df924e/.macroscope/check-run-agents/test-signal.md,
  https://github.com/pingdotgg/t3code/blob/47f2c8d29e981c7723467efe137ee19e91df924e/.github/pull_request_template.md
- Temporal, replay corpus with must-fail histories, fault injection that fails if unused, flake
  attribution:
  https://github.com/temporalio/sdk-go/blob/3ad2ee1f2d7036c22583c7313d4f02b53f8f77f5/test/replaytests/replay_test.go,
  https://github.com/temporalio/temporal/blob/49b2e1e954022de8ab4325dd8ec482f753ba6173/docs/development/testing.md,
  https://github.com/temporalio/temporal/blob/49b2e1e954022de8ab4325dd8ec482f753ba6173/tools/flakereport/doc.go

---
name: independent-verification
description: Verify a change with a fresh agent that did not build it and tries to break it. Use before a required gate is reported as passed, when one agent built a change and another must certify it, or when a repository requires separation of builder and verifier.
---

# Independent verification

The builder never certifies its own work. A verifier with fresh context reads the diff, reruns the
checks and tries to break the change. Self-review is useful, but it does not satisfy a required gate.

## Activate when

- A change is ready for its required gate.
- The repository sets `"verification": {"independent": true}` in `.agents/engineering.json`.
- A builder agent reports "done" and the work is about to merge.

## Inputs and assumptions

- The diff, the task's acceptance criteria and the builder's evidence id — not the builder's
  conversation or conclusions.
- Access to run the repository's checks in a clean worktree.

## Permissions and restrictions

- The verifier does not edit the change. It reports findings; the builder (or a new owner) fixes.
- The verifier is a different identity from the builder: a different agent run, model session or
  person. Record both.
- Identities in evidence are declared, not authenticated; the record shows separation of duties, it
  does not prove it. Keep the harness logs that show which run did what.

## Workflow

1. Start from a clean checkout of the change's head; do not reuse the builder's worktree or output.
2. Read the diff and the acceptance criteria. Write down what would make the change wrong.
3. Try to break it: edge inputs, error paths, concurrency, compatibility, security boundaries, the
   behavior the change claims to preserve. Add a test for anything you find.
4. Run the gate yourself:
   `./.agents/bin/eng verify --profile full --builder <builder> --verifier <you> --run-id <id>`.
5. Report findings with file and line, the evidence id, and a verdict: accept, accept with notes, or
   reject.

## Verification

- The evidence record has `run.builder` and `run.verifier`, and they differ.
- The verifier's evidence is on the same revision the builder reported.
- Each finding is either fixed with a test or explicitly accepted by the owner.

## Failure and escalation

- The verifier cannot reproduce the builder's green result: the gate is not passed; report both
  records.
- No independent verifier is available: report the gate as `blocked`, not passed.
- Builder and verifier disagree on a requirement: escalate to the task owner.

## Done when

A verifier other than the builder has run the gate on the final revision, recorded both identities,
and its findings are resolved or accepted by the owner.

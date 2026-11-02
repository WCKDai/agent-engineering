---
name: parallel-agent-work
description: Run many agents on many repositories at once without collisions. Use when several agents or sub-agents work concurrently, share a build machine, or open pull requests against the same target; covers isolation, ownership, machine limits, merge queues, stop conditions and handoff.
---

# Parallel agent work

One task is one git worktree, one container (or equivalent sandbox), one branch and one pull
request. Agents never share a working tree. Work that cannot run yet waits in a queue; it does not
collide. `parallel-executor` splits a single task into units; this skill runs many tasks at once.

## Activate when

- Two or more agents or sub-agents will run at the same time on one machine or one repository.
- Builds are offloaded to a shared server or runner.
- Several pull requests will target the same branch in the same window.

## Inputs and assumptions

- A task list with an owner per task and the files or modules each task may change.
- The machine budget: cores, memory, disk, and how many builds it can take at once.
- The target branch's required checks and whether it has a merge queue or auto-merge.

## Permissions and restrictions

- No two concurrent agents own the same file or module. Shared files (lockfiles, schemas, generated
  code, CI, release metadata) belong to one integration owner and change in sequence.
- An agent works only in its own worktree: `./.agents/bin/eng worktree create <task> --owner <agent>`.
- No concurrent writes to a shared cache, database, device, port or fixture unless the tool is built
  for it (a compiler cache with locking is; a test database is not).
- Rewriting shared or published history, deploying and merging without the required checks need
  explicit human approval.

## Workflow

1. Write the ownership table: task, owner, owned paths, verification command, dependencies. Reject a
   plan where two rows own the same path.
2. Set machine limits before starting: a cap on concurrent builds (`parallel.max_worktrees`, build
   job flags such as `CARGO_BUILD_JOBS`, or cgroup/`systemd-run` CPU and memory limits). When the cap
   is reached, new work queues.
3. Give each agent: its scope, owned paths, verification command, budget, stop conditions and the
   handoff format below.
4. Each agent baselines in its worktree, implements, and runs `eng verify --profile fast`, then the
   repository's required gate.
5. Land through the merge queue or auto-merge with required checks, one change at a time. A change
   that touches a shared file waits for the integration owner.
6. After each merge, dependent branches update onto the new target and re-run their gate.
7. Remove finished worktrees with `eng worktree remove <task>`; run `eng digest` across the
   repositories to see stalled worktrees and failed gates.

## Stop conditions

An agent stops and hands off when it needs a path it does not own, its budget is spent, the same
check fails twice for an unexplained reason, it needs a credential or approval, or the target moved
under it in a way that changes its plan.

## Handoff note

State: task, branch, last commit, what is done, what is not, commands run with results and
evidence id, open questions, and the next concrete step. A handoff without evidence is a status
update, not a result.

## Verification

- Every merged change has its own passing gate evidence on the revision that merged.
- No two branches in flight changed the same owned path.
- The machine never ran more concurrent builds than its cap (record the cap and the peak).
- `eng digest` lists no stalled worktree that nobody owns.

## Failure and escalation

- Ownership conflict discovered mid-task: the later agent stops and proposes a patch to the owner.
- The shared machine is saturated: lower concurrency; do not drop required checks to fit.
- The merge queue keeps failing on one change: remove it from the queue and investigate with
  `failure-investigator`; do not retry blindly.

## Done when

Every task is merged with evidence, handed off with a note, or explicitly abandoned with a reason,
and no worktree, container or branch is left without an owner.

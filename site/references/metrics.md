# Delivery metrics

The weekly improvement loop (`skills/improvement-loop`) reads these numbers. Each has one
definition, a source and a direction. A metric without a recorded source value is unknown, not zero.

The kit records some inputs in evidence (`duration_s`, `cache`, `cost`, `run`, `profile`); it does
not compute these metrics itself. Compute them with a script over evidence files and forge data,
keep the script and its output with the review, and use the same definitions every week.

| Metric | Definition | Source | Better |
| --- | --- | --- | --- |
| Lead time per change | Time from the first commit of a change to its merge on the target branch. Report the median and p95 for the week. | Forge API (pull request created, first commit, merged times). | Lower |
| CI duration p50 / p95 | Wall-clock time of the required gate per run, for runs of the same profile. | `duration_s` of `full` evidence records, or the CI system's run durations. Do not mix profiles. | Lower |
| Cache hit rate | Compile requests served from cache / all cacheable compile requests, per project and toolchain. | `cache` in evidence (for example `sccache --show-stats --stats-format json`). | Higher |
| Flake rate | Runs whose verdict changed on a rerun of the same revision with no code change / all runs. Count active quarantines alongside it. | Evidence records for the same `git.head`; `.agents/quarantine.json`. | Lower |
| Queue depth | Changes waiting to merge (approved or auto-merge queued, not yet merged), sampled at a fixed time each day. | Forge API or merge-queue API. | Lower |
| Rework rate | Merged changes that were reverted or needed a follow-up fix within 7 days / merged changes. | Forge history (`Revert` commits, fixes that reference the original change). | Lower |
| Cost per merged change | Recorded cost of all runs in the window / changes merged in the window. Runs without a cost are counted and reported, never assumed free. | `cost` in evidence; forge merge count. | Lower |

## Rules

- Measure before optimising, and keep the number: store the before and after values with the change
  that moved them.
- One change per loop iteration, so a movement can be attributed.
- A speed gain that lowers the evidence level (fewer required checks, a narrower scope reported as
  full) is a regression, whatever the duration says.
- Small samples are reported as small. A week with three merges has no meaningful p95.

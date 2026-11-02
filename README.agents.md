# eng — repository engineering controls

This directory is a self-contained copy of the `eng` kit. It gives an agent, a human and CI the
same answers about what to run, what changed, what was verified, and what remains unverified.

It is deliberately small: Python standard library plus git, with optional external scanners. It does
not run a background service, require a database, or call a model.

## Layout

```text
.agents/
  bin/eng                 entry point
  lib/eng.py              one dependency-free CLI
  skills/                 seventeen task skills (SKILL.md)
  references/             lifecycle, evidence and trust policy
  config/                 semgrep, gitleaks and guard allowlist
  hooks/                  pre-commit and pre-push
  ci/                     standalone workflow template
  engineering.json        this repository's authoritative commands
  evidence/               hash-chained run records (gitignored)
```

`AGENTS.md` remains the repository's policy. `engineering.json` holds commands; this file explains
the generic workflow. Do not duplicate the same rule in three places.

## Daily loop

1. **Map** — `./.agents/bin/eng detect` and read `AGENTS.md`.
2. **Impact** — `./.agents/bin/eng impact --base origin/main` before editing shared code.
3. **Baseline** — `./.agents/bin/eng verify --profile fast`; record pre-existing failures.
4. **Isolate** — `./.agents/bin/eng worktree create <task>` for parallel or risky work.
5. **Implement** — smallest reversible change; add the regression test.
6. **Verify** — fast profile, targeted tests, then full profile for risky surfaces.
7. **Report** — commands run, results, skips, residual risk, evidence id.

## Commands

| Command | Purpose |
| --- | --- |
| `eng detect [--json]` | Stacks, manifests, modules, tests, CI, interfaces, ownership. |
| `eng init [--force] [--hooks] [--ci]` | Write config, AGENTS section, harness links, hooks, CI. |
| `eng verify --profile fast` | Run configured fast commands; write evidence. |
| `eng verify --profile full` | Fast/full commands + required security scans. |
| `eng verify --profile nightly` | Configured nightly commands (fuzzing, mutation, benchmarks, heavy suites) + security scans. No fallback: an empty nightly profile is blocked. |
| `eng impact --base <ref>` | Changed files, symbols, references, likely tests, contracts. |
| `eng security [--json] [--require]` | gitleaks, semgrep, OSV, actionlint, zizmor when installed. |
| `eng audit-actions` | Require every `uses:` to be a 40-hex commit SHA (or a reviewed exception). |
| `eng artifact <paths...>` | SHA-256 and size for release artifacts. |
| `eng release-check ...` | Require clean HEAD, passing full evidence, version, notes, rollback, artifacts and a performance comparison; write release evidence. |
| `eng perf-check ...` | Compare measured metrics with an accepted baseline; fail on a regression beyond the tolerance. |
| `eng guard staged` | Pre-commit guard: secrets, conflict markers, sensitive/large files. |
| `eng worktree create/list/remove` | Isolated `.worktrees/<name>` with an owner record. |
| `eng evidence verify/list/show` | Recompute hashes and check the evidence chain. |
| `eng digest [repos...] [--json]` | Exception-only "needs you" list across repositories. |
| `eng doctor [--json]` | Tool and repository readiness. |

`--json` works before or after the subcommand. `--root <path>` selects another repository.

## Skills

| Skill | Use |
| --- | --- |
| `repo-intelligence` | Map an unfamiliar repository with evidence. |
| `change-impact` | Estimate blast radius and required verification. |
| `regression-guardian` | Red-then-green regression tests. |
| `security-auditor` | Threat model, scanners, findings, remediation. |
| `safe-refactor` | Behavior-preserving structural change. |
| `parallel-executor` | Isolated units, ownership, sequential integration. |
| `performance-engineer` | Baseline, profile, measure, detect regressions. |
| `contract-guardian` | APIs, schemas, formats, migrations. |
| `failure-investigator` | Reproduce, root-cause, permanent guard. |
| `release-verifier` | Artifact-bound release evidence and rollback. |
| `verification-tiers` | fast / full / nightly profiles and their recorded scope. |
| `independent-verification` | A verifier other than the builder certifies the gate. |
| `parallel-agent-work` | Many agents on many repositories: ownership, machine limits, merge queue, handoff. |
| `build-performance` | Faster builds and CI with before/after numbers and an unchanged gate. |
| `agent-sandboxing` | Isolated execution, scoped short-lived credentials, egress allowlist. |
| `autopilot-readiness` | Attended → supervised autopilot → autopilot, one repository at a time. |
| `improvement-loop` | Weekly: worst bottleneck, one change, measured, kept or reverted. |

Skills activate from their frontmatter description. They are task-specific; repository rules stay in
`AGENTS.md`.

## Evidence

Every `verify` writes `.agents/evidence/<id>.json` plus logs under `<id>/`. The JSON records exact
commands, exit codes, durations, output hashes, git state, config hash, scanner versions and the
verdict. Each record is linked to the previous one by hash.

```sh
./.agents/bin/eng evidence verify   # integrity and chain
./.agents/bin/eng evidence list
./.agents/bin/eng evidence show <id>
```

`verify` records the profile, a `scope` (`--scope "<what ran>"`, default the configured commands) and
the total duration. `--run-id`, `--builder`, `--verifier`, `--cost` and `--cache-stats <json>` add
optional fields. Anything outside the recorded scope is unverified.

Set `"verification": {"independent": true}` in `engineering.json` to require that a `full` or
`nightly` gate names a `--verifier` different from the `--builder`; otherwise the gate is `blocked`.
Identities are declared by the caller, not authenticated: this records separation of duties, it
does not prove it.

A flaky test is quarantined in `.agents/quarantine.json` (`eng-quarantine/v1`): each entry names the
`test`, an `owner`, an `expires` date (`YYYY-MM-DD`) and a `reason`. The file only declares the
quarantine; the repository's test command must exclude the test itself. While active, every
`verify` lists the test as unverified. An expired or incomplete entry blocks the gate.

```json
{"schema": "eng-quarantine/v1", "entries": [
  {"test": "tests/test_net.py::test_retry", "owner": "agent-a", "expires": "2026-11-16", "reason": "times out on shared runners; see #123"}
]}
```

Evidence is local and gitignored; CI uploads it. Never edit a record to change a verdict. A check
that did not run is `skipped` or `blocked`, never `pass`. See `references/evidence.md`.

## Digest

```sh
./.agents/bin/eng digest ~/src/repo-a ~/src/repo-b --cost-cap 50
```

`eng digest` reads each repository's evidence, quarantine file and worktrees and lists only what
needs a human: the latest `fail` or `blocked` verdict per profile, every `unverified` note in those
records, a broken or tampered chain, a repository with no evidence, expired or soon-expiring
quarantines, spend over the cap (`--cost-cap`, or `budget.cost_cap` and `budget.window_days` in
`engineering.json`) and runs with no recorded cost, and worktrees with no commit or evidence for
`--stale-hours` (default 24). It exits `0` when nothing needs you and `1` otherwise; `--json` emits
`eng-digest/v1`. It never drops a blocked, skipped or unverified item to shorten the list. It reads
local files only; collecting CI evidence artifacts into those directories is the caller's job.

## Worktrees and parallelism

```sh
./.agents/bin/eng worktree create api-fix --owner agent-a
./.agents/bin/eng worktree list
./.agents/bin/eng worktree remove api-fix
```

The CLI refuses a dirty tree by default (uncommitted changes are not copied), refuses duplicate
names/branches, enforces `parallel.max_worktrees`, and refuses to remove a dirty worktree without
`--force`. Integration is sequential; re-run the full gate on the latest target revision.

## Release checks

```sh
./.agents/bin/eng artifact dist/app.tar.gz --json
./.agents/bin/eng release-check \
  --version 1.2.3 \
  --artifact dist/app.tar.gz \
  --notes notes/1.2.3.md \
  --rollback docs/rollback-1.2.3.md \
  --performance-baseline bench/baseline.json \
  --performance-current bench/current.json
```

A performance file is JSON with `schema: eng-perf/v1` and `metrics`; each metric has a
`value`, a `direction` (`higher` or `lower`) and an optional `unit`. The gate allows 5% by
default; pass `--max-regression 2` to tighten it. A missing metric, a non-numeric value or a
regression fails the release.

The check refuses a dirty tree, a version absent from `CHANGELOG.md`, missing notes or rollback, a
missing artifact, or a full evidence record that is not for the current HEAD. On success it writes a
hash-chained release record containing the artifact digest and the evidence it relied on. It does
not publish, sign or deploy; human approval remains required. `--require-sbom` and `--sbom`,
`--signature`, `--provenance` record optional artifact material.

## Security

- `gitleaks` scans tracked files only (a hard-linked tree), so build output and evidence logs are not
  scanned. History scanning is opt-in (`security.gitleaks_history`).
- `semgrep` uses the high-signal rules in `.agents/config/semgrep.yml`; add a test with every rule.
- `osv-scanner` needs a lockfile; "no package sources" is reported as skipped, not pass.
- `actionlint` checks `.github/workflows`. `zizmor` is used when installed.
- The pre-commit guard is a narrow, offline backstop — not a replacement for the scanners.
- Missing required scanners make a full run `blocked`; they are never silently skipped.

## CI

`.agents/ci/agent-verify.yml` is a standalone template. It installs pinned scanner versions, runs
`eng verify --profile full --ci`, and uploads evidence. Repositories with an existing workflow should
add the verify step after their toolchain setup instead of replacing working CI. Actions are pinned
to commit SHAs in the template; update them deliberately.

## Harnesses

- Claude Code: `.claude/skills` symlinks to `.agents/skills` (created by `init`).
- OpenCode: `.opencode/skills` symlinks to `.agents/skills`.
- Codex CLI and other AGENTS.md readers: discover the controls through `AGENTS.md`.
- Any harness: `./.agents/bin/eng` is a plain executable.

## Upgrade and rollback

Install/upgrade with `install.sh --target <repo>`; kit-owned code and skills are replaced, while
`engineering.json` and `guard-allow.txt` are preserved unless `--force`. Rollback is a git checkout of
the previous `.agents/` directory; evidence records remain valid because their schema is versioned.

## Known limits

- Impact analysis is textual, not a build graph.
- Secret scanning covers tracked files (and optionally history), not untracked files.
- OSV needs network and a supported lockfile.
- The agent evaluation harness is a separate, opt-in layer; it is not a model benchmark.
- A green gate is evidence about the checks that ran, not a proof of correctness or security.

# Changelog

## 1.3.0 — 2026-11-02

Skills generalized from how OpenCode, t3code, Sentry, Twenty and Temporal build software.

- Skills: safe-migrations, compatibility-and-deprecation, progressive-delivery, test-design,
  diff-hygiene, pull-request-craft, behavior-review and agent-guidance, each with pinned sources.
- verification-tiers: change-scoped test selection fails open; files with global effect always
  trigger the full suite.
- `references/inspiration.md` credits the five projects and the revisions read.
- No CLI, schema or evidence change.

## 1.2.0 — 2026-11-02

Running many agents on many repositories, fast, at the same evidence standard.

- `eng verify --profile nightly`: configured nightly commands plus security scanners; an empty
  nightly profile is blocked, never a fallback.
- Evidence records state `scope` and `duration_s`; optional `run` (id, builder, verifier), `cost`
  and `cache` fields are recorded when supplied. Additive within `eng-evidence/v1`; 1.1.x records
  still verify in the same chain.
- `"verification": {"independent": true}` blocks a full or nightly gate unless a verifier other
  than the builder is recorded.
- `.agents/quarantine.json` (`eng-quarantine/v1`): quarantined tests are reported unverified; an
  expired or incomplete entry blocks.
- `eng digest`: an exception-only "needs you" list across local repositories (`eng-digest/v1`).
- Skills: parallel-agent-work, verification-tiers, build-performance, independent-verification,
  agent-sandboxing, autopilot-readiness and improvement-loop; failure-investigator covers flake
  quarantine and golden/property tests.
- Build paths: parallel agents, fast Rust CI, autopilot promotion, hardware-in-the-loop (candidate).
- Toolbox: a failure mode for every tool; new conditional and candidate entries with the version
  and date checked. Nothing new is adopted.
- Principles: speed never lowers the evidence level; report by exception; keep the number.
- `references/metrics.md` defines the delivery metrics for the weekly improvement loop.

## 1.1.1 — 2026-10-30

- `security.osv_lockfile` lets a repository with historical nested vendor lockfiles scan only
  the workspace lockfile that is actually built.
- Record the Polykrom #281 merge, the open #282/#287 quality and security PRs, and PolyCore PR
  #28 on the ADAMANT repository status.
- No product behavior change; site and release artifact stay in sync.


## 1.1.0 — 2026-10-30

- ADAMANT portal generated from the kit, with `agents.json`, `llms.txt`, a skill explorer,
  build paths, a tool catalog, a hash-chained evidence model and a downloadable kit.
- `eng perf-check` and a release performance gate: higher/lower-is-better metrics are compared
  with an accepted baseline; a regression beyond the tolerance blocks the release.
- `eng release-check` now records and enforces performance alongside clean HEAD, full evidence,
  version, notes, rollback and artifact hashes.
- `eng audit-actions` requires full commit-SHA pins; the kit and pilot workflows are pinned.
- Node 24 action releases for checkout, setup-python and upload-artifact.
- Expanded Semgrep rules for `os.system`, `pickle.loads` and `execSync`, with positive and
  negative fixtures.

## 1.0.1 — 2026-10-29

- OSV scans inside worktrees; `install.sh` reads `VERSION`.

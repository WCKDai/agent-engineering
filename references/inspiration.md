# Inspiration

Eight skills in 1.3.0, and one extension to `verification-tiers`, generalize practices read in five
open-source projects. Each practice was read in the source at the pinned revision below on
2026-11-02; each skill's `## Sources` section links the exact files. What a project does is cited
as observed there; nothing here claims a WCKD repository already does it.

| Project | Revision read | Taken from it |
| --- | --- | --- |
| [OpenCode](https://github.com/anomalyco/opencode) | `67139d6827af3a337c80472c33f9cb7c6c2ce500` | Layered `AGENTS.md` files and skills activated by the artifact touched; "three questions" before adding a test; anti-slop style rules, the `/rmslop` self-review and "leave touched files clean"; experimental-first API with generated deprecated aliases; PR title and issue rules; stop and hand back on conflicts. |
| [t3code](https://github.com/pingdotgg/t3code) | `47f2c8d29e981c7723467efe137ee19e91df924e` | Named irreversible actions; the "hit every surface" checklist; suppressions that must state a reason; deterministic tests (no sleeps, polls or retries); lowest failing layer and "extend before you add"; evidence by kind of change; change-scoped checks that fail open; a size budget and evals for agent-facing text; triage policy loaded from a trusted ref. |
| [Sentry](https://github.com/getsentry/sentry) | `c692fefae8eaee263af3491f30747bae2eb2d756` and [develop.sentry.dev](https://develop.sentry.dev/) | Two-phase deletes and checked migrations; split PRs across non-atomic deploys; feature flags and options with defaults and reviewed rollout config; full-suite triggers for selective testing; one-label reverts; dated API deprecation with in-band headers and blackouts; review to reduce risk; `AGENTS.md` as the single source with path-scoped AI review. |
| [Twenty](https://github.com/twentyhq/twenty) | `99ac0c8ab050f8f329254a00a7e4e9b07da96cc8` | Reimplemented utilities named as the common AI defect; cache-free verification; append-only upgrade commands and cross-version upgrade CI; breaking-change detection from two running servers; approval for sensitive paths; CI agents with read-only tools and a schema; a CI check that rejects AI attribution; QA that inspects logs and database effects. |
| [Temporal](https://github.com/temporalio/temporal) and [sdk-go](https://github.com/temporalio/sdk-go) | server `49b2e1e954022de8ab4325dd8ec482f753ba6173`, sdk-go `3ad2ee1f2d7036c22583c7313d4f02b53f8f77f5` | Replay corpora with must-fail histories; behavior flags recorded in history and off by default for a release; add-only schema with a minimum compatible version; mixed-version tests; `buf breaking` against the merge base and regenerate-and-diff; fault injection that fails if the fault never fires; flake attribution over time; stable-hash rollouts; behavior-first review. |

## Mapping

| Skill | Main sources |
| --- | --- |
| `safe-migrations` | Sentry, Temporal, Twenty |
| `compatibility-and-deprecation` | OpenCode, Twenty, Temporal, Sentry |
| `progressive-delivery` | Sentry, Temporal |
| `test-design` | OpenCode, t3code, Temporal |
| `diff-hygiene` | OpenCode, t3code, Twenty, Temporal |
| `pull-request-craft` | OpenCode, t3code, Twenty, Sentry, Temporal |
| `behavior-review` | Temporal, Sentry, t3code, Twenty |
| `agent-guidance` | OpenCode, t3code, Twenty, Sentry |
| `verification-tiers` (extended) | t3code, Sentry |

## Limits

The practices were read, not run: no WCKD repository has adopted them yet, and a project may have
changed since the pinned revision. Where a practice depends on a project's own tools (Django
migration checks, Nx, Temporal's replayer), the skills state the general rule and give the tool
only as an example.

---
name: compatibility-and-deprecation
description: Prove that old and new versions work together across a rollout, and retire interfaces on a timeline. Use when two versions exchange data during an upgrade (wire protocols, stored messages, public or SDK/plugin APIs, separately deployed frontend and backend), or when deprecating an interface. Load contract-guardian first for the contract inventory, fixtures and change classification; use safe-migrations for database schemas.
---

# Compatibility and deprecation

contract-guardian says what the contract is and whether a change breaks it. This skill covers what
happens over time: N and N-1 running side by side during every deploy, clients lagging servers for
months, and removal as a dated process instead of an edit. Compatibility is proven from real
artifacts and real old states, not by reading the diff.

## Activate when

- Producer and consumer of a change deploy separately (frontend and backend, server and client,
  service and worker), or old and new instances share state during a rollout.
- Behavior that stored data or in-flight work depends on is changing.
- New public surface is being added, or existing surface is being deprecated or removed.

## Inputs and assumptions

- contract-guardian's inventory and classification (compatible, conditionally compatible,
  breaking) for the change.
- The repository's compatibility promise: supported versions, upgrade order, deprecation window.
- A way to build each side's real contract artifact at the merge base and at the head.

## Outputs

- A machine diff of the contract between merge base and head, attached to the PR.
- The deploy order for non-atomic boundaries.
- For new surface: where it lives while experimental and the condition for graduating it.
- For a deprecation: the deprecated alias kept, the removal version or date, how callers are warned,
  and the list of known callers.
- Evidence that an N-1 component worked with the N component.

## Permissions and restrictions

Do not remove shipped public surface without a deprecation period the owner approved; an immediate
removal needs an incident or a blocking vulnerability and the owner's sign-off. Do not hand-write
aliases a generator can produce. A diff tool that errors or cannot compare is a failure, not a
pass. Do not ship a change that needs both sides deployed at the same instant.

## Workflow

1. Name the boundary and both sides. If they do not deploy atomically, plan two changes: the side
   that must understand the new form ships first (the reader, or the backend before the frontend
   that calls it).
2. Build the contract at the merge base and at the head from real artifacts (built schema images,
   introspection of a running server, generated OpenAPI) and diff them with a format-aware tool,
   for example `buf breaking <head image> --against <base image>` for protobuf, or a GraphQL or
   OpenAPI differ. Removing something already deprecated is expected; anything else breaking goes
   back to contract-guardian's decision.
3. New public surface starts experimental: an unstable path, namespace or flag, with a test that
   pins the naming so it cannot leak into the stable namespace by accident.
4. Behavior that stored data or in-flight work depends on changes only behind a version recorded
   with that data. The new behavior defaults off until at least one release after the reader ships,
   so a rollback to N-1 can still read what N wrote.
5. Run old and new together: replay states recorded by N-1 (see test-design), run an N-1 client
   against the N server, or a mixed-version cluster where the project has one.
6. Deprecate on a timeline: remove in-house usage first, find the remaining callers, announce the
   removal version or date, warn in-band, and keep a generated alias until then.
   - Network APIs (HTTP, RPC): warn in responses (for example deprecation headers); after the
     date, fail intermittently before failing always, so the change reads as a deprecation and
     not an outage.
   - SDK, library and plugin APIs: mark the symbol deprecated so the compiler or runtime warns,
     and remove it only in the release the versioning policy allows (usually the next major, or
     the stated minor).

## Verification

- The contract diff ran on real artifacts from both revisions; its output is attached.
- Every breaking finding is reverted or has contract-guardian's approved decision.
- An N-1/N combination ran (replay, old client, or mixed cluster), not only on paper.
- Generated aliases and clients are reproducible: regenerate and `git diff --exit-code`.

## Failure and escalation

- The differ cannot build or parse one side: the check is blocked; fix that side's build.
- No compatibility policy exists: stop and ask the owner (contract-guardian).
- A change cannot be made compatible: escalate with the caller list and a proposed window; land
  nothing breaking until the owner decides.

## Done when

The contract diff ran on real artifacts and is clean or approved, the deploy order is stated, an
N-1/N combination was exercised, and any deprecation has a removal date or version, in-band
warnings and a generated alias.

## Sources

- OpenCode, experimental-first API and generated deprecated aliases until the next minor:
  https://github.com/anomalyco/opencode/blob/67139d6827af3a337c80472c33f9cb7c6c2ce500/AGENTS.md
- Twenty, breaking-change detection by diffing GraphQL and OpenAPI output of two running servers:
  https://github.com/twentyhq/twenty/blob/99ac0c8ab050f8f329254a00a7e4e9b07da96cc8/.github/workflows/ci-breaking-changes.yaml
- Temporal, `buf breaking` against the merge base, history-recorded SDK flags, mixed-version tests:
  https://github.com/temporalio/temporal/blob/49b2e1e954022de8ab4325dd8ec482f753ba6173/develop/buf-breaking.sh,
  https://github.com/temporalio/sdk-go/blob/3ad2ee1f2d7036c22583c7313d4f02b53f8f77f5/internal/internal_flags.go,
  https://github.com/temporalio/temporal/blob/49b2e1e954022de8ab4325dd8ec482f753ba6173/tests/mixedbrain/mixed_brain_test.go
- Sentry, non-atomic frontend/backend deploys and the HTTP API deprecation policy with blackouts:
  https://github.com/getsentry/sentry/blob/c692fefae8eaee263af3491f30747bae2eb2d756/AGENTS.md,
  https://develop.sentry.dev/backend/api/deprecation-policy/

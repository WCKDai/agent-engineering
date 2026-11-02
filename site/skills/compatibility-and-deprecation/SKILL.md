---
name: compatibility-and-deprecation
description: Keep old and new versions working together across a rollout, and retire interfaces on a timeline instead of breaking them. Use when a change touches a wire protocol, stored message, public API, SDK or plugin surface, or anything two versions of the software exchange during an upgrade. Use contract-guardian to inventory and classify the change; use safe-migrations for database schemas.
---

# Compatibility and deprecation

During every deploy, version N and N-1 run side by side, and clients lag servers for months. A
change is compatible only if it was proven from the real output on both sides, not by reading the
diff. Removal is a process with dates, not an edit.

## Activate when

- A change alters a protobuf/GraphQL/OpenAPI schema, an event, a queue message or an RPC.
- A public or SDK/plugin API gains, moves or loses a route, type, field or default.
- Producer and consumer of a change deploy separately (frontend and backend, server and client,
  service and worker).
- An interface is to be deprecated or removed.

## Inputs and assumptions

- The repository's compatibility promise: supported versions, upgrade order, deprecation window.
- A way to produce each side's real contract: generated schema, introspection, build image at the
  merge base and at the head.
- Which units deploy atomically and which do not.

## Outputs

- A machine diff of the contract between the merge base and the head, with its classification.
- For new surface: where it lives while experimental, and the condition for graduating it.
- For a break: the deprecated alias or version kept, the removal date, how callers are warned,
  and the list of known callers.
- The deploy order when producer and consumer ship separately.

## Permissions and restrictions

Do not remove or rename shipped public surface without a deprecation period the owner approved.
Do not hand-write deprecation aliases that a generator can produce. Do not treat a diff tool that
errors or cannot compare as a pass. Do not ship a change that needs both sides deployed at the
same instant. An immediate removal needs an incident or a blocking vulnerability and the owner's
sign-off.

## Workflow

1. Name the boundary and both sides. If they do not deploy atomically, plan two changes: the side
   that must understand the new form ships first (usually the consumer/reader, or the backend
   before the frontend that calls it).
2. Produce the contract at the merge base and at the head from the real artifacts (built schema
   images, introspection of a running server, generated OpenAPI). Diff them with a tool that
   understands the format, for example `buf breaking <head image> --against <base image>` for
   protobuf, a GraphQL schema differ, or an OpenAPI differ. Commit no hand-maintained copy.
3. Classify every finding: additive, dangerous, breaking. A removal of something already marked
   deprecated is expected; an undeprecated removal is breaking.
4. New public surface starts experimental: a clearly unstable path, namespace or flag, with a test
   that pins the naming so it cannot leak into the stable namespace by accident.
5. Behavior that existing stored data or in-flight work depends on changes only behind a version
   recorded with that data. New behavior defaults off until at least one release after the reader
   ships, so a rollback to N-1 can still read what N wrote.
6. For a deprecation: remove in-house usage first; find the remaining callers; announce a date;
   warn in-band (a response header, a log line, a compiler deprecation); keep a generated alias
   until the stated release. After the date, fail intermittently before failing always, so the
   change reads as a deprecation and not an outage.
7. Run old and new versions together against the same state where the project allows it (a
   mixed-version cluster, an N-1 client against the N server, replay of N-1 recorded data).

## Verification

- The contract diff ran on real artifacts from both revisions and its output is attached.
- Every breaking finding has an approved deprecation path or is reverted.
- An N-1 component worked against the N component (test, replay or mixed run), not only on paper.
- Generated aliases and clients are reproducible from the source (regenerate and `git diff
  --exit-code`).

## Failure and escalation

- No compatibility policy is written down: stop and ask the owner; do not assume "nobody uses it".
- The differ cannot parse one side: the check is blocked, not passed; fix the build of that side.
- A required change cannot be made compatible: escalate with the caller list and a proposed
  window; land nothing breaking until the owner decides.

## Done when

The contract diff is clean or every break has an approved, dated, in-band-warned deprecation; deploy
order is stated for non-atomic boundaries; an N-1/N combination was exercised.

## Sources

- OpenCode, experimental-first API and generated deprecated aliases until the next minor:
  https://github.com/anomalyco/opencode/blob/67139d6827af3a337c80472c33f9cb7c6c2ce500/AGENTS.md
- Twenty, breaking-change detection by diffing GraphQL and OpenAPI output of two running servers:
  https://github.com/twentyhq/twenty/blob/99ac0c8ab050f8f329254a00a7e4e9b07da96cc8/.github/workflows/ci-breaking-changes.yaml
- Temporal, `buf breaking` against the merge base, history-recorded SDK flags, mixed-version tests:
  https://github.com/temporalio/temporal/blob/49b2e1e954022de8ab4325dd8ec482f753ba6173/develop/buf-breaking.sh,
  https://github.com/temporalio/sdk-go/blob/3ad2ee1f2d7036c22583c7313d4f02b53f8f77f5/internal/internal_flags.go,
  https://github.com/temporalio/temporal/blob/49b2e1e954022de8ab4325dd8ec482f753ba6173/tests/mixedbrain/mixed_brain_test.go
- Sentry, non-atomic frontend/backend deploys and the API deprecation policy with blackouts:
  https://github.com/getsentry/sentry/blob/c692fefae8eaee263af3491f30747bae2eb2d756/AGENTS.md,
  https://develop.sentry.dev/backend/api/deprecation-policy/

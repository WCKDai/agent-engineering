---
name: agent-sandboxing
description: Run agents in isolated, least-privilege environments. Use when setting up where agents execute, giving an agent credentials or network access, running untrusted code or dependencies, sharing caches or artifacts between agents, or deciding who may approve releases and deploys.
---

# Agent sandboxing

Assume an agent can be steered by what it reads. Contain what it can reach: isolated execution,
short-lived scoped credentials, a network allowlist, no production secrets, and a human at every
release or deploy. The policy behind this skill is `references/trust.md`.

## Activate when

- Provisioning an execution environment for agents or sub-agents.
- An agent needs a token, network access, a shared cache or an artifact store.
- Running code, scripts or dependencies that have not been reviewed.

## Inputs and assumptions

- What the task needs to read, write and reach — and nothing more.
- The secrets and systems that must stay out of reach (production, signing keys, billing).

## Permissions and restrictions

- One task runs in one isolated container or VM. Untrusted work (unreviewed dependencies, fetched
  code, third-party PRs) gets stronger isolation, such as a user-space kernel or a microVM.
- Credentials are per task, scoped to the minimum (one repository, read-only where possible) and
  short-lived. No long-lived personal tokens inside an agent environment.
- No production secrets in agent environments. Deploy and release credentials live in the release
  pipeline behind human approval.
- Network egress goes through an allowlist (package registries, the forge, the cache endpoint).
- Shared caches and artifact stores are written only by trusted main-branch jobs; agents read
  (see `build-performance`).
- No agent approves its own release or deploy. A human gates both.

## Workflow

1. List what the task must access. Grant exactly that: repository, scopes, network hosts, duration.
2. Start the task in a fresh sandbox from a pinned image or environment definition.
3. Inject credentials at runtime; never write them to files that are committed, logged or uploaded.
4. Keep dependency checks in the required gate: licence, advisories and unused dependencies
   (for example cargo-deny, cargo-audit, cargo-machete in Rust).
5. Tear down the sandbox and revoke the credentials when the task ends.

## Verification

- The sandbox definition, token scopes, expiry and egress allowlist are written down and reviewed.
- A deliberately disallowed request (an unlisted host, a write to the cache from a PR job) fails.
- Release and deploy jobs require a human approval step that agents cannot satisfy.

## Failure and escalation

- A task needs broader access: stop and ask the owner; do not widen the sandbox from inside it.
- A secret appears in a log or artifact: stop, do not echo it, notify the owner and rotate it.
- A cache or artifact may have been written by an untrusted job: treat it as poisoned, purge it and
  rebuild from main.

## Done when

The task ran with only the access it needed, credentials are revoked, and nothing it touched can
reach production or a release without a human.

# Rollback — eng 1.2.0

Restore only the kit-owned files from `v1.1.1` (`.agents/bin`, `.agents/lib`, `.agents/skills`,
`.agents/references`, `.agents/hooks`, `.agents/ci`, `.agents/templates`, `.agents/README.md`) and
`VERSION`, for example by re-running the 1.1.1 `install.sh`. Do not replace `.agents/` wholesale:
leave `.agents/evidence/` (records and `index.jsonl`), `engineering.json` and `quarantine.json`
untouched. Then rebuild the site artifact and redeploy the previous Worker version. Evidence written
by 1.2.0 stays verifiable by 1.1.1 (the new fields are hashed like any other).

1.1.1 ignores two 1.2.0 controls, so replace them before rolling back:

- `verification.independent`: until the repository is back on 1.2.0 or later, require independent
  verification outside the kit (a required human or second-agent review on the pull request) and
  record the verifier in the PR. Do not simply delete the setting.
- `.agents/quarantine.json`: 1.1.1 does not report quarantined tests as unverified. Before rolling
  back, put each quarantined test back into the test command, or list every entry as unverified in
  each report and PR until it is fixed.

Keep the v1.2.0 evidence immutable; publish a new patch rather than rewriting assets.

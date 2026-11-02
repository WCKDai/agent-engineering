# Rollback — eng 1.2.0

Restore `v1.1.1`'s `.agents/` and `VERSION`, rebuild the site artifact, and redeploy the previous
Worker version. Evidence written by 1.2.0 stays verifiable by 1.1.1 (the new fields are hashed like
any other). Remove `verification.independent` from `engineering.json` and stop relying on
`.agents/quarantine.json` before rolling back, since 1.1.1 ignores both. Keep the v1.2.0 evidence
immutable; publish a new patch rather than rewriting assets.

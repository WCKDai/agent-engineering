# Rollback — eng 1.3.0

1.3.0 adds skills and one reference; it changes no CLI behavior, schema or evidence field. Restore
the kit-owned files from `v1.2.0` (`.agents/skills`, `.agents/references`, `.agents/README.md`) and
`VERSION`, for example by re-running the 1.2.0 `install.sh`, then delete the eight added skill
directories: the installer copies over existing files and does not remove any. Leave `.agents/evidence/`, `engineering.json`
and `quarantine.json` untouched. Then rebuild the site artifact and redeploy the previous Worker
version. Evidence is unaffected in either direction.

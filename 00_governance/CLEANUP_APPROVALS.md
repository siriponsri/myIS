# Cleanup approval register

No exact path is deleted by the restructure. Each candidate below requires a
separate Owner YES/NO decision before move or removal.

| Group | Evidence | Default action | Owner decision |
|---|---|---|---|
| Research legacy shells: `artifacts`, `config`, `docs`, `mlartifacts`, `mlruns`, `research`, `runtime`, `templates`, `tracks` | Empty after staged migration | Archive or remove after path checks | PENDING |
| Root `Projects` legacy wrapper | Mostly empty `Projects/myIS/App` | Archive after process handles close | PENDING |
| Root `Tools/experience-brain-is1-runtime` | Historical runtime, ~17k files | Preserve/archive; semantic review required | PENDING |
| Duplicate PDF groups | 17 SHA-256 groups / 34 files | Verify title/DOI then retain canonical | PENDING |

`PENDING` is intentional. A future cleanup change must name the exact paths and
record the Owner decision before using `git mv`, `git rm`, or filesystem removal.

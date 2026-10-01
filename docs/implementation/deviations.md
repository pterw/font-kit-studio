# Decisions and deviations

| ID | Decision / deviation | Basis | Cost if wrong |
|---|---|---|---|
| D001 | Ruling: use supplied v0.1.1 HTML as preserved baseline; characterize existing features and fix actual defects, without reconstructing v0.1.0. | Input already implements rows; no original v0.1.0 was supplied. | A genuine earlier baseline would require a separate import. |
| D002 | Ruling: use installed dispatching-parallel-agents as equivalent of requested dispatching-parallel-subagents; audits run concurrently, app writers sequentially. | Same purpose; all app tasks share one file. | Workflow naming may differ; no product effect. |
| D003 | Ruling: work in a new dedicated local repository on a feature branch; retain permanent plans/reports/ledgers rather than deleting SDD records. | User explicitly requests a repository and logs usable by any agent. | Local folder can be relocated later. |
| D004 | Ruling: map historical /mnt/data paths to this repository and supplement structural checks with behavioral tests. | Windows workspace; runtime evidence tests the specification. | Verification tooling differs from historical environment. |
| D005 | Evidence limitation: graph service Transport closed, no project/generation/coverage available; direct-source fallback. | Actual tool errors. | No indexed structural assurance; source/runtime checks govern. |
| D006 | Evidence limitation: earlier conversation requires sign-in and could not be read; proceed on the supplied spec and HTML. | Actual URL retrieval. | Unavailable chat decisions may require later reconciliation. |
- D006 retry: user supplied title Generate Font Specimen HTML. Retried conversation URL in a browser (access challenge) and web retrieval (login page); exact local title lookup returned no match. No prior discussion recovered.

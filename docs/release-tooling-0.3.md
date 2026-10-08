# Exact branch context for hosted release audits

The expected branch is mandatory and explicit. Candidate review before promotion
uses `dev/0.3.0`; final review after promotion uses `main`. The auditor compares
the actual branch exactly with this single argument; it has no default or generic
allowlist. It also requires the exact SHA, repository, successful push run and
all 28 expected job identities completed successfully. Artifact names/counts,
expiration, ZIP CRC, source/installed bytes, tool/log/report hashes, package
metadata, licensing, privacy and dataset checks remain required.

```bash
python -I tools/audit_hosted_delivery.py --folder candidate-ci --sha COMMIT --expected-branch dev/0.3.0 --output candidate-audit.json
python -I tools/audit_hosted_delivery.py --folder final-main-ci --sha COMMIT --expected-branch main --output final-audit.json
```

The 0.3.0 final tooling correction adds eight regression tests (1,008 total unit
tests per full matrix job). It covers both valid contexts, branch/SHA mismatches,
incomplete/duplicate/unexpected/failed jobs, failed runs, repository/event
provenance and missing/invalid branch context. The exact unit count was increased
from 1,000 to 1,008 to match these additions, without reducing any requirement.

Commit `43a38d5accf87f77731bc2fa4170dc77125e42a7` is a previous candidate,
not the final release commit. Its CI succeeded, but the older auditor rejected
the main context. No tag, GitHub Release or PyPI upload was made in that round.
The corrected commit requires its own main CI, branch-specific hosted audit and
rebuilt/audited wheel/sdist hashes. The 80/80 human acceptance remains recorded;
it does not replace these exact-commit gates or authorize bypassing a failure.

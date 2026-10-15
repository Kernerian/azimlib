# Publication state — 0.4.0

The 112 original IDs remain intact. Before publication the source checklist has
107 completed, exactly four deferred (2.08, 9.08, 13.06, 13.07), and 14.08 unchecked.
The immutable source checklist is not required to claim a completed publication
before uploading. Authorization and observed completion are separate records.

| State | Required evidence | Meaning |
|---|---|---|
| `pending` | No validated exact-candidate final authorization | Publication blocked |
| `authorized` | Versioned final human authorization, 107 completed, exactly four named deferments, only 14.08 pending, exact SHA/hashes/artifact provenance and both successful CI matrices | 107/108 active IDs complete; 14.08 authorized to start, not completed |
| `completed` | Authorization plus verified main/CI/tag/Release/PyPI hashes, clean PyPI install/smoke and public documentation observations | 108 active IDs complete, four still deferred; publication actually verified |

## Immutable candidate and separately versioned authorization

The final candidate SHA and archive hashes cannot be embedded in their own input
tree without a circular dependency. Build/audit the source candidate first, then
commit `release-authorizations/0.4.0.json` on the separate
`release/0.4.0-authorization` branch. This record does not change the candidate
tree, version, canonical archives or their hashes. Pass its exact immutable Git
commit as `authorization_ref`; the workflow verifies that it is the current tip
of that specific branch and reads the file at that commit via the repository API.

Required record fields:

- `schema: 1`, `version: "0.4.0"`, `state: "authorized"`;
- `candidate_sha`, exact wheel/sdist `package_sha256`, and `artifact` run/ID;
- `expected_inventory`: 112 original, 107 completed, four exact named deferments,
  `authorized_item: "14.08"`, active 107/108;
- `human_final_acceptance: true`, `approval_reference`, visual acceptance
  reference and SHA-256 of the versioned visual acceptance record;
- `allows_start_14_08: true`, `considers_14_08_completed: false`;
- `publication_execution_permitted`: false for a dry-run-only authorization.

An explicit later human publication confirmation is required to version an
execution-permitted record. Dry-run permission never grants permission to upload.
Changing the authorization record alone does not require rebuilding source
packages, but every new candidate SHA requires fresh CI/build/audits/hashes.

## Workflow preflight

`publish.yml` defaults to `dry_run: true`. Dry-run uses only
`validation/0.4-candidate` and read permissions; the OIDC publish job is skipped.
It verifies the versioned record, exact current branch/SHA, all 28 principal and
42 complementary jobs at that SHA/context, original artifact provenance,
canonical wheel/sdist hashes, strict twine, distribution/RECORD/notices/privacy,
and a clean wheel installation. It emits `state: authorized`, `completed: false`.

Real execution additionally requires explicit execution permission in the
versioned record, `dry_run: false`, exact current `main`, and both main-context CI
matrices. It retains the separate main CI gate and uses Trusted Publishing only
after the build/preflight job succeeds. It retrieves already audited bytes;
it does not rebuild packages or infer completion.

## Post-publication completion

`release_state040.completed` validates structured observations collected by the
post-publication audits: exact main and CI; annotated tag and published Release;
PyPI metadata hashes and independently downloaded hashes; isolated installation
from the public PyPI index, imports and smoke log hash; deployed documentation
version, exact source SHA, verified files and link-audit hash. Missing, stale or
divergent evidence fails closed. A checked box, `passed: true`, or an authorization
record alone is insufficient. This offline validator does not itself fetch those
observations and must not be presented as a live publication check.

Only the validated post-publication record may report 14.08 completed and an
operational 108/108 active total. The source checklist remains a historical
snapshot of the candidate; it must not be silently edited to change its identity.
The four deferred scientific/performance/planetary gates remain deferred.

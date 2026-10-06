# Publishing Azimlib

The publication workflow is manual. It checks that its commit is the current
`main` and that all 24 jobs of the test workflow passed for that exact commit.
It builds and audits wheel/sdist, runs an isolated installation smoke check,
and passes those distributions to a separate, narrowly authorized publish job.
It never publishes on an ordinary push or pull request.

## First PyPI project

Create a PyPI account, verify its email and enable two-factor authentication.
For a new project, register a pending GitHub Trusted Publisher under your PyPI
account's publishing settings with:

| Field | Value |
| --- | --- |
| PyPI project | `azimlib` |
| GitHub owner | `Kernerian` |
| Repository | `azimlib` |
| Workflow filename | `publish.yml` |
| Environment | `pypi` |

See [PyPI's new-project instructions](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).
No long-lived token, account password or recovery code belongs in this repository.
Registration of a pending publisher does not guarantee a project name is available.

## Release

1. Review the version, changelog, package metadata and third-party notices.
2. Require source/history privacy audits and a green 24-job CI matrix at `main`.
3. Run **Actions → publish → Run workflow** on `main` after publisher registration.
4. Check both publish jobs, PyPI version/files and their SHA-256 digests against
   the workflow's audited distributions. Test installation from PyPI.
5. Announce only the version actually uploaded. Update any prepublication note
   in the README after upload confirmation, and tag the exact released source.

PyPI version uploads are immutable. A failed or absent publisher registration
must be resolved rather than bypassing checks or committing a credential.
The project remains independent of Matplotlib and other GIS engines after upload.

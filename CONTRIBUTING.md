# Contributing to Azimlib

Small, reproducible reports and focused pull requests help improve the library.
Use GitHub Issues for bugs, proposals and questions. Before a substantial change,
explain the use case and check the [roadmap](docs/roadmap.md).

## Develop and verify

```bash
git clone https://github.com/Kernerian/azimlib.git
cd azimlib
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
python tools/audit_licenses.py
python tools/audit_publication_privacy.py
python -m build
python -m twine check --strict dist/*
```

The hosted CI tests Python 3.10–3.14 on Windows, Linux and macOS, with separate
compiler and desktop integration jobs. GUI checks require Tk and a display.
The [architecture](docs/architecture.md) and [API scope](docs/artist-scope-0.2.md)
describe the current contracts. Add meaningful regression checks when behavior
changes; keep examples reproducible and identify synthetic data.

## Independent implementations and provenance

Azimlib implements cartography itself. Do not add Matplotlib or another GIS
engine as a runtime backend. API compatibility does not authorize copying an
implementation, logo, icon or documentation. Identify sources, licenses and
copyrights for new external material; preserve applicable notices.
Do not bundle datasets unless redistribution rights are established.

Do not commit credentials, personal paths, private communication, build outputs
or local environments. Prefer portable paths in diagnostic reports.

By submitting a contribution, identify any relevant external sources and make
the original contribution available under the project's BSD-3-Clause license.
You retain copyright in your contribution; third-party licenses remain separate.
Follow the [code of conduct](CODE_OF_CONDUCT.md).

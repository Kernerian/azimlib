# Preparation for a future public distribution

The original implementation is BSD-3-Clause, Copyright (c) 2026 Kernerian.
Kernerian is a public identifier; no civil identity or company is inferred.
The separate licenses in [THIRD_PARTY_LICENSES](../THIRD_PARTY_LICENSES.md)
remain applicable. This preparation does not publish a release.

## Corrections

- ColorBrewer Blues includes its complete specific terms, referenced Apache
  license, required credit and an explicit package license reference.
- The undocumented Category10 sequence is replaced by the independently
  selected AZIM10 palette. TAB10 is an import compatibility alias only.
- The dark-background cycle is a lightened AZIM10 variant, not the reference
  tool's preset. Geographic data, CC0 samples and font binaries are unchanged.
- Reports use portable environment/source paths. Development conversations and
  quotations are removed while numerical measurements and limitations remain.
- Historical source snapshots are sanitized for distribution; original recorded
  execution hashes are not relabeled as new measurements. The publication
  mapping records original versus published hashes when the bytes differ.
- Wheel and sdist are rebuilt locally and audited after these corrections.

## Verification

```bash
python tools/audit_licenses.py --report .ci-results/licenses.json
python tools/audit_publication_privacy.py --history --report .ci-results/privacy.json
python tools/check_release_progress.py
python -m build
python -m twine check --strict dist/*
python tools/audit_distribution.py --wheel dist/azimlib-0.2.0-py3-none-any.whl --sdist dist/azimlib-0.2.0.tar.gz --output .ci-results/distribution.json
```

Archive hashes live outside their payload to avoid a circular hash. Local
results are separate from previously recorded hosted CI. The corrected implementation passed a subsequent 24-job hosted CI matrix.
For any later presentation or packaging changes, require a fresh successful
run at the exact publication commit; historical reports remain historical.

## Boundaries before a future public release

Local and remote histories were sanitized. GitHub Support removed the old PR
and unreferenced commits; subsequent API/ref verification confirmed their
absence. Old Actions runs and artifacts were removed, with no old caches.
Always repeat current ref/archive/privacy verification before changing visibility.
Recovery copies stay outside this repository and must never enter a release.

External IBGE inputs remain excluded. Their specific redistribution terms must
be established before any dataset bundling. Optional dependency binaries need
their own license review if shipped in an installer; future version resolution
is not fixed by this project's permissive license.

Technical scanning cannot prove exclusive authorship of every line, determine
all rights in AI-assisted code, or clear trademarks/patents. Git metadata is not
a chain-of-title instrument. Those legal limits cannot be removed by changing
a notice and are not represented as completed legal clearance.

## Local results and generated previews

[Remediation status](publication-remediation.md) separates resolved findings,
excluded materials and remaining server/legal boundaries. Current machine
reports are under `.ci-results/publication-*`; they are outside archive payloads
to avoid circular hashes. Historical CI JSON remains historical, including its
original MIT metadata; it does not describe the new package metadata.

The curated [README showcase](showcase.md) and final branding PNGs are committed
and included in the sdist; they do not enter the wheel runtime. Extended generated
previews are deliberately not committed or included in the wheel.
An optional local source ZIP can contain audited previews beside the source.
Documentation-link checks cover that local gallery, not the existence of images
in a fresh thin clone. Historical comparison previews and newly rendered maps
are distinguished by their separate inventories. Comparators are development
tools; Azimlib exports use its own renderer.

The manual [publishing workflow](publishing.md) gates a PyPI upload on the full
CI matrix at the exact source commit. Account setup is a separate prerequisite.

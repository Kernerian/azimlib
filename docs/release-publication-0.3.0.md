# Published Azimlib 0.3.0

Azimlib **0.3.0 was published on 2026-10-08** through GitHub Trusted Publishing.
The [checklist](release-progress-0.3.md) is complete at **80/80**.

- [PyPI version and files](https://pypi.org/project/azimlib/0.3.0/)
- [GitHub Release](https://github.com/Kernerian/azimlib/releases/tag/v0.3.0)
- [Exact released source](https://github.com/Kernerian/azimlib/tree/270405cb0030d3cb3a547f01ec78a2e3e728cd88)
- [Main CI: 28/28 jobs](https://github.com/Kernerian/azimlib/actions/runs/37717760902), with 1,008 tests in each unit matrix job
- [Successful Trusted Publishing](https://github.com/Kernerian/azimlib/actions/runs/37720613169)
- [Machine-readable publication evidence](release-publication-0.3.0.json)

## Distribution integrity

The annotated tag `v0.3.0` points exactly to `270405cb0030d3cb3a547f01ec78a2e3e728cd88`.
The wheel and sdist downloaded from both GitHub and PyPI are byte-identical
to the audited artifacts; the workflow reused those files without rebuilding.

| File | SHA-256 |
| --- | --- |
| `azimlib-0.3.0-py3-none-any.whl` | `83b78a6d953cc1cfecce8b3485631d1792fe3d66e33e9674211761ee256a04cf` |
| `azimlib-0.3.0.tar.gz` | `d334df9a9602f3612279663ee3a6659aaaa01631fc4c052c8a8e49aa4b578af4` |

A clean, uncached install of `azimlib==0.3.0` directly from PyPI passed the
installed core smoke, version/metadata checks, and both import styles:
`import azimlib as azl` and `import azimlib.pyplot as plt`. No optional,
reference or external geospatial library was required by that smoke.

Original code is BSD-3-Clause, copyright Kernerian. The metadata retains
`BSD-3-Clause AND CC0-1.0 AND LicenseRef-DejaVu AND LicenseRef-ColorBrewer`.
Separate [third-party notices](../THIRD_PARTY_LICENSES.md) remain applicable.

## Documentation revisions

[Stable](https://kernerian.github.io/azimlib/stable/),
[0.3.0](https://kernerian.github.io/azimlib/0.3.0/) and
[development](https://kernerian.github.io/azimlib/dev/) documentation are delivered
separately. Each site manifest records its exact source revision. Documentation
corrections do not move `v0.3.0`, replace either distribution or change the
recorded release CI. Earlier candidate reports remain historical snapshots.

The PyPI description belongs to the README embedded at the release commit;
later repository documentation edits do not replace it. Technical audits are
scoped evidence, not legal opinions or guarantees of exhaustive secret detection.

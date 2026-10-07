# Dependencies and distribution boundaries

The core has no mandatory third-party Python dependency. The declared build
and optional requirements are in `pyproject.toml`. Versions are not locked:
dependency licenses and binary payloads must be reviewed for each combined
application or installer that redistributes them.

| Group | Components | Terms |
|---|---|---|
| Optional rendering | Pillow; aggdraw, including AGG 2.0 | MIT-CMU/PIL-style permissive notices; AGG's specific notice |
| Optional arrays/compiler | NumPy; Numba; llvmlite; LLVM | BSD, additional bundled notices, Apache-2.0 with LLVM exception |
| Build and validation | setuptools, build, wheel, pytest, twine, packaging, PyYAML, tomli | MIT/BSD/Apache as applicable; preserve component notices if redistributing the tools themselves |
| Comparisons and font preparation | Matplotlib, fontTools, cycler, contourpy | Matplotlib's agreement; MIT; BSD. No runtime backend or vendored implementation |
| GUI/browser comparisons | Playwright/browser | Playwright Apache-2.0; browser terms vary. Not included in the wheel |
| Hosted CI | GitHub checkout/setup-python/upload-artifact actions; Xvfb/xauth | Separate CI tooling; no action implementation is shipped in Azimlib |
| Local history remediation | git-filter-repo 2.47.0 | MIT; external one-off tool, not vendored or required by Azimlib |

## Relevant transitive packages

Packaging tools can install pyproject_hooks, requests, urllib3,
charset-normalizer, idna, certifi, keyring, jaraco.classes/context/functools,
more-itertools, rich, markdown-it-py, mdurl, nh3, Pygments, docutils,
requests-toolbelt, rfc3986 and id. Comparators can install python-dateutil,
six, pyparsing, kiwisolver and tornado. Conditional dependencies include
SecretStorage, jeepney, cryptography, cffi, pycparser, importlib-metadata,
zipp, pluggy, iniconfig and exceptiongroup.

Most use permissive MIT/BSD/Apache terms, but certifi is MPL-2.0. Some tool
distributions include additional files: setuptools can include LGPL-licensed
autocommand; Docutils includes separately licensed editor integration. Their
presence in a build environment does not mean they are embedded in the wheel.
Do not summarize the entire development environment as exclusively BSD/MIT.

Pillow binaries can include FreeType, HarfBuzz, Brotli, Little CMS, libavif,
libjpeg-turbo, libpng, libwebp, OpenJPEG, TIFF, XZ and zlib-ng. NumPy binaries can
include OpenBLAS, LAPACK and a GCC runtime under GPL with its runtime exception.
Check complete bundled licenses and the exception for the exact binary shipped.
Do not infer a license only from the top-level project's package metadata.

No package-level third-party license is replaced by Azimlib's BSD-3-Clause.
Materials actually shipped by Azimlib are inventoried in
[THIRD_PARTY_LICENSES](../THIRD_PARTY_LICENSES.md).

The [observed development inventory](dependency-license-inventory.json) records
versions, declared requirements and hashes of available installed license files.
It is evidence of that environment, not a lockfile or a license clearance for
future binaries. `tools/inventory_dependency_licenses.py` regenerates it without
publishing home-directory paths.

## Geographic numeric comparison — development only

Stage3 uses an isolated pyproj 3.8.0/GeographicLib 2.1 environment exclusively as
black-box numerical oracles. Neither package is imported by runtime or required
by tests; no source code or upstream test dataset is vendored. Recorded numeric
outputs and versions are in [the core guide](geodesy.md). These tools are not
included in wheel/sdist or package requirements. Redistributing an oracle
environment would require reviewing its own licenses and binary dependencies.


## Optional UI integration in 0.3 development

The `qt` extra requires Pillow and PySide6-Essentials >=6.5; shiboken6 is its
binding dependency. Local 6.11.2 metadata declares LGPL-3.0-only OR GPL-2.0-only
OR GPL-3.0-only; Qt's proprietary commercial route is separate. Only QtCore,
QtGui and QtWidgets are used. Code/binaries/modules/licenses from this dependency
are not bundled into Azimlib's wheel/sdist. A frozen or combined application that
redistributes Qt must comply with its chosen license and the exact binary's
third-party terms; declaring the application BSD does not cancel those duties.
See [material boundaries](../THIRD_PARTY_LICENSES.md).

The `notebook` extra uses IPython >=8, public display_id/update and post_run_cell
hooks. IPython 9.17.1 has BSD-3-Clause metadata. Its transitive traitlets and
prompt_toolkit retain BSD notices; jedi/parso retain MIT; Pygments BSD-2-Clause;
asttokens, executing, pure-eval, decorator, stack-data, wcwidth, colorama/pexpect
and conditional typing/exception packages must be reviewed at their resolved
versions when bundling. None are vendored. Both extras are absent from core
installation/imports. Stdlib HTTP/threading/JSON supply the local live bridge.
Node is a development-only executable for the own client-protocol fixture.

The [observed optional dependency closure](interaction-dependencies-0.3.json)
records actual Windows versions, declared requirements and license-file hashes
for the two new extras. It is not a lockfile or permission to redistribute an
entire Qt binary installation without reviewing its complete notices.

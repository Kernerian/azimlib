# Third-party materials

The original Azimlib implementation, documentation and original toolbar artwork
are licensed under BSD-3-Clause, Copyright (c) 2026 Kernerian. This notice does
not relicense the materials below or claim exclusive ownership of them.

## Materials shipped in the package

| Material | Files and origin | Terms and notices |
|---|---|---|
| ColorBrewer Blues, five classes | `src/azimlib/styles.py`, and the corresponding development baseline; https://colorbrewer2.org/export/colorbrewer.json | Copyright 2002 Cynthia Brewer, Mark Harrower and The Pennsylvania State University. The complete specific terms are in `licenses/LicenseRef-ColorBrewer.txt`; the referenced Apache-2.0 text is in `licenses/Apache-2.0.txt`. |
| Viridis, magma, inferno and plasma | `src/azimlib/data/colormaps.json`, plus the five-stop viridis scale in `styles.py` and its development baseline; BIDS/colormap, https://github.com/BIDS/colormap/blob/master/colormaps.py | CC0-1.0. Nathaniel J. Smith, Stefan van der Walt and, for viridis, Eric Firing. See `NOTICE_COLORMAPS` and `licenses/CC0-1.0.txt`. RGB8 quantization and the smaller scale change the representation, not the upstream authorship. |
| Natural Earth geographic layers | Six compressed GeoJSON files in `src/azimlib/data/`; upstream commit and per-file hashes in `src/azimlib/data/manifest.json` | Public-domain data according to the publisher. Primary authors Tom Patterson and Nathaniel Vaughn Kelso, with contributors. See `licenses/Natural-Earth.txt` and https://www.naturalearthdata.com/about/terms-of-use/. |
| DejaVu Sans 2.35, four variants | `src/azimlib/fonts/*.ttf`; official upstream hashes in `docs/fonts-upstream.json` | Copyright 2003 Bitstream, Inc.; Arev portions copyright 2006 Tavmjong Bah; DejaVu changes are public domain. Preserve the complete `src/azimlib/fonts/LICENSE_DEJAVU`. Renaming restrictions apply to modified fonts; standalone font sales are restricted. |
| Font metrics | `src/azimlib/fonts/metrics.json`, extracted by `tools/font_metrics.py` | Derived from the above fonts; retain the same provenance and font notices. The extraction implementation is original Azimlib code. |

This product includes color specifications and designs developed by Cynthia
Brewer (http://colorbrewer.org/).

Commercial use of the materials above is permitted subject to their respective
terms. The BSD license of the implementation does not erase those terms.

## Original palette

`AZIM10` in `src/azimlib/cycles.py` is a new ten-color sequence selected for
Azimlib. The default and dark-background cycles use this sequence or its own
lightened variant. `TAB10` remains a compatibility alias for `AZIM10`; it does
not contain the Tableau/D3/Matplotlib Category10 sequence. Individual color
values are not represented as globally unique or exclusively owned.
The historical series oracle retains default-cycle roles rather than the
retired ten RGB values; tests materialize those roles with AZIM10.

## Separately installed dependencies

No external Python packages are embedded in the Azimlib wheel. Optional extras
install Pillow (MIT-CMU), aggdraw (permissive PIL-style terms including AGG),
NumPy (BSD and additional bundled notices), and Numba/llvmlite (BSD plus LLVM
and other component notices). Python and Tcl/Tk retain their own terms.
Redistributing a combined application requires auditing and preserving the
licenses of the actual dependency binaries, including Pillow codecs, NumPy's
BLAS/LAPACK and any GCC runtime exception. See `docs/dependencies.md`.

Matplotlib, fontTools, cycler, contourpy, Qt/PySide and Playwright are development
or comparison tools, not the cartographic backend. Their code/assets are not
vendored into the package. Using them does not make their licenses the license
of Azimlib's original implementation. Distributing those tools is a separate
licensing task.

External IBGE benchmark inputs are not shipped. Their specific redistribution
terms have not been established here; they must be checked before bundling any
such dataset. Numerical benchmark records do not grant a dataset license.

Generated gallery illustrations use synthetic fields/routes and the separately
credited geographic/font resources above. Reference-comparison previews are
rendered with development tools and retain their producer metadata. They are
not vendored implementations or toolbar artwork. The wheel contains no gallery;
see `docs/publication-readiness.md` for the local source ZIP and preview scope.

## Copyright identity and scope

Kernerian is the project's public copyright identifier, not a claim that a
company or verified legal entity of that name exists. Third-party copyright
notices remain unchanged. Git author labels, including automated labels, do
not by themselves establish legal authorship or exclusive title. This inventory
is technical documentation, not a legal opinion or a trademark/patent clearance.

## Optional OpenStreetMap database (development examples)

`optional-data/urban-sao-paulo-1.0` is a small, modified OpenStreetMap database,
© OpenStreetMap contributors, licensed under **ODbL 1.0**. It retains its own
LICENSE.txt, README, provenance and hashed catalog; it is excluded from both the
wheel and sdist. No OSM code or automatic download is used. The BSD license of
Azimlib code does not replace the database license. Derivative databases must
respect applicable ODbL sharing requirements; produced maps credit OpenStreetMap
and identify the ODbL data license. See [the data guide](docs/optional-data.md),
[OSM copyright](https://www.openstreetmap.org/copyright) and
[ODbL](https://opendatacommons.org/licenses/odbl/1-0/).

## Geographic numeric oracle records (development)

`docs/geodesy-reference-0.3.json` records factual coordinate outputs computed
through black-box calls to pyproj 3.8.0 and GeographicLib 2.1, in an isolated
development environment. No implementation, protected prose or published test
dataset from either project is vendored. The package does not redistribute
these libraries or depend on them. New geodesy, TM, topology and clipping code
is independently written under the original-code BSD 3-Clause license; published
mathematical references and numeric limits are listed in `docs/geodesy.md`.


## Optional UI / notebook dependencies (0.3 development)

The independently written Qt backend imports **PySide6-Essentials** (QtCore,
QtGui, QtWidgets) and its **shiboken6** binding dependency dynamically; it does
not vendor their code/binaries, Qt examples or icons. Installed 6.11.2 metadata
declares `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only`; Qt also offers a
commercial licensing route. These terms are **not replaced by Azimlib BSD**.
The Python archives declare an optional requirement only, not a combined Qt
installer. If bundling/freezing Qt/bindings, review the exact Qt build/modules,
third-party notices, license copies, source availability, user replacement and
modification/debugging rights required by the chosen LGPL/commercial terms.
No GPL-only Qt add-on module is imported by this backend. See [Qt's licensing
documentation](https://doc.qt.io/qtforpython-6/commercial/index.html),
[open-source obligations](https://www.qt.io/development/open-source-lgpl-obligations)
and [the dependency inventory](docs/dependencies.md). UI text uses the already
licensed bundled DejaVu font; no new font or toolbar artwork is copied.

The notebook adapter imports **IPython** through public display/event interfaces.
IPython 9.17.1 metadata declares BSD-3-Clause; copyright belongs to the IPython
Development Team. No IPython/Jupyter implementation is vendored. Optional
transitive packages retain their own notices: traitlets (IPython Development
Team, BSD), prompt_toolkit (Jonathan Slenders, BSD), jedi/parso (MIT), Pygments
(BSD-2-Clause), plus other version-dependent dependencies. Preserve their
actual notices if distributing these packages in a combined application.
Neither their licenses nor authorship become exclusive Azimlib property.

## Wordmark typography (artwork only)

The wordmark PNG in `docs/_static/branding` uses **Carlito Bold Italic**,
designed by Łukasz Dziedzic, **SIL OFL 1.1**. This voluntary credit records
rasterized lettering; Carlito font software is not shipped in source, wheel
or sdist. The exact design-time font binary/version is not retained. Upstream
reference: https://github.com/googlefonts/carlito and
https://github.com/google/fonts/blob/main/ofl/carlito/OFL.txt (copyright 2013
The Carlito Project Authors; Reserved Font Name Carlito). The official FAQ
https://openfontlicense.org/ofl-faq/ permits logos/commercial artwork without
mandatory acknowledgement or OFL relicensing of that artwork. Redistributing
or embedding the font itself would require preserving its actual OFL/copyright.
The code and original logo composition keep their existing BSD terms.

## Optional video encoder

`animation.FFMpegWriter` invokes an explicitly selected, separately installed
FFmpeg executable. No FFmpeg, libx264 or codec binary/source is redistributed
or required by the Python archives. FFmpeg builds/codecs have version/build-
dependent LGPL/GPL and possible patent obligations; embedding or distributing
an encoder requires an audit of that exact build. The Azimlib writer is original
BSD code; it does not grant codec rights. GIF encoding uses the optional Pillow
installation already listed above.

### Optional documentation parser

markdown-it-py and mdurl retain their upstream MIT terms. The docs extra/build
uses these separately installed development tools; their implementations are
not distributed in Azimlib or copied into generated site assets. Preserve their
license notices if bundling their packages. See docs/dependencies.md.

# Third-party materials

## Static planetary reference parameters (0.5 development)

`bodies.py` records four sets of numerical radii from NASA NAIF pck00011
(2022-12-27), with URL and source SHA-256 in BodySource and the
[foundation guide](docs/foundation-0.5.md). These factual parameters are
converted from kilometres to metres. No PCK kernel, CSPICE implementation,
NAIF prose or artwork is bundled or relicensed as Azimlib code.
WGS84 retains its existing parameter source and notices.

`tests/fixtures/planetary-050.json` contains 25 original numeric test inputs
and corresponding outputs computed using CSPICE georec via SpiceyPy. Generator
version, equations/reference URLs and numerical tolerances are recorded in the
fixture. It contains no third-party implementation or documentation text.
SpiceyPy/CSPICE are reference-only QA tools, not new runtime dependencies;
they are unnecessary to run the frozen numeric tests. Original static
conversion code reuses Azimlib's existing frame equations and generic radial
surface geometry. These distinctions do not change third-party rights.

## Phase B numeric QA records (0.5 development)

`tests/fixtures/surfaces-050.json` records original test inputs and factual
black-box outputs from pyproj 3.8.0 / PROJ 9.8.1, GeographicLib 2.1 and
SpiceyPy 8.3.0 / CSPICE N0067. The generator and fixture identify origins,
versions, normalization and tolerances. No implementation, kernels, upstream
prose, imagery or dataset is incorporated. These QA tools are not imported by
the runtime or frozen tests. Existing upstream license notices elsewhere in
this inventory remain applicable to the tools where installed separately.
The gallery's non-Earth elevations and texture are original deterministic
synthetic data, BSD-3-Clause, Copyright (c) 2026 Kernerian. Natural Earth,
fonts, colormaps and all other existing third-party terms remain unchanged.

## Optional GPU rendering

The `gpu` extra uses ModernGL and glcontext as generic OpenGL/context bindings.
The tested versions are 5.13.0 and 3.1.0, respectively. Their MIT notices remain
in [ModernGL.txt](licenses/ModernGL.txt) and [Glcontext.txt](licenses/Glcontext.txt),
with package/source identity in [gpu-dependencies-0.4.json](docs/gpu-dependencies-0.4.json).
Their binaries and source implementations are not bundled in Azimlib archives.
Copyright (c) 2017-2024 Szabolcs Dombi, Einar Forselv (ModernGL); Copyright (c)
2021 ModernGL Contributors (glcontext). Preserve these notices with any
redistribution of those components. Azimlib's original shaders, coverage/stroke
meshes, caches, texture atlas and depth/UV integration remain BSD 3-Clause.
Graphics drivers/OpenGL implementations are installed separately and retain
their own terms; Azimlib does not distribute them. Pillow is credited below.

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

## Optional official datum grids (0.4 development)

The pinned model descriptions in `src/azimlib/data/optional-grids.json` refer to
data published by Toitū Te Whenua Land Information New Zealand (LINZ), package
`proj-datumgrid-nz` version 20200110, upstream commit
`62ff69da8713f0167d319d0263f1657ac380f273`.
Only model metadata are bundled; **NTv2/GTX grid payloads are not in wheel/sdist**.
This does not incorporate PROJ software or its implementation.

Downloaded LINZ data retain [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/),
attribution to LINZ, the original upstream notice, and the complete license in
`licenses/CC-BY-4.0.txt`. The acquisition tool preserves all three with the data.
Redistributors must retain attribution, link the license and indicate modifications;
no endorsement is implied. Azimlib's BSD license does not replace these terms.
See [model provenance and validation](docs/datum-grids.md).

## Own routing implementation and optional graph data (0.4 development)

`routing.py` and `_routing_osm.py` contain original Azimlib graph construction,
spherical snapping, stateful A*/Dijkstra and OSM tag interpretation. Published
OSM format/tag facts were consulted; no third-party router implementation,
code, generated schema or documentation snippet is incorporated. See the
[coverage and protocol references](docs/routing-0.4.md).

Optional OpenStreetMap-derived graph indexes retain their source ODbL terms,
copyright, attribution and complete license text in the graph payload. They are
not bundled into wheel/sdist. Azimlib's BSD 3-Clause license covers its original
implementation and synthetic fixtures, not exclusive ownership of OSM data.

## Optional complex typography (0.4 development)

The original `text_engine.py` compositor and `_unicode_icu.py` C-API binding use
separately installed generic text engines, not Matplotlib implementations:
uharfbuzz (Apache-2.0), HarfBuzz (permissive upstream notices), fontTools (MIT),
aggdraw (its existing PIL/AGG notices) and the operating system's ICU.
No engine binary, source, generated Unicode table or third-party Python binding
is vendored. The `text` extra does not introduce python-bidi or LGPL bidi code.
`_bidi.py` is an original implementation of the normative UAX #9 rules, using
ICU character properties rather than ICU's bidi resolver. No bidi implementation
was copied, translated or ported from another project.

Full reference notices are in `licenses/UHarfBuzz.txt`, `licenses/HarfBuzz.txt`,
`licenses/FontTools.txt` and `licenses/ICU.txt`; origins/versions/SHA-256 are in
`docs/text-dependencies-0.4.json`. ICU's notice is a pinned upstream reference,
not a declaration that all installed ICU releases have identical terms. When
redistributing engine binaries, preserve the notices for the actual resolved
version, including transitive notices supplied by its distributor.

Optional Unicode 15.1 conformance datasets are acquired separately, with pinned
sizes/hashes by `tools/validate_unicode_text.py`. They are not in wheel/sdist.
Their Unicode copyrights remain in the unmodified files; the acquisition also
preserves the full official permission notice in `licenses/Unicode-Data.txt`.
That notice is not replaced by Azimlib's BSD license. The standard's algorithmic
rules inform the original resolver; no prose or reference implementation from
the standard is incorporated into it.

Optional Noto Devanagari and Noto CJK validation fonts retain OFL-1.1 and their
upstream copyrights, including reserved-name conditions where present. Complete
licenses are `licenses/Noto-Devanagari.txt` and `licenses/Noto-CJK.txt`; immutable
download records are `src/azimlib/data/optional-fonts.json`. **Neither font is
distributed in Azimlib wheel/sdist.** Acquisition preserves unmodified bytes and
full notices. Outputs retain font provenance/license text; those fonts and
contours are not claimed as exclusively owned original Azimlib material.

User-supplied fonts require explicit source, license and permission for outline
exports; OpenType restrictions are checked but do not establish legal rights.
See [international text policies and boundaries](docs/international-text-0.4.md).

## Optional real TeX integration (0.4 development)

`tex.py` and `_tex_process.py` are original Azimlib integration code. They invoke
separately installed executables through files/CLI, without linking or copying
their implementations. **Tectonic, pdftocairo/Poppler, their dependencies, TeX
packages/cache and TeX font binaries are not included in wheel/sdist.**

The tested Tectonic 0.17.0 distribution has its own MIT and dependency notices;
`licenses/Tectonic.txt` is the pinned top-level reference, not a replacement for
the full binary distributor's notices. The tested conda-forge Poppler 26.07.0
package identifies GPL-2.0-only; other builds must be assessed on their own terms.
Redistributing those tools is a separate licensing decision. Azimlib's BSD
license does not relicense them. No assertion is made that bundling them into
a proprietary product has the same obligations as independently invoking an
installed command-line tool.

The Python `tex` extra uses separately installed fontTools (MIT), psutil
(BSD 3-Clause; copyright Jay Loden, Dave Daeschler, Giampaolo Rodola) and aggdraw
(existing PIL/AGG notices). Full psutil notice: `licenses/Psutil.txt`.

The fixed validation specimen uses Latin Modern (GUST Font License, referring
to LPPL 1.3c or later) and canonical Computer Modern Type 1 from AMSFonts
(OFL-1.1). Reference texts are `licenses/Latin-Modern.txt`, `licenses/LPPL-1.3c.txt`
and `licenses/AMSFonts.txt`. Their glyph contours remain third-party material;
exports carry the provided full font notices. No exclusive ownership is claimed.
Other preambles/fonts need their actual source, permission and notices.

Sources and hashes: `docs/tex-dependencies-0.4.json`. These are reference notices,
not certification of every separately installed TeX distribution or font.
See [the explicit real-TeX contract](docs/tex-0.4.md).

## Solar model definitions and reference-only validation (0.4 development)

`solar.py`, `solar_artists.py` and `validate_solar.py` are original Azimlib code.
Mathematical model definitions are credited to the USNO approximate solar
equations; the optional atmospheric approximation is described by NOAA.
Their code, prose, binaries and datasets have not been incorporated. Sources,
validity and model limitations are recorded in [the solar guide](docs/solar-0.4.md).
JPL Horizons is an independently queried validation reference with its own
terms; no raw responses, numerical ephemeris tables, kernels or JPL code are
packaged or relicensed under BSD. Only original analysis, query identities
and input hashes appear in development evidence. These distinctions do not
change the license of any existing bundled third-party material.

## Lunar model definitions and reference-only validation (0.4 development)

`lunar.py`, `lunar_artists.py` and the lunar validation tools are independently
written Azimlib code. The mathematical short-series definitions are credited
to the Almanac model reviewed in David G. Simpson's NASA GSFC paper, equations
1–4, pages 176–177. NTRS record 19990040527 identifies the work as US government
material permitting public use. Only the model's numerical definitions are
expressed in code; no paper text, third-party implementation or ephemeris
kernel is bundled or claimed as exclusive property. The Moon's mean radius
is a numerical physical fact credited to the NASA factsheet. Sources, hashes,
frames and limitations are documented in `docs/lunar-model-0.4.json` and
[the lunar guide](docs/lunar-0.4.md). JPL Horizons is validation-only, under its
own terms: no raw numerical reference tables/responses are distributed or
relicensed. Original error statistics and query hashes are retained.

## Physical light and finite-source geometry (0.4 development)

`lighting.py`, `eclipse.py`, `eclipse_artists.py` and their validation/examples
are independently written Azimlib implementations of generic geometric ideas.
The nominal Sun radius is a numerical definition credited to IAU 2015 B3
([source](https://arxiv.org/abs/1510.07674)); Earth/Moon constants retain the
credits recorded in `docs/lighting-model-0.4.json` and `docs/lunar-model-0.4.json`.
No third-party ray tracer, eclipse implementation or ephemeris kernel is included.
Fred Espenak's NASA/GSFC eclipse path table is an independent reference only:
raw HTML, numerical tables, text and images are not distributed. Original
diagnostic statistics and input hashes do not claim ownership of those sources.
Precise real-event prediction is unsupported; this does not change the license
of any previously bundled third-party material.

## Experimental eclipse ephemeris validation (0.4 development)

`_spk.py` is an independently written, bounded reader/evaluator based on the
public NAIF DAF/SPK format specifications. No SPICE, SOFA, ERFA or jplephem
implementation is included. JPL DE440s remains externally supplied reference
data under its own terms; the kernel is neither bundled nor relicensed here.
The separate comparison with jplephem 2.24 is development-only, not a runtime
dependency or an independent validation of the underlying dynamical model.

`_eclipse_ephemeris.py` contains original experimental reductions and geometry.
Conventional IAU-1976 precession parameters, truncated nutation, light time,
aberration and Chebyshev recurrence are mathematical/physical definitions;
their use does not establish an exclusive right over those definitions.
It is not a complete IAU/IERS Earth-orientation implementation.

Solar path and lunar contact references are credited as:
**Eclipse Predictions by Fred Espenak, NASA's GSFC**.
The validation tool includes twelve numeric lunar contact expectations;
original PDFs/HTML tables, prose, artwork and ephemeris kernels are not shipped.
NASA's published lunar-limb and Danjon effective-shadow conventions retain
their attribution and are separate from the physical mean-radius defaults.
Sources, input hashes and the unpassed scientific accuracy criteria are in
[the experimental eclipse guide](docs/eclipse-precision-0.4.md).

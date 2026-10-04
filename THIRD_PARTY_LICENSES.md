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

# Font resources

Unmodified DejaVu Sans regular, bold, oblique and bold-oblique from the official
DejaVu 2.35 upstream release. All four files are verified byte for byte against
the upstream archive; provenance and hashes are in docs/fonts-upstream.json.
These are generic font resources. Their original
copyright and redistribution terms are in LICENSE_DEJAVU and accompany the
fonts. The original Azimlib implementation is BSD-3-Clause; the fonts and their
derived metrics retain the separate terms above. The same TTF notices remain
inside fonts embedded in SVG/HTML exports.

metrics.json contains glyph advances and legacy kerning extracted by the
development-only tools/font_metrics.py using fontTools. The runtime needs
neither fontTools nor Matplotlib. Complex-script shaping is not implemented.

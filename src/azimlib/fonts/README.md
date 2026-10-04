# Font resources

Unmodified DejaVu Sans regular, bold, oblique and bold-oblique from the official
DejaVu 2.35 upstream release. All four files are verified byte for byte against
the upstream archive; provenance and hashes are in docs/fonts-upstream.json.
These are generic font resources. Their original
copyright and redistribution terms are in LICENSE_DEJAVU and accompany the
fonts. Azimlib original code is BSD-3-Clause licensed; these fonts retain their separate terms.

metrics.json contains glyph advances and legacy kerning extracted by the
development-only tools/font_metrics.py using fontTools. The runtime needs
neither fontTools nor Matplotlib. Complex-script shaping is not implemented.

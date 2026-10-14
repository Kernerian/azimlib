# 0.4 schema compatibility with preserved 0.3 reference pixels

All three PNG files and expected numeric scene keys are byte-identical to
[release030](../release030/README.md). No expected pixels or tolerances changed.
0.4 added empty Raster3D texture, UV and volume fields; these contain no painted
content. The key serializer omits only those absent optional payloads. Populated
payloads remain hashed. Old manifests/tools remain historical evidence.

Diagnosis: old/new depth differed only in absent texture/uv and empty volumes;
geometry, text, layout and raster comparison must still satisfy the original
criteria. Original compositions: BSD-3-Clause / Kernerian; DejaVu and CC0 Viridis
terms remain as documented in release030.

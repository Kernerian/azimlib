# Own renderer before temporary-buffer changes

Snapshot of Azimlib's own `pillow.py` and `coverage.py`, including the contained
half-plane optimization. Used only by development comparisons and regression
tests; never imported by the installed library. Covered by the project license.

Compare exactly the same Scene and PNG encoding with `compare_raster_versions.py`
and fresh-process memory with `compare_raster_memory.py`. No Matplotlib backend.

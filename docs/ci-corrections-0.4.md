# Candidate CI diagnostics — 0.4 preparation

Prior validation SHA `750056c2b60d2e16db4f5236f1cf5d886fe55532` is not an
accepted final candidate. Its failures and artifacts remain retained.

- Tk smoke instrumented the global raster function after the viewer had
  retained a callable. Instrument the actual retained renderer; require the
  same exact rerasterization counts, event/history and pixel assertions.
- The solar-light integration compared two normalized float64 tuples by bit
  equality. Independent normalization differed by one representable value on
  Linux; require a four-ULP component bound. No physical/scientific tolerance changed.
- The source-mutation fixture relied on a rapid same-size write changing its
  timestamp. Set a distinct timestamp explicitly to exercise the stat guard.
  Independent initial full-file and per-brick corruption checks remain.
- The historical depth scene hash serialized three newly added empty fields.
  Omit only absent texture/UV and empty volume payloads. Preserve all geometry,
  text, case keys, PNG bytes and original visual thresholds. Populated payloads
  remain included. [Compatibility baseline](../tools/baselines/release040/README.md).

These corrections change validation tooling/fixtures, not delivered rendering,
light calculations or file readers. The complete new-SHA matrices must rerun;
no failed prior job or indeterminate deferred check is treated as passed.

The native review exporter preserves each example's designed figure size.
Forcing six projection panels into 600x400 pixels introduced title overlaps in
the review packet itself. This correction changes export preparation only; no
renderer/font layout or human approval is inferred.

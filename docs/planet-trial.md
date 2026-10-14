# Full-planet PBF acceptance procedure (2.08 pending)

This is a future, offline trial, **not an executed validation**. The implementation
and regional tests exist. Only a successful run over a complete real planet dump
can supply the missing evidence for 2.08. It does not block independent stages;
review it before the final 0.4 release gate. Failure keeps 2.08 open; no sampling,
regional substitution, relaxed reference policy or automatic checkbox completion.

## Freeze the input and environment

Use an existing, dated, complete `planet-YYMMDD.osm.pbf` from
[OSM's official planet service](https://planet.openstreetmap.org/pbf/), not
`latest` or an extract. Record the actual filename, snapshot date/version,
official HTTPS URL, byte size and **SHA-256 of that exact file**. The expected
SHA-256 must be independently approved before ingestion; do not fill it from the
reader's own output. Preserve any publisher checksum/signature and its verification
separately. No date or digest has been invented for the future input.

Pin the source commit, Python/SQLite/kernel versions, CPU, RAM and filesystem.
Use a clean checkout and record `git rev-parse HEAD` and `git status --porcelain`.
Retain a SHA-256 manifest of the tools/runtime as well. Original OSM data remains
ODbL-1.0, © OpenStreetMap contributors; the reader does not sanitize the raw dump.
Keep raw data, indices and logs private until separately reviewed.

## Hard budgets before starting

Choose and record integer byte ceilings before the run. A suggested **memory
ceiling is 8,589,934,592 bytes (8 GiB)**; a different explicit ceiling is allowed
on a suitable future machine, with the reason recorded. The tool verifies a fresh
dedicated Linux cgroup v2's `memory.max` equals the declared limit and
`memory.swap.max` equals zero. It reads `memory.peak` and OOM counters. A mere
`tracemalloc` measurement or `ulimit -m` is not an enforced memory ceiling.
Unsupported/missing cgroup enforcement aborts the planet trial.

Choose an explicit total storage ceiling large enough for input + SQLite index +
16 MiB report/filesystem reservation. Record the resulting **index/temp ceiling**
(`total - input_bytes - 16 MiB`) and reserve free space. For the current development
environment the total remains **20,000,000,000 bytes** and free-space reserve
**15,000,000,000 bytes**: these do not permit a planet trial. A larger future
ceiling requires suitable storage and explicit authorization; the commands below
are a template, not permission to raise the current ceiling.

Use a dedicated empty filesystem/directory with an OS quota no larger than the
declared generated-file budget, including reports and logs. Store no unrelated
files there. Set `TMPDIR` to that directory. SQLite's page ceiling, bounded
entities, disabled journal, indexed ordered scans and periodic free-space checks
constrain normal operation; the OS quota provides a hard backstop for filesystem
overhead and other temporary files. Preserve at least the declared free reserve
on the containing volume: the quota must also fit below initial free space minus
the reserve. Exclude competing writers on that volume for the run. A quota/full-disk/
OOM abort is a failed trial.

## Run once, without filtering or skipping

The following Bash template requires values set from the approved manifest and
preconfigured filesystem quota. `PYTHON` and `CHECKOUT` must be absolute paths.
Run from the clean checkout. `systemd-run` needs permission to create the unit;
check the cgroup controller is available and delegated on that host first.

```bash
# Required: PYTHON, CHECKOUT, INPUT, EXPECTED_SHA256, SNAPSHOT, SOURCE_URL,
# TRIAL_DIR, TOTAL_STORAGE_BYTES, FREE_RESERVE_BYTES, MEMORY_BYTES.
# TRIAL_DIR is a dedicated, quota-limited empty directory.
# SNAPSHOT is the actual YYYY-MM-DD matching planet-YYMMDD.osm.pbf.
(
  while :; do
    printf '%s ' "$(date -u +%FT%TZ)"
    du --summarize --block-size=1 "$TRIAL_DIR" | cut -f1
    sleep 1
  done
) > "$TRIAL_DIR/disk-samples.tsv" &
DISK_MONITOR_PID=$!
trap 'kill "$DISK_MONITOR_PID" 2>/dev/null || true' EXIT INT TERM
RUN_STATUS=0
systemd-run --unit=azimlib-planet-trial --wait --pipe \
  --property=MemoryAccounting=yes --property=MemoryMax="$MEMORY_BYTES" \
  --property=MemorySwapMax=0 --property=RemainAfterExit=yes \
  --property=WorkingDirectory="$CHECKOUT" --setenv=TMPDIR="$TRIAL_DIR" \
  "$PYTHON" -I tools/benchmark_pbf.py "$INPUT" \
  --scope planet --dataset-version "$SNAPSHOT" --source-url "$SOURCE_URL" \
  --sha256 "$EXPECTED_SHA256" --missing error --full-reference-audit \
  --max-memory-bytes "$MEMORY_BYTES" \
  --max-storage-bytes "$TOTAL_STORAGE_BYTES" \
  --reserve-free-bytes "$FREE_RESERVE_BYTES" \
  --index-directory "$TRIAL_DIR" --output "$TRIAL_DIR/result.json" || RUN_STATUS=$?
systemctl show azimlib-planet-trial \
  --property=Result,ExecMainCode,ExecMainStatus,ControlGroup,MemoryPeak
kill "$DISK_MONITOR_PID"
wait "$DISK_MONITOR_PID" 2>/dev/null || true
trap - EXIT INT TERM
awk 'BEGIN { peak=0 } $2>peak { peak=$2 } END { print peak }' \
  "$TRIAL_DIR/disk-samples.tsv"
test "$RUN_STATUS" -eq 0
```

A fresh unit/cgroup is required on each retry (stop the old unit first). Retain
the service result and cgroup `memory.max`, `memory.swap.max`, `memory.peak`,
`memory.events` and quota configuration before stopping it. The tool refuses
pre-existing OOM events. An exit without a successful report never constitutes
acceptance, including an OS kill that prevents writing a failure report.

Monitor the dedicated directory's **allocated disk usage** externally and retain
its peak and sampling interval; retain the filesystem quota's hard maximum too.
`index_peak_bytes` in JSON is the SQLite logical high-water size (no truncation
during this reader's run), not a claim to measure every filesystem allocation.
Retain wall-clock build/total seconds, Python allocation peak, native RSS peak,
cgroup memory peak (includes charged page cache), and allocated disk peak as
distinct metrics. Never label a sampled disk peak an exact high-water measurement.

## Evidence and acceptance

Require all of the following in one reviewed evidence bundle:

- Successful process/service exit; no OOM, corruption, resource-limit or parser
  errors. All supported geometry extraction is consumed, not just index ingestion.
- `passed=true`, `complete_input_verified=true`, input SHA-256 equals the approved
  manifest and `statistics.input_bytes_read` equals the full input byte size.
  The framing reader reaches EOF and hashes every framing/payload byte.
- Counts of blocks, nodes, ways, relations, extracted features and vertices;
  header snapshot information consistent with the pinned source.
- `references.complete=true`, `references.passed=true`, **zero missing way nodes
  and zero missing relation members**, including unsupported/raw relation types.
  `missing_ways`/`missing_relations` must also be zero. All primitives are scanned
  via disk indexes. Relation cycles are not missing references.
- Structural SHA-256 of every primitive ID and every way/member reference in a
  deterministic ID order; hash the JSON report and evidence manifest as well.
  This supplements, and does not replace, the full raw-file SHA-256. It is not a
  hash of every coordinate/tag. A second independent full-file primitive count
  (with tool/version/source recorded) is recommended to detect decoder omissions.
- Actual memory and disk measurements within predeclared caps, recorded quota
  and cgroup enforcement, elapsed time, clean source commit and runtime hashes.
- Review any unsupported polygon/restriction semantics or real data errors. Such
  a failure requires diagnosis and a fresh complete run; do not bypass it using
  `missing=skip`, a bbox, fewer records or a regional input.

The report deliberately retains `planet_scale_confirmed=false`: a scope string
cannot certify provenance or human acceptance. Only after reviewing the entire
bundle can a maintainer record the successful real trial at 2.08. The procedure
does not change its existing criterion. Keep the evidence reproducible; publish
only sanitized summary/metrics, never private paths, editor metadata or raw logs.

References: [Linux cgroup v2 memory controller](https://docs.kernel.org/admin-guide/cgroup-v2.html),
[systemd resource controls](https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html),
[reader contract and regional evidence](osm-pbf.md).

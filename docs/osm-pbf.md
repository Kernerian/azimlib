# OSM PBF: independent streaming and regional extraction

**0.4 development feature in the source checkout; not shipped in the published
0.3.0.** The reader, protobuf interpretation and geographic assembly are Azimlib
implementations. Only Python's generic `zlib`, `sqlite3` and other standard-library
facilities are used. No GIS reader, generated protobuf code or schema is bundled.

## Familiar plotting, explicit data

```python
import azimlib as azl

data = azl.read_osm_pbf(
    'region.osm.pbf',
    bbox=(7.41, 43.72, 7.46, 43.76),  # west, south, east, north
    missing='skip',  # explicit policy for an incomplete regional extract
)
roads = data.select(
    geometry_types=('LineString', 'MultiLineString'),
    predicate=lambda feature: 'highway' in feature.properties,
)
fig, ax = azl.subplots(projection='mercator')
ax.streets(roads, color='#87949e', linewidth=.7)
ax.set_extent((7.41, 7.46, 43.72, 43.76))  # axes: west, east, south, north
ax.set_title('Regional streets')
fig.text(.5, .03, '© OpenStreetMap contributors · openstreetmap.org/copyright',
         ha='center', fontsize=8)
fig.savefig('streets.svg')
```

`import azimlib.pyplot as plt` continues to share the same figure state. Reading
data is explicit; neither import nor `show()` downloads a database. Feature IDs
are typed strings (`node/…`, `way/…`, `relation/…`); `properties['osm']` preserves
primitive kind/ID. OSM tag values remain strings, not guessed numeric categories.
Urban layers, styles, Artists and PNG/SVG exports use the existing rendering path.
Grid, legend, scale, compass, north arrow and minimap remain optional additions.

## Three consumption paths

| API | Contract |
| --- | --- |
| `iter_osm_pbf(source)` | Sequential immutable `OSMRecord` objects; no all-file reference resolution. One decoded block at a time. |
| `OSMIndex(source)` | Disposable SQLite index on disk; references resolve across unsorted blocks, including forward references. Context manager or explicit `close()` required. |
| `read_osm_pbf(source)` | Index plus bounded materialization of the selected `FeatureCollection` for drawing. |

Sources may be paths, bytes or binary streams, including non-seekable short reads.
Caller-owned streams are not closed. Exhaust raw iteration to validate the whole
file and an optional `expected_sha256`; a later corruption/hash failure can follow
earlier yielded records. Indexed extraction does not become available until the
entire input has passed framing, decoding, duplicate-ID and hash checks.

```python
with azl.OSMIndex('region.osm.pbf', missing='skip',
                 max_disk_bytes=8_000_000_000,
                 reserve_free_bytes=15_000_000_000) as index:
    for feature in index.features(bbox=(7.41, 43.72, 7.46, 43.76),
                                  where={'highway': 'residential'}):
        process(feature)  # stream; do not accumulate the entire database
    for restriction in index.relations(restrictions_only=True):
        process_restriction(restriction.members, restriction.tags)
    print(index.statistics)
```

`process`/`process_restriction` above are application callbacks, not Azimlib APIs.
Closing releases paused query cursors and temporary files, including on Windows.

## Supported snapshot semantics

- OSM 0.6 PBF framing, string tables, nodes/dense nodes, ways and relations;
  packed/unpacked repeated values, repeated packed chunks, signed IDs/deltas,
  granularity and offsets. IDs are never converted through floating point.
- Raw and zlib Blobs. LZMA, obsolete bzip2, LZ4 and Zstandard produce explicit
  unsupported-codec errors. Unknown bounded file-block types after the header
  and unknown ordinary protobuf fields can be skipped; protobuf groups fail.
- Optional `LocationsOnWays` arrays are decoded, require their feature declaration
  and must agree with referenced nodes when indexed. They do not silently replace
  absent nodes. Required unknown features, history/diffs and deleted objects fail.
- Tagged nodes become points. Ways become lines; closed area-tagged ways become
  polygons using the same classification as the existing XML reader. Untagged
  primitives appear only with `include_untagged=True`.
- Multipolygons and boundaries join reversible way fragments by node identity,
  assemble outer rings and holes, and suppress duplicate standalone member ways.
  Boundary `admin_centre`/`label` nodes and `subarea` child relations remain in raw
  members but do not become boundary-ring coordinates. Member ways may be shared
  between relations; repeated ways inside one polygon relation are rejected.
- Restriction relations retain from/to ways, via node/ordered ways, conditional,
  vehicle-specific and exception tags. Necessary members/references are checked.
  This is input for a future router, not a routing engine or conditional evaluator.
- All other relations, including nested route relations, remain available as raw
  members/tags through `relations()`. Their references/semantics are not claimed
  to be resolved. No route or geometry is invented for them.

Missing node/way references or missing restriction roles fail by default. Explicit
`missing='skip'` omits the entire affected derived feature/restriction and records
`missing_ways`/`missing_relations`; `relations(include_incomplete=True)` retains
incomplete raw relation records. It does not truncate a geometry into a plausible
partial one. Unsupported polygon member roles/nested polygon members, branched,
open or self-touching rings still fail; skip is not a corruption bypass. Hole
assignment uses the existing planar containment contract; arbitrary global
topological overlay is the separate step 4.

## Filters and budgets

`where` maps tag strings to exact string values (AND). `bbox` is geographic
`(west,south,east,north)`; `west > east` crosses the antimeridian. Selection uses
conservative envelope intersection, including crossing ways whose vertices lie
outside the region. Wide/wrapped longitude envelopes retain extra candidates.
This is not exact geometry intersection or clipping. Complete selected geometries
can extend beyond the display region; set the axes extent explicitly.

The complete input must still be scanned/indexed to resolve arbitrary forward
references correctly. Filters bound returned data; they do not magically avoid
reading the planet, or promise a prebuilt spatial index. Disk sequence indexes
preserve primitive input order without a whole-dataset in-memory sort.

| Guard | Default |
| --- | --- |
| BlobHeader | strictly below 64 KiB |
| Uncompressed block | strictly below 32 MiB |
| Encoded Blob | at most 32 MiB + 64 KiB |
| Structural fields retained per protobuf message | 100,000 |
| Decoded fields/numeric items per block | 2,000,000 shared budget |
| String table entries | at most 100,000, also subject to shared item budget |
| References/members and assembled polygon vertices | `max_refs=100_000` per entity/relation |
| Serialized indexed entity | 8 MiB |
| SQLite page cache | 8 MiB; filesystem page cache is OS-managed |
| Database file | `max_disk_bytes=8_000_000_000` |
| Free space reserve | `reserve_free_bytes=64 MiB` in the library; 15 GB in trial/example tools |
| Materialized collection | 100,000 features, 1,000,000 vertices, 64 MiB serialized GeoJSON bytes |

Limits are checked, not preallocated. `max_features`, `max_vertices`, `max_bytes`
can narrow the collection budget; use streaming for larger data. These guards
bound explicit allocations/accumulation; they are not an absolute RSS guarantee.
Native SQLite/OS caches and Python object overhead are measured separately.
Disk-full/budget errors abort and clean the disposable index. The index uses no
journal, performs no unbounded global sort, and checks free space with a block
reserve before bounded write batches. Input files, outputs and concurrent
applications' usage are outside the library's database limit.

## Catalog, acquisition, licenses and privacy

`DatasetCatalog` supports `format: "osm-pbf"` with explicit EPSG:4326, version,
source, license, copyright, attribution and hashes for data and notices. `verify()`
hashes incrementally. `load()` uses collection budgets; `open_pbf()` returns a
context-managed index and validates the hash of the exact bytes ingested, rather
than verifying a path and reopening it without verification.

Acquisition is a separate explicit command with a pinned SHA256. For a reproducible
small trial, the Geofabrik `monaco-260101.osm.pbf` input is 673,493 bytes:

```bash
python tools/acquire_osm_pbf.py \
  --url https://download.geofabrik.de/europe/monaco-260101.osm.pbf \
  --sha256 2c0debd7676c0d0d80ec534251cb004a6797441d14512cb83d01fe1ad81363bf \
  --version monaco-260101 \
  --license-file optional-data/urban-sao-paulo-1.0/LICENSE.txt \
  --output local-data/monaco-260101
```

This creates a new local catalog only after verified, bounded HTTPS acquisition.
Existing destinations are never overwritten. The complete audited SPDX Markdown
ODbL-1.0 text is content-checked (LF-normalized SHA256
`77d2692c3d64efdd4db18dce2407699baf62930e2b50d6e5ed90b48acf16b7c1`),
copied byte-for-byte and hashed in the catalog. Obtain that optional directory
from the source checkout, not the wheel/sdist. No base is installed at import.

OSM data remains **ODbL-1.0, © OpenStreetMap contributors**, separate from original
BSD-3-Clause implementation code. Keep its license and source/version/hash/credit
when distributing data; displayed maps need the applicable attribution. Consult
the [OSM copyright requirements](https://www.openstreetmap.org/copyright/en) and
[ODbL legal text](https://opendatacommons.org/licenses/odbl/1-0/).

Reader outputs exclude editor usernames, user IDs, changesets, versions and edit
timestamps. The source file is not rewritten/sanitized, and ordinary tags can
contain names, addresses or contact details. Acquisition is not a privacy approval:
review the raw file, tags, output maps and any derived database before publication.
The trial data/indices/maps are kept outside this repository and archives; optional
databases remain excluded by MANIFEST.in. No third-party material is reclassified
as Azimlib-owned code. See [optional data](optional-data.md).

## Validation and future planet trial

[Original fixture encoder](../tests/pbf_fixture.py) and [tests](../tests/test_pbf.py)
cover XML equivalence, reversed fragments/holes, multi-block forward references,
normal/dense representations, codecs, malformed/truncated wire data, missing refs,
hashes, filters, collection budgets, actual SQLite page-limit aborts, paused-cursor
cleanup, acquisition and PNG/SVG urban integration. The generated fixtures are
Azimlib test material; they do not establish an independent producer by themselves.
The independently produced Geofabrik regional file supplies the real-input trial.

```bash
python -I tools/benchmark_pbf.py local-data/monaco-260101/data.osm.pbf \
  --sha256 2c0debd7676c0d0d80ec534251cb004a6797441d14512cb83d01fe1ad81363bf \
  --scope regional --missing skip \
  --max-storage-bytes 20000000000 --reserve-free-bytes 15000000000 \
  --output regional-trial.json
```

The trial tool conservatively counts input + database + a 16 MiB report/filesystem
reservation against the total storage ceiling. It measures Python allocations,
native process working-set high-water mark, index size, counts and elapsed time,
and removes the index on exit. RSS includes imports and is not stage-specific.

**2.08 remains pending only for the planet-scale proof.** No planet download/run
was performed. Regional/synthetic results are not extrapolated into planet claims.
The [full-planet procedure](planet-trial.md) requires a pinned official snapshot,
SHA256, complete byte count, a full disk-backed reference audit, Linux cgroup v2
memory enforcement, a storage quota and reviewed resource/completion evidence.
`OSMIndex.audit_references()` includes raw relation types as well as ways; the
benchmark's `--full-reference-audit` fails on any missing primitive reference.
A scope label never automatically marks planet support as validated. The planet
proof does not block independent next stages but must be revisited before the
final release gate. No network fetch is performed by the trial. Platform acceptance remains
part of step 14, not claimed from this local Windows execution.

## Primary protocol references and provenance

The implementation was independently written from field/encoding contracts:

- [OSM PBF format](https://wiki.openstreetmap.org/wiki/PBF_Format).
- [Canonical field definitions](https://github.com/openstreetmap/OSM-binary/blob/master/osmpbf/osmformat.proto)
  and [framing definitions](https://github.com/openstreetmap/OSM-binary/blob/master/osmpbf/fileformat.proto).
- [Protobuf wire encoding](https://protobuf.dev/programming-guides/encoding/).
- [Geofabrik Monaco source/metadata policy](https://download.geofabrik.de/europe/monaco.html).

Protocol field numbers, wire types and coordinate equations are interoperability
facts. No `.proto` text, generated bindings, OSM-binary reader code, documentation
paragraphs or examples were incorporated. Generic delta/varint decoding and the
original fixture writer are implemented here; no GIS library does the decoding or
geographic assembly underneath.

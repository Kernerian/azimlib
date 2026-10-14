# Local geocoding — 0.4 development

This API is in the development source tree, **not in the published 0.3.0**.
The local engine is Azimlib's own implementation. SQLite provides generic disk
storage, not a geocoder/GIS engine. No service, account, download or query log
is enabled automatically. Routing is a separate stage.

## Build and search an optional licensed dataset

```python
import azimlib as azl

catalog = azl.DatasetCatalog("optional-data/urban-sao-paulo-1.0/catalog.json")
with azl.LocalGeocoder.from_catalog(
    catalog, "urban-sao-paulo", "local-search-index",
    include_addresses=False,  # default: no addr:* import
) as geocoder:
    results = geocoder.search("Rua", prefix=True, kinds=("street",))
    for result in results:
        print(result.name, result.precision, result.source.attribution)
    print(results.total, results.ambiguous, results.truncated)
    fig, ax = azl.subplots()
    layer = ax.geojson(results.to_features(boundary=True))
    layer.set_picker(True)
    ax.labels(layer, halo="white")
    fig.savefig("search.svg")
```

The directory must not exist before a build. Reopen it using
`LocalGeocoder("local-search-index")`; files are read-only and hash checked.
The same plotting state works with `import azimlib.pyplot as plt`.
The [complete example](../examples/local_geocoding.py) exports PNG/SVG with
OpenStreetMap attribution. All components remain opt-in.

Catalog import verifies the dataset and license hashes and preserves source,
version, SHA-256, copyright, attribution and full license text in the index.
The optional São Paulo dataset and any derived database retain **ODbL 1.0**;
Azimlib's BSD license covers its original code, not exclusive rights over data.
Redistribution/public use of a derived OSM database requires reviewing ODbL's
attribution and share-alike/access obligations. Indexes are not shipped in the
Python archives. See [optional data](optional-data.md) and
[third-party terms](../THIRD_PARTY_LICENSES.md).

## Models, provenance and import

| Type | Contract |
| --- | --- |
| `GeocodingSource` | Safe namespace, version, source URL/URN, declared hash, license/copyright/attribution and notices |
| `Address` | Literal house number, street, neighborhood, city, state, country and postcode; absent fields stay empty |
| `GeocodingRecord` | Stable source ID/object ID, `address`/`street`/`locality`/`poi`/`interpolation`, original names/aliases and geometry, optional **declared** accuracy |
| `AddressRange` | Explicit source line plus two numeric point-address IDs and step; endpoints/context must agree |
| `GeocodingResult` | Record/source, representative or matched position, precision, match type, score, optional distance and containment |
| `GeocodingResults` | All-match count, ambiguity and truncation even when returning only one item |

`records_from_features(features, source, include_addresses=False)` imports
allowlisted OSM tags from own XML/PBF readers or compatible GeoJSON. Named ways
become streets, `place=*` and administrative boundaries become localities,
amenities/shops/tourism/leisure/offices/public transport become POIs. Address
import requires `include_addresses=True`. Named buildings without these tags
are not inferred to be POIs. Country-specific administrative levels are not
guessed, and a nearby city point does not establish administrative membership.
The opt-in requires an actual boolean; strings/numbers are rejected. Null address
fields remain absent and non-string address tags fail, instead of becoming
invented literal house numbers such as `None` or `True`.

For custom adapters, construct typed records and stream them to
`LocalGeocoder.build(directory, records, sources=(source,))`. Manually supplied
provenance/accuracy is a caller declaration, not a verified ownership claim.
`LocalGeocoder.from_osm_index(index, source, directory, ...)` streams the own PBF
disk index, requires its input hash to match, and rejects missing references.
The caller budgets both indexes and controls their lifecycles.

Display names are preserved. `name:*`, official/short/alternate/old/local names
are explicit aliases. Arbitrary properties, contact details, editor IDs,
timestamps, notes and local source paths are not copied. An address database
can still be sensitive: explicitly assess the source, lawful use and retention;
do not treat the allowlist as anonymization of supplied names/addresses.

## Search, ranking and uncertainty

```python
results = geocoder.search(
    "Rua Teste", filters={"city": "Cidade", "house_number": "12-B"},
    kinds=("address",), limit=10,
)
nearby = geocoder.search("Biblioteca", near=(-46.64, -23.54), radius_m=1500)
approximate = geocoder.search("Bibliteca", fuzzy=True)  # explicit approximation
```

Names use NFKC/casefold and accent folding for search, preserving original text
for display. Normalization concepts follow [Unicode UAX #15](https://www.unicode.org/reports/tr15/);
the implementation uses Python's Unicode database. Tokenization splits by
Unicode letter/number/mark categories. It is **not UAX #29 segmentation**, a
language dictionary, transliteration or complex text shaping. Scripts without
spaces support exact stored names and explicit prefix search, not inferred
linguistic word boundaries. A Unicode database version change requires rebuilding
the index rather than silently using different normalization.

All query tokens must match stored names/address fields. Exact token matches
score 100 minus 10 per token edit cost; exact full name/address adds 20. Prefix
matches cost 0.25 per token. Optional own Levenshtein matching allows one code-point
edit for tokens below five characters, two otherwise. Interpolation subtracts
30. Scores are deterministic ordering signals, **not confidence probabilities**.
Equal scores sort by optional geometry distance, then source ID/object ID.
Every multi-match result is marked ambiguous; there is no automatic winner.
`limit` truncates returned items, not the match count or ambiguity flag.

Administrative/address filters compare only explicit source fields, with search
normalization; spatial `bbox=(west,south,east,north)` filters representatives,
and `near` limits spherical distance to source geometry. Split wrapped bboxes
explicitly. Reverse radius searches support the antimeridian/poles. Missing
results mean missing coverage or no match, not proof that an address does not exist.

## Reverse and geometry precision

```python
results = geocoder.reverse(-46.639, -23.545, radius_m=300,
                           kinds=("street", "address", "locality"))
for result in results:
    print(result.distance_m, result.precision, result.record.accuracy_m)
```

Distances use a sphere of radius **6,371,008.8 m**, source points and minor
great-circle segments. They are not ellipsoidal survey accuracy, parcel access,
postal certification or travel distance. Line representatives are halfway along
the longest part. Regional polygons retain original boundaries and use an own
exact planar scanline interior representative, outside holes. Containment uses
regional straight lon/lat boundaries; outside-boundary distances use spherical
segments. This declared hybrid is not a global spherical administrative model.

`source_point`, `centerline_representative`, `boundary_representative`,
`nearest_centerline`, `nearest_boundary`, `containing_boundary` and
`interpolated` are distinct. A containing boundary returns zero distance and the
query position; it does not invent an address. `to_features()` yields markers;
`to_features(boundary=True)` preserves source geometry for layers/picking/labels.
Source coordinate accuracy stays `None` unless explicitly declared.

Supported geometry: finite 2D WGS84 lon/lat points, lines/multilines and valid
regional polygons/multipolygons. Polygon longitude span must be below 180°;
unwrapped coordinates, global administrative polygons, antipodal street arcs,
empty/invalid/3D/collection geometries fail explicitly. Use the separate spherical
topology API for global regions. No implicit reprojection or topology repair.

## Explicit interpolation

`AddressRange(record, start_id, end_id, step=2)` can represent an even/odd range;
`step=1` represents all integer numbers; other positive integer steps are explicit.
Build with `ranges=(address_range,)`. The two source point addresses must exist,
have numeric house numbers, the same street and complete declared context, and
exactly match the source line endpoints. Descending ranges are supported.

Query with a structured `house_number` filter and `interpolate=True`; the position
is proportional to spherical polyline length. The match is always `interpolated`,
keeps both endpoint IDs and has no asserted coordinate accuracy. Explicit address
points rank ahead. No extrapolation, automatic nearest-street association,
alphabetic/suffixed/hyphen-number interpolation or invented endpoint references.
Raw OSM interpolation ways are skipped by the generic feature adapter; supply
verified explicit ranges when node references are available. The
[OSM address specification](https://wiki.openstreetmap.org/wiki/Addresses)
describes broader tagging variants; unsupported variants are not guessed.

## Resources, external providers and validation

The own adaptive lon/lat tile postings, inverted tokens and bounded edit ranking
use generic SQLite persistence. Defaults: 250,000 records, 256 MiB generated
storage, 64 MiB free-disk reserve, 5,000 candidates, 32 MiB cumulative decoded
JSON per query, 1 MiB per record and 4,096 geometry vertices. Polygon validation/
interior construction can be quadratic; this is a regional address index, not
a claim of planet geocoding throughput. Names are bounded to 64 aliases and
4,096 characters per individual/search string; concatenated indexed text shares
the 4,096-character bound. Fuzzy queries allow 16 tokens of 128 characters.
Candidate/vocabulary overflow raises `GeocodingLimitError`; it does not silently
return a partial/unique result. Increase budgets deliberately or narrow data.

`ExternalGeocoder(search_callable, reverse_callable=None)` is a **separate**
explicit adapter. It requires typed provenance-bearing results; caller code owns
network, credentials, consent and provider terms. The local engine never calls
it or falls back to it. No provider implementation or service is bundled.

Reproduce `tests/test_geocoding_040.py`, `tools/validate_geocoding.py` and
`examples/local_geocoding.py`. The offline trial validates synthetic names,
spatial queries and the pinned real São Paulo OSM sample, records timings,
traced Python memory and a conservative peak-disk bound, and removes indexes.
It enforces **<=20 GB** storage and **>=15 GB** free reserve. It neither downloads
nor substitutes for the full planet trial in **2.08, which remains pending**.
This stage's evidence is [recorded separately](geocoding-validation-0.4.json).

# Optional São Paulo urban sample 1.0

A frozen OpenStreetMap extraction around Praça Ramos de Azevedo / Theatro
Municipal, retrieved 2026-10-06. Geometry and public place names are real.
This is a small derivative database under **ODbL 1.0**, separately from Azimlib's
BSD code. It is not bundled in the Python wheel or sdist and is never downloaded
implicitly. Copy this entire directory to use its local catalog.

© OpenStreetMap contributors. Data is available under the Open Database License:
[copyright/attribution](https://www.openstreetmap.org/copyright),
[full license](LICENSE.txt). Preserve these notices and share derivative databases
under ODbL when its sharing obligations apply. Produced maps must visibly credit
OpenStreetMap and identify the ODbL data license. This does not make original
Azimlib implementation code ODbL.

The [provenance](provenance.json) records the exact API URL, retrieval date,
raw source hash, selection rules, removed metadata, retained tags and file hashes.
The unfiltered API response is not distributed. Relations, addresses, contacts,
editor identities and changeset metadata are excluded. Ways retain complete
referenced geometry and can extend beyond the requested display bbox.

Run from the source checkout:

```bash
python examples/urban_real.py --catalog optional-data/urban-sao-paulo-1.0/catalog.json --output gallery/urban-real
```

The catalog verifies data, license, provenance and this notice before loading.
No geocoding, route calculation or network access occurs.

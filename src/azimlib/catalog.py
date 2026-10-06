"""Local versioned optional data catalogs; integrity and license metadata first."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

from ._readers import binary


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise ValueError('Duplicate catalog JSON key')
        result[key] = value
    return result


class DatasetCatalog:
    """Read schema-1 catalog.json; never downloads, installs or registers globally.

    Each dataset declares id/version/format/file/crs/license/copyright/source/
    attribution and a files mapping of relative paths to SHA256 digests, including
    its license text. A version must be explicit when multiple versions exist.
    Paths must resolve inside the catalog directory (including symlink checks).
    Loading verifies the exact bytes consumed, including sidecars and notices.
    """
    def __init__(self, manifest):
        self._path = Path(manifest).resolve()
        self._root = self._path.parent
        raw = binary(self._path, 1024*1024)
        try: data = json.loads(raw, object_pairs_hook=_unique_object)
        except (ValueError, UnicodeError) as exc: raise ValueError('Invalid catalog JSON') from exc
        if not isinstance(data, dict) or data.get('schema_version') != 1 or not isinstance(data.get('datasets'), list):
            raise ValueError('Expected schema-1 data catalog')
        self._entries = {}
        required = ('id', 'version', 'format', 'file', 'crs', 'license', 'copyright', 'source', 'attribution', 'license_file')
        for item in data['datasets']:
            if not isinstance(item, dict) or any(not isinstance(item.get(key), str) or not item[key] for key in required):
                raise ValueError('Dataset is missing required string metadata')
            if any(not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', item[key]) for key in ('id', 'version')):
                raise ValueError('Invalid dataset ID/version')
            if item['format'] not in ('geojson', 'csv', 'shapefile', 'kml', 'osm', 'raster', 'geotiff'):
                raise ValueError('Unsupported catalog data format')
            files = item.get('files')
            if not isinstance(files, dict) or not files or any(not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest) for digest in files.values()):
                raise ValueError('Dataset files must declare SHA256 hashes')
            if item['file'] not in files or item['license_file'] not in files:
                raise ValueError('Data and license file must both have hashes')
            for name in files: self._resolve(name)
            key = item['id'], item['version']
            if key in self._entries: raise ValueError('Duplicate dataset ID/version')
            options = item.get('options', {})
            if not isinstance(options, dict): raise ValueError('Dataset options must be an object')
            allowed = {'geojson': set(), 'csv': {'longitude', 'latitude', 'id_column', 'delimiter', 'encoding'},
                       'shapefile': {'dbf', 'shx', 'encoding', 'include_deleted'}, 'kml': set(),
                       'osm': {'include_untagged'}, 'raster': {'world_file', 'extent', 'nodata', 'max_pixels'},
                       'geotiff': {'nodata', 'max_pixels'}}[item['format']]
            if not options.keys() <= allowed: raise ValueError('Unsupported catalog reader options')
            for name in ('dbf', 'shx', 'world_file'):
                if name in options and options[name] not in files:
                    raise ValueError('Sidecar must be declared and hashed')
            if item['format'] in ('kml', 'osm', 'csv', 'geojson') and item['crs'] != 'EPSG:4326':
                raise ValueError('This catalog vector format requires explicit EPSG:4326')
            self._entries[key] = deepcopy(item)

    def _resolve(self, name):
        if not isinstance(name, str) or '\\' in name or ':' in name:
            raise ValueError('Catalog paths must be relative POSIX paths')
        path = PurePosixPath(name)
        if not name or path.is_absolute() or any(p in ('..', '.') for p in path.parts):
            raise ValueError('Catalog path escapes its directory')
        target = (self._root / name).resolve()
        if not target.is_relative_to(self._root): raise ValueError('Catalog symlink escapes its directory')
        return target

    def available(self):
        """Return detached metadata; editing it does not change the catalog."""
        return tuple(deepcopy(value) for value in self._entries.values())

    def _entry(self, identifier, version):
        keys = [key for key in self._entries if key[0] == identifier and (version is None or key[1] == version)]
        if not keys: raise KeyError('Dataset ID/version not present in local catalog')
        if len(keys) != 1: raise ValueError('Select an explicit dataset version')
        return self._entries[keys[0]]

    def _payloads(self, entry):
        payloads = {}
        for name, digest in entry['files'].items():
            raw = binary(self._resolve(name))
            if hashlib.sha256(raw).hexdigest() != digest:
                raise ValueError(f'Dataset integrity mismatch: {name}')
            payloads[name] = raw
        return payloads

    def verify(self, identifier=None, *, version=None):
        entries = self._entries.values() if identifier is None else (self._entry(identifier, version),)
        if identifier is None and version is not None: raise ValueError('version requires a dataset ID')
        count = 0
        for entry in entries:
            count += len(self._payloads(entry))
        return {'passed': True, 'files_verified': count}

    def load(self, identifier, *, version=None):
        entry = self._entry(identifier, version)
        payloads = self._payloads(entry); raw = payloads[entry['file']]
        options = deepcopy(entry.get('options', {})); kind = entry['format']
        for name in ('dbf', 'shx', 'world_file'):
            if name in options: options[name] = payloads[options[name]]
        if kind == 'geojson':
            from .io import read_geojson
            return read_geojson(raw)
        if kind == 'csv':
            from .tabular import read_csv
            return read_csv(raw, **options)
        if kind == 'shapefile':
            from .shapefile import read_shapefile
            return read_shapefile(raw, crs=entry['crs'], **options)
        if kind in ('kml', 'osm'):
            from .xmlio import read_kml, read_osm
            return (read_kml if kind == 'kml' else read_osm)(raw, **options)
        from .raster import read_raster, read_geotiff
        return (read_raster if kind == 'raster' else read_geotiff)(raw, crs=entry['crs'], **options)

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
            if item['format'] not in ('geojson', 'csv', 'shapefile', 'kml', 'osm', 'osm-pbf', 'raster', 'geotiff', 'ntv2', 'gtx'):
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
                       'osm-pbf': {'include_untagged', 'bbox', 'where', 'missing', 'max_features', 'max_vertices', 'max_bytes', 'max_disk_bytes', 'reserve_free_bytes', 'max_refs'},
                       'geotiff': {'nodata', 'max_pixels'},
                       'ntv2': {'nodata', 'max_bytes', 'max_nodes', 'max_tiles'},
                       'gtx': {'nodata', 'max_bytes', 'max_nodes'}}[item['format']]
            if not options.keys() <= allowed: raise ValueError('Unsupported catalog reader options')
            for name in ('dbf', 'shx', 'world_file'):
                if name in options and options[name] not in files:
                    raise ValueError('Sidecar must be declared and hashed')
            if item['format'] in ('kml', 'osm', 'osm-pbf', 'csv', 'geojson') and item['crs'] != 'EPSG:4326':
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
            for name, expected in entry['files'].items():
                self._verify_file(name, expected)
                count += 1
        return {'passed': True, 'files_verified': count}

    def _verify_file(self, name, expected):
        digest = hashlib.sha256()
        with self._resolve(name).open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
        if digest.hexdigest() != expected:
            raise ValueError(f'Dataset integrity mismatch: {name}')

    def open_pbf(self, identifier, *, version=None, **index_options):
        """Open a verified disk index; caller must close it (prefer ``with``).

        Notices/sidecars are verified by streaming. The PBF hash is calculated
        on the same bytes ingested, before the index becomes available to callers.
        No network acquisition is performed.
        """
        from .pbf import OSMIndex
        entry = self._entry(identifier, version)
        if entry['format'] != 'osm-pbf':
            raise ValueError('open_pbf requires an osm-pbf catalog entry')
        for name, digest in entry['files'].items():
            if name != entry['file']:
                self._verify_file(name, digest)
        if 'expected_sha256' in index_options:
            raise ValueError('Catalog SHA256 cannot be overridden')
        options = {k: v for k, v in entry.get('options', {}).items()
                   if k in ('missing', 'max_disk_bytes', 'reserve_free_bytes', 'max_refs')}
        options.update(index_options)
        return OSMIndex(self._resolve(entry['file']), expected_sha256=entry['files'][entry['file']], **options)

    def load(self, identifier, *, version=None):
        entry = self._entry(identifier, version)
        if entry['format'] in ('ntv2','gtx'):
            # Bounded chunk reads avoid allocating the configured 128/256 MiB
            # ceiling for a small file. Hash the exact bytes passed to the reader.
            from .datum_grids import read_ntv2, read_gtx, _bytes, _limit
            options = deepcopy(entry.get('options',{}))
            budget = _limit(options.get('max_bytes',128*1024*1024),'max_bytes')
            raw = None; total = 0
            for name,digest in entry['files'].items():
                payload = _bytes(self._resolve(name),min(budget, budget if name == entry['file'] else 1024*1024))
                total += len(payload)
                if total > budget or hashlib.sha256(payload).hexdigest() != digest:
                    raise ValueError('Grid catalog exceeds byte budget or integrity mismatch')
                if name == entry['file']: raw = payload
            return (read_ntv2 if entry['format']=='ntv2' else read_gtx)(raw,**options)
        if entry['format'] == 'osm-pbf':
            options = {k: v for k, v in entry.get('options', {}).items()
                       if k in ('bbox', 'where', 'include_untagged', 'max_features', 'max_vertices', 'max_bytes')}
            with self.open_pbf(identifier, version=version) as index:
                return index.collection(**options)
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

    def grid_operation(self, identifier, *, version=None):
        """Load an exact declared grid operation, verifying data and legal notices.

        Grid catalogs additionally require operation frame, registration, units,
        direction, interpolation and published accuracy/source metadata. These
        are explicit declarations, not authority certification by the library.
        """
        from .grid_operations import GridOperation
        from .coordinate_operations import CoordinateFrame
        from .geodesy import Datum, Ellipsoid
        entry = self._entry(identifier,version)
        model = entry.get('operation')
        required = {'kind','source','target','factor','registration','units','interpolation','accuracy','reference'}
        if entry['format'] not in ('ntv2','gtx') or not isinstance(model,dict) or not required <= model.keys() or not model.keys() <= required|{'valid_epochs'}:
            raise ValueError('Require complete explicit grid operation metadata')
        expected = 'arcseconds' if entry['format'] == 'ntv2' else 'metres'
        if model['registration'] != 'source-horizontal' or model['units'] != expected or model['interpolation'] != 'bilinear' or any(not isinstance(model[k],str) or not model[k].strip() for k in ('accuracy','reference')):
            raise ValueError('Unsupported grid registration/units/interpolation/accuracy metadata')
        def frame(spec):
            keys = {'name','datum','ellipsoid','height_reference'}
            if not isinstance(spec,dict) or spec.keys() != keys or not isinstance(spec['ellipsoid'],dict) or spec['ellipsoid'].keys() != {'name','semi_major_axis','inverse_flattening'}:
                raise ValueError('Require exact explicit grid frame profile')
            return CoordinateFrame(spec['name'],'geographic',Datum(spec['datum'],Ellipsoid(**spec['ellipsoid'])),spec['height_reference'])
        source,target = frame(model['source']),frame(model['target'])
        if entry['crs'] != source.name:
            raise ValueError('Grid registration must name the exact source horizontal frame')
        return GridOperation(source,target,self.load(identifier,version=version),
                             model['kind'],model['factor'],model.get('valid_epochs'))

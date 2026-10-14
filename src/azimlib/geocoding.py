"""Independent local geocoding with explicit coverage, provenance and ambiguity.

SQLite supplies generic persistence only. Name matching, ranking, spatial
postings, geometry interpretation and interpolation are implemented here.
No download, remote provider, query log or address enrichment is implicit.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile
from types import MappingProxyType
import unicodedata
from urllib.parse import urlsplit, parse_qsl

from .geometry import Feature, FeatureCollection, Geometry
from ._geocode_text import normalize_name, tokens, edit_distance
from . import _geocode_geometry as geo

KINDS = ('address','street','locality','poi','interpolation')
ADDRESS_FIELDS = ('house_number','street','neighborhood','city','state','country','postcode')
SCHEMA = 1


class GeocodingLimitError(RuntimeError):
    """A budget was reached; no partial result or false uniqueness is returned."""


def _text(value, name, *, empty=False):
    if not isinstance(value,str) or len(value)>4096 or (not value.strip() and not empty) or '\x00' in value:
        raise ValueError(f'Invalid {name}: expected bounded text')
    return value


def _integer(value, name, low=1):
    if isinstance(value,bool) or not isinstance(value,int) or value<low:
        raise ValueError(f'{name} must be an integer >= {low}')
    return value


def _digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''): result.update(chunk)
    return result.hexdigest()


@dataclass(frozen=True)
class GeocodingSource:
    """Declared source, not proof of ownership; notices keep their own license."""
    id: str
    version: str
    license: str
    copyright: str
    attribution: str
    origin: str
    sha256: str
    notices: tuple[str,...] = ()

    def __post_init__(self):
        for name in ('id','version','license','copyright','attribution','origin'):
            _text(getattr(self,name),name)
        if not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]*',self.id): raise ValueError('Source ID must be a safe namespace')
        if not re.fullmatch('[0-9a-f]{64}',self.sha256): raise ValueError('Source requires lowercase SHA-256')
        parsed = urlsplit(self.origin)
        if parsed.scheme not in ('https','http','urn') or parsed.username or parsed.password or parsed.fragment:
            raise ValueError('Source origin must be a public URL or a nonpersonal urn, not a local path or credential')
        if parsed.scheme != 'urn' and not parsed.netloc: raise ValueError('Source URL requires a host')
        if any(re.search('token|secret|password|signature|api.?key',key,re.I) for key,_ in parse_qsl(parsed.query)):
            raise ValueError('Source URL must not contain credentials')
        notices = tuple(self.notices)
        if len(notices)>16 or any(not isinstance(t,str) or len(t)>262144 or '\x00' in t for t in notices):
            raise ValueError('Source notices exceed the text budget')
        object.__setattr__(self,'notices',notices)

    def as_dict(self): return {name:getattr(self,name) for name in self.__dataclass_fields__}


@dataclass(frozen=True)
class Address:
    house_number: str = ''
    street: str = ''
    neighborhood: str = ''
    city: str = ''
    state: str = ''
    country: str = ''
    postcode: str = ''

    def __post_init__(self):
        for name in ADDRESS_FIELDS: _text(getattr(self,name),name,empty=True)

    def as_dict(self): return {name:getattr(self,name) for name in ADDRESS_FIELDS}

    def display(self):
        first = ' '.join(v for v in (self.street,self.house_number) if v)
        return ', '.join(v for v in (first,self.neighborhood,self.city,self.state,self.country,self.postcode) if v)


@dataclass(frozen=True)
class GeocodingRecord:
    """One source object; boundary geometry is distinct from its representative."""
    id: str
    kind: str
    names: tuple[str,...]
    geometry: Geometry
    source: str
    address: Address = field(default_factory=Address)
    category: str = ''
    accuracy_m: float | None = None

    def __post_init__(self):
        for name in ('id','source'): _text(getattr(self,name),name)
        if self.kind not in KINDS: raise ValueError('Unknown geocoding record kind')
        if isinstance(self.names,(str,bytes)): raise ValueError('Names must be a sequence of strings')
        names = tuple(dict.fromkeys(self.names))
        if len(names)>64 or any(not isinstance(n,str) or not n.strip() or len(n)>4096 for n in names):
            raise ValueError('Names require at most 64 bounded nonempty strings')
        if not isinstance(self.geometry,Geometry) or not isinstance(self.address,Address):
            raise TypeError('Record requires Geometry and Address')
        if not names and not self.address.display(): raise ValueError('A record needs a name or address')
        _text(self.category,'category',empty=True)
        if self.accuracy_m is not None and (isinstance(self.accuracy_m,bool) or not isinstance(self.accuracy_m,(int,float)) or not math.isfinite(self.accuracy_m) or self.accuracy_m<0):
            raise ValueError('Declared coordinate accuracy must be finite nonnegative metres or None')
        object.__setattr__(self,'names',names)

    @property
    def name(self): return self.names[0] if self.names else self.address.display()

    def as_dict(self):
        return dict(id=self.id,kind=self.kind,names=self.names,geometry=self.geometry.to_geojson(),
                    source=self.source,address=self.address.as_dict(),category=self.category,accuracy_m=self.accuracy_m)

    @classmethod
    def from_dict(cls,data):
        return cls(data['id'],data['kind'],tuple(data['names']),Geometry(data['geometry']['type'],data['geometry']['coordinates']),
                   data['source'],Address(**data['address']),data['category'],data['accuracy_m'])


@dataclass(frozen=True)
class AddressRange:
    """Explicit numeric interpolation along a source line, with source endpoints.

    Endpoints must exist in the same source, with the same explicit street and
    other address context, and coincide with the line endpoints. No nearest-road
    inference, extrapolation or assumption of uniform real building spacing.
    """
    record: GeocodingRecord
    start_id: str
    end_id: str
    step: int = 1

    def __post_init__(self):
        if self.record.kind!='interpolation' or self.record.geometry.type!='LineString':
            raise ValueError('AddressRange requires an interpolation LineString record')
        _text(self.start_id,'start_id'); _text(self.end_id,'end_id'); _integer(self.step,'step')


@dataclass(frozen=True)
class GeocodingResult:
    record: GeocodingRecord
    source: GeocodingSource
    coordinate: tuple[float,float]
    precision: str
    score: float = 0.
    match: str = 'exact'
    distance_m: float | None = None
    contains: bool = False
    range_ids: tuple[str,...] = ()

    def __post_init__(self):
        if not isinstance(self.record,GeocodingRecord) or not isinstance(self.source,GeocodingSource) or self.record.source!=self.source.id:
            raise ValueError('Result needs a record and its declared source')
        object.__setattr__(self,'coordinate',geo.coordinate(self.coordinate))
        if not math.isfinite(self.score): raise ValueError('Result score must be finite')
        if self.distance_m is not None and (not math.isfinite(self.distance_m) or self.distance_m<0):
            raise ValueError('Distance must be nonnegative finite metres or None')
        _text(self.precision,'precision'); _text(self.match,'match')
        object.__setattr__(self,'range_ids',tuple(self.range_ids))

    @property
    def name(self): return self.record.address.display() if self.match=='interpolated' else self.record.name

    def to_feature(self, *, boundary=False):
        """Normal layer/picking/labels integration; no contacts or query history."""
        props = dict(name=self.name,kind=self.record.kind,record_id=self.record.id,
                     source_id=self.source.id,source_version=self.source.version,
                     source_sha256=self.source.sha256,license=self.source.license,
                     attribution=self.source.attribution,copyright=self.source.copyright,
                     precision=self.precision,match=self.match,score=self.score,
                     distance_m=self.distance_m,accuracy_m=self.record.accuracy_m,
                     contains=self.contains,category=self.record.category,
                     address=self.record.address.as_dict(),range_ids=self.range_ids)
        geometry = self.record.geometry if boundary else Geometry('Point',self.coordinate)
        return Feature(geometry,props,f'{self.source.id}:{self.record.id}')


@dataclass(frozen=True)
class GeocodingResults:
    items: tuple[GeocodingResult,...]
    total: int
    ambiguous: bool
    truncated: bool
    diagnostics: tuple[str,...] = ()

    def __post_init__(self):
        items = tuple(self.items); _integer(self.total,'total',0)
        if any(not isinstance(r,GeocodingResult) for r in items) or len(items)>self.total:
            raise ValueError('Results need typed items and a complete match count')
        if self.ambiguous!=(self.total>1) or self.truncated!=(len(items)<self.total):
            raise ValueError('Ambiguity/truncation must agree with total matches')
        object.__setattr__(self,'items',items); object.__setattr__(self,'diagnostics',tuple(self.diagnostics))

    def __iter__(self): return iter(self.items)
    def __len__(self): return len(self.items)
    def __getitem__(self,index): return self.items[index]
    def to_features(self, *, boundary=False):
        return FeatureCollection(tuple(r.to_feature(boundary=boundary) for r in self.items))


def records_from_features(features, source, *, include_addresses=False):
    """Allowlisted OSM/GeoJSON tags; aliases/language names retain display text.

    addr:* import is deliberately opt-in. Administrative membership is taken
    only from explicit fields; proximity to a city point does not establish it.
    Non-numeric house numbers remain literal. Interpolation needs AddressRange.
    """
    if not isinstance(source,GeocodingSource): raise TypeError('Explicit GeocodingSource required')
    if not isinstance(include_addresses,bool): raise ValueError('include_addresses must be an explicit boolean')
    for feature in features:
        p = feature.properties; g = feature.geometry
        if g is None: continue
        if feature.id is None: raise ValueError('Geocoding import requires stable feature IDs')
        if p.get('addr:interpolation'): continue  # no guessing endpoint references
        def address_tag(name):
            value = p.get('addr:'+({'house_number':'housenumber','neighborhood':'suburb'}.get(name,name)))
            if value is None: return ''
            if not isinstance(value,str): raise ValueError('Address tags must be strings or absent, never inferred from another type')
            return value
        address = Address(**{name:address_tag(name) for name in ADDRESS_FIELDS}) if include_addresses else Address()
        names = []
        for key,value in p.items():
            if key=='name' or key.startswith('name:') or key in ('official_name','short_name','alt_name','old_name','loc_name'):
                if isinstance(value,str): names.extend(n.strip() for n in value.split(';') if n.strip())
        if address.house_number: kind = 'address'
        elif p.get('highway') and g.type in ('LineString','MultiLineString'): kind = 'street'
        elif p.get('place') or p.get('boundary')=='administrative': kind = 'locality'
        elif any(p.get(key) for key in ('amenity','shop','tourism','leisure','office','public_transport')): kind = 'poi'
        else: continue
        if not names and not address.display(): continue
        if kind=='street' and not address.street and names: address = replace(address,street=names[0])
        category = next((str(p[k]) for k in ('place','amenity','shop','tourism','highway','boundary','leisure','office','public_transport') if p.get(k)),'')
        yield GeocodingRecord(str(feature.id),kind,tuple(names),g,source.id,address,category)


class LocalGeocoder:
    """Read-only, integrity-checked own local index. Context manager recommended."""

    def __init__(self, directory, *, max_candidates=5000):
        self.directory = Path(directory)
        self.max_candidates = _integer(max_candidates,'max_candidates')
        manifest_file = self.directory/'manifest.json'
        if manifest_file.stat().st_size>8*1024*1024: raise GeocodingLimitError('Manifest exceeds 8 MiB')
        manifest = json.loads(manifest_file.read_text(encoding='utf8'))
        if manifest.get('schema')!=SCHEMA or manifest.get('database_sha256')!=_digest(self.directory/'index.sqlite'):
            raise ValueError('Geocoding schema or database integrity mismatch')
        self.sources = MappingProxyType({s['id']:GeocodingSource(**s) for s in manifest['sources']})
        if len(self.sources)!=len(manifest['sources']): raise ValueError('Duplicate source manifest')
        self.metadata = MappingProxyType(manifest)
        self._db = sqlite3.connect((self.directory/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)
        self._db.execute('PRAGMA query_only=ON')
        if self._db.execute('PRAGMA user_version').fetchone()[0]!=SCHEMA:
            self.close(); raise ValueError('Unsupported database version')
        # Source provenance also lives in the hashed database; sidecar edits fail.
        expected = self._db.execute('SELECT value FROM metadata WHERE key="sources"').fetchone()[0]
        if json.loads(expected)!=manifest['sources']:
            self.close(); raise ValueError('Source notice/provenance integrity mismatch')
        if manifest['unicode_version']!=unicodedata.unidata_version:
            self.close(); raise ValueError('Unicode database version differs; rebuild index with this Python runtime')
        stored = self._db.execute('SELECT value FROM metadata WHERE key="manifest"').fetchone()[0]
        if json.loads(stored)!={k:v for k,v in manifest.items() if k!='database_sha256'}:
            self.close(); raise ValueError('Manifest metadata integrity mismatch')

    @classmethod
    def build(cls, directory, records, *, sources, ranges=(), max_records=250000,
              max_bytes=256*1024*1024, min_free_bytes=64*1024*1024, max_candidates=5000):
        """Stream records into a new directory atomically; never overwrite data.

        Budgets bound records, SQLite pages, JSON records (1 MiB each) and the
        complete generated directory. SQLite journaling is disabled only for the
        private unpublished staging DB; failures remove that staging directory.
        """
        max_records = _integer(max_records,'max_records'); max_bytes = _integer(max_bytes,'max_bytes',65536)
        _integer(min_free_bytes,'min_free_bytes',0); _integer(max_candidates,'max_candidates')
        directory = Path(directory).resolve()
        if directory.exists(): raise FileExistsError('Geocoder destination already exists')
        if not directory.parent.is_dir(): raise FileNotFoundError('Geocoder parent directory must exist')
        sources = tuple(sources)
        if not sources or len(sources)>64 or any(not isinstance(s,GeocodingSource) for s in sources):
            raise ValueError('Explicit bounded source declarations required')
        source_ids = {s.id for s in sources}
        if len(source_ids)!=len(sources): raise ValueError('Duplicate source IDs')
        source_json = json.dumps([s.as_dict() for s in sources],ensure_ascii=False,sort_keys=True)
        if len(source_json.encode('utf8'))>4*1024*1024: raise GeocodingLimitError('Source notices exceed 4 MiB')
        if shutil.disk_usage(directory.parent).free<min_free_bytes+65536:
            raise GeocodingLimitError('Insufficient free disk reserve')
        staging = Path(tempfile.mkdtemp(prefix='.geocode-build-',dir=directory.parent)); db = None
        count = 0
        def budget():
            if sum(p.stat().st_size for p in staging.iterdir() if p.is_file())>max_bytes:
                raise GeocodingLimitError('Geocoder storage budget exceeded')
            if shutil.disk_usage(staging).free<min_free_bytes:
                raise GeocodingLimitError('Free disk reserve reached')
        try:
            db = sqlite3.connect(staging/'index.sqlite')
            db.executescript('''PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;
                PRAGMA temp_store=MEMORY; PRAGMA cache_size=-2048; PRAGMA user_version=1;
                CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
                CREATE TABLE records(rid INTEGER PRIMARY KEY,source TEXT,id TEXT,data TEXT,UNIQUE(source,id));
                CREATE TABLE representatives(rid INTEGER PRIMARY KEY,x REAL,y REAL,precision TEXT);
                CREATE TABLE words(word TEXT,rid INTEGER,PRIMARY KEY(word,rid)) WITHOUT ROWID;
                CREATE TABLE letters(letter TEXT,word TEXT,PRIMARY KEY(letter,word)) WITHOUT ROWID;
                CREATE TABLE filters(field TEXT,value TEXT,rid INTEGER,PRIMARY KEY(field,value,rid)) WITHOUT ROWID;
                CREATE TABLE spatial(level INTEGER,x INTEGER,y INTEGER,rid INTEGER,PRIMARY KEY(level,x,y,rid)) WITHOUT ROWID;
                CREATE TABLE ranges(rid INTEGER PRIMARY KEY,start INTEGER,end INTEGER,step INTEGER,start_id TEXT,end_id TEXT);
            ''')
            # Reserve manifest space before SQLite can consume the storage budget.
            pages = max(1,(max_bytes-len(source_json.encode('utf8'))-8192)//4096)
            db.execute(f'PRAGMA max_page_count={pages}')
            db.execute('INSERT INTO metadata VALUES (?,?)',('sources',source_json))
            def insert(record):
                nonlocal count
                if not isinstance(record,GeocodingRecord): raise TypeError('Expected GeocodingRecord')
                if record.source not in source_ids: raise ValueError('Record refers to an undeclared source')
                if count>=max_records: raise GeocodingLimitError('Geocoding record budget exceeded')
                if sum(1 for _ in record.geometry.iter_positions())>4096:
                    raise GeocodingLimitError('Geocoding record geometry exceeds 4096 vertices; use a regional simplified boundary')
                point,precision = geo.representative(record.geometry)  # preserve source geometry
                raw = json.dumps(record.as_dict(),ensure_ascii=False,separators=(',',':'))
                if len(raw.encode('utf8'))>1024*1024: raise GeocodingLimitError('Record exceeds 1 MiB')
                try: cursor = db.execute('INSERT INTO records(source,id,data) VALUES (?,?,?)',(record.source,record.id,raw))
                except sqlite3.IntegrityError as exc: raise ValueError('Duplicate source/record ID') from exc
                rid = cursor.lastrowid; count += 1
                db.execute('INSERT INTO representatives VALUES (?,?,?,?)',(rid,*point,precision))
                text = ' '.join((*record.names,record.address.display()))
                words = tokens(text)
                db.executemany('INSERT INTO words VALUES (?,?)',((w,rid) for w in words))
                db.executemany('INSERT OR IGNORE INTO letters VALUES (?,?)',((c,w) for w in words for c in set(w)))
                db.executemany('INSERT INTO filters VALUES (?,?,?)',
                    ((key,normalize_name(value),rid) for key,value in record.address.as_dict().items() if value))
                db.execute('INSERT INTO filters VALUES (?,?,?)',('kind',record.kind,rid))
                db.executemany('INSERT INTO spatial VALUES (?,?,?,?)',((*cell,rid) for cell in geo.postings(record.geometry)))
                budget()
                return rid
            for record in records:
                if not isinstance(record,GeocodingRecord): raise TypeError('Expected GeocodingRecord')
                if record.kind=='interpolation': raise ValueError('Interpolation records must be supplied as AddressRange')
                insert(record)
            for address_range in ranges:
                if not isinstance(address_range,AddressRange): raise TypeError('Expected AddressRange')
                r = address_range.record; endpoints = []
                for identifier in (address_range.start_id,address_range.end_id):
                    row = db.execute('SELECT data FROM records WHERE source=? AND id=?',(r.source,identifier)).fetchone()
                    if row is None: raise ValueError('Interpolation endpoint is missing')
                    endpoint = GeocodingRecord.from_dict(json.loads(row[0]))
                    if endpoint.kind!='address' or endpoint.geometry.type!='Point' or not re.fullmatch('[0-9]+',endpoint.address.house_number):
                        raise ValueError('Interpolation endpoints require explicit numeric point addresses')
                    if not endpoint.address.street or any(normalize_name(getattr(endpoint.address,k))!=normalize_name(getattr(r.address,k)) for k in ADDRESS_FIELDS if k!='house_number'):
                        raise ValueError('Interpolation street/address context mismatch')
                    endpoints.append(endpoint)
                if endpoints[0].geometry.coordinates!=r.geometry.coordinates[0] or endpoints[1].geometry.coordinates!=r.geometry.coordinates[-1]:
                    raise ValueError('Interpolation endpoint coordinates must match the source line exactly')
                first,last = (int(e.address.house_number) for e in endpoints)
                if first==last or (last-first)%address_range.step: raise ValueError('Invalid numeric range or step/parity')
                if r.address.house_number: raise ValueError('Range record must not claim an individual house number')
                rid = insert(r)
                db.execute('INSERT INTO ranges VALUES (?,?,?,?,?,?)',(rid,first,last,address_range.step,address_range.start_id,address_range.end_id))
            manifest = dict(schema=SCHEMA,sources=json.loads(source_json),
                            records=count,normalization='NFKC/casefold; optional accent folding; category tokens',
                            unicode_version=unicodedata.unidata_version,coverage='Only imported objects and explicit interpolation ranges; incomplete by design',
                            distance_model='sphere, radius 6371008.8 m; regional polygon containment in lon/lat',
                            query_logging=False,storage_budget_bytes=max_bytes)
            db.execute('INSERT INTO metadata VALUES (?,?)',('manifest',json.dumps(manifest,ensure_ascii=False)))
            db.commit(); db.close(); db = None; budget()
            manifest['database_sha256'] = _digest(staging/'index.sqlite')
            (staging/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
            budget(); staging.rename(directory)
        except Exception as exc:
            if db is not None: db.close()
            if staging.exists(): shutil.rmtree(staging)
            if isinstance(exc,sqlite3.OperationalError) and 'full' in str(exc).lower():
                raise GeocodingLimitError('SQLite storage budget exceeded') from exc
            raise
        return cls(directory,max_candidates=max_candidates)

    @classmethod
    def from_catalog(cls, catalog, identifier, directory, *, version=None, include_addresses=False, **budgets):
        """Verify the optional catalog bytes and copy its license/attribution text."""
        entries = [e for e in catalog.available() if e['id']==identifier and (version is None or e['version']==version)]
        if len(entries)!=1: raise ValueError('Choose an unambiguous catalog dataset/version')
        entry = entries[0]
        if entry['crs']!='EPSG:4326': raise ValueError('Geocoder catalog import requires explicit WGS84 lon/lat')
        catalog.verify(identifier,version=entry['version'])
        # The catalog already enforces safe relative paths and byte hashes.
        notice = catalog._resolve(entry['license_file'])
        if notice.stat().st_size>262144: raise GeocodingLimitError('Catalog license exceeds 256 KiB')
        notice_bytes = notice.read_bytes()
        if hashlib.sha256(notice_bytes).hexdigest()!=entry['files'][entry['license_file']]:
            raise ValueError('Catalog license integrity mismatch')
        source = GeocodingSource(entry['id'],entry['version'],entry['license'],entry['copyright'],
                                entry['attribution'],entry['source'],entry['files'][entry['file']],
                                (notice_bytes.decode('utf8'),))
        features = catalog.load(identifier,version=entry['version'])
        if not isinstance(features,FeatureCollection): raise ValueError('Geocoder requires vector features')
        return cls.build(directory,records_from_features(features,source,include_addresses=include_addresses),sources=(source,),**budgets)

    @classmethod
    def from_osm_index(cls, index, source, directory, *, include_addresses=False, bbox=None, where=None, **budgets):
        """Stream from the own PBF disk index, checking its fully consumed hash.

        The OSM index retains its separate budget/lifecycle; the caller must
        budget both indexes. Explicitly skipped missing references are rejected
        here rather than treated as complete geocoding input.
        """
        from .pbf import OSMIndex
        if not isinstance(index,OSMIndex) or not isinstance(source,GeocodingSource): raise TypeError('Expected OSMIndex and source')
        if index.sha256!=source.sha256: raise ValueError('PBF input hash differs from declared geocoding source')
        if index.statistics['missing_ways'] or index.statistics['missing_relations']:
            raise ValueError('PBF index has missing references; resolve them before geocoding import')
        return cls.build(directory,records_from_features(index.features(bbox=bbox,where=where),source,include_addresses=include_addresses),
                         sources=(source,),**budgets)

    def __enter__(self): return self
    def __exit__(self,*args): self.close()
    def close(self):
        if getattr(self,'_db',None) is not None: self._db.close(); self._db = None

    def _connection(self):
        if self._db is None: raise RuntimeError('Geocoder is closed')
        return self._db

    def _record(self,rid):
        return GeocodingRecord.from_dict(json.loads(self._connection().execute('SELECT data FROM records WHERE rid=?',(rid,)).fetchone()[0]))

    def _records(self,ids):
        consumed = 0
        for rid in sorted(ids):
            raw = self._connection().execute('SELECT data FROM records WHERE rid=?',(rid,)).fetchone()[0]
            consumed += len(raw.encode('utf8'))
            if consumed>32*1024*1024: raise GeocodingLimitError('Query decoded-record budget exceeds 32 MiB')
            yield rid,GeocodingRecord.from_dict(json.loads(raw))

    def _ids(self,sql,parameters=()):
        rows = self._connection().execute(sql+' LIMIT ?',(*parameters,self.max_candidates+1)).fetchall()
        ids = {row[0] for row in rows}
        if len(ids)>self.max_candidates: raise GeocodingLimitError('Candidate budget reached; narrow query or increase explicit max_candidates')
        return ids

    def _matching_ids(self,sql,parameters=(),within=None):
        if within is None: return self._ids(sql,parameters)
        ordered = sorted(within); found = set()
        for offset in range(0,len(ordered),400):
            part = ordered[offset:offset+400]
            found.update(self._ids(sql+' AND rid IN ('+','.join('?' for _ in part)+')',(*parameters,*part)))
        return found

    def _spatial(self,boxes):
        found = set()
        for box in boxes:
            for level in range(13):
                x0,y0,x1,y1 = geo.cells(box,level)
                found.update(self._ids('SELECT DISTINCT rid FROM spatial WHERE level=? AND x BETWEEN ? AND ? AND y BETWEEN ? AND ?',
                                      (level,x0,x1,y0,y1)))
                if len(found)>self.max_candidates: raise GeocodingLimitError('Spatial candidate budget reached')
        return found

    def _filter(self,ids,filters,kinds):
        if filters is not None:
            for key,value in filters.items():
                if key not in ADDRESS_FIELDS: raise ValueError('Unknown address filter')
                allowed = self._matching_ids('SELECT rid FROM filters WHERE field=? AND value=?',(key,normalize_name(value)),ids)
                ids = allowed if ids is None else ids & allowed
        if kinds is not None:
            kinds = tuple(kinds)
            if not kinds or any(k not in KINDS for k in kinds): raise ValueError('Unknown/empty kinds filter')
            marks = ','.join('?' for _ in kinds)
            allowed = self._matching_ids(f'SELECT DISTINCT rid FROM filters WHERE field="kind" AND value IN ({marks})',kinds,ids)
            ids = allowed if ids is None else ids & allowed
        return ids

    def search(self, query='', *, filters=None, kinds=None, bbox=None, near=None,
               radius_m=5000., fuzzy=False, prefix=False, interpolate=False, limit=10):
        """Own exact/prefix/fuzzy token ranking; score is not a probability.

        Filters match declared source address fields, never inferred membership.
        Ambiguous means multiple matches, even if limit=1 hides lower results.
        Approximation and interpolation require explicit opt-in. No top result
        is silently chosen for the caller. Candidate overflow raises.
        """
        _integer(limit,'limit'); normalized = normalize_name(query); words = tokens(query)
        if fuzzy and (len(words)>16 or any(len(w)>128 for w in words)):
            raise GeocodingLimitError('Fuzzy search allows at most 16 tokens of 128 characters')
        filters = dict(filters or {})
        ids = None
        if words:
            if not fuzzy and not prefix:
                words = tuple(sorted(words,key=lambda w:self._connection().execute('SELECT count(*) FROM words WHERE word=?',(w,)).fetchone()[0]))
            found = None
            for word in words:
                if prefix:
                    matches = self._matching_ids('SELECT DISTINCT rid FROM words WHERE substr(word,1,?)=?',(len(word),word),found)
                else: matches = self._matching_ids('SELECT rid FROM words WHERE word=?',(word,),found)
                if fuzzy:
                    vocab = self._connection().execute('SELECT DISTINCT word FROM letters WHERE letter IN ('+','.join('?' for _ in set(word))+') LIMIT ?',(*sorted(set(word)),self.max_candidates+1)).fetchall()
                    if len(word)<=2:
                        vocab += self._connection().execute('SELECT DISTINCT word FROM words WHERE length(word)<=? LIMIT ?',(len(word)+1,self.max_candidates+1)).fetchall()
                        vocab = sorted(set(vocab))
                    if len(vocab)>self.max_candidates: raise GeocodingLimitError('Fuzzy vocabulary budget reached')
                    for (candidate,) in vocab:
                        if edit_distance(word,candidate,1 if len(word)<5 else 2)<= (1 if len(word)<5 else 2):
                            matches.update(self._matching_ids('SELECT rid FROM words WHERE word=?',(candidate,),found))
                found = matches if found is None else found & matches
                if len(found)>self.max_candidates: raise GeocodingLimitError('Text candidate budget reached')
            ids = found
        ordinary_filters = {k:v for k,v in filters.items() if not (interpolate and k=='house_number')}
        if interpolate and 'house_number' in filters:
            range_ids = self._ids('SELECT rid FROM ranges')
            if ids is None:
                ids = self._ids('SELECT rid FROM filters WHERE field="house_number" AND value=?',(normalize_name(filters['house_number']),))
            ids.update(range_ids)
            if len(ids)>self.max_candidates: raise GeocodingLimitError('Interpolation candidate budget reached')
        ids = self._filter(ids,ordinary_filters,kinds)
        if bbox is not None:
            if len(bbox)!=4: raise ValueError('bbox requires west,south,east,north')
            west,south,east,north = bbox
            geo.coordinate((west,south)); geo.coordinate((east,north))
            if west>east or south>north: raise ValueError('Split wrapped bbox explicitly')
            spatial = self._spatial((bbox,)); ids = spatial if ids is None else ids & spatial
        if near is not None:
            geo.coordinate(near)
            if not isinstance(radius_m,(int,float)) or isinstance(radius_m,bool) or not math.isfinite(radius_m) or radius_m<0:
                raise ValueError('radius_m must be finite nonnegative metres')
            spatial = self._spatial(geo.cap_boxes(near,radius_m)); ids = spatial if ids is None else ids & spatial
        if ids is None: raise ValueError('Supply search text, address filters or a spatial/kind filter')
        matches = []; skipped_ranges = 0
        for rid,record in self._records(ids):
            if record.kind=='interpolation' and not interpolate: skipped_ranges += 1; continue
            if record.kind!='interpolation' and 'house_number' in filters and normalize_name(record.address.house_number)!=normalize_name(filters['house_number']): continue
            if record.kind=='interpolation' and filters.get('house_number'):
                search_text = filters['house_number']+' '+' '.join((*record.names,record.address.display()))
            else: search_text = ' '.join((*record.names,record.address.display()))
            record_words = tokens(search_text)
            distances = []
            for word in words:
                distances.append(min((0 if word==w else .25 if prefix and w.startswith(word)
                                      else edit_distance(word,w,1 if len(word)<5 else 2) if fuzzy else 100
                                      for w in record_words),default=100))
            if any(d>(1 if len(w)<5 else 2) if fuzzy else d>=1 for w,d in zip(words,distances)): continue
            x,y,precision = self._connection().execute('SELECT x,y,precision FROM representatives WHERE rid=?',(rid,)).fetchone()
            point = (x,y)
            match = 'approximate' if any(d>=1 for d in distances) else 'prefix' if any(distances) else 'exact'
            range_ids = ()
            if record.kind=='interpolation':
                number = filters.get('house_number','')
                if not re.fullmatch('[0-9]+',number): continue
                row = self._connection().execute('SELECT start,end,step,start_id,end_id FROM ranges WHERE rid=?',(rid,)).fetchone()
                first,last,step,start_id,end_id = row; number_int = int(number)
                if not min(first,last)<=number_int<=max(first,last) or (number_int-first)%step: continue
                point = geo.at_fraction(record.geometry.coordinates,(number_int-first)/(last-first))
                precision = match = 'interpolated'; range_ids = (start_id,end_id)
                record = replace(record,address=replace(record.address,house_number=number),accuracy_m=None)
            distance = None; contains = False
            if near is not None:
                _,distance,contains = geo.nearest(Geometry('Point',point) if match=='interpolated' else record.geometry,near)
                if distance>radius_m: continue
            if bbox is not None and not (west<=point[0]<=east and south<=point[1]<=north): continue
            exact_name = normalized and any(normalize_name(n)==normalized for n in (*record.names,record.address.display()))
            score = 100.-10*sum(distances)+(20 if exact_name else 0)-(30 if match=='interpolated' else 0)
            matches.append(GeocodingResult(record,self.sources[record.source],point,precision,score,match,distance,contains,range_ids))
        matches.sort(key=lambda r:(-r.score,r.distance_m if r.distance_m is not None else 0,r.source.id,r.record.id))
        diagnostics = ['Coverage is limited to imported data; no result does not prove an address is absent.']
        if skipped_ranges: diagnostics.append('Interpolation ranges were not used; opt in explicitly.')
        return GeocodingResults(tuple(matches[:limit]),len(matches),len(matches)>1,len(matches)>limit,tuple(diagnostics))

    def reverse(self, lon, lat, *, radius_m=1000., kinds=None, filters=None, limit=10):
        """Nearest imported objects/containing regional boundaries, in spherical metres.

        Distances are to source points or minor-arc line/boundary segments, not
        survey accuracy or travel distance. Containing boundaries have distance
        zero and retain the query point plus the original boundary separately.
        """
        _integer(limit,'limit'); point = geo.coordinate((lon,lat))
        if isinstance(radius_m,bool) or not isinstance(radius_m,(int,float)) or not math.isfinite(radius_m) or radius_m<0:
            raise ValueError('radius_m must be finite nonnegative metres')
        ids = self._filter(self._spatial(geo.cap_boxes(point,radius_m)),filters,kinds)
        matches = []
        for rid,record in self._records(ids):
            if record.kind=='interpolation': continue  # nearest range is not an address
            coordinate,distance,contains = geo.nearest(record.geometry,point)
            if distance>radius_m+1e-6: continue
            precision = 'containing_boundary' if contains else 'source_point' if record.geometry.type=='Point' else 'nearest_centerline' if record.geometry.type in ('LineString','MultiLineString') else 'nearest_boundary'
            matches.append(GeocodingResult(record,self.sources[record.source],coordinate,precision,0.,'reverse',distance,contains))
        matches.sort(key=lambda r:(r.distance_m,r.source.id,r.record.id))
        return GeocodingResults(tuple(matches[:limit]),len(matches),len(matches)>1,len(matches)>limit,
                                ('Nearest imported object does not establish a postal address or administrative membership.',))


class ExternalGeocoder:
    """Explicit separate adapter; caller owns provider terms, network and privacy.

    It never falls back from LocalGeocoder. Callables must return typed results
    with a declared source. No requests, credentials or provider are built in.
    """
    def __init__(self, search, reverse=None):
        if not callable(search) or (reverse is not None and not callable(reverse)): raise TypeError('Provider requires callables')
        self._search,self._reverse = search,reverse

    @staticmethod
    def _result(result):
        if not isinstance(result,GeocodingResults): raise TypeError('External provider must return GeocodingResults')
        return result

    def search(self,*args,**kwargs): return self._result(self._search(*args,**kwargs))
    def reverse(self,*args,**kwargs):
        if self._reverse is None: raise NotImplementedError('Provider does not implement reverse geocoding')
        return self._result(self._reverse(*args,**kwargs))

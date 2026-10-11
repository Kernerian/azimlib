"""Original, finite CRS capability catalog, not a copy of an authority database.

Identifier numbers are interoperability facts. Geodetic constants: NGA WGS84;
UTM convention: USGS Professional Paper 1395. See docs/crs-0.4.md.
"""
from dataclasses import dataclass
from types import MappingProxyType

CATALOG_VERSION = 'azimlib-crs-1'
_SOURCES = ('https://earth-info.nga.mil/index.php?action=wgs84&dir=wgs84',
            'https://pubs.usgs.gov/pp/1395/report.pdf')


def identifier(value):
    code = str(value).strip().upper()
    if code.isdigit():
        code = 'EPSG:' + code
    if code in ('WGS84', 'WGS 84', 'CRS84', 'OGC:CRS84'):
        code = 'EPSG:4326'
    return code


@dataclass(frozen=True)
class CRSDefinition:
    code: str
    kind: str
    dimensions: int
    axes: tuple
    authority_axes: tuple
    axis_units: tuple
    area_of_use: tuple
    domain: str
    datum: str = 'WGS84'
    catalog_version: str = CATALOG_VERSION
    sources: tuple = _SOURCES
    definition_license: str = 'BSD-3-Clause'

    def to_dict(self):
        """Azimlib's own exact profile, not WKT or PROJJSON."""
        return dict(profile='azimlib-crs', version=1, catalog_version=self.catalog_version,
                    code=self.code, kind=self.kind, dimensions=self.dimensions,
                    axes=list(self.axes), authority_axes=list(self.authority_axes),
                    axis_units=list(self.axis_units), area_of_use=list(self.area_of_use),
                    domain=self.domain, datum=self.datum)


def _definitions():
    world = (-180, -90, 180, 90)
    yield CRSDefinition('EPSG:4326', 'geographic', 2, ('longitude', 'latitude'),
                        ('latitude', 'longitude'), ('degrees', 'degrees'), world,
                        'Canonical lon/lat; no realization, epoch or datum shift inferred')
    yield CRSDefinition('EPSG:4979', 'geographic', 3, ('longitude', 'latitude', 'height'),
                        ('latitude', 'longitude', 'height'), ('degrees', 'degrees', 'metres'), world,
                        'Ellipsoidal height >= -10000 m; no orthometric height/geoid inferred')
    yield CRSDefinition('EPSG:4978', 'geocentric', 3, ('X', 'Y', 'Z'), ('X', 'Y', 'Z'),
                        ('metres',)*3, world, 'Earth-fixed XYZ; shallow/exterior domain h >= -10000 m')
    yield CRSDefinition('EPSG:3857', 'projected', 2, ('easting', 'northing'), ('easting', 'northing'),
                        ('metres',)*2, (-180, -85.0511287798066, 180, 85.0511287798066),
                        'Conventional Web Mercator square; spherical map equations on WGS84 axes')
    for hemisphere, base in (('north', 32600), ('south', 32700)):
        for zone in range(1, 61):
            yield CRSDefinition(f'EPSG:{base+zone}', 'projected', 2,
                                ('easting', 'northing'), ('easting', 'northing'), ('metres',)*2,
                                (-180+6*(zone-1), 0 if hemisphere == 'north' else -80,
                                 -180+6*zone, 84 if hemisphere == 'north' else 0),
                                'Regional TM: within 6 degrees of meridian; hemisphere; E [0,1e6], N [0,1e7]')


class CRSCatalog:
    """Read-only versioned declarations of implemented conversions only.

    Nominal UTM zone bounds are metadata, distinct from the regional solver's
    numerical domain. No network, authority database or automatic grid acquisition.
    """
    version = CATALOG_VERSION

    def __init__(self):
        self._entries = MappingProxyType({entry.code: entry for entry in _definitions()})

    def get(self, code):
        value = identifier(getattr(code, 'code', code))
        try:
            return self._entries[value]
        except KeyError:
            raise ValueError(f'unsupported CRS {value!r}; consult crs_catalog.codes()') from None

    def codes(self, *, kind=None):
        if kind is not None and kind not in ('geographic', 'geocentric', 'projected'):
            raise ValueError('Unknown CRS kind')
        return tuple(code for code, entry in self._entries.items() if kind is None or entry.kind == kind)


crs_catalog = CRSCatalog()

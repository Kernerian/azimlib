"""Own KML and OSM XML geometry interpretation, with no network resources."""
from ._readers import xml_root, assign_holes
from .geometry import Feature, FeatureCollection, Geometry, position


def _name(element):
    return element.tag.rsplit('}', 1)[-1]


def _children(element, name):
    return [child for child in element if _name(child) == name]


def _text(element, name, default=None):
    children = _children(element, name)
    if len(children) > 1: raise ValueError(f'Duplicate KML {name}')
    return default if not children else (children[0].text or '').strip()


def _kml_geometry(element):
    kind = _name(element)
    if kind == 'MultiGeometry':
        return Geometry('GeometryCollection', geometries=tuple(_kml_geometry(child) for child in element))
    if kind == 'Polygon':
        outers = _children(element, 'outerBoundaryIs')
        if len(outers) != 1: raise ValueError('KML polygon requires one outerBoundaryIs')
        boundaries = outers + _children(element, 'innerBoundaryIs')
        rings = []
        for boundary in boundaries:
            children = _children(boundary, 'LinearRing')
            if len(children) != 1: raise ValueError('KML boundary requires one LinearRing')
            rings.append(_kml_coordinates(children[0]))
        return Geometry('Polygon', rings)
    if kind in ('Point', 'LineString'):
        coords = _kml_coordinates(element)
        if kind == 'Point':
            if len(coords) != 1: raise ValueError('KML Point requires one position')
            return Geometry('Point', coords[0])
        return Geometry('LineString', coords)
    raise ValueError(f'Unsupported KML geometry {kind}')


def _kml_coordinates(element):
    text = _text(element, 'coordinates')
    if text is None: raise ValueError('KML geometry requires coordinates')
    values = []
    for item in text.split():
        try: values.append(position(tuple(float(v) for v in item.split(','))))
        except ValueError as exc: raise ValueError('Invalid KML coordinate tuple') from exc
    return tuple(values)


def read_kml(source):
    """Local KML 2.2/2.3 Point/LineString/Polygon/MultiGeometry placemarks.

    Preserve optional elevation, altitudeMode, names and ExtendedData strings.
    Styles are not interpreted. DTD/entity/include/NetworkLink are forbidden;
    Track/Model/overlays and standalone LinearRing are rejected. No KMZ/network.
    """
    root = xml_root(source)
    if _name(root) != 'kml' or root.tag not in ('kml', '{http://www.opengis.net/kml/2.2}kml', '{http://www.opengis.net/kml/2.3}kml'):
        raise ValueError('Expected KML root/namespace')
    forbidden = {'NetworkLink', 'NetworkLinkControl', 'GroundOverlay', 'ScreenOverlay', 'PhotoOverlay', 'Model', 'Track', 'MultiTrack'}
    if any(_name(element) in forbidden for element in root.iter()):
        raise ValueError('External resources or unsupported KML feature')
    allowed_namespaces = ('http://www.opengis.net/kml/2.2', 'http://www.opengis.net/kml/2.3')
    for element in root.iter():
        if element.tag.startswith('{') and element.tag[1:].split('}', 1)[0] not in allowed_namespaces:
            raise ValueError('Unsupported KML extension namespace')
    features = []; ids = set()
    for placemark in root.iter():
        if _name(placemark) != 'Placemark': continue
        geometries = [child for child in placemark if _name(child) in ('Point', 'LineString', 'Polygon', 'MultiGeometry', 'LinearRing')]
        if len(geometries) > 1: raise ValueError('Placemark has multiple geometry elements; use MultiGeometry')
        geometry = None if not geometries else _kml_geometry(geometries[0])
        properties = {}
        for key in ('name', 'description'):
            value = _text(placemark, key)
            if value is not None: properties[key] = value
        altitude_modes = {_text(e, 'altitudeMode') for e in (geometries[0].iter() if geometries else ())}
        altitude_modes.discard(None)
        if not altitude_modes <= {'clampToGround', 'relativeToGround', 'absolute'}:
            raise ValueError('Unsupported KML altitudeMode')
        if altitude_modes: properties['altitude_modes'] = sorted(altitude_modes)
        extended = {}
        for container in _children(placemark, 'ExtendedData'):
            for item in container.iter():
                kind = _name(item)
                if kind not in ('Data', 'SimpleData'): continue
                name = item.get('name')
                if not name or name in extended: raise ValueError('Duplicate/missing ExtendedData name')
                extended[name] = _text(item, 'value', '') if kind == 'Data' else (item.text or '').strip()
        if extended: properties['extended_data'] = extended
        identifier = placemark.get('id')
        if identifier is not None:
            if identifier in ids: raise ValueError('Duplicate placemark ID')
            ids.add(identifier)
        features.append(Feature(geometry, properties, identifier))
    return FeatureCollection(tuple(features))


def _osm_tags(element):
    tags = {}
    for child in _children(element, 'tag'):
        key, value = child.get('k'), child.get('v')
        if key is None or value is None or key in tags or key == 'osm':
            raise ValueError('OSM tag is duplicate, reserved or missing k/v')
        tags[key] = value
    return tags


def _osm_id(value):
    try:
        number = int(value)
        if str(number) != value or not number: raise ValueError()
    except (TypeError, ValueError) as exc:
        raise ValueError('OSM ID/reference must be a nonzero integer string') from exc
    return str(number)


def _rings(segments):
    """Join reversed/open relation members by node identity, not float proximity."""
    pending = [list(segment) for segment in segments]; rings = []
    while pending:
        chain = pending.pop(0)
        if len(chain) < 2: raise ValueError('Multipolygon way has too few nodes')
        while chain[-1] != chain[0]:
            matches = [(i, part[-1] == chain[-1]) for i, part in enumerate(pending)
                       if part[0] == chain[-1] or part[-1] == chain[-1]]
            if len(matches) != 1: raise ValueError('Open or branched OSM multipolygon ring')
            index, reverse = matches[0]; part = pending.pop(index)
            if reverse: part.reverse()
            chain.extend(part[1:])
        if len(chain) < 4 or len(set(chain[:-1])) != len(chain)-1:
            raise ValueError('Degenerate/self-touching OSM multipolygon ring')
        rings.append(chain)
    return rings


def read_osm(source, *, include_untagged=False):
    """Interpret local OSM 0.6 nodes/ways and multipolygon relations strictly.

    Tagged nodes become POIs; open ways become lines. Closed ways with an area
    tag (building/landuse/leisure/amenity/natural water, or area=yes) are polygons,
    unless area=no. Closed highways otherwise remain lines. Multipolygon member
    ways are not duplicated as standalone features. IDs include primitive type.
    Missing nodes/ways, duplicate IDs and incomplete rings raise, never truncate.
    Non-multipolygon relations are not imported. Editor/user/timestamp metadata
    is not retained; original tag strings and coordinates are retained.
    """
    root = xml_root(source)
    if root.tag != 'osm' or root.get('version') != '0.6': raise ValueError('Expected OSM 0.6 XML')
    nodes = {}; ways = {}; relations = {}; order = []
    for element in root:
        kind = element.tag
        if kind not in ('node', 'way', 'relation'): continue
        identifier = _osm_id(element.get('id'))
        target = {'node': nodes, 'way': ways, 'relation': relations}[kind]
        if identifier in target: raise ValueError(f'Duplicate OSM {kind} ID {identifier}')
        if element.get('visible', 'true') != 'true': raise ValueError('Deleted OSM objects are unsupported')
        tags = _osm_tags(element)
        if kind == 'node':
            try: coords = position((float(element.get('lon')), float(element.get('lat'))))
            except (TypeError, ValueError) as exc: raise ValueError(f'Invalid OSM node {identifier}') from exc
            target[identifier] = (coords, tags)
        elif kind == 'way':
            target[identifier] = (tuple(_osm_id(nd.get('ref')) for nd in _children(element, 'nd')), tags)
        else: target[identifier] = (tuple(_children(element, 'member')), tags)
        order.append((kind, identifier))
    def coordinates(refs, context):
        missing = [ref for ref in refs if ref not in nodes]
        if missing: raise ValueError(f'{context}: missing node references: {", ".join(missing[:5])}')
        return tuple(nodes[ref][0] for ref in refs)
    for identifier, (refs, _) in ways.items():
        if len(refs) < 2: raise ValueError(f'OSM way {identifier} has too few references')
        coordinates(refs, f'OSM way {identifier}')
    polygons = {}; consumed = set()
    for identifier, (members, tags) in relations.items():
        if tags.get('type') != 'multipolygon': continue
        segments = {'outer': [], 'inner': []}
        for member in members:
            role = member.get('role', '') or 'outer'
            if member.get('type') != 'way' or role not in segments:
                raise ValueError(f'OSM relation {identifier}: unsupported member type/role')
            ref = _osm_id(member.get('ref'))
            if ref not in ways: raise ValueError(f'OSM relation {identifier}: missing way {ref}')
            if ref in consumed: raise ValueError('Multipolygon way reused by multiple relations')
            segments[role].append(ways[ref][0])
            consumed.add(ref)
        rings = {role: [coordinates(ring, f'OSM relation {identifier}') for ring in _rings(parts)]
                 for role, parts in segments.items()}
        groups = assign_holes(rings['outer'], rings['inner'])
        polygons[identifier] = Geometry('Polygon', groups[0]) if len(groups) == 1 else Geometry('MultiPolygon', groups)
    features = []
    for kind, identifier in order:
        if kind == 'node':
            coords, tags = nodes[identifier]
            if not tags and not include_untagged: continue
            geometry = Geometry('Point', coords)
        elif kind == 'way':
            refs, tags = ways[identifier]
            if identifier in consumed: continue
            coords = coordinates(refs, f'OSM way {identifier}')
            closed = refs[0] == refs[-1]
            is_area = tags.get('area') == 'yes' or any(tags.get(k) not in (None, 'no') for k in ('building', 'landuse', 'leisure', 'amenity')) or tags.get('natural') == 'water'
            geometry = Geometry('Polygon', (coords,)) if closed and is_area and tags.get('area') != 'no' else Geometry('LineString', coords)
            if not tags and not include_untagged: continue
        else:
            if identifier not in polygons: continue
            tags = relations[identifier][1]; geometry = polygons[identifier]
        features.append(Feature(geometry, dict(tags, osm={'type': kind, 'id': identifier}), f'{kind}/{identifier}'))
    return FeatureCollection(tuple(features))

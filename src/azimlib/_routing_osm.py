"""Own OSM routing interpretation, from tag/protocol facts, not a vendor router.

No regional traffic-law inference. Unsupported applicable rules fail closed.
Original implementation; references and coverage are in docs/routing-0.4.md.
"""
from dataclasses import dataclass, field
import math
import re
from types import MappingProxyType

from ._pbf_decode import OSMRecord, OSMMember
from ._readers import xml_root
from .xmlio import _osm_id, _osm_tags, _children
from ._geocode_geometry import coordinate


class RoutingError(ValueError):
    """Invalid/inapplicable network or no feasible route."""


class RoutingLimitError(RuntimeError):
    """A resource budget was exhausted; never a partial optimal route."""


class UnsupportedRoutingRule(RoutingError):
    """An applicable rule cannot be safely interpreted."""


def positive(value, name, *, zero=False):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value < 0 or (not zero and not value):
        raise ValueError(f'{name} requires finite ' + ('nonnegative' if zero else 'positive') + ' numeric units')
    return float(value)


def budget(value, name):
    if isinstance(value,bool) or not isinstance(value,int) or value<1:
        raise ValueError(f'{name} requires a positive integer')
    return value


def identifier(value):
    if isinstance(value,bool) or not isinstance(value,int) or not value or not -(1<<63)<=value<(1<<63):
        raise RoutingError('OSM identifiers must be nonzero int64 integers')
    return value


CAR = dict(motorway=100,motorway_link=50,trunk=80,trunk_link=40,primary=60,primary_link=35,
           secondary=50,secondary_link=30,tertiary=40,tertiary_link=25,residential=30,
           unclassified=30,living_street=10,service=15,road=20)
BIKE = {**{key:18 for key in CAR if not key.startswith(('motorway','trunk'))},
        'cycleway':20,'path':12,'track':12,'living_street':10}
FOOT = {**{key:5 for key in CAR if not key.startswith(('motorway','trunk'))},
        'footway':5,'pedestrian':5,'path':5,'steps':3,'track':4}
MODES = {'car':('motorcar','motor_vehicle','vehicle','access'),
         'bicycle':('bicycle','vehicle','access'), 'foot':('foot','access')}
ALLOW = {'yes','designated','permissive','official'}
DENY = {'no','private','destination','customers','delivery','agricultural','forestry','use_sidepath','dismount'}


@dataclass(frozen=True)
class RoutingProfile:
    """Estimated speeds in km/h; explicit highway allowlist and access hierarchy.

    Defaults are generic modelling assumptions, not regional law or live traffic.
    Destination/customer-only ways are conservatively excluded.
    """
    mode: str = 'car'
    speeds_kmh: object = field(default=None)
    max_speed_kmh: float = 130.

    def __post_init__(self):
        if self.mode not in MODES: raise ValueError('mode must be car, bicycle or foot')
        speeds = dict(self.speeds_kmh if self.speeds_kmh is not None else {'car':CAR,'bicycle':BIKE,'foot':FOOT}[self.mode])
        maximum = positive(self.max_speed_kmh,'max_speed_kmh')
        if maximum>300 or not speeds or len(speeds)>128: raise ValueError('Invalid profile speed budget')
        for key,value in speeds.items():
            if not isinstance(key,str) or not key or len(key)>128: raise ValueError('Invalid highway class')
            speeds[key] = min(positive(value,'speed in km/h'),maximum)
        object.__setattr__(self,'speeds_kmh',MappingProxyType(speeds))
        object.__setattr__(self,'max_speed_kmh',maximum)

    def as_dict(self):
        return dict(mode=self.mode,speeds_kmh=dict(self.speeds_kmh),max_speed_kmh=self.max_speed_kmh)


def allowed(tags, profile):
    # Conditional rules cannot be discarded by selecting an unconditional tag.
    access = MODES[profile.mode]
    applicable = (*access,*(k+suffix for k in access for suffix in (':forward',':backward')),
                  'oneway',*('oneway:'+m for m in access[:-1]),'maxspeed','maxspeed:forward','maxspeed:backward')
    if any(key+':conditional' in tags for key in applicable):
        raise UnsupportedRoutingRule('Conditional access/direction/speed needs a time-aware policy')
    if any(key+suffix in tags for key in MODES[profile.mode] for suffix in (':forward',':backward')):
        raise UnsupportedRoutingRule('Directional access needs an explicit policy')
    for key in MODES[profile.mode]:
        if key in tags:
            if tags[key] in DENY: return False
            if tags[key] not in ALLOW: raise UnsupportedRoutingRule('Unsupported access value for '+key)
            break
    return True


def directions(tags, profile):
    keys = tuple('oneway:'+mode for mode in MODES[profile.mode][:-1])
    value = next((tags[k] for k in keys if k in tags),None)
    if value is None:
        value = 'no' if profile.mode=='foot' else tags.get('oneway','yes' if tags.get('junction')=='roundabout' or tags.get('highway')=='motorway' else 'no')
    if value in ('yes','1','true'): return (1,)
    if value == '-1': return (-1,)
    if value in ('no','0','false'): return (1,-1)
    raise UnsupportedRoutingRule('Unsupported/reversible one-way direction')


def speed(tags, profile, direction):
    value = tags.get('maxspeed:'+('forward' if direction==1 else 'backward'),tags.get('maxspeed'))
    baseline = profile.speeds_kmh[tags['highway']]
    if value is None: return baseline
    match = re.fullmatch(r'([0-9]+(?:\.[0-9]+)?)\s*(km/h|kmh|kph|mph)?',value)
    if not match: raise UnsupportedRoutingRule('Unsupported symbolic/lane/variable maxspeed')
    limit = positive(float(match[1]),'posted maxspeed') * (1.609344 if match[2]=='mph' else 1)
    return min(baseline,limit,profile.max_speed_kmh)


def node_open(tags, profile):
    if not allowed(tags,profile): return False
    barrier = tags.get('barrier')
    if barrier is None or barrier=='no': return True
    if barrier in ('wall','fence','block','jersey_barrier'): return False
    if barrier in ('bollard','cycle_barrier','stile','kissing_gate'):
        return profile.mode=='foot' or profile.mode=='bicycle' and barrier=='bollard'
    if barrier in ('gate','lift_gate','swing_gate'):
        # Access=yes is explicit permission; unspecified gate state is unknown.
        if any(tags.get(k) in ALLOW for k in MODES[profile.mode]): return True
        return False
    raise UnsupportedRoutingRule('Unknown barrier requires explicit routing policy')


def kept_tags(tags):
    keys = {'name','ref','highway','junction','bridge','tunnel','layer','barrier','type','except','area',
            'restriction','maxspeed','maxspeed:forward','maxspeed:backward','oneway',
            'day_on','day_off','hour_on','hour_off','no_u_turn','u_turn'}
    keys.update(k for values in MODES.values() for k in values)
    keys.update(k+suffix for values in MODES.values() for k in values for suffix in (':forward',':backward'))
    conditional = set(MODES['car']+MODES['bicycle']+MODES['foot'])
    conditional |= {k+suffix for k in tuple(conditional) for suffix in (':forward',':backward')}
    conditional |= {'maxspeed','maxspeed:forward','maxspeed:backward'}
    return {k:v for k,v in tags.items() if k in keys or k.startswith(('oneway:','restriction:')) or
            k.endswith(':conditional') and k[:-12] in conditional}


def xml_records(source):
    """Bounded, entity-free XML snapshot primitives with original IDs/references."""
    root = xml_root(source)
    if root.tag!='osm' or root.get('version')!='0.6': raise RoutingError('Expected OSM 0.6 XML')
    for element in root:
        kind = element.tag
        if kind not in ('node','way','relation'): continue
        if element.get('visible','true')!='true': raise RoutingError('Deleted OSM objects are unsupported')
        oid = int(_osm_id(element.get('id')))
        tags = _osm_tags(element)
        if kind=='node':
            try: point = coordinate((float(element.get('lon')),float(element.get('lat'))))
            except (TypeError,ValueError) as exc: raise RoutingError('Invalid OSM routing coordinate') from exc
            yield OSMRecord(kind,oid,tags,point)
        elif kind=='way':
            yield OSMRecord(kind,oid,tags,refs=tuple(int(_osm_id(e.get('ref'))) for e in _children(element,'nd')))
        else:
            members = tuple(OSMMember(e.get('type'),int(_osm_id(e.get('ref'))),e.get('role','')) for e in _children(element,'member'))
            yield OSMRecord(kind,oid,tags,members=members)


def restriction_value(tags, profile):
    modes = MODES[profile.mode][:-1]
    if any(m in tags.get('except','').split(';') for m in modes): return None
    typed = tags.get('type','restriction').split(':',1)
    if len(typed)==2 and typed[1] not in modes: return None
    keys = tuple('restriction:'+mode for mode in modes)+('restriction',)
    if profile.mode=='foot' and not any(k in tags for k in ('restriction:foot','restriction:foot:conditional')) and typed!=['restriction','foot']: return None
    if any(key+':conditional' in tags for key in keys) or any(key in tags for key in ('day_on','day_off','hour_on','hour_off')):
        raise UnsupportedRoutingRule('Conditional turn restriction needs an explicit time-aware policy')
    value = next((tags[k] for k in keys if k in tags),None)
    if value is None and any(k.startswith('restriction:') for k in tags): return None
    if value not in ('no_right_turn','no_left_turn','no_u_turn','no_straight_on','no_entry','no_exit',
                     'only_right_turn','only_left_turn','only_u_turn','only_straight_on'):
        raise UnsupportedRoutingRule('Unsupported turn restriction value')
    return value

"""Own bounded road graphs, spherical edge snapping and stateful A*/Dijkstra.

No network service, external GIS, traffic feed or navigation-law inference.
Persistence retains source notices; graph data do not acquire the code license.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from concurrent.futures import CancelledError
import hashlib
import heapq
import itertools
import json
import math
from pathlib import Path
import shutil
import tempfile
import threading
from types import MappingProxyType

from .geometry import Geometry, Feature, FeatureCollection, haversine
from .geocoding import GeocodingSource
from . import _geocode_geometry as geo
from ._pbf_decode import OSMRecord, OSMMember
from ._routing_osm import (RoutingProfile, RoutingError, RoutingLimitError,
                          UnsupportedRoutingRule, positive, budget, identifier,
                          kept_tags, allowed, directions, speed, node_open,
                          restriction_value, xml_records)


class RoutingSource(GeocodingSource):
    """Explicit dataset provenance using the shared source/notice contract."""


@dataclass(frozen=True)
class RoadNode:
    id: int
    coordinate: tuple


@dataclass(frozen=True)
class RoadEdge:
    id: str
    way_id: int
    segment_index: int
    start: int
    end: int
    direction: int
    geometry: tuple
    distance_m: float
    speed_kmh: float
    tags: object

    @property
    def duration_s(self): return self.distance_m / (self.speed_kmh / 3.6)


@dataclass(frozen=True)
class NetworkSnap:
    """Nearest source segment or node; distance is off-network, in metres."""
    coordinate: tuple
    distance_m: float
    node: int | None
    segment: tuple | None
    fraction: float
    _network: object = field(repr=False,compare=False)


@dataclass(frozen=True)
class RouteStep:
    edge: RoadEdge
    start_fraction: float
    end_fraction: float
    geometry: tuple

    @property
    def distance_m(self): return self.edge.distance_m * (self.end_fraction-self.start_fraction)

    @property
    def duration_s(self): return self.edge.duration_s * (self.end_fraction-self.start_fraction)


@dataclass(frozen=True)
class RouteInstruction:
    maneuver: str
    coordinate: tuple
    way_id: int | None
    name: str
    distance_m: float
    duration_s: float


def _bearing(a,b):
    lon1,lat1,lon2,lat2 = map(math.radians,(*a,*b))
    return math.degrees(math.atan2(math.sin(lon2-lon1)*math.cos(lat2),
        math.cos(lat1)*math.sin(lat2)-math.sin(lat1)*math.cos(lat2)*math.cos(lon2-lon1)))


@dataclass(frozen=True)
class RoadRoute:
    steps: tuple
    stops: tuple
    source: RoutingSource
    profile: RoutingProfile
    objective: str
    algorithm: str
    expanded_states: int

    @property
    def distance_m(self): return sum(s.distance_m for s in self.steps)

    @property
    def duration_s(self): return sum(s.duration_s for s in self.steps)

    @property
    def geometry(self):
        points = [self.stops[0].coordinate]
        for step in self.steps: points.extend(step.geometry[1:])
        return Geometry('LineString',points) if len(points)>1 else Geometry('Point',points[0])

    @property
    def instructions(self):
        result = []
        previous = None
        for step in self.steps:
            name = step.edge.tags.get('name',step.edge.tags.get('ref',''))
            if previous is None: maneuver = 'depart'
            else:
                angle = (_bearing(*step.geometry)-_bearing(*previous.geometry)+180)%360-180
                maneuver = 'u_turn' if abs(angle)>150 else 'continue' if abs(angle)<30 else 'right' if angle>0 else 'left'
            if previous is not None and previous.edge.way_id==step.edge.way_id and maneuver=='continue':
                old = result.pop()
                result.append(RouteInstruction(old.maneuver,old.coordinate,old.way_id,old.name,
                                               old.distance_m+step.distance_m,old.duration_s+step.duration_s))
            else:
                result.append(RouteInstruction(maneuver,step.geometry[0],step.edge.way_id,name,step.distance_m,step.duration_s))
            previous = step
        result.append(RouteInstruction('arrive',self.stops[-1].coordinate,None,'',0.,0.))
        return tuple(result)

    def to_features(self):
        """Editable/pickable source-edge features, without query logs or input addresses."""
        common = dict(source_id=self.source.id,source_version=self.source.version,
                      source_sha256=self.source.sha256,license=self.source.license,
                      attribution=self.source.attribution,mode=self.profile.mode,estimated_duration=True)
        if not self.steps:
            return FeatureCollection((Feature(self.geometry,common,'route/stationary'),))
        return FeatureCollection(tuple(Feature(Geometry('LineString',s.geometry),
            dict(common,edge_id=s.edge.id,osm_way_id=s.edge.way_id,
                 name=s.edge.tags.get('name',''),distance_m=s.distance_m,duration_s=s.duration_s,
                 start_fraction=s.start_fraction,end_fraction=s.end_fraction),f'route/{i}')
            for i,s in enumerate(self.steps)))

    def sample(self, seconds):
        """Clamped estimated-time position; spherical interpolation, not a GPS fix."""
        seconds = positive(seconds,'seconds',zero=True)
        for step in self.steps:
            if seconds<=step.duration_s:
                return geo.at_fraction(step.geometry,seconds/step.duration_s)
            seconds -= step.duration_s
        return self.stops[-1].coordinate

    def playback(self, ax, *, frames=100, interval=100, autoplay=False, **marker_style):
        """Own FuncAnimation edits one marker on the viewer thread; hold the handle."""
        from .animation import FuncAnimation
        frames = budget(frames,'frames')
        if not 2<=frames<=10000: raise ValueError('Playback needs 2..10000 frames')
        point = self.sample(0)
        marker = ax.scatter([point[0]],[point[1]],**marker_style)
        times = tuple(self.duration_s*i/(frames-1) for i in range(frames))
        animation = FuncAnimation(ax.figure,lambda t:marker.set_offsets([self.sample(t)]),
                                  times,interval=interval,autoplay=autoplay)
        animation.route_marker = marker
        return animation


def _payload(record):
    return dict(kind=record.kind,id=record.id,tags=dict(record.tags),coordinates=record.coordinates,
                refs=record.refs,members=[(m.kind,m.id,m.role) for m in record.members])


def _json(data): return json.dumps(data,ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False).encode('ascii')


def _unique(pairs):
    result = {}
    for key,value in pairs:
        if key in result: raise RoutingError('Duplicate graph JSON key')
        result[key] = value
    return result


class RoadGraph:
    """Read-only profile-specific directed graph, bounded in memory.

    Only shared OSM node IDs connect roads. Bridges/tunnels/layers remain edge
    attributes; coincident coordinates and geometric crossings never add links.
    The graph is safe for concurrent searches; query state belongs to each call.
    """
    def __init__(self):
        raise TypeError('Use RoadGraph.from_records/from_osm/from_catalog/load')

    def __setattr__(self,name,value):
        if getattr(self,'_frozen',False): raise AttributeError('RoadGraph is immutable')
        object.__setattr__(self,name,value)

    @classmethod
    def from_records(cls, records, *, source, profile=None, max_records=250000,
                     max_edges=250000, max_bytes=64*1024*1024, max_rule_states=100000):
        if not isinstance(source,RoutingSource): raise TypeError('An explicit RoutingSource is required')
        profile = RoutingProfile() if profile is None else profile
        if not isinstance(profile,RoutingProfile): raise TypeError('profile requires RoutingProfile')
        for value,name in ((max_records,'max_records'),(max_edges,'max_edges'),(max_bytes,'max_bytes'),(max_rule_states,'max_rule_states')): budget(value,name)
        nodes = {}; ways = {}; relations = {}; seen = set(); consumed = 0
        for count,record in enumerate(records,1):
            if count>max_records: raise RoutingLimitError('Routing input record budget exceeded')
            if not isinstance(record,OSMRecord): raise TypeError('Routing imports OSMRecord primitives, not inferred feature topology')
            oid = identifier(record.id); key = (record.kind,oid)
            if record.kind not in ('node','way','relation') or key in seen: raise RoutingError('Duplicate/unknown OSM primitive')
            seen.add(key)
            if len(record.tags)>256 or len(record.refs)>100000 or len(record.members)>4096:
                raise RoutingLimitError('Routing primitive exceeds field/reference budget')
            if any(not isinstance(k,str) or not isinstance(v,str) or len(k)>4096 or len(v)>4096 for k,v in record.tags.items()):
                raise RoutingError('OSM tags require bounded strings')
            tags = kept_tags(record.tags)
            clean = OSMRecord(record.kind,oid,tags,record.coordinates,record.refs,record.members)
            consumed += len(_json(_payload(clean)))
            if consumed>max_bytes: raise RoutingLimitError('Routing decoded input byte budget exceeded')
            if record.kind=='node':
                nodes[oid] = OSMRecord('node',oid,tags,geo.coordinate(record.coordinates))
            elif record.kind=='way':
                if len(record.refs)<2: raise RoutingError('Way needs at least two node references')
                for ref in record.refs: identifier(ref)
                ways[oid] = clean
            elif tags.get('type','').split(':',1)[0]=='restriction':
                for m in record.members:
                    if not isinstance(m,OSMMember): raise RoutingError('Invalid restriction member')
                    identifier(m.id)
                relations[oid] = clean
        for way in ways.values():
            if any(ref not in nodes for ref in way.refs): raise RoutingError('Missing way node reference')
        self = object.__new__(cls)
        self.source,self.profile = source,profile
        edges = {}; adjacency = {}; by_way = {}; segments = {}; used = set()
        for way in sorted(ways.values(),key=lambda w:w.id):
            if way.tags.get('highway') not in profile.speeds_kmh: continue
            if way.tags.get('area')=='yes': raise UnsupportedRoutingRule('Highway areas require a centerline routing dataset')
            if not allowed(way.tags,profile): continue
            if way.tags.get('no_u_turn')=='yes' or way.tags.get('u_turn')=='no':
                raise UnsupportedRoutingRule('Way-wide U-turn policy requires explicit turn relations')
            for direction in directions(way.tags,profile):
                velocity = speed(way.tags,profile,direction)
                for i,(a,b) in enumerate(zip(way.refs,way.refs[1:])):
                    if not node_open(nodes[a].tags,profile) or not node_open(nodes[b].tags,profile): continue
                    start,end = (a,b) if direction==1 else (b,a)
                    points = (nodes[start].coordinates,nodes[end].coordinates)
                    length = haversine(*points)
                    if length<=1e-8 or length>=math.pi*6371008.8-1:
                        raise RoutingError('Zero-length/antipodal road edge is ambiguous')
                    eid = f'{way.id}:{i}:{direction}'
                    edge = RoadEdge(eid,way.id,i,start,end,direction,points,length,velocity,way.tags)
                    edges[eid] = edge; adjacency.setdefault(start,[]).append(eid)
                    by_way.setdefault(way.id,[]).append(eid); segments.setdefault((way.id,i),[]).append(eid)
                    used.update((start,end))
                    if len(edges)>max_edges: raise RoutingLimitError('Routing directed edge budget exceeded')
        if not edges: raise RoutingError('No traversable roads for the selected profile')
        self.nodes = MappingProxyType({oid:RoadNode(oid,nodes[oid].coordinates) for oid in sorted(used)})
        self.edges = MappingProxyType(edges)
        self._adj = MappingProxyType({n:tuple(ids) for n,ids in adjacency.items()})
        self._segments = MappingProxyType({s:tuple(ids) for s,ids in segments.items()})
        self._network = object()
        self._no,self._only,self._history_size = self._restrictions(relations,ways,nodes,by_way,max_rule_states)
        # Persist only routing objects, filtered tags, and applicable relations.
        self._records = tuple(nodes[n] for n in sorted(nodes))+tuple(ways[w] for w in sorted(ways))+tuple(relations[r] for r in sorted(relations))
        self._postings = {}
        for segment,ids in self._segments.items():
            edge = edges[ids[0]]
            for cell in geo.postings(Geometry('LineString',edge.geometry)):
                self._postings.setdefault(cell,[]).append(segment)
        self._postings = MappingProxyType({k:tuple(v) for k,v in self._postings.items()})
        self.max_speed_mps = max(e.speed_kmh for e in edges.values())/3.6
        self._frozen = True
        return self

    @classmethod
    def from_osm(cls, data, *, source, **options):
        """Read bounded OSM XML and verify the exact consumed bytes."""
        from ._readers import binary
        raw = data.encode('utf8') if isinstance(data,str) and data.lstrip().startswith('<') else binary(data,64*1024*1024)
        if hashlib.sha256(raw).hexdigest()!=source.sha256: raise RoutingError('OSM bytes differ from declared routing source')
        return cls.from_records(xml_records(raw),source=source,**options)

    @classmethod
    def from_osm_index(cls, index, *, source, **options):
        """Import own verified PBF disk references, bounded by graph budgets."""
        index._open()
        if index.sha256!=source.sha256: raise RoutingError('PBF hash differs from declared routing source')
        if index.statistics['missing_ways'] or index.statistics['missing_relations']: raise RoutingError('PBF has missing references')
        def records():
            for oid,x,y,tags in index._rows('SELECT id,x,y,tags FROM nodes ORDER BY id'):
                yield OSMRecord('node',oid,json.loads(tags),(x,y))
            for oid,refs,tags in index._rows('SELECT id,refs,tags FROM ways ORDER BY id'):
                yield OSMRecord('way',oid,json.loads(tags),refs=tuple(json.loads(refs)))
            yield from index.relations(restrictions_only=True)
        return cls.from_records(records(),source=source,**options)

    @classmethod
    def from_catalog(cls, catalog, name, *, version=None, **options):
        entry = catalog._entry(name,version)
        if entry['crs']!='EPSG:4326' or entry['format'] not in ('osm','osm-pbf'): raise RoutingError('Routing catalog requires WGS84 OSM primitives')
        catalog.verify(name,version=entry['version'])
        from ._readers import binary
        notice = binary(catalog._resolve(entry['license_file']),262144)
        if hashlib.sha256(notice).hexdigest()!=entry['files'][entry['license_file']]: raise RoutingError('License hash mismatch')
        source = RoutingSource(entry['id'],entry['version'],entry['license'],entry['copyright'],
            entry['attribution'],entry['source'],entry['files'][entry['file']],(notice.decode('utf8'),))
        if entry['format']=='osm': return cls.from_osm(catalog._resolve(entry['file']),source=source,**options)
        with catalog.open_pbf(name,version=entry['version']) as index:
            return cls.from_osm_index(index,source=source,**options)

    def _restrictions(self, relations, ways, nodes, by_way, limit):
        no = set(); only = {}; longest = 1; explored = 0; compiled = 0
        for relation in relations.values():
            tags = relation.tags
            value = restriction_value(tags,self.profile)
            if value is None: continue
            groups = {'from':[],'via':[],'to':[]}
            for member in relation.members:
                if member.role not in groups or member.kind not in ('node','way'): raise RoutingError('Unsupported restriction member role/type')
                if member.id not in (nodes if member.kind=='node' else ways): raise RoutingError('Missing restriction member reference')
                groups[member.role].append(member)
            if not all(groups.values()) or any(m.kind!='way' for role in ('from','to') for m in groups[role]):
                raise RoutingError('Restriction needs from/to ways and via node/ways')
            if len(groups['from'])!=1 or len(groups['to'])!=1:
                if value not in ('no_entry','no_exit'): raise UnsupportedRoutingRule('Multiple from/to only supported for no_entry/no_exit')
            vias = groups['via']
            if len({m.kind for m in vias})!=1 or (vias[0].kind=='node' and len(vias)!=1): raise RoutingError('Invalid via chain')
            from_ids = [m.id for m in groups['from']]; to_ids = {m.id for m in groups['to']}
            # Relations touching an excluded road are irrelevant to this profile.
            if not any(w in by_way for w in from_ids): continue
            if not any(w in by_way for w in to_ids):
                if value.startswith('only_'): raise UnsupportedRoutingRule('Mandatory turn leads to an inaccessible road')
                continue
            patterns = []
            if vias[0].kind=='node':
                via = vias[0].id
                for wid in from_ids:
                    for eid in by_way.get(wid,()):
                        a = self.edges[eid]
                        if a.end!=via: continue
                        for next_id in self._adj.get(via,()):
                            explored += 1
                            if explored>limit: raise RoutingLimitError('Turn-rule expansion budget exceeded')
                            b = self.edges[next_id]
                            if b.way_id not in to_ids: continue
                            if a.way_id==b.way_id:
                                uturn = b.end==a.start
                                if ('u_turn' in value)!=uturn: continue
                            patterns.append((eid,next_id))
            else:
                chain = tuple(m.id for m in vias)
                if any(w not in by_way for w in chain):
                    if value.startswith('only_'): raise UnsupportedRoutingRule('Mandatory turn has an inaccessible via way')
                    continue
                for wid in from_ids:
                    for eid in by_way.get(wid,()):
                        stack = [(self.edges[eid].end,0,(eid,))]
                        while stack:
                            node,stage,path = stack.pop(); explored += 1
                            if explored>limit: raise RoutingLimitError('Turn-rule expansion budget exceeded')
                            if len(path)>256: raise RoutingLimitError('Turn-rule path exceeds 256 edges')
                            for next_id in self._adj.get(node,()):
                                if next_id in path: continue
                                edge = self.edges[next_id]
                                if len(path)>1 and edge.way_id in to_ids and stage==len(chain)-1:
                                    patterns.append(path+(next_id,))
                                if edge.way_id==chain[stage]: stack.append((edge.end,stage,path+(next_id,)))
                                elif stage+1<len(chain) and edge.way_id==chain[stage+1] and len(path)>1:
                                    stack.append((edge.end,stage+1,path+(next_id,)))
            if not patterns: raise RoutingError('Restriction has no traversable connected path; incomplete topology')
            for pattern in patterns:
                compiled += len(pattern)
                if compiled>limit: raise RoutingLimitError('Compiled turn-rule budget exceeded')
                longest = max(longest,len(pattern))
                if value.startswith('no_'): no.add(pattern)
                else:
                    for length in range(1,len(pattern)):
                        only.setdefault((relation.id,pattern[:length]),set()).add(pattern[length])
        return frozenset(no),MappingProxyType({k:frozenset(v) for k,v in only.items()}),longest-1

    def _turn(self, history, eid):
        if history and history[-1]==eid: return history
        for pattern in self._no:
            if eid==pattern[-1] and history[-len(pattern)+1:]==pattern[:-1]: return None
        for (_relation,prefix),allowed_next in self._only.items():
            if len(history)>=len(prefix) and history[-len(prefix):]==prefix and eid not in allowed_next: return None
        return (history+(eid,))[-self._history_size:] if self._history_size else ()

    def snap(self, location, *, radius_m=1000, max_candidates=10000):
        """Nearest physical edge; ties at disconnected coincident roads are errors."""
        if isinstance(location,NetworkSnap):
            if location._network is not self._network: raise RoutingError('Snap belongs to another graph')
            return location
        if isinstance(location,int) and not isinstance(location,bool):
            if location not in self.nodes: raise RoutingError('Node is absent or inaccessible for this profile')
            return NetworkSnap(self.nodes[location].coordinate,0.,location,None,0.,self._network)
        point = geo.coordinate(getattr(location,'coordinate',location))
        radius = positive(radius_m,'snap radius in metres',zero=True); budget(max_candidates,'max_candidates')
        segments = set(); visited_cells = 0
        for box in geo.cap_boxes(point,radius):
            for level in range(13):
                x0,y0,x1,y1 = geo.cells(box,level)
                cells = (x1-x0+1)*(y1-y0+1)
                visited_cells += cells
                if visited_cells>100000: raise RoutingLimitError('Snap spatial-cell budget exceeded; use a smaller radius')
                for x in range(x0,x1+1):
                    for y in range(y0,y1+1): segments.update(self._postings.get((level,x,y),()))
                if len(segments)>max_candidates: raise RoutingLimitError('Snap candidate budget exceeded')
        matches = []
        for segment in sorted(segments):
            edge = self.edges[self._segments[segment][0]]
            points = edge.geometry if edge.direction==1 else edge.geometry[::-1]
            found,distance,_ = geo.nearest(Geometry('LineString',points),point)
            if distance>radius+1e-7: continue
            fraction = max(0.,min(1.,haversine(points[0],found)/edge.distance_m))
            start,end = (edge.start,edge.end) if edge.direction==1 else (edge.end,edge.start)
            node = start if fraction<1e-9 else end if fraction>1-1e-9 else None
            if node is not None: found = self.nodes[node].coordinate
            matches.append(NetworkSnap(found,distance,node,None if node is not None else segment,
                                       0. if node is not None else fraction,self._network))
        if not matches: raise RoutingError('No accessible network within snap radius')
        matches.sort(key=lambda s:(s.distance_m,s.node is None,str(s.node),str(s.segment)))
        best = matches[0]
        for other in matches[1:]:
            if other.distance_m-best.distance_m>1e-6: break
            if (other.node,other.segment)!=(best.node,best.segment): raise RoutingError('Ambiguous snap at coincident/disconnected roads; select a node or explicit snap')
        return best

    def route(self, origin, destination, *, via=(), objective='distance', algorithm='astar',
              snap_radius_m=1000, max_states=250000, max_candidates=10000, cancel=None):
        """Globally optimal path through ordered stops, retaining turn history.

        A* uses a spherical lower bound and maximum actual edge speed. Dijkstra
        uses zero heuristic. Budgets/cancellation raise, never return partial paths.
        """
        if objective not in ('distance','time') or algorithm not in ('astar','dijkstra'): raise ValueError('Unknown route objective/algorithm')
        budget(max_states,'max_states')
        if not isinstance(via,(tuple,list)) or len(via)>64: raise ValueError('via requires at most 64 ordered stops')
        if cancel is not None and not isinstance(cancel,threading.Event): raise TypeError('cancel requires threading.Event')
        if cancel is not None and cancel.is_set(): raise CancelledError('Routing cancelled')
        stops = tuple(self.snap(p,radius_m=snap_radius_m,max_candidates=max_candidates) for p in (origin,*via,destination))
        # Split all stops into directed partial arcs without adding cross-road links.
        coordinates = {n:p.coordinate for n,p in self.nodes.items()}
        extra = {}; stop_nodes = []; splits = {}
        for snap in stops:
            if snap.node is not None: stop_nodes.append(snap.node); continue
            key = (snap.segment,round(snap.fraction,12))
            if key not in extra:
                # Virtual nodes use strings, separate from positive/negative OSM IDs.
                node = 'snap/'+str(len(extra)); extra[key] = node; coordinates[node] = snap.coordinate
                splits.setdefault(snap.segment,[]).append((snap.fraction,node))
            stop_nodes.append(extra[key])
        split_adj = {}; replaced = set()
        for segment,points in splits.items():
            for eid in self._segments[segment]:
                edge = self.edges[eid]; replaced.add(eid)
                middle = sorted((f if edge.direction==1 else 1-f,n) for f,n in points)
                chain = [(0.,edge.start),*middle,(1.,edge.end)]
                for (a,start),(b,end) in zip(chain,chain[1:]):
                    if b<=a: continue
                    step = RouteStep(edge,a,b,(coordinates[start],coordinates[end]))
                    split_adj.setdefault(start,[]).append((end,step))
        targets = stop_nodes[1:]
        def advance(node,index):
            while index<len(targets) and node==targets[index]: index += 1
            return index
        def heuristic(node,index):
            if algorithm=='dijkstra' or index==len(targets): return 0.
            points = [coordinates[node]]+[coordinates[n] for n in targets[index:]]
            lower = sum(haversine(a,b) for a,b in zip(points,points[1:]))
            return lower if objective=='distance' else lower/self.max_speed_mps
        start = (stop_nodes[0],(),advance(stop_nodes[0],0))
        distances = {start:0.}; previous = {}; counter = itertools.count(); expanded = 0
        queue = [(heuristic(start[0],start[2]),0.,next(counter),start)]
        while queue:
            if cancel is not None and cancel.is_set(): raise CancelledError('Routing cancelled')
            _priority,cost,_seq,state = heapq.heappop(queue)
            if cost!=distances.get(state): continue
            node,history,index = state; expanded += 1
            if expanded>max_states: raise RoutingLimitError('Route expanded-state budget exceeded')
            if index==len(targets):
                steps = []
                while state!=start:
                    state,step = previous[state]; steps.append(step)
                steps.reverse()
                return RoadRoute(tuple(steps),stops,self.source,self.profile,objective,algorithm,expanded)
            arcs = list(split_adj.get(node,()))
            for eid in self._adj.get(node,()):
                if eid not in replaced:
                    edge = self.edges[eid]; arcs.append((edge.end,RouteStep(edge,0.,1.,edge.geometry)))
            for end,step in arcs:
                next_history = self._turn(history,step.edge.id)
                if next_history is None: continue
                next_state = (end,next_history,advance(end,index))
                new_cost = cost+(step.distance_m if objective=='distance' else step.duration_s)
                if new_cost<distances.get(next_state,math.inf):
                    if next_state not in distances and len(distances)>=max_states: raise RoutingLimitError('Route discovered-state budget exceeded')
                    distances[next_state] = new_cost; previous[next_state] = (state,step)
                    if len(queue)>=max_states: raise RoutingLimitError('Route queue budget exceeded')
                    heapq.heappush(queue,(new_cost+heuristic(end,next_state[2]),new_cost,next(counter),next_state))
        raise RoutingError('No feasible route through the ordered stops for this profile')

    def submit(self, executor, origin, destination, **options):
        """Caller-owned executor; no worker touches Artists or opens a viewer."""
        if 'cancel' in options: raise ValueError('submit owns its cancellation event')
        event = threading.Event()
        future = executor.submit(self.route,origin,destination,cancel=event,**options)
        return RoutingTask(future,event)

    def save(self, directory, *, max_bytes=128*1024*1024, reserve_free_bytes=64*1024*1024):
        """Atomic new-directory JSON index, SHA-256 manifest and original notices."""
        budget(max_bytes,'max_bytes'); positive(reserve_free_bytes,'reserve_free_bytes',zero=True)
        directory = Path(directory)
        if directory.exists(): raise FileExistsError('Graph directory already exists')
        directory.parent.mkdir(parents=True,exist_ok=True)
        if shutil.disk_usage(directory.parent).free<reserve_free_bytes+max_bytes: raise RoutingLimitError('Insufficient graph free-space reserve')
        data = _json(dict(schema=1,source=self.source.as_dict(),profile=self.profile.as_dict(),records=[_payload(r) for r in self._records]))
        manifest = _json(dict(schema=1,file='graph.json',sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
        if len(data)+len(manifest)>max_bytes: raise RoutingLimitError('Graph persistence byte budget exceeded')
        with tempfile.TemporaryDirectory(prefix='routing-',dir=directory.parent) as temporary:
            folder = Path(temporary)/'graph'; folder.mkdir()
            (folder/'graph.json').write_bytes(data); (folder/'manifest.json').write_bytes(manifest)
            if directory.exists(): raise FileExistsError('Graph directory appeared while writing')
            folder.rename(directory)
        return hashlib.sha256(data).hexdigest()

    @classmethod
    def load(cls, directory, *, max_bytes=128*1024*1024, **budgets):
        from ._readers import binary
        budget(max_bytes,'max_bytes'); directory = Path(directory)
        for name in ('manifest.json','graph.json'):
            if (directory/name).is_symlink(): raise RoutingError('Graph symlinks are unsupported')
        manifest = json.loads(binary(directory/'manifest.json',4096),object_pairs_hook=_unique)
        data = binary(directory/'graph.json',max_bytes)
        if manifest.get('schema')!=1 or manifest.get('file')!='graph.json' or manifest.get('bytes')!=len(data) or manifest.get('sha256')!=hashlib.sha256(data).hexdigest():
            raise RoutingError('Graph integrity/schema mismatch')
        payload = json.loads(data,object_pairs_hook=_unique)
        if payload.get('schema')!=1: raise RoutingError('Unknown routing schema')
        def records():
            for row in payload['records']:
                yield OSMRecord(row['kind'],row['id'],row['tags'],tuple(row['coordinates']),tuple(row['refs']),
                                tuple(OSMMember(*m) for m in row['members']))
        return cls.from_records(records(),source=RoutingSource(**payload['source']),
                                profile=RoutingProfile(**payload['profile']),**budgets)


class RoutingTask:
    """Cooperative bounded worker; consume/apply the result on the owner thread."""
    def __init__(self,future,event):
        self.future,self._event = future,event
        self._owner = threading.get_ident()

    def cancel(self):
        self._event.set(); return self.future.cancel()

    def done(self): return self.future.done()

    def result(self,timeout=None): return self.future.result(timeout)

    def draw(self,ax,**style):
        if threading.get_ident()!=self._owner: raise RuntimeError('Apply routing Artists on the requesting/viewer thread')
        if not self.done(): raise RuntimeError('Route is not ready; poll with a viewer timer')
        return ax.route(self.result(),**style)

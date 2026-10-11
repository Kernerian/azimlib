"""Explicit planar/spherical set operations and opt-in topology repair.

Implementations, graph construction and classifiers belong to Azimlib. Closed
regularized areas are preserved; planar intersections also retain isolated
line/point contacts. No CRS inference, automatic repair or external GIS engine.
"""
from dataclasses import dataclass

from .geometry import Geometry,Feature,FeatureCollection
from .topology import TopologyReport,ValidationIssue
from . import _overlay_planar as plane
from . import _overlay_sphere as sphere

TopologyError=plane.TopologyError
TopologyPrecisionError=plane.TopologyPrecisionError
TopologyGraph=plane.Graph
TopologyEdge=plane.Edge
SphericalRegion=sphere.SphericalRegion


def is_empty(geometry):
    if isinstance(geometry,SphericalRegion):return geometry.is_empty
    if not isinstance(geometry,Geometry):raise TypeError('Expected Geometry/SphericalRegion')
    return not geometry.geometries if geometry.type=='GeometryCollection' else not geometry.coordinates


@dataclass(frozen=True)
class OverlayResult:
    geometry: object
    topology: TopologyGraph
    operation: str
    domain: str

    @property
    def is_empty(self):return is_empty(self.geometry)

    def area(self,*,radius=None):
        if self.domain=='spherical':return self.geometry.area(**({} if radius is None else {'radius':radius}))
        if radius is not None:raise ValueError('Planar area is in squared coordinate units; radius is spherical only')
        def area(g):
            if g.type=='GeometryCollection':return sum(area(member) for member in g.geometries)
            if g.type not in ('Polygon','MultiPolygon'):return 0.
            shape=plane.prepare(g)
            return float(sum(abs(plane.signed_area(p[0]))-sum(abs(plane.signed_area(h)) for h in p[1:]) for p in shape.polygons))
        return area(self.geometry)

    def shared_boundaries(self,*,step=2.):
        """Input-coincident edges with source provenance, not polygon outlines."""
        edges=self.topology.shared_edges
        if self.domain=='planar':return Geometry('MultiLineString',tuple(tuple(tuple(map(float,self.topology.nodes[i])) for i in (e.start,e.end)) for e in edges))
        from math import ceil,degrees,sin
        step=plane.Q(step)
        if not .01<=step<=30:raise ValueError('step must be .01..30 degrees')
        lines=[]
        for e in edges:
            a,b=self.topology.nodes[e.start],self.topology.nodes[e.end];theta=sphere.angle(a,b);n=max(1,ceil(degrees(theta)/float(step)))
            lines.append(tuple(sphere.coordinate(sphere.unit(sphere.add(sphere.mul(a,sin((1-i/n)*theta)),sphere.mul(b,sin(i/n*theta))))) for i in range(n+1)))
        return Geometry('MultiLineString',tuple(lines))


def overlay(left,right,operation='intersection',*,domain='planar',max_segments=20000,max_pairs=2000000,max_edges=100000):
    """Return geometry and a shared noded graph with source-edge lineage.

    Planar input Geometry coordinates are used literally, without longitude
    wrapping. Spherical inputs MUST be SphericalRegion, with explicit interiors.
    Budgets abort before returning a partial geometry. Difference/symmetric
    difference use closed regularized area semantics: subtracting a line cannot
    punch a zero-width slit in an area. Sphere outputs are regularized regions;
    zero-area spherical contacts remain in the graph, not in the filled region.
    """
    budgets=dict(max_segments=max_segments,max_pairs=max_pairs,max_edges=max_edges)
    if domain=='planar':
        for geometry in (left,right):
            if not isinstance(geometry,Geometry):raise TypeError('Planar overlay requires Geometry')
            if sum(1 for _ in geometry.iter_positions())>2*max_segments+max_edges:raise TopologyError('Input position budget exceeded')
        result,graph=plane.compute(left,right,operation,**budgets)
    elif domain=='spherical':result,graph=sphere.compute(left,right,operation,**budgets)
    else:raise ValueError('domain must be planar or spherical')
    return OverlayResult(result,graph,operation,domain)


def intersection(left,right,**kwargs):return overlay(left,right,'intersection',**kwargs)
def union(left,right,**kwargs):return overlay(left,right,'union',**kwargs)
def difference(left,right,**kwargs):return overlay(left,right,'difference',**kwargs)
def symmetric_difference(left,right,**kwargs):return overlay(left,right,'symmetric_difference',**kwargs)


def overlay_features(left,right,operation='intersection',**kwargs):
    """Keep both property namespaces/IDs; never silently overwrite a field."""
    if not isinstance(left,Feature) or not isinstance(right,Feature) or left.geometry is None or right.geometry is None:raise TypeError('Expected two non-null Features')
    result=overlay(left.geometry,right.geometry,operation,**kwargs)
    if not isinstance(result.geometry,Geometry):raise TypeError('Spherical regions require explicit rendering/export; no implicit GeoJSON interior conversion')
    return Feature(result.geometry,{'left':{'id':left.id,'properties':left.properties},
                                    'right':{'id':right.id,'properties':right.properties},'operation':operation})


def validate_topology(geometry,*,domain='planar'):
    """Diagnose the new overlay contract without modifying any coordinates."""
    try:
        if domain=='planar':plane.prepare(geometry)
        elif domain=='spherical':
            if not isinstance(geometry,SphericalRegion):raise TypeError('Expected explicit SphericalRegion')
            # Output loops can meet at already noded vertices. Reconstructing
            # the arrangement checks arc budgets/precision without treating a
            # valid point contact between output components as a crossing.
            sphere.node((geometry,))
        else:raise ValueError('domain must be planar or spherical')
    except TopologyError as exc:return TopologyReport((ValidationIssue('precision' if isinstance(exc,TopologyPrecisionError) else 'invalid_topology',(),str(exc)),))
    return TopologyReport(())


@dataclass(frozen=True)
class RepairResult:
    geometry: Geometry
    changes: tuple
    before: TopologyReport
    after: TopologyReport


def repair_geometry(geometry,*,method='normalize',max_segments=20000,max_pairs=2000000,max_edges=100000):
    """Explicit planar deduplication/winding, optionally even-odd polygonization.

    normalize refuses crossings and misplaced/nested holes. even_odd rebuilds
    the shell's even-odd fill minus its holes; holes outside a shell contribute
    nothing. It can split a bow-tie into polygons and reports this semantic
    choice. No spherical/height repair is inferred.
    """
    if method not in ('normalize','even_odd'):raise ValueError('method must be normalize or even_odd')
    before=validate_topology(geometry);changes=[]
    if geometry.type not in ('Polygon','MultiPolygon','LineString','MultiLineString'):raise TopologyError('Repair supports planar polygonal/linear Geometry only')
    def dedup(coords):
        out=[]
        for p in coords:
            if not out or p!=out[-1]:out.append(p)
            else:changes.append('removed consecutive duplicate position')
        return tuple(out)
    c=geometry.coordinates
    if geometry.type in ('LineString','MultiLineString'):
        lines=(c,) if geometry.type=='LineString' else c
        cleaned=tuple(dedup(line) for line in lines)
        result=Geometry(geometry.type,cleaned[0] if geometry.type=='LineString' else cleaned)
    else:
        polys=(c,) if geometry.type=='Polygon' else c;cleaned=[]
        for polygon in polys:
            rings=[]
            for i,ring in enumerate(polygon):
                ring=dedup(ring)
                area=plane.signed_area(tuple(map(plane.point,ring)))
                if area and (area>0)!=(i==0):ring=ring[::-1];changes.append('normalized ring winding')
                rings.append(ring)
            cleaned.append(tuple(rings))
        result=Geometry(geometry.type,cleaned[0] if geometry.type=='Polygon' else tuple(cleaned))
        if method=='even_odd':
            result,_=plane.compute(result,Geometry('Polygon'),'union',_validate=False,max_segments=max_segments,max_pairs=max_pairs,max_edges=max_edges)
            changes.append('rebuilt shell even-odd fill minus holes; outside holes ignored; original partition may change')
    after=validate_topology(result)
    if not after.valid:raise TopologyError('; '.join(i.message for i in after.issues))
    return RepairResult(result,tuple(changes),before,after)


def clip_collection(collection,region,**kwargs):
    if not isinstance(collection,FeatureCollection):raise TypeError('Expected FeatureCollection')
    features=[]
    for feature in collection:
        if feature.geometry is None:continue
        result=intersection(feature.geometry,region,**kwargs)
        if not result.is_empty:features.append(Feature(result.geometry,feature.properties,feature.id))
    return FeatureCollection(tuple(features))


def select_collection(collection,region,**kwargs):
    if not isinstance(collection,FeatureCollection):raise TypeError('Expected FeatureCollection')
    return FeatureCollection(tuple(f for f in collection if f.geometry is not None and not intersection(f.geometry,region,**kwargs).is_empty))


def mask_raster(raster,region,*,domain='planar',invert=False):
    """Pixel-centre coverage in geographic lon/lat; preserve original NoData."""
    from .raster import GeoRaster
    from .crs import transform
    if not isinstance(raster,GeoRaster):raise TypeError('Expected GeoRaster')
    if not isinstance(invert,bool):raise TypeError('invert must be bool')
    if domain=='planar':
        shape=plane.prepare(region)
        if shape.lines or shape.points:raise TopologyError('Raster mask requires an area')
        covers=lambda x,y:shape.location(plane.point((x,y)))>=0
    elif domain=='spherical' and isinstance(region,SphericalRegion):covers=region.covers
    else:raise ValueError('Use planar Geometry or explicit spherical SphericalRegion')
    rows=[]
    for j,row in enumerate(raster.values):
        output=[]
        for i,value in enumerate(row):
            x,y=transform(*raster.coordinate(i,j,center=True),raster.crs,4326)
            keep=covers(x,y)^invert
            output.append(value if keep else None)
        rows.append(tuple(output))
    return GeoRaster(tuple(rows),raster.affine,raster.crs,color_mode=raster.color_mode,height_frame=raster.height_frame)


def draw_region(axes,region,*,fill_step=5.,boundary_step=2.,facecolor='#5b9db8',edgecolor='#223f4b',linewidth=.8,alpha=.6,max_cells=100000):
    """Render an explicitly sampled spherical fill and geodesic boundary.

    Boolean operations remain spherical. Fill is a geographic pixel-centre
    mask with visible accuracy controlled by fill_step, not an exact vector
    tessellation. Boundary interpolation is controlled by boundary_step. Both
    returned Artists retain normal visibility/style controls.
    """
    from math import ceil
    from .geometry import _number
    from .colors import ListedColormap
    if not isinstance(region,SphericalRegion):raise TypeError('Expected SphericalRegion')
    step=_number(fill_step)
    if not .1<=step<=30:raise ValueError('fill_step must be .1..30 degrees')
    if isinstance(max_cells,bool) or not isinstance(max_cells,int) or max_cells<1:raise ValueError('max_cells must be positive integer')
    ny,nx=ceil(180/step),ceil(360/step)
    if ny*nx>max_cells:raise TopologyError('Spherical fill cell budget exceeded')
    boundary=region.boundary(step=boundary_step)
    lon=tuple(-180+360*i/nx for i in range(nx+1));lat=tuple(-90+180*j/ny for j in range(ny+1))
    rows=tuple(tuple(1 if region.covers((lon[i]+lon[i+1])/2,(lat[j]+lat[j+1])/2) else None for i in range(nx)) for j in range(ny))
    mesh=axes.pcolormesh(lon,lat,rows,cmap=ListedColormap([facecolor]),vmin=0,vmax=1,alpha=alpha)
    outline=axes.geojson(boundary,fit=False,color=edgecolor,linewidth=linewidth,alpha=alpha)
    return mesh,outline

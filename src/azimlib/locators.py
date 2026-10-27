"""Owned geographic locator footprints and explicit acyclic viewport links."""
import math,weakref
from .artist import artist_mutation
from .layers import Layer
from .geometry import Geometry,wrap_longitude
from .styles import style_dict,path_style
from .bodies import UnsupportedBodyOperation

def _viewport(ax):
 from .render_map import axes_viewport
 vp=getattr(ax,'_active_viewport',None)
 if vp is not None and tuple(vp.extent)==tuple(ax._get_extent()) and vp.projection==ax.projection and vp.bearing==ax.get_bearing():return vp
 # A source not yet drawn still has a deterministic physical viewport.
 x,y,w,h=ax.position;fw,fh=(v*100 for v in ax.figure.figsize)
 return axes_viewport(ax,(x*fw,(1-y-h)*fh,w*fw,h*fh))[0]

def viewport_footprint(ax,*,samples=256):
 """Inverse-map the actual screen boundary; a globe uses its visible limb.

 Orthographic domains are convex ellipses, so radial bisection discovers the
 single complete limb/rectangle intersection. No multi-component claim.
 """
 if type(samples) is not int or not 32<=samples<=2048:raise ValueError('Footprint samples must be32..2048')
 vp=_viewport(ax);x,y,w,h=vp.box;cx,cy=x+w/2,y+h/2
 if vp.inverse(cx,cy) is None:raise UnsupportedBodyOperation('Locator requires a visible convex footprint seed')
 method=getattr(vp.projection,'method',vp.projection.name)
 if method in ('stereographic','azimuthal_equidistant') and abs(vp.projection.central_latitude)>=89.999 and vp.extent[2]-vp.extent[0]>=359.999:
  rings=[]
  for latitude in (vp.extent[1],vp.extent[3]):
   if abs(latitude)<90:rings.append(tuple((-180+360*i/samples,latitude) for i in range(samples+1)))
  if not rings:raise UnsupportedBodyOperation('Degenerate polar footprint')
  return Geometry('MultiLineString',tuple(rings))
 boundary=[]
 angles=sorted(set([i*math.tau/samples for i in range(samples)]+[math.atan2(dy,dx)%math.tau for dx,dy in ((w,h),(-w,h),(-w,-h),(w,-h))]))
 for t in angles:
  dx,dy=math.cos(t),math.sin(t)
  reach=min(w/(2*abs(dx)) if abs(dx)>1e-15 else math.inf,h/(2*abs(dy)) if abs(dy)>1e-15 else math.inf)
  p=(cx+reach*dx,cy+reach*dy);q=vp.inverse(*p)
  if q is None:
   if method!='orthographic':raise UnsupportedBodyOperation('Non-rectangular locator footprint is demonstrated only for orthographic convex horizons')
   lo,hi=0.,reach
   for _ in range(48):
    mid=(lo+hi)/2
    if vp.inverse(cx+mid*dx,cy+mid*dy) is None:hi=mid
    else:lo=mid
   p=(cx+lo*dx,cy+lo*dy);q=vp.inverse(*p)
  if q is None:raise ArithmeticError('Footprint inverse did not converge')
  boundary.append((wrap_longitude(q[0]),q[1]))
 boundary.append(boundary[0]);return Geometry('LineString',tuple(boundary))

class LocatorArtist(Layer):
 def __init__(self,target,source,*,sync=True,connectors=False,shade=False,mask_outside=False,samples=256,**style):
  if source is target or source.figure is None or source.figure is not target.figure:raise ValueError('Locator requires distinct live Axes in one Figure')
  if source.get_context()!=target.get_context():raise ValueError('Locator between different Bodies/frames requires an explicit transform; none is inferred')
  # Validate before attachment, including horizon support and sample limits.
  geometry=viewport_footprint(source,samples=samples)
  super().__init__('locator',geometry,style_dict(dict(color='#ad593b',linewidth=1.2,**style)),{})
  self._source=weakref.ref(source);self._body_context=target.get_context();self.sync=bool(sync);self.connectors=bool(connectors);self.shade=bool(shade);self.mask_outside=bool(mask_outside);self.samples=samples;self._fixed=geometry
  from .thematic import _attach
  _attach(target,self)
 def get_source(self):return self._source()
 def footprint(self):
  source=self._source()
  if source is None or source.figure is None:raise ValueError('Locator source was removed')
  return viewport_footprint(source,samples=self.samples) if self.sync else self._fixed
 def render(self,vp,scene):
  from .render_map import _geometry
  from .scene import Path
  start=len(scene.items);g=self.footprint();_geometry(g,dict(self.style),vp,scene)
  outlines=tuple(scene.items[start:]);points=g.coordinates if g.type=='LineString' else tuple(p for r in g.coordinates for p in r)
  longitude=[points[0][0]]
  for p in points[1:]:longitude.append(longitude[-1]+wrap_longitude(p[0]-longitude[-1]))
  if (self.shade or self.mask_outside) and g.type!='LineString':raise UnsupportedBodyOperation('Multi-component polar locator supports boundary only, not an ambiguous filled interior')
  if self.shade or self.mask_outside:
   if max(longitude)-min(longitude)>=180 or any(abs(p[1])>=89.999 for p in points):raise UnsupportedBodyOperation('Global/polar locator fill is ambiguous; boundary remains available without fill')
   if self.mask_outside:
    method=getattr(vp.projection,'method',vp.projection.name)
    if method not in ('equirectangular','mercator'):raise UnsupportedBodyOperation('Outside locator mask requires a demonstrated cylindrical target')
    temporary=type(scene)(scene.width,scene.height)
    _geometry(Geometry('Polygon',(points,)),{'facecolor':'black','edgecolor':'none'},vp,temporary)
    x,y,w,h=vp.box;rings=[[(x,y),(x+w,y),(x+w,y+h),(x,y+h)]]
    rings.extend(r for item in temporary.items if isinstance(item,Path) and item.closed for r in item.paths)
    scene.add(Path(rings,True,dict(fill=self.style.get('color','#ad593b'),opacity=.12),vp.box))
   else:_geometry(Geometry('Polygon',(points,)),dict(self.style,facecolor=self.style.get('color','#ad593b'),edgecolor='none',alpha=.12),vp,scene)
  if self.connectors:
   source_vp=_viewport(self.get_source());pairs=[]
   for p in (points[0],points[len(points)//2]):
    a,b=vp.project(*p),source_vp.project(*p)
    if a is not None and b is not None:pairs.append((a,b))
   for a,b in pairs:scene.add(Path([(a,b)],False,path_style(dict(self.style,alpha=.5)),None))
  scene._pick_records.append((self,0,start,len(scene.items)))

class ViewLink:
 """Explicit one/two-way same-context limit synchronization; never implicit."""
 def __init__(self,source,target,*,bidirectional=False):
  if source is target or source.figure is None or source.figure is not target.figure or source.get_context()!=target.get_context():raise ValueError('View links require distinct live same-context Axes in one Figure')
  links=getattr(source.figure,'_view_links',[]);edges=[]
  for link in links:
   if link.active:
    edges.append((link.source(),link.target()))
    if link.bidirectional:edges.append((link.target(),link.source()))
  def reachable(a,b):
   todo=[a];seen=set()
   while todo:
    n=todo.pop()
    if n is b:return True
    if id(n) in seen:continue
    seen.add(id(n));todo.extend(y for x,y in edges if x is n)
   return False
  if reachable(target,source) or bidirectional and reachable(source,target):raise ValueError('View synchronization cycle/duplicate path')
  self.source,self.target=weakref.ref(source),weakref.ref(target);self.bidirectional=bool(bidirectional);self.active=True;self._busy=False;self._connections=[]
  for a,b in ((source,target),(target,source)) if bidirectional else ((source,target),):
   for event in ('xlim_changed','ylim_changed'):
    ident=a.callbacks.connect(event,lambda *args,a=a,b=b:self._sync(a,b));self._connections.append((weakref.ref(a),ident))
  source.figure._view_links=[*links,self];self._sync(source,target)
 def _sync(self,source,target):
  if self._busy or not self.active:return
  if source.figure is None or target.figure is None:self.remove();return
  self._busy=True
  try:
   if source.get_extent()!=target.get_extent():target.set_extent(source.get_extent())
  finally:self._busy=False
 def remove(self):
  if not self.active:return
  self.active=False
  for owner,ident in self._connections:
   if owner() is not None:owner().callbacks.disconnect(ident)
  self._connections.clear()

def link_view(source,target,*,bidirectional=False):return ViewLink(source,target,bidirectional=bidirectional)

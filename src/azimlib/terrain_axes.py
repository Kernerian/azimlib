"""Experimental physical terrain facade; own meshes, camera and depth raster.

Opaque flat-shaded triangles only. Geographic terrain uses an explicit local
metric frame; no vertical datum transformation, GPU or external 3D backend.
"""
import math
from dataclasses import replace
from .axes import MapAxes
from .artist import Artist,artist_mutation
from .cm import ScalarMappable
from .terrain3d import Camera,Mesh,LocalFrame,finite,length_unit,cross,normalized,dot,transform_point
from .scene import Raster3D,Rect,Path,Text
from .styles import text_style
from .colors import to_rgba
from .components import TextArtist

class SurfaceArtist(ScalarMappable,Artist):
    kind='terrain3d'
    def __init__(self,mesh,*,norm=None,cmap='terrain',color=None,shade=True,light=(1,-1,2),elevation_reference='unspecified'):
        Artist.__init__(self);ScalarMappable.__init__(self,norm,cmap)
        self.mesh=mesh;self.visible=True;self._axes=None;self.style={};self.options={};self._zorder=1
        self.color=None if color is None else to_rgba(color)
        if self.color is not None and self.color[3] not in (0,1):raise ValueError('Experimental 3D faces must be opaque or hidden')
        self.shade=bool(shade);self.light=normalized(tuple(finite(v) for v in light))
        if len(self.light)!=3:raise ValueError('light needs three components')
        self.elevation_reference=str(elevation_reference)
        used={i for t in mesh.triangles for i in t}
        self.set_array([p[2] if i in used else None for i,p in enumerate(mesh.vertices)])
    def set_array(self,values):
        from .scientific import scalar
        values=[scalar(v) for v in values]
        if len(values)!=len(self.mesh.vertices):raise ValueError('Surface scalar array needs one value per mesh vertex')
        self._apply_mapping(self._prepare_mapping({},array=values))
    @property
    def axes(self):return self._axes
    def get_visible(self):return self.visible
    @artist_mutation
    def set_visible(self,value):self.visible=bool(value)
    @artist_mutation
    def set_shade(self,value):self.shade=bool(value)
    @artist_mutation
    def set_color(self,value):
        color=None if value is None else to_rgba(value)
        if color is not None and color[3] not in (0,1):raise ValueError('Experimental 3D faces must be opaque or hidden')
        self.color=color
    def get_zorder(self):return self._zorder
    def get_label(self):return ''
    def remove(self):
        if self.axes is not None:self.axes.layers.remove(self);self.axes._changed()
        self._axes=None;self._bind_parent(None)
    def faces(self,camera,bounds,aspect,exaggeration):
        matrix=camera.matrix(bounds,aspect,exaggeration)
        projected=tuple(transform_point(matrix,v) for v in self.mesh.vertices)
        result=[]
        for face in self.mesh.triangles:
            verts=[self.mesh.vertices[i] for i in face]
            values=[self._array[i] for i in face]
            if self.color is None and any(v is None for v in values):continue
            value=sum(v for v in values if v is not None)/3
            color=self.color if self.color is not None else to_rgba(self.to_color(value))
            if color[3] not in (0,1):raise ValueError('Experimental 3D colormaps must produce opaque or hidden faces')
            if not color[3]:continue
            strength=1.
            if self.shade:
                a,b,c=verts;n=cross(tuple(b[i]-a[i] for i in range(3)),tuple(c[i]-a[i] for i in range(3)))
                if not any(n):continue
                strength=.35+.65*max(0,dot(normalized(n),self.light))
            rgba=tuple(round(v*strength*255) for v in color[:3])+(255,)
            result.append((tuple(projected[i] for i in face),rgba))
        return result

def surface_mesh(X,Y,Z,horizontal_unit,vertical_unit):
    hu,vu=length_unit(horizontal_unit).to_si,length_unit(vertical_unit).to_si
    rows=tuple(tuple(row) for row in Z)
    if len(rows)<2 or len(rows[0])<2 or any(len(row)!=len(rows[0]) for row in rows):raise ValueError('Z must be a rectangular grid of at least 2 by 2')
    nr,nc=len(rows),len(rows[0])
    if nr*nc>50000 or 2*(nr-1)*(nc-1)>20000:raise ValueError('Terrain mesh budget exceeded; resample explicitly')
    def coordinates(data,name,axis):
        values=list(data)
        if values and isinstance(values[0],(int,float)) or values and getattr(values[0],'ndim',None)==0:
            if len(values)!=(nc if axis==0 else nr):raise ValueError(name+' length differs from Z')
            return [[finite(values[j if axis==0 else i])*hu for j in range(nc)] for i in range(nr)]
        values=tuple(tuple(row) for row in values)
        if len(values)!=nr or any(len(row)!=nc for row in values):raise ValueError(name+' shape differs from Z')
        return [[finite(v)*hu for v in row] for row in values]
    xx,yy=coordinates(X,'X',0),coordinates(Y,'Y',1)
    from .scientific import scalar
    heights=[[scalar(v) for v in row] for row in rows]
    vertices=tuple((xx[i][j],yy[i][j],0. if heights[i][j] is None else heights[i][j]*vu) for i in range(nr) for j in range(nc))
    faces=[]
    for i in range(nr-1):
        for j in range(nc-1):
            if any(heights[a][b] is None for a,b in ((i,j),(i+1,j),(i,j+1),(i+1,j+1))):continue
            a=i*nc+j;b=a+1;c=a+nc;d=c+1
            for t in ((a,b,d),(a,d,c)):
                p,q,r=(vertices[k] for k in t);area=(q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
                if abs(area)<1e-12:raise ValueError('Degenerate terrain cell')
                faces.append(t if area>0 else tuple(reversed(t)))
    return Mesh(vertices,tuple(faces))

def triangulate_ring(points):
    """Independent bounded ear clipping of a simple concave XY ring."""
    def segments_intersect(a,b,c,d):
        def side(p,q,r):return (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
        def on(p,q,r):return abs(side(p,q,r))<1e-12 and min(p[0],q[0])<=r[0]<=max(p[0],q[0]) and min(p[1],q[1])<=r[1]<=max(p[1],q[1])
        return side(a,b,c)*side(a,b,d)<0 and side(c,d,a)*side(c,d,b)<0 or any((on(a,b,c),on(a,b,d),on(c,d,a),on(c,d,b)))
    points=tuple(points[:-1] if points[0]==points[-1] else points)
    n=len(points)
    if not 3<=n<=256 or len(set(points))!=n:raise ValueError('Footprint needs 3..256 distinct vertices')
    for i in range(n):
        for j in range(i+1,n):
            if j in (i,(i+1)%n) or (j+1)%n==i:continue
            if segments_intersect(points[i],points[(i+1)%n],points[j],points[(j+1)%n]):raise ValueError('Footprint must be a simple ring')
    def orient(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    area=sum(points[i][0]*points[(i+1)%n][1]-points[(i+1)%n][0]*points[i][1] for i in range(n))
    if abs(area)<1e-12:raise ValueError('Degenerate footprint')
    indices=list(range(n)) if area>0 else list(reversed(range(n)));faces=[]
    while len(indices)>3:
        for k,b in enumerate(indices):
            a,c=indices[k-1],indices[(k+1)%len(indices)]
            if orient(points[a],points[b],points[c])<=1e-12:continue
            if any(all(orient(points[u],points[v],points[p])>=-1e-12 for u,v in ((a,b),(b,c),(c,a))) for p in indices if p not in (a,b,c)):continue
            faces.append((a,b,c));indices.pop(k);break
        else:raise ValueError('Unable to triangulate footprint')
    faces.append(tuple(indices));return points,tuple(faces)

class TerrainAxes(MapAxes):
    _terrain3d=True
    def __init__(self,figure,position,*,elev=35,azim=-60,roll=0,proj_type='persp',vertical_exaggeration=1):
        self._terrain_grid=False
        super().__init__(figure,position,'equirectangular')
        self.camera=Camera(elev=elev,azim=azim,roll=roll,projection=proj_type)
        self._world_limits={};self._zlabel=None;self.local_frame=None
        self.vertical_exaggeration=finite(vertical_exaggeration)
        if self.vertical_exaggeration<=0:raise ValueError('vertical_exaggeration must be positive')
    def get_projection(self):return '3d'
    def _attach(self,artist):
        if sum(len(a.mesh.triangles) for a in self.layers)+len(artist.mesh.triangles)>20000:raise ValueError('3D axes triangle budget exceeded')
        artist._axes=self;artist._bind_parent(self);self.layers.append(artist);self._changed();return artist
    def plot_surface(self,X,Y,Z,*,horizontal_unit='m',vertical_unit='m',cmap='terrain',norm=None,color=None,shade=True,light=(1,-1,2),elevation_reference='unspecified'):
        mesh=surface_mesh(X,Y,Z,horizontal_unit,vertical_unit)
        return self._attach(SurfaceArtist(mesh,norm=norm,cmap=cmap,color=color,shade=shade,light=light,elevation_reference=elevation_reference))
    def terrain(self,raster,*,origin,elevation_unit='m',elevation_reference='unspecified',**style):
        from .raster import GeoRaster
        from .crs import transform
        if not isinstance(raster,GeoRaster) or raster.color_mode!='scalar':raise TypeError('terrain requires a scalar GeoRaster')
        if raster.shape[0]*raster.shape[1]>50000 or 2*(raster.shape[0]-1)*(raster.shape[1]-1)>20000:raise ValueError('Terrain mesh budget exceeded; resample explicitly')
        frame=LocalFrame(*origin)
        if self.local_frame is not None and self.local_frame!=frame:raise ValueError('Use one local frame per 3D axes')
        X=[];Y=[]
        for row in range(raster.shape[0]):
            xx=[];yy=[]
            for col in range(raster.shape[1]):
                x,y=raster.coordinate(col,row,center=True)
                lon,lat=transform(x,y,raster.crs,'EPSG:4326');east,north=frame.horizontal(lon,lat)
                xx.append(east);yy.append(north)
            X.append(xx);Y.append(yy)
        artist=self.plot_surface(X,Y,raster.values,vertical_unit=elevation_unit,elevation_reference=elevation_reference,**style)
        self.local_frame=frame
        return artist
    def buildings(self,data,*,height,base=0,coordinates='world',unit='m',color='#aab1b8',shade=True):
        from .io import read_geojson
        if coordinates not in ('world','geographic'):raise ValueError('coordinates must be world or geographic')
        if coordinates=='geographic' and self.local_frame is None:raise ValueError('Add terrain with an explicit origin first')
        if coordinates=='geographic':collection=read_geojson(data)
        else:
            from types import SimpleNamespace
            if not isinstance(data,dict) or data.get('type')!='FeatureCollection':raise TypeError('World footprints require a GeoJSON-like FeatureCollection mapping')
            collection=SimpleNamespace(features=tuple(SimpleNamespace(id=f.get('id'),properties=f.get('properties',{}),geometry=SimpleNamespace(type=f['geometry']['type'],coordinates=f['geometry']['coordinates'])) for f in data['features']))
        scale=length_unit(unit).to_si;vertices=[];faces=[]
        def value(spec,feature):return finite(spec(feature) if callable(spec) else feature.properties[spec] if isinstance(spec,str) else spec)*scale
        for feature in collection.features:
            g=feature.geometry
            if g.type!='Polygon' or len(g.coordinates)!=1:raise ValueError('Experimental extrusion accepts simple Polygon footprints without holes')
            h,b=value(height,feature),value(base,feature)
            if h<=0:raise ValueError('Building height must be positive')
            points=[]
            for p in g.coordinates[0]:
                if len(p)!=2:raise ValueError('Provide XY footprints and explicit height/base')
                points.append(self.local_frame.horizontal(*p) if coordinates=='geographic' else tuple(finite(v)*scale for v in p))
            points,cap=triangulate_ring(tuple(points));n=len(points);start=len(vertices)
            vertices.extend((x,y,z) for z in (b,b+h) for x,y in points)
            faces.extend(tuple(start+n+i for i in t) for t in cap)
            faces.extend(tuple(start+i for i in reversed(t)) for t in cap)
            # Follow the CCW roof winding for outward side normals.
            winding=range(n) if sum(points[i][0]*points[(i+1)%n][1]-points[(i+1)%n][0]*points[i][1] for i in range(n))>0 else reversed(range(n))
            winding=list(winding)
            for k,i in enumerate(winding):
                j=winding[(k+1)%n];a,c=start+i,start+j
                faces.extend(((a,c,c+n),(a,c+n,a+n)))
            if len(faces)>20000 or len(vertices)>50000:raise ValueError('Extrusion budget exceeded')
        artist=SurfaceArtist(Mesh(tuple(vertices),tuple(faces)),color=color,shade=shade)
        artist.feature_ids=tuple(f.id for f in collection.features)
        return self._attach(artist)
    @artist_mutation
    def set_camera(self,camera):
        if not isinstance(camera,Camera):raise TypeError('Require an Azimlib terrain3d.Camera')
        self.camera=camera
    def view_init(self,elev=None,azim=None,roll=None):
        self.set_camera(replace(self.camera,**{k:finite(v) for k,v in dict(elev=elev,azim=azim,roll=roll).items() if v is not None}))
    def set_proj_type(self,proj_type,*,fov=None):self.set_camera(replace(self.camera,projection=proj_type,**({} if fov is None else {'fov':fov})))
    @artist_mutation
    def set_vertical_exaggeration(self,value):
        value=finite(value)
        if value<=0:raise ValueError('vertical_exaggeration must be positive')
        self.vertical_exaggeration=value
    def get_world_bounds(self):
        bounds=[a.mesh.bounds for a in self.layers if a.get_visible()]
        result=[]
        for k,name in enumerate(('x','y','z')):
            lo=min((b[2*k] for b in bounds),default=0);hi=max((b[2*k+1] for b in bounds),default=1)
            if lo==hi:lo-=.5;hi+=.5
            result.extend(self._world_limits.get(name,(lo,hi)))
        return tuple(result)
    def _limit(self,name,a,b=None):
        a,b=a if b is None else (a,b);a,b=finite(a),finite(b)
        if a>=b:raise ValueError('Experimental world limits must be increasing')
        self._world_limits[name]=(a,b);self._changed();return (a,b)
    def set_xlim(self,left,right=None,**kwargs):
        if kwargs:raise TypeError('Experimental 3D limits accept only physical endpoints')
        return self._limit('x',left,right)
    def set_ylim(self,bottom,top=None,**kwargs):
        if kwargs:raise TypeError('Experimental 3D limits accept only physical endpoints')
        return self._limit('y',bottom,top)
    def set_zlim(self,bottom,top=None):return self._limit('z',bottom,top)
    def get_xlim(self):return self.get_world_bounds()[:2]
    def get_ylim(self):return self.get_world_bounds()[2:4]
    def get_zlim(self):return self.get_world_bounds()[4:6]
    @artist_mutation
    def set_xlabel(self,text,**style):
        artist=TextArtist(text,self,'_xlabel',**style);self._xlabel=artist;return artist
    @artist_mutation
    def set_ylabel(self,text,**style):
        artist=TextArtist(text,self,'_ylabel',**style);self._ylabel=artist;return artist
    @artist_mutation
    def set_zlabel(self,text,**style):
        artist=TextArtist(text,self,'_zlabel',**style);self._zlabel=artist;return artist
    @artist_mutation
    def grid(self,visible=None,**kwargs):
        if kwargs:raise TypeError('Experimental 3D grid accepts only visibility')
        self._terrain_grid=not self._terrain_grid if visible is None else bool(visible)
    def clear(self):
        super().clear();self.camera=Camera();self._world_limits={};self._zlabel=None;self.local_frame=None;self.vertical_exaggeration=1;self._terrain_grid=False
        return self
    def _add(self,*args,**kwargs):raise NotImplementedError('Use plot_surface/terrain/buildings on experimental 3D axes')
    def add_collection(self,*args,**kwargs):raise NotImplementedError('Use own 3D surface artists')
    def set_projection(self,*args,**kwargs):raise NotImplementedError('Use set_proj_type for the 3D camera')
    def set_extent(self,*args,**kwargs):raise NotImplementedError('Use physical XYZ limits on 3D axes')
    def north_arrow(self,*args,**kwargs):raise NotImplementedError('A 2D north indicator is not a 3D orientation transform')
    compass=north_arrow;compass_rose=north_arrow;scale_bar=north_arrow;overview=north_arrow;legend=north_arrow
    text=north_arrow;annotate=north_arrow;geojson=north_arrow;map=north_arrow;states=north_arrow;rivers=north_arrow;scatter=north_arrow;line=north_arrow;plot=north_arrow;imshow=north_arrow;contour=north_arrow;contourf=north_arrow;pcolormesh=north_arrow;inset_axes=north_arrow
    def get_children(self):return super().get_children()+([self._zlabel] if getattr(self,'_zlabel',None) is not None else [])

def render_terrain(ax,scene,box):
    from .render_map import _add_text as add_text
    def _add_text(scene,x,y,text,style):add_text(scene,x,y,text,text_style(style))
    start=len(scene.items);x,y,w,h=box;bounds=ax.get_world_bounds();aspect=w/h
    if ax._colorbar is not None:
        from .colorbar_render import colorbar_layout,render_colorbar
        box,barbox=colorbar_layout(ax._colorbar,box);x,y,w,h=box;aspect=w/h
        render_colorbar(ax._colorbar,barbox,scene)
    scene.add(Rect(*box,dict(fill=ax.facecolor)))
    matrix=ax.camera.matrix(bounds,aspect,ax.vertical_exaggeration)
    triangles=tuple(face for a in ax.layers if a.get_visible() for face in a.faces(ax.camera,bounds,aspect,ax.vertical_exaggeration))
    scene.add(Raster3D(*box,triangles,clip=box))
    if ax._frame:
        # Project a metric wire box. Screen decorations are not mesh occluders.
        corners=[(bounds[i],bounds[2+j],bounds[4+k]) for k in (0,1) for j in (0,1) for i in (0,1)]
        def screen(p):
            q=transform_point(matrix,p)
            return (x+(q[0]/q[3]+1)*w/2,y+(1-q[1]/q[3])*h/2) if q[3]>0 else None
        from .terrain3d import clip_triangle
        edges=[(i,i^(1<<k)) for i in range(8) for k in range(3) if not i&(1<<k)]
        paths=[]
        for a,b in edges:
            qa,qb=transform_point(matrix,corners[a]),transform_point(matrix,corners[b])
            # Homogeneous segment clipping (same six halfspaces as triangles).
            t0,t1=0.,1.
            for axis,sign in ((0,1),(0,-1),(1,1),(1,-1),(2,1),(2,-1)):
                fa,fb=qa[3]+sign*qa[axis],qb[3]+sign*qb[axis]
                if fa<0 and fb<0:t0,t1=1,0;break
                if fa<0:t0=max(t0,fa/(fa-fb))
                elif fb<0:t1=min(t1,fa/(fa-fb))
            if t0<=t1:
                part=[]
                for t in (t0,t1):
                    q=tuple(a+(b-a)*t for a,b in zip(qa,qb))
                    if q[3]>0:part.append((x+(q[0]/q[3]+1)*w/2,y+(1-q[1]/q[3])*h/2))
                if len(part)==2:paths.append(part)
        scene.add(Path(paths,style=dict(stroke='#999999',stroke_width=.6),clip=box))
        from .ticker import MaxNLocator
        from .label_layout import text_box
        label_boxes=[]
        center=screen(tuple((bounds[k]+bounds[k+1])/2 for k in (0,2,4)))
        for axis,name in enumerate(('x','y','z')):
            lo,hi=bounds[axis*2:axis*2+2]
            base=[bounds[0] if axis!=1 else bounds[1],bounds[2],bounds[4]]
            a=base[:];b=base[:];a[axis]=lo;b[axis]=hi;a,b=screen(a),screen(b)
            if not a or not b:continue
            dx,dy=b[0]-a[0],b[1]-a[1];size=math.hypot(dx,dy)
            if size<12:continue
            mid=((a[0]+b[0])/2,(a[1]+b[1])/2);nx,ny=-dy/size,dx/size
            if center and nx*(mid[0]-center[0])+ny*(mid[1]-center[1])<0:nx,ny=-nx,-ny
            tick_style=dict(fontsize=8,ha='center',va='center')
            for value in MaxNLocator(nbins=max(1,min(4,int(size/45)))).tick_values(lo,hi):
                if not lo<=value<=hi:continue
                point=base[:];point[axis]=value;q=screen(point)
                if not q or not x<=q[0]<=x+w or not y<=q[1]<=y+h:continue
                tx,ty=q[0]+nx*13,q[1]+ny*13;text=f'{value:.5g}'
                bounds_text=text_box(tx,ty,text,text_style(tick_style),padding=2)
                def overlaps(a,b):return a[0]<b[0]+b[2] and a[0]+a[2]>b[0] and a[1]<b[1]+b[3] and a[1]+a[3]>b[1]
                if not any(overlaps(bounds_text,old) for old in label_boxes):
                    _add_text(scene,tx,ty,text,tick_style);label_boxes.append(bounds_text)
                    scene.add(Path(((q,(q[0]+nx*3,q[1]+ny*3)),),style=dict(stroke='#555555',stroke_width=.6)))
                if ax._terrain_grid and axis<2:
                    end=point[:];end[1-axis]=bounds[(1-axis)*2+1];other=screen(end)
                    if other:scene.add(Path(((q,other),),style=dict(stroke='#dddddd',stroke_width=.5),clip=box))
            label=getattr(ax,('_xlabel','_ylabel','_zlabel')[axis])
            if label and label.get_visible():
                angle=math.degrees(math.atan2(dy,dx))
                if angle>90:angle-=180
                if angle<-90:angle+=180
                style=dict(label[1],ha='center',va='center');style.setdefault('rotation',-angle)
                _add_text(scene,mid[0]+nx*40,mid[1]+ny*40,label[0],style)
    for loc,slot in (('left','_left_title'),('center','_title'),('right','_right_title')):
        title=getattr(ax,slot)
        if title and title.get_visible():_add_text(scene,x+dict(left=0,center=.5,right=1)[loc]*w,y-ax._title_pads[loc]*100/72,title[0],dict(title[1],ha=dict(left='left',center='center',right='right')[loc],va='bottom'))
    scene.maps.append(dict(box=box,navigation_box=box,terrain3d=True,extent=(-1,1,-1,1),projected_bounds=(-1,-1,1,1),ox=x,oy=y,scale=1,bearing=0,projection=dict(name='equirectangular'),axes_path=ax._axes_path(),axes_index=ax.figure.axes.index(ax),inset=False,tick_indices=[],grid_indices=[],static_indices=[],frame_indices={},anchor_ranges=[],start=start,end=len(scene.items),ticks=False))
    scene._layout_groups.append(((ax,),start,len(scene.items),box))

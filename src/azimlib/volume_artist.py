"""Editable volumetric ScalarMappable on the existing physical 3D axes."""
from .artist import Artist,artist_mutation
from .cm import ScalarMappable
from .colors import Normalize,LogNorm,to_rgba
from .volume import VolumeField,_packed
from .volume_render import OpacityTransfer,VolumeLight,VolumeLayer,inverse_matrix,trace_ray
from .terrain3d import finite,normalized


class VolumeArtist(ScalarMappable,Artist):
    kind='volume3d'
    def __init__(self,field,*,norm=None,cmap='viridis',opacity=None,step=None,reference_length=None,density=1.,light=None):
        if norm is not None and type(norm) not in (Normalize,LogNorm):raise NotImplementedError('Volume norm must be Normalize or LogNorm')
        Artist.__init__(self);ScalarMappable.__init__(self,norm,cmap);self._axes=None;self.style={};self.options={};self._zorder=1;self.visible=True
        self.field=self._validate_field(field);self.opacity=OpacityTransfer() if opacity is None else opacity if isinstance(opacity,OpacityTransfer) else OpacityTransfer.constant(opacity)
        self.step=finite(min(field.spacing)*.75 if step is None else step);self.reference_length=finite(min(field.spacing) if reference_length is None else reference_length);self.density=finite(density);self.light=light
        ScalarMappable.set_array(self,field.summary['minimum']+field.summary['maximum']);self._validate_parameters()
    @property
    def axes(self):return self._axes
    @property
    def zorder(self):return self._zorder
    def get_zorder(self):return self._zorder
    def get_visible(self):return self.visible
    @artist_mutation
    def set_visible(self,value):self.visible=bool(value)
    def get_label(self):return ''
    @staticmethod
    def _validate_field(field):
        if not isinstance(field,VolumeField) or field.components!=1:raise ValueError('plot_volume requires a scalar VolumeField; extract a vector component explicitly')
        if field.values is None:
            if __import__('math').prod(field.shape)*4>field.budget.max_dense_bytes:raise ValueError('Select a bounded region of a streaming volume before rendering')
            field=field.select(field.bounds)
        return field
    def _validate_parameters(self):
        self.layer((1.,0,0,0,0,1.,0,0,0,0,1.,0,0,0,0,1.))
    @artist_mutation
    def set_data(self,field):
        field=self._validate_field(field)
        if self.axes is not None and field.frame!=self.axes.local_frame:raise ValueError('Temporal volume update cannot silently change axes spatial frame')
        mapping=self._prepare_mapping({},array=list(field.summary['minimum']+field.summary['maximum']))
        self.field=field;self._apply_mapping(mapping)
    def get_data(self):return self.field
    def get_array(self):return self.field
    def set_array(self,field):return self.set_data(field)
    def set_norm(self,norm):
        if norm is not None and type(norm) not in (Normalize,LogNorm):raise NotImplementedError('Volume norm must be Normalize or LogNorm')
        return ScalarMappable.set_norm(self,norm)
    @artist_mutation
    def set_opacity(self,value):self.opacity=value if isinstance(value,OpacityTransfer) else OpacityTransfer.constant(value)
    def get_opacity(self):return self.opacity
    @artist_mutation
    def set_step(self,value):
        value=finite(value)
        if value<=0:raise ValueError('Volume step requires positive metres')
        self.step=value
    @artist_mutation
    def set_reference_length(self,value):
        value=finite(value)
        if value<=0:raise ValueError('Opacity reference length requires positive metres')
        self.reference_length=value
    @artist_mutation
    def set_density(self,value):
        value=finite(value)
        if not 0<=value<=1e6:raise ValueError('Volume density must be in 0..1e6')
        self.density=value
    @artist_mutation
    def set_light(self,value):
        if value is not None and not isinstance(value,VolumeLight):raise TypeError('Require VolumeLight or None')
        self.light=value
    def layer(self,matrix):
        if type(self.norm) not in (Normalize,LogNorm):raise NotImplementedError('Volume transfer currently supports exact linear Normalize or LogNorm')
        self.autoscale_None();lo,hi=self.get_clim()
        if lo is None or hi is None:raise ValueError('Volume has no finite nodes; supply explicit norm limits')
        table=[]
        for i in range(256):
            rgba=to_rgba(self.cmap(i/255));table.extend((*rgba[:3],rgba[3]*self.opacity(i/255)))
        return VolumeLayer(self.field,inverse_matrix(matrix),_packed(table),(lo,hi),isinstance(self.norm,LogNorm),self.step,self.reference_length,self.density,self.light)
    def pick_ray(self,origin,direction,*,maximum=float('inf')):
        origin=tuple(finite(v) for v in origin);direction=normalized(tuple(finite(v) for v in direction))
        if len(origin)!=3 or len(direction)!=3:raise ValueError('Volume picking requires XYZ origin/direction')
        _,hit=trace_ray((self.layer((1.,0,0,0,0,1.,0,0,0,0,1.,0,0,0,0,1.)),),origin,direction,maximum,pick=True)
        return hit
    def remove(self):
        if self.axes is not None:self.axes.layers.remove(self);self.axes._changed()
        self._axes=None;self._bind_parent(None)


def slice_mesh(field,axis,position):
    from .terrain3d import Mesh
    if not isinstance(field,VolumeField) or field.components!=1:raise ValueError('Slices require a scalar VolumeField')
    if axis not in ('x','y','z'):raise ValueError('Slice axis must be x,y,z')
    k=('x','y','z').index(axis);position=finite(position)
    if not field.bounds[2*k]<=position<=field.bounds[2*k+1]:raise ValueError('Slice position outside field')
    other=[a for a in range(3) if a!=k];dims=field.shape[::-1];a,b=other;vertices=[];values=[];faces=[];sampler=field.sampler()
    if dims[a]*dims[b]>50000:raise ValueError('Slice mesh exceeds vertex budget; select/resample first')
    for j in range(dims[b]):
        for i in range(dims[a]):
            p=list(field.origin);p[k]=position;p[a]+=i*field.spacing[a];p[b]+=j*field.spacing[b];vertices.append(tuple(p));values.append(sampler.sample(p))
    for j in range(dims[b]-1):
        for i in range(dims[a]-1):
            n=j*dims[a]+i
            for face in ((n,n+1,n+1+dims[a]),(n,n+1+dims[a],n+dims[a])):
                if all(values[v] is not None for v in face):faces.append(face)
                if len(faces)>20000:raise ValueError('Slice triangle budget exceeded')
    if not faces:raise ValueError('Slice contains no finite cells')
    return Mesh(tuple(vertices),tuple(faces)),values


def isosurface_mesh(field,level):
    """Original marching tetrahedra, fixed shared cube diagonal; bounded output."""
    import math
    from .terrain3d import Mesh,cross,dot
    if not isinstance(field,VolumeField) or field.components!=1:raise ValueError('Isosurfaces require a scalar field')
    level=finite(level);nz,ny,nx=field.shape
    if (nx-1)*(ny-1)*(nz-1)>1_000_000:raise ValueError('Isosurface cell budget exceeded; select ROI')
    sampler=field.sampler();vertices=[];faces=[];corners=((0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1));tetra=((0,1,2,6),(0,2,3,6),(0,3,7,6),(0,7,4,6),(0,4,5,6),(0,5,1,6))
    for z in range(nz-1):
        for y in range(ny-1):
            for x in range(nx-1):
                points=[tuple(field.origin[k]+(base+offset)*field.spacing[k] for k,(base,offset) in enumerate(zip((x,y,z),c))) for c in corners]
                values=[sampler.node(x+dx,y+dy,z+dz)[0] for dx,dy,dz in corners]
                if not all(math.isfinite(v) for v in values):continue
                for t in tetra:
                    polygon=[]
                    for i,j in ((0,1),(0,2),(0,3),(1,2),(1,3),(2,3)):
                        a,b=t[i],t[j];va,vb=values[a],values[b]
                        if (va<level)==(vb<level):continue
                        f=(level-va)/(vb-va);p=tuple(a+f*(b-a) for a,b in zip(points[a],points[b]))
                        if p not in polygon:polygon.append(p)
                    if len(polygon)<3:continue
                    center=tuple(sum(p[k] for p in polygon)/len(polygon) for k in range(3));u=tuple(polygon[0][k]-center[k] for k in range(3));n=cross(tuple(polygon[1][k]-polygon[0][k] for k in range(3)),tuple(polygon[2][k]-polygon[0][k] for k in range(3)))
                    if dot(n,n)<1e-24:continue
                    high=[points[i] for i in t if values[i]>=level];low=[points[i] for i in t if values[i]<level]
                    toward=tuple(sum(p[k] for p in high)/len(high)-sum(p[k] for p in low)/len(low) for k in range(3))
                    if dot(n,toward)<0:n=tuple(-v for v in n)
                    v=cross(n,u);polygon.sort(key=lambda p:math.atan2(dot(tuple(p[k]-center[k] for k in range(3)),v)/math.sqrt(dot(v,v)),dot(tuple(p[k]-center[k] for k in range(3)),u)/math.sqrt(dot(u,u))))
                    for i in range(1,len(polygon)-1):
                        start=len(vertices);vertices.extend((polygon[0],polygon[i],polygon[i+1]));faces.append((start,start+1,start+2))
                        if len(vertices)>50000 or len(faces)>20000:raise ValueError('Isosurface mesh budget exceeded; select ROI or resample')
    if not faces:raise ValueError('Isosurface is empty at this level')
    return Mesh(tuple(vertices),tuple(faces))


class VolumeBinding:
    """Bounded prevalidated volume timeline, preserving camera and components."""
    def __init__(self,series,artist,*,scale='global',norm=None):
        from .temporal import normalizer
        if artist.axes is None or scale not in ('global','frame'):raise ValueError('Volume binding requires an attached Artist and global/frame scale')
        fields=tuple(artist._validate_field(frame.data) for frame in series)
        reference=artist.field
        if any((v.shape,v.origin,v.spacing,v.frame,v.value_unit)!=(reference.shape,reference.origin,reference.spacing,reference.frame,reference.value_unit) for v in fields):raise ValueError('Volume frames must preserve shape, metric frame, placement and value units')
        if sum(len(v.values) for v in fields)>128*1024**2:raise ValueError('Volume timeline exceeds 128 MiB dense payload budget')
        values=[v.summary['minimum']+v.summary['maximum'] for v in fields];template=artist.norm if norm is None else norm
        global_norm=normalizer(template,[a for row in values for a in row],rescale=norm is None)
        self.norms=tuple(normalizer(template,row,rescale=True) if scale=='frame' and any(a is not None for a in row) else global_norm for row in values)
        self.fields=fields;self.artist=artist;self.index=None
    def apply(self,index):
        if isinstance(index,bool) or not isinstance(index,int) or not 0<=index<len(self.fields):raise IndexError('Invalid volume frame index')
        if self.artist.axes is None:raise RuntimeError('Volume Artist was removed')
        current=self.artist.field;target=self.fields[index]
        if (current.shape,current.origin,current.spacing,current.frame,current.value_unit)!=(target.shape,target.origin,target.spacing,target.frame,target.value_unit):raise ValueError('Volume geometry/frame changed outside binding')
        with self.artist._batch_changes():self.artist.set_data(self.fields[index]);self.artist.set_norm(self.norms[index])
        self.index=index;return self.artist

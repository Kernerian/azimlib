"""Subfigure ownership and regional subplot composition on the root canvas."""
from .artist import Artist,artist_mutation
from .gridspec import GridSpec,_track_edges,_dimension,_ratios
from .transforms import Transform,_pair

class SubFigureTransform(Transform):
    def __init__(self,subfigure):self.subfigure=subfigure
    def owners(self):return (self.subfigure.figure,)
    def transform_point(self,p):
        x,y=_pair(p);l,b,w,h=self.subfigure.position
        return self.subfigure.figure.transFigure.transform_point((l+x*w,b+y*h))
    def _inverse(self,p):
        x,y=self.subfigure.figure.transFigure.inverted().transform_point(p);l,b,w,h=self.subfigure.position
        return (x-l)/w,(y-b)/h
    def inverted(self):
        from .transforms import _Inverse
        return _Inverse(self)

class SubFigure(Artist):
    """A region with its own axes/grids/text, sharing the root export and viewer.

    add_axes/text positions are local fractions. Returned GridSpecs use root
    figure fractions. Independent roots must have disjoint explicit regions.
    """
    def __init__(self,figure,position,parent=None):
        Artist.__init__(self,parent or figure)
        self.figure,self.position=figure,tuple(position)
        self._texts=[];self.subfigs=[];self.transSubfigure=SubFigureTransform(self)
    def get_size_inches(self):
        w,h=self.figure.figsize;return w*self.position[2],h*self.position[3]
    def get_dpi(self):return self.figure.dpi
    @property
    def axes(self):return [ax for ax in self.figure.axes if getattr(ax,'_subfigure',None) is self]
    @property
    def canvas(self):return self.figure.canvas
    def _attach(self,ax):ax._subfigure=self;ax._bind_parent(self);return ax
    def _rect(self,rect):
        l,b,w,h=self.position;x,y,dx,dy=map(float,rect)
        if min(x,y)<0 or min(dx,dy)<=0 or x+dx>1 or y+dy>1:raise ValueError('Subfigure axes must fit local region')
        return l+x*w,b+y*h,dx*w,dy*h
    def add_axes(self,rect=(.125,.11,.775,.77),**kwargs):return self._attach(self.figure.add_axes(self._rect(rect),**kwargs))
    def add_gridspec(self,nrows=1,ncols=1,**kwargs):
        l,b,w,h=self.position
        local={k:kwargs.pop(k,v) for k,v in (('left',.125),('right',.9),('bottom',.11),('top',.88))}
        if not 0<=local['left']<local['right']<=1 or not 0<=local['bottom']<local['top']<=1:raise ValueError('Invalid local grid region')
        grid=self.figure.add_gridspec(nrows,ncols,left=l+w*local['left'],right=l+w*local['right'],bottom=b+h*local['bottom'],top=b+h*local['top'],**kwargs)
        grid._layout_region=self.position;grid._subfigure=self
        return grid
    def add_subplot(self,*args,**kwargs):
        from .gridspec import SubplotSpec
        if len(args)==1 and isinstance(args[0],SubplotSpec):spec=args[0]
        else:
            if len(args)==1 and isinstance(args[0],int):nrows,ncols,index=map(int,str(args[0]))
            elif len(args)==3:nrows,ncols,index=args
            elif not args:nrows,ncols,index=1,1,1
            else:raise ValueError('Require subplot spec or grid index')
            spec=self.add_gridspec(nrows,ncols)[index-1]
        region=getattr(spec.get_topmost_subplotspec().get_gridspec(),'_subfigure',None)
        if region is not self:raise ValueError('SubplotSpec belongs to another subfigure')
        return self._attach(self.figure.add_subplot(spec,**kwargs))
    def subplots(self,nrows=1,ncols=1,*,gridspec_kw=None,width_ratios=None,height_ratios=None,**kwargs):
        options=dict(gridspec_kw or {})
        if width_ratios is not None:options['width_ratios']=width_ratios
        if height_ratios is not None:options['height_ratios']=height_ratios
        subplot_kw=kwargs.pop('subplot_kw',None)
        if subplot_kw:kwargs.update(subplot_kw)
        grid=self.add_gridspec(nrows,ncols,**options);before=set(map(id,self.figure.axes))
        result=grid.subplots(**kwargs)
        for ax in self.figure.axes:
            if id(ax) not in before:self._attach(ax)
        return result
    def text(self,x,y,text,**kwargs):
        x,y=_pair((x,y));l,b,w,h=self.position
        artist=SubFigureText(x,y,text,_owner=self.figure,**kwargs)
        artist._subfigure=self;artist._bind_parent(self)
        self.figure._texts.append((x,y,artist));self._texts.append(artist);self._changed();return artist
    def suptitle(self,text,**kwargs):return self.text(.5,.98,text,**dict({'ha':'center','va':'top','fontsize':12},**kwargs))
    def supxlabel(self,text,**kwargs):return self.text(.5,.02,text,**dict({'ha':'center','va':'bottom'},**kwargs))
    def supylabel(self,text,**kwargs):return self.text(.02,.5,text,**dict({'ha':'left','va':'center','rotation':90},**kwargs))
    def colorbar(self,mappable,*,ax=None,**kwargs):return self.figure.colorbar(mappable,ax=self.axes if ax is None else ax,**kwargs)
    def subfigures(self,*args,**kwargs):return subfigures(self,*args,**kwargs)
    def get_children(self):return [*self.axes,*self._texts,*self.subfigs]
    @artist_mutation
    def clear(self):
        for child in tuple(self.subfigs):child.clear()
        for ax in tuple(self.axes):ax.remove()
        for artist in tuple(self._texts):artist.remove()
        self._texts.clear();self.subfigs.clear()

from .figure_text import FigureTextArtist
class SubFigureText(FigureTextArtist):
    def _scene_text(self,width,height):
        from .styles import text_style
        x,y=self._position;l,b,w,h=self._subfigure.position
        style=text_style(self.style);style['rotation_mode']=self._rotation_mode
        return (l+x*w)*width,(1-b-y*h)*height,style

def subfigures(owner,nrows=1,ncols=1,*,squeeze=True,wspace=.02,hspace=.02,width_ratios=None,height_ratios=None):
    import math
    from .figure import AxesGrid
    nrows,ncols=_dimension(nrows),_dimension(ncols)
    if not all(math.isfinite(float(v)) and 0<=v<1 for v in (wspace,hspace)):raise ValueError('Subfigure gaps must lie in [0,1)')
    wr,hr=_ratios(width_ratios,ncols),_ratios(height_ratios,nrows)
    root=owner.figure if isinstance(owner,SubFigure) else owner
    l,b,w,h=owner.position if isinstance(owner,SubFigure) else (0,0,1,1)
    xs,xe=_track_edges(l,w,wr,wspace*w/ncols);ys,ye=_track_edges(0,h,hr,hspace*h/nrows)
    matrix=[]
    for r in range(nrows):
        row=[]
        for c in range(ncols):
            sf=SubFigure(root,(xs[c],b+h-ye[r],xe[c]-xs[c],ye[r]-ys[r]),owner)
            owner.subfigs.append(sf);row.append(sf)
        matrix.append(row)
    owner._changed()
    return matrix[0][0] if squeeze and nrows==ncols==1 else AxesGrid(matrix,squeeze=squeeze)

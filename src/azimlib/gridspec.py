"""Independent subplot allocation in figure fractions.

GridSpec describes cells; SubplotSpec describes a rectangular selection. No
rendering framework or numeric dependency participates in the calculations.
"""
from __future__ import annotations
import math
import operator

_DEFAULTS=dict(left=.125,bottom=.11,right=.9,top=.88,wspace=.2,hspace=.2)


class SubplotBox(tuple):
    """Immutable (left, bottom, width, height) with bounds/extent accessors."""
    def __new__(cls,left,bottom,width,height):return tuple.__new__(cls,(left,bottom,width,height))
    @property
    def bounds(self):return tuple(self)
    @property
    def extents(self):return self.x0,self.y0,self.x1,self.y1
    x0=property(lambda s:s[0]);y0=property(lambda s:s[1])
    width=property(lambda s:s[2]);height=property(lambda s:s[3])
    x1=property(lambda s:s[0]+s[2]);y1=property(lambda s:s[1]+s[3])


class _Parameters(dict):
    def __getattr__(self,key):
        try:return self[key]
        except KeyError:raise AttributeError(key) from None


def _dimension(value):
    try:value=operator.index(value)
    except TypeError:raise ValueError('Grid dimensions must be positive integers') from None
    if value<1:raise ValueError('Grid dimensions must be positive integers')
    return value


def _ratios(values,count):
    result=(1.0,)*count if values is None else tuple(float(v) for v in values)
    if len(result)!=count or not all(math.isfinite(v) and v>0 for v in result):
        raise ValueError('Ratios must contain one positive finite value per row/column')
    if not math.isfinite(sum(result)):raise ValueError('Ratio sum must be finite')
    return result


def _validate_params(values):
    if not all(math.isfinite(v) for v in values.values()):raise ValueError('Subplot parameters must be finite')
    if not (0<=values['left']<values['right']<=1 and 0<=values['bottom']<values['top']<=1):
        raise ValueError('Require 0<=left<right<=1 and 0<=bottom<top<=1')
    if min(values['wspace'],values['hspace'])<0:raise ValueError('Subplot spaces must be non-negative')


def _track_edges(start,total,ratios,gap):
    """Increasing track bounds, distributing available area by relative weight."""
    area=total-gap*(len(ratios)-1)
    weight_sum=sum(ratios)
    if area<=0:raise ValueError('No space remains for subplot tracks')
    starts=[];ends=[];cursor=start
    for weight in ratios:
        starts.append(cursor);cursor+=area*(weight/weight_sum);ends.append(cursor);cursor+=gap
    ends[-1]=start+total
    return tuple(starts),tuple(ends)


class GridSpec:
    """Allocate nrows × ncols cells, with optional ratios, margins and gaps.

    Spacing is a fraction of average cell size. Indexing selects contiguous
    rectangles. A grid belongs to at most one Figure; unattached grids bind
    when their first axes is added.
    """
    def __init__(self,nrows,ncols,figure=None,*,left=None,bottom=None,right=None,top=None,
                 wspace=None,hspace=None,width_ratios=None,height_ratios=None):
        self.nrows=_dimension(nrows);self.ncols=_dimension(ncols)
        self.figure=figure
        self._width_ratios=_ratios(width_ratios,self.ncols)
        self._height_ratios=_ratios(height_ratios,self.nrows)
        values=dict(left=left,bottom=bottom,right=right,top=top,wspace=wspace,hspace=hspace)
        self._params={k:None if v is None else float(v) for k,v in values.items()}
        self.get_subplot_params(figure)

    def get_geometry(self):return self.nrows,self.ncols
    def get_width_ratios(self):return list(self._width_ratios)
    def get_height_ratios(self):return list(self._height_ratios)

    def set_width_ratios(self,width_ratios):
        self._width_ratios=_ratios(width_ratios,self.ncols)
        if self.figure is not None:self.figure._changed()

    def set_height_ratios(self,height_ratios):
        self._height_ratios=_ratios(height_ratios,self.nrows)
        if self.figure is not None:self.figure._changed()

    def get_subplot_params(self,figure=None):
        """Return a copied mapping (also supporting attribute access)."""
        figure=self.figure if figure is None else figure
        values=dict(_DEFAULTS if figure is None else figure.subplotpars)
        values.update((k,v) for k,v in self._params.items() if v is not None)
        _validate_params(values)
        return _Parameters(values)

    def locally_modified_subplot_params(self):return [k for k,v in self._params.items() if v is not None]

    def get_grid_positions(self,fig=None):
        """Return bottoms, tops, lefts, rights as immutable tuples."""
        p=self.get_subplot_params(fig)
        def tracks(a,b,ratios,space):
            count=len(ratios)
            average=(b-a)/(count+space*(count-1))
            return _track_edges(a,b-a,ratios,space*average)
        lefts,rights=tracks(p.left,p.right,self._width_ratios,p.wspace)
        distances,end_distances=tracks(0,p.top-p.bottom,self._height_ratios,p.hspace)
        tops=tuple(p.top-v for v in distances);bottoms=tuple(p.top-v for v in end_distances)
        return bottoms,tops,lefts,rights

    def update(self,**kwargs):
        """Edit explicit margins/gaps; None restores inheritance from the figure.

        As in Matplotlib, update() also applies changed ratios to existing
        manual subplot positions. Automatic engines use ratios on every draw.
        """
        if set(kwargs)-set(_DEFAULTS):raise TypeError('Unknown GridSpec subplot parameter')
        candidate=dict(self._params)
        candidate.update((k,None if v is None else float(v)) for k,v in kwargs.items())
        effective=dict(_DEFAULTS if self.figure is None else self.figure.subplotpars)
        effective.update((k,v) for k,v in candidate.items() if v is not None)
        _validate_params(effective)
        self._params=candidate
        if self.figure is not None:
            with self.figure._mutation():
                self.figure._reposition_subplots(self)
                self.figure._changed()

    def __getitem__(self,key):
        def interval(value,count):
            if isinstance(value,slice):
                if value.step not in (None,1):raise ValueError('Subplot selections require contiguous slices (step=1)')
                start,stop,_=value.indices(count)
                if stop<=start:raise IndexError('Subplot selection is empty')
                return start,stop
            try:index=operator.index(value)
            except TypeError:raise TypeError('Grid indices must be integers or slices') from None
            if index<0:index+=count
            if not 0<=index<count:raise IndexError('Grid index is out of range')
            return index,index+1
        if isinstance(key,tuple):
            if len(key)!=2:raise ValueError('Use gs[row, column]')
            r0,r1=interval(key[0],self.nrows);c0,c1=interval(key[1],self.ncols)
            return SubplotSpec(self,r0*self.ncols+c0,(r1-1)*self.ncols+c1-1)
        start,stop=interval(key,self.nrows*self.ncols)
        return SubplotSpec(self,start,stop-1)

    def subplots(self,*,projection='equirectangular',projection_kw=None,squeeze=True,subplot_kw=None,sharex=False,sharey=False):
        """Create one axes per cell in the owning Figure."""
        if self.figure is None:raise ValueError('GridSpec.subplots requires a figure')
        from .shared_axes import sharing_mode,configure_grid
        sharex,sharey=sharing_mode(sharex),sharing_mode(sharey)
        from .figure import AxesGrid
        options=dict(subplot_kw or {})
        projection=options.pop('projection',projection);projection_kw=options.pop('projection_kw',projection_kw)
        if options:raise TypeError('Unsupported subplot_kw: '+', '.join(options))
        with self.figure._mutation():
            matrix=[[self.figure.add_subplot(self[row,col],projection=projection,projection_kw=projection_kw)
                     for col in range(self.ncols)] for row in range(self.nrows)]
            configure_grid(matrix,sharex,sharey)
        if squeeze and self.nrows==self.ncols==1:return matrix[0][0]
        return AxesGrid(matrix,squeeze=squeeze)


class SubplotSpec:
    """A rectangular cell selection in a GridSpec (zero-based endpoints)."""
    def __init__(self,gridspec,num1,num2=None):
        if not isinstance(gridspec,GridSpec):raise TypeError('SubplotSpec requires a GridSpec')
        num1=operator.index(num1);num2=num1 if num2 is None else operator.index(num2)
        if not 0<=num1<=num2<gridspec.nrows*gridspec.ncols:raise ValueError('Invalid subplot cell endpoints')
        self._gridspec=gridspec;self.num1=num1;self.num2=num2
    def get_gridspec(self):return self._gridspec
    def get_topmost_subplotspec(self):
        spec=self
        while isinstance(spec.get_gridspec(),GridSpecFromSubplotSpec):spec=spec.get_gridspec()._subplot_spec
        return spec
    def subgridspec(self,nrows,ncols,**kwargs):
        """Subdivide this rectangular selection using independent child tracks."""
        return GridSpecFromSubplotSpec(nrows,ncols,self,**kwargs)
    def get_geometry(self):return (*self._gridspec.get_geometry(),self.num1,self.num2)
    @property
    def rowspan(self):return range(self.num1//self._gridspec.ncols,self.num2//self._gridspec.ncols+1)
    @property
    def colspan(self):
        cols=(self.num1%self._gridspec.ncols,self.num2%self._gridspec.ncols)
        return range(min(cols),max(cols)+1)
    def is_first_row(self):return self.rowspan.start==0
    def is_last_row(self):return self.rowspan.stop==self._gridspec.nrows
    def is_first_col(self):return self.colspan.start==0
    def is_last_col(self):return self.colspan.stop==self._gridspec.ncols
    def get_position(self,figure=None):
        bottoms,tops,lefts,rights=self._gridspec.get_grid_positions(figure)
        r,c=self.rowspan,self.colspan
        return SubplotBox(lefts[c.start],bottoms[r.stop-1],rights[c.stop-1]-lefts[c.start],tops[r.start]-bottoms[r.stop-1])
    def __eq__(self,other):
        return isinstance(other,SubplotSpec) and self._gridspec is other._gridspec and (self.num1,self.num2)==(other.num1,other.num2)
    def __hash__(self):return hash((self._gridspec,self.num1,self.num2))


class GridSpecFromSubplotSpec(GridSpec):
    """A grid whose margins are the nominal bounds of a parent SubplotSpec."""
    def __init__(self,nrows,ncols,subplot_spec,*,wspace=None,hspace=None,width_ratios=None,height_ratios=None):
        if not isinstance(subplot_spec,SubplotSpec):raise TypeError('subplot_spec must be a SubplotSpec')
        self._subplot_spec=subplot_spec
        super().__init__(nrows,ncols,figure=subplot_spec.get_gridspec().figure,
                         wspace=wspace,hspace=hspace,width_ratios=width_ratios,height_ratios=height_ratios)

    def get_subplot_params(self,figure=None):
        figure=self.figure if figure is None else figure
        box=self._subplot_spec.get_position(figure)
        values=dict(_DEFAULTS if figure is None else figure.subplotpars)
        values.update(left=box.x0,bottom=box.y0,right=box.x1,top=box.y1)
        values.update((k,self._params[k]) for k in ('wspace','hspace') if self._params[k] is not None)
        _validate_params(values)
        return _Parameters(values)

    def get_topmost_subplotspec(self):return self._subplot_spec.get_topmost_subplotspec()

    def update(self,**kwargs):
        """Own convenience: edit child gaps; margins always follow the parent."""
        if set(kwargs)-{'wspace','hspace'}:raise TypeError('Child grid margins are controlled by its parent')
        return super().update(**kwargs)


def grid_ancestors(grid):
    """Leaf-to-root grids; own hierarchy cannot be rebound across figures."""
    chain=[grid]
    while isinstance(grid,GridSpecFromSubplotSpec):
        grid=grid._subplot_spec.get_gridspec();chain.append(grid)
    return tuple(chain)

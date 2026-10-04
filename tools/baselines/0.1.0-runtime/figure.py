"""Figures, subplot layout and export, independent of plotting frameworks."""
from __future__ import annotations
import math
import os
from pathlib import Path
import tempfile
import webbrowser

from .axes import MapAxes
from .scene import Scene, Text
from .styles import style_dict, text_style, normalize_aliases
from .config import rcParams
from .components import TextArtist
from .figure_text import FigureTextArtist,label_fontsize
from .artist import Artist,artist_mutation
from .gridspec import GridSpec,SubplotSpec,GridSpecFromSubplotSpec,grid_ancestors,_validate_params


class Figure(Artist):
    _is_figure=True
    def __init__(self, figsize=None, dpi=None, facecolor=None,layout=None):
        Artist.__init__(self)
        self._composing=False
        figsize=rcParams['figure.figsize'] if figsize is None else figsize
        dpi=rcParams['figure.dpi'] if dpi is None else dpi
        facecolor=rcParams['figure.facecolor'] if facecolor is None else facecolor
        if len(figsize)!=2 or not all(math.isfinite(float(v)) and float(v)>0 for v in figsize):
            raise ValueError("figsize must be a pair of positive finite inch dimensions")
        if not math.isfinite(float(dpi)) or dpi<=0:
            raise ValueError("dpi must be finite and positive")
        self.figsize=tuple(float(v) for v in figsize)
        self.dpi=float(dpi)
        self.facecolor=facecolor
        self.axes=[]
        self._axes_stack=[]
        self.number=None
        self._label=''
        self._colorbars=[]
        self._texts=[]
        self._suptitle=None
        self._supxlabel=None
        self._supylabel=None
        self._closed=False
        self._grid_shape=None
        self._gridspecs=[]
        self._layout_engine=None
        self.subplotpars=dict(left=.125,bottom=.11,right=.9,top=.88,wspace=.2,hspace=.2)
        self.canvas=FigureCanvas(self)
        if layout is not None:self.set_layout_engine(layout)

    @artist_mutation
    def add_axes(self, rect=(.06,.07,.88,.86), *, projection="equirectangular", projection_kw=None,sharex=None,sharey=None):
        """Add axes at figure fractions (left,bottom,width,height)."""
        if len(rect)!=4 or not all(math.isfinite(float(v)) for v in rect):
            raise ValueError("rect must be four finite fractions")
        x,y,w,h=rect
        if min(x,y)<0 or min(w,h)<=0 or x+w>1 or y+h>1:
            raise ValueError("Axes must fit inside the figure")
        for other in (sharex,sharey):
            if other is not None and not isinstance(other,MapAxes):raise TypeError('Sharing requires a MapAxes')
            if other is not None and other._colorbar_artist is not None:raise ValueError('Cannot share a colorbar axis')
        ax=MapAxes(self,rect,projection,projection_kw)
        if sharex is not None:ax.sharex(sharex)
        if sharey is not None:ax.sharey(sharey)
        self.axes.append(ax)
        self.sca(ax)
        return ax

    def get_label(self):return self._label

    def get_size_inches(self):return tuple(self.figsize)
    def get_figwidth(self):return self.figsize[0]
    def get_figheight(self):return self.figsize[1]
    def get_dpi(self):return self.dpi

    def _forward_size(self):
        viewer=getattr(self,'_viewer',None)
        if viewer is not None and not viewer.closed:
            viewer.resize_figure(*(round(v*self.dpi) for v in self.figsize))

    @artist_mutation
    def set_size_inches(self,w,h=None,forward=True):
        """Set physical figure size; optionally resize an existing desktop canvas."""
        try:
            size=tuple(float(v) for v in (w if h is None else (w,h)))
        except (TypeError,ValueError) as exc:
            raise ValueError('figsize must be two finite positive inch dimensions') from exc
        if len(size)!=2 or not all(math.isfinite(v) and v>0 for v in size):
            raise ValueError('figsize must be two finite positive inch dimensions')
        self.figsize=size
        if forward:self._forward_size()

    def set_figwidth(self,val,forward=True):return self.set_size_inches(val,self.figsize[1],forward=forward)
    def set_figheight(self,val,forward=True):return self.set_size_inches(self.figsize[0],val,forward=forward)

    @artist_mutation
    def set_dpi(self,val):
        try:dpi=float(val)
        except (TypeError,ValueError) as exc:raise ValueError('dpi must be finite and positive') from exc
        if not math.isfinite(dpi) or dpi<=0:raise ValueError('dpi must be finite and positive')
        self.dpi=dpi
        self._forward_size()

    @artist_mutation
    def set_label(self,label):
        self._label='' if label is None else str(label)
        viewer=getattr(self,'_viewer',None)
        if viewer and not viewer.closed:viewer.window.title(self._window_title())

    def _window_title(self):
        number=self.number if self.number is not None else 1
        return f'Figure {number}'+(f': {self._label}' if self._label else '')

    def _forget_axes(self,ax):
        self._axes_stack[:]=[a for a in self._axes_stack if a is not ax]

    def sca(self,ax):
        """Select an existing axes without changing Figure.axes creation order."""
        if ax not in self.axes:raise ValueError('Axes is not in this figure')
        self._forget_axes(ax);self._axes_stack.append(ax)
        return ax

    def gca(self):
        self._axes_stack[:]=[a for a in self._axes_stack if a in self.axes]
        return self._axes_stack[-1] if self._axes_stack else self.add_subplot(111)

    def delaxes(self,ax):
        if ax not in self.axes:raise ValueError('Axes is not in this figure')
        ax.remove()

    @artist_mutation
    def clear(self):
        """Detach contents, retaining size, DPI, identity and layout engine."""
        bars=list(self._colorbars)+[a._colorbar for a in self.axes if a._colorbar is not None]
        for bar in bars:bar.remove()
        for ax in tuple(self.axes):ax.clear();ax.remove()
        for text in [*[a for _,_,a in self._texts],*self._figure_labels()]:
            text._owner=None;text._bind_parent(None)
        self._texts.clear();self._suptitle=None;self._supxlabel=None;self._supylabel=None
        self._axes_stack.clear();self._gridspecs.clear();self._grid_shape=None
        return self

    clf=clear

    @artist_mutation
    def add_gridspec(self,nrows=1,ncols=1,**kwargs):
        """Create a GridSpec owned by this figure, with ratios/margins/gaps."""
        grid=GridSpec(nrows,ncols,figure=self,**kwargs)
        self._gridspecs.append(grid)
        self._grid_shape=grid.get_geometry()
        return grid

    @artist_mutation
    def subplots(self,nrows=1,ncols=1,*,projection="equirectangular",projection_kw=None,squeeze=True,
                 subplot_kw=None,gridspec_kw=None,width_ratios=None,height_ratios=None,sharex=False,sharey=False):
        from .shared_axes import sharing_mode
        sharex,sharey=sharing_mode(sharex),sharing_mode(sharey)
        options=dict(subplot_kw or {})
        projection=options.pop("projection",projection)
        projection_kw=options.pop("projection_kw",projection_kw)
        if options:
            raise TypeError(f"Unsupported subplot_kw: {', '.join(options)}")
        grid_options=dict(gridspec_kw or {})
        for name,value in (('width_ratios',width_ratios),('height_ratios',height_ratios)):
            if value is not None:
                if name in grid_options:raise ValueError(name+' supplied both directly and in gridspec_kw')
                grid_options[name]=value
        grid=self.add_gridspec(nrows,ncols,**grid_options)
        return grid.subplots(projection=projection,projection_kw=projection_kw,squeeze=squeeze,sharex=sharex,sharey=sharey)

    @artist_mutation
    def subplot_mosaic(self,mosaic,*,projection='equirectangular',projection_kw=None,
                       empty_sentinel='.',subplot_kw=None,per_subplot_kw=None,
                       gridspec_kw=None,width_ratios=None,height_ratios=None,sharex=False,sharey=False):
        """Create named maps in a root/nested grid hierarchy; empty slots create no axes."""
        from .mosaic import prepare
        if not isinstance(sharex,bool) or not isinstance(sharey,bool):raise TypeError('Mosaic sharex/sharey must be bool')
        grid,specs,projections=prepare(mosaic,self,projection=projection,projection_kw=projection_kw,
            empty_sentinel=empty_sentinel,subplot_kw=subplot_kw,per_subplot_kw=per_subplot_kw,
            gridspec_kw=gridspec_kw,width_ratios=width_ratios,height_ratios=height_ratios)
        axes={}
        for key,spec in specs.items():
            ax=self.add_subplot(spec,projection=projections[key])
            ax.set_label(str(key));axes[key]=ax
        if axes:
            first=next(iter(axes.values()))
            for ax in axes.values():
                for name,enabled in (('x',sharex),('y',sharey)):
                    if enabled:
                        if ax is not first:getattr(ax,'share'+name)(first)
                        ax._label_outer_axis(name)
        return axes

    @artist_mutation
    def add_subplot(self,*args,projection="equirectangular",projection_kw=None,sharex=None,sharey=None):
        """Add a subplot using a SubplotSpec, 111 or (rows, columns, index).

        A one-based index pair spans the rectangle between its endpoint cells.
        """
        if len(args)==1 and isinstance(args[0],SubplotSpec):
            spec=args[0]
            grid=spec.get_gridspec()
            if any(g.figure is not None and g.figure is not self for g in grid_ancestors(grid)):raise ValueError('GridSpec belongs to another figure')
        elif len(args)==1 and isinstance(args[0],int) and 100<=args[0]<=999:
            nrows,ncols,index=map(int,str(args[0]))
        elif len(args)==3:
            nrows,ncols,index=args
        elif not args:
            nrows,ncols,index=1,1,1
        else:raise ValueError('Use add_subplot(spec), add_subplot(111) or add_subplot(rows,cols,index)')
        if not (len(args)==1 and isinstance(args[0],SubplotSpec)):
            if any(not isinstance(v,int) or v<1 for v in (nrows,ncols)):raise ValueError('Invalid subplot grid')
            endpoints=index if isinstance(index,tuple) else (index,index)
            if len(endpoints)!=2 or any(not isinstance(v,int) or not 1<=v<=nrows*ncols for v in endpoints) or endpoints[0]>endpoints[1]:
                raise ValueError('Invalid subplot index or span')
            grid=next((g for g in reversed(self._gridspecs) if not isinstance(g,GridSpecFromSubplotSpec) and g.get_geometry()==(nrows,ncols)),None)
            if grid is None:grid=GridSpec(nrows,ncols,figure=self)
            spec=SubplotSpec(grid,endpoints[0]-1,endpoints[1]-1)
        ax=self.add_axes(spec.get_position(self),projection=projection,projection_kw=projection_kw,sharex=sharex,sharey=sharey)
        for ancestor in reversed(grid_ancestors(grid)):
            ancestor.figure=self
            if ancestor not in self._gridspecs:self._gridspecs.append(ancestor)
        self._grid_shape=grid_ancestors(grid)[-1].get_geometry()
        ax._subplot_spec=spec
        return ax

    def _subplot_axes(self,*,for_layout=True):
        return [a for a in self.axes if getattr(a,'_subplot_spec',None) is not None
                and a._colorbar_artist is None
                and (not for_layout or a.get_visible() and a.get_in_layout())]

    def _reposition_subplots(self,grid=None):
        for ax in self._subplot_axes(for_layout=False):
            spec=ax.get_subplotspec()
            if grid is None or grid in grid_ancestors(spec.get_gridspec()):ax.position=spec.get_position(self).bounds

    @artist_mutation
    def subplots_adjust(self,*,left=None,bottom=None,right=None,top=None,wspace=None,hspace=None):
        """Adjust a regular grid using Matplotlib's fraction/gap vocabulary."""
        if self._layout_engine is not None and not self._layout_engine.adjust_compatible:
            import warnings
            warnings.warn("The active layout engine is incompatible with subplots_adjust; use set_layout_engine(None) first.",UserWarning,stacklevel=2)
            return self
        options=dict(left=left,bottom=bottom,right=right,top=top,wspace=wspace,hspace=hspace)
        values={k:self.subplotpars[k] if v is None else v for k,v in options.items()}
        left,bottom,right,top,wspace,hspace=(values[k] for k in options)
        vals=(left,bottom,right,top,wspace,hspace)
        if not all(math.isfinite(float(v)) for v in vals) or not (0<=left<right<=1 and 0<=bottom<top<=1) or min(wspace,hspace)<0:
            raise ValueError("Require 0<=left<right<=1, 0<=bottom<top<=1 and non-negative spaces")
        # GridSpec overrides take precedence over these figure-wide defaults.
        for grid in self._gridspecs:
            effective=dict(values)
            effective.update((k,v) for k,v in grid._params.items() if v is not None)
            _validate_params(effective)
        self.subplotpars.update(values)
        self._reposition_subplots()
        return self

    @artist_mutation
    def tight_layout(self,*,pad=1.08,w_pad=None,h_pad=None,rect=(0,0,1,1)):
        """Adjust once using measured decoration bounds; padding is font units."""
        from .layout_engine import TightLayoutEngine,PlaceHolderLayoutEngine,ConstrainedLayoutEngine
        engine=TightLayoutEngine(pad=pad,w_pad=w_pad,h_pad=h_pad,rect=rect)
        previous=self._layout_engine
        engine.execute(self)
        if isinstance(previous,ConstrainedLayoutEngine):
            import warnings
            warnings.warn('The figure layout has changed to tight',UserWarning,stacklevel=2)
        self._layout_engine=PlaceHolderLayoutEngine(adjust_compatible=True)
        return self

    @artist_mutation
    def set_layout_engine(self,layout=None,**kwargs):
        from .layout_engine import LayoutEngine,TightLayoutEngine,ConstrainedLayoutEngine,PlaceHolderLayoutEngine
        if isinstance(layout,LayoutEngine):
            if kwargs:raise TypeError('Configure the engine object before passing it')
            engine=layout
        elif layout is None or layout=='none':
            if kwargs:raise TypeError('No layout engine to configure')
            engine=PlaceHolderLayoutEngine(self._layout_engine.adjust_compatible) if layout=='none' and self._layout_engine is not None else None
        elif layout=='tight':engine=TightLayoutEngine(**kwargs)
        elif layout=='constrained':engine=ConstrainedLayoutEngine(**kwargs)
        else:raise ValueError('layout must be None, none, tight, constrained or a LayoutEngine')
        self._layout_engine=engine
        return self

    def get_layout_engine(self):return self._layout_engine

    @artist_mutation
    def text(self,x,y,text,**kwargs):
        if not all(math.isfinite(float(v)) for v in (x,y)):
            raise ValueError("Figure text coordinates must be finite")
        artist=FigureTextArtist(x,y,text,_owner=self,**kwargs)
        self._texts.append((float(x),float(y),artist))
        return artist

    @artist_mutation
    def suptitle(self,text,**kwargs):
        return self._global_text('_suptitle',text,(.5,.98),'center','top',0,'title','y',kwargs)

    @artist_mutation
    def supxlabel(self,text,**kwargs):
        """Add/reuse a shared longitude label at the bottom of the Figure."""
        return self._global_text('_supxlabel',text,(.5,.01),'center','bottom',0,'label','y',kwargs)

    @artist_mutation
    def supylabel(self,text,**kwargs):
        """Add/reuse a shared latitude label at the left of the Figure."""
        return self._global_text('_supylabel',text,(.02,.5),'left','center',90,'label','x',kwargs)

    def _figure_labels(self):
        return [a for a in (self._suptitle,self._supxlabel,self._supylabel) if a is not None]

    def get_suptitle(self):return self._suptitle.get_text() if self._suptitle is not None else ''
    def get_supxlabel(self):return self._supxlabel.get_text() if self._supxlabel is not None else ''
    def get_supylabel(self):return self._supylabel.get_text() if self._supylabel is not None else ''

    def _global_text(self,slot,text,position,ha,va,rotation,rc,automatic,kwargs):
        kwargs=dict(kwargs)
        autopos=kwargs.get(automatic) is None
        x=kwargs.pop('x',None);y=kwargs.pop('y',None)
        x=position[0] if x is None else x;y=position[1] if y is None else y
        # Normalize aliases before defaults, so an explicit size/alignment wins.
        kwargs=normalize_aliases(kwargs)
        defaults=dict(ha=ha,va=va,rotation=rotation,
                      fontsize=label_fontsize(rcParams['figure.'+rc+'size']),
                      fontweight=rcParams['figure.'+rc+'weight'])
        defaults.update(kwargs)
        artist=getattr(self,slot)
        if artist is None:
            artist=FigureTextArtist(x,y,text,_owner=self,_slot=slot,**defaults)
            artist._autopos=autopos;setattr(self,slot,artist)
        else:
            with artist._mutation():
                artist.set(text=text,position=(x,y),**defaults);artist._autopos=autopos
        return artist

    def to_scene(self,*,cull=False):
        """Compose a scene; optionally omit safely invisible geometry.

        Keep cull=False for consumers that transform the scene to other views,
        including the portable HTML viewer. Static exports and the desktop
        recomposition path can discard wholly invisible cylindrical geometry.
        """
        previous=self._composing;self._composing=True
        try:
            if self._layout_engine is not None:self._layout_engine.execute(self)
            scene=self._compose_scene(cull=cull)
            return scene.scaled(self.dpi/100) if self.dpi!=100 else scene
        finally:self._composing=previous

    def get_children(self):
        return [*self.axes,*self._colorbars,*[a for _,_,a in self._texts],*self._figure_labels()]

    def _draw_complete(self):
        for artist in self.findobj():artist.stale=False

    def _compose_scene(self,*,measure_layout=False,cull=False):
        from .render_map import render_axes, _add_text
        # Compose in logical 100-dpi pixels, then scale every primitive and
        # hit-testing coordinate together. Changing dpi preserves typography.
        width,height=(value*100 for value in self.figsize)
        scene=Scene(width,height,self.facecolor)
        from .colorbar_render import colorbar_layout,render_colorbar
        boxes={id(ax):(ax.position[0]*width,(1-ax.position[1]-ax.position[3])*height,ax.position[2]*width,ax.position[3]*height) for ax in self.axes}
        shared=[]
        for bar in self._colorbars:
            if not bar.get_visible():continue
            parents=[ax for ax in bar.parents if ax in self.axes and ax.get_visible()]
            if bar.cax is not None:
                if bar.cax.get_visible():shared.append((bar,boxes[id(bar.cax)]))
                continue
            if not parents:continue
            parentboxes=[boxes[id(ax)] for ax in parents]
            left=min(b[0] for b in parentboxes);top=min(b[1] for b in parentboxes)
            right=max(b[0]+b[2] for b in parentboxes);bottom=max(b[1]+b[3] for b in parentboxes)
            union=(left,top,right-left,bottom-top)
            available,barbox=colorbar_layout(bar,union)
            for ax,box in zip(parents,parentboxes):
                boxes[id(ax)]=(available[0]+(box[0]-left)*available[2]/union[2],
                               available[1]+(box[1]-top)*available[3]/union[3],
                               box[2]*available[2]/union[2],box[3]*available[3]/union[3])
            shared.append((bar,barbox))
        for ax in self.axes:
            if not ax.get_visible() or ax._colorbar_artist is not None:continue
            allocated=boxes[id(ax)]
            scene._layout_scales[ax]=(allocated[2]/(ax.position[2]*width),allocated[3]/(ax.position[3]*height))
            render_axes(ax,scene,boxes[id(ax)],measure_layout=measure_layout,cull=cull)
        for bar,box in shared:
            first=len(scene.items)
            with scene.layout_artist(bar):render_colorbar(bar,box,scene)
            scene._layout_bars.append((bar,first,len(scene.items)))
            if bar.cax is None:
                parentboxes=[(a.position[0]*width,(1-a.position[1]-a.position[3])*height,a.position[2]*width,a.position[3]*height) for a in bar.parents if a in self.axes]
                from .layout_engine import union_bounds
                scene._layout_groups.append((bar.parents,first,len(scene.items),union_bounds(parentboxes)))
        for slot in ('_suptitle','_supxlabel','_supylabel'):
            artist=getattr(self,slot)
            if artist is None or not artist.get_visible():continue
            first=len(scene.items)
            with scene.layout_artist(artist):
                x,y,style=artist._scene_text(width,height)
                _add_text(scene,x,y,artist.text,style)
            from .layout_engine import item_bounds
            setattr(scene,'_layout'+slot,item_bounds(scene,first))
        for x,y,artist in self._texts:
            if artist.get_visible():
                x,y,style=artist._scene_text(width,height)
                with scene.layout_artist(artist):_add_text(scene,x,y,artist.text,style)
        return scene

    def to_svg(self):
        from .renderers import render_svg
        return render_svg(self.to_scene())

    @artist_mutation
    def colorbar(self,mappable,*,ax=None,cax=None,**kwargs):
        from .colorbar import Colorbar
        if ax is None:
            owner=getattr(mappable,'_axes',None)
            ax=owner or next((a for a in reversed(self.axes) if a._colorbar_artist is None and a is not cax),None)
        targets=[ax] if isinstance(ax,MapAxes) else list(ax.flat) if hasattr(ax,'flat') else list(ax) if ax is not None else []
        if not targets or any(not isinstance(a,MapAxes) or a.figure is not self or a not in self.axes or a._colorbar_artist is not None for a in targets):raise ValueError('Colorbar requires axes belonging to this figure')
        if len({id(a) for a in targets})!=len(targets):raise ValueError('Duplicate colorbar parent axes')
        if cax is not None and (not isinstance(cax,MapAxes) or cax.figure is not self or cax not in self.axes or cax in targets or cax.layers or cax.insets or cax._colorbar_artist is not None or cax._colorbar):raise ValueError('cax must be a distinct empty axes in this figure')
        if len(targets)==1 and cax is None:return targets[0].colorbar(mappable,**kwargs)
        bar=Colorbar(targets[0],mappable,**kwargs);bar.parents=tuple(targets);bar.cax=cax;bar.slot=None
        if cax is not None:cax._colorbar_artist=bar;bar.ax=cax
        bar._bind_parent(self)
        self._colorbars.append(bar)
        return bar

    def to_html(self, title=None):
        from .viewer import render_html
        return render_html(self.to_scene(), title=self._window_title() if title is None else title)

    def _repr_svg_(self):
        """Automatic inline display in notebooks, without an IPython dependency."""
        return self.to_svg()

    def save(self,path,*,format=None,dpi=None):
        """Export static .svg or .png without UI; streams require format.

        dpi changes PNG output resolution without changing the figure layout.
        SVG retains editable text and vector geometry.
        """
        stream=hasattr(path,"write")
        fmt=(format or (Path(path).suffix[1:] if not stream else "")).lower()
        if fmt not in ("svg","png"):
            raise ValueError("savefig supports static svg/png only; use show(path=...) for an interactive viewer")
        if dpi is not None and (not math.isfinite(float(dpi)) or dpi<=0):
            raise ValueError("dpi must be finite and positive")
        # A smaller export DPI widens raster overscan relative to logical units;
        # retain the complete scene rather than guessing that safety margin.
        scene=self.to_scene(cull=dpi is None or dpi>=self.dpi)
        from .renderers import render_svg,render_png
        def write(target):
            if fmt=="svg":
                value=render_svg(scene)
                if hasattr(target,"write"):
                    target.write(value)
                else:
                    Path(target).write_text(value,encoding="utf-8")
            else:
                render_png(scene,target,scale=(dpi or self.dpi)/self.dpi)
        if stream:
            write(path)
            return path
        target=Path(path)
        target.parent.mkdir(parents=True,exist_ok=True)
        handle,tmp=tempfile.mkstemp(prefix=".azimlib-",suffix="."+fmt,dir=target.parent)
        os.close(handle)
        try:
            write(tmp)
            os.replace(tmp,target)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        return target

    savefig=save

    def show(self,*,backend="tk",block=False,open_browser=True,path=None):
        """Display a native figure, or explicitly request the browser viewer.

        Figure.show is non-blocking by default, matching the object-oriented
        desktop convention. pyplot.show() runs the native GUI event loop.
        """
        if backend not in ("tk","browser"):
            raise ValueError("Interactive backends: tk or browser")
        if path is not None and backend!="browser":
            raise ValueError("An HTML path requires show(backend='browser', path=...)")
        if backend=="tk":
            from .backends.tk import show
            return show(self,block=block)
        if path is None:
            folder=Path(tempfile.mkdtemp(prefix="azimlib-"))
            path=folder/"map.html"
        result=Path(path)
        if result.suffix.lower() not in (".html",".htm"):
            raise ValueError("show(path=...) requires an .html path; use savefig for static output")
        result.parent.mkdir(parents=True,exist_ok=True)
        content=self.to_html()
        handle,tmp=tempfile.mkstemp(prefix=".azimlib-",suffix=".html",dir=result.parent)
        os.close(handle)
        try:
            Path(tmp).write_text(content,encoding="utf-8")
            os.replace(tmp,result)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        if open_browser:
            webbrowser.open(result.resolve().as_uri())
        return result

    def close(self):
        from . import close
        close(self)

    def __enter__(self):
        return self

    def __exit__(self,*args):
        self.close()


class FigureCanvas:
    """Public draw/event facade available even before a GUI is opened."""
    def __init__(self,figure):
        self.figure=figure
        self._callbacks={}
        self._next_id=0

    def draw(self):
        if getattr(self,'_drawing',False):return None
        self._drawing=True
        try:
            scene=self.figure.to_scene()
            self.figure._draw_complete()
            from types import SimpleNamespace
            event=SimpleNamespace(name='draw_event',canvas=self,renderer=scene)
            for name,callback in tuple(self._callbacks.values()):
                if name=='draw_event':callback(event)
            return scene
        finally:self._drawing=False

    def draw_idle(self):
        viewer=getattr(self.figure,"_viewer",None)
        if viewer and not viewer.closed:return viewer.draw_idle()
        if getattr(self,'_idle_drawing',False):return None
        self._idle_drawing=True
        try:return self.draw()
        finally:self._idle_drawing=False

    def mpl_connect(self,event,callback):
        if not callable(callback):raise TypeError("callback must be callable")
        self._next_id+=1
        self._callbacks[self._next_id]=(event,callback)
        return self._next_id

    def mpl_disconnect(self,cid):self._callbacks.pop(cid,None)

    def flush_events(self):
        viewer=getattr(self.figure,"_viewer",None)
        if viewer and not viewer.closed:viewer.flush_events()

    def get_width_height(self):
        return tuple(round(v*self.figure.dpi) for v in self.figure.figsize)


class AxesGrid:
    """Lightweight subplot array: iteration, [row,col], shape and .flat."""
    def __init__(self,matrix,squeeze=True):
        self._matrix=tuple(tuple(row) for row in matrix)
        rows,cols=len(matrix),len(matrix[0])
        self._one_dimensional=squeeze and (rows==1 or cols==1)
        self.shape=(rows*cols,) if self._one_dimensional else (rows,cols)

    @property
    def flat(self):
        return tuple(ax for row in self._matrix for ax in row)

    def flatten(self):
        return self.flat

    def __len__(self):
        return self.shape[0]

    def __iter__(self):
        return iter(self.flat if self._one_dimensional else self._matrix)

    def __getitem__(self,index):
        if isinstance(index,tuple):
            if len(index)!=2:
                raise IndexError("Use [row,column]")
            return self._matrix[index[0]][index[1]]
        return (self.flat if self._one_dimensional else self._matrix)[index]

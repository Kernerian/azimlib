"""A map-aware Axes with familiar plotting vocabulary."""
from __future__ import annotations
import math
import re
import warnings
from collections.abc import Mapping
from numbers import Real

from . import datasets
from .io import read_geojson
from .geometry import Feature, FeatureCollection, Geometry, great_circle
from .layers import Layer
from .text_artists import MapText,Annotation,ANNOTATION_COORDS,coordinate_pair
from .collections import ScatterCollection
from .field_artists import MeshCollection,ScalarImage,VectorCollection,scalar_rows,image_extent,image_edges
from .projections import get_projection
from .styles import CATEGORY_COLORS, sample_color, style_dict, normalize_aliases
from .components import AxisComponents,TextArtist,Legend,MapComponent,ScaleBar,OrientationIndicator
from .config import rcParams
from .artist import Artist,artist_mutation


def _collection(kind, coordinates):
    return read_geojson({"type": kind, "coordinates": coordinates})


def _defaults(values, **defaults):
    """Merge plotting defaults with caller overrides, including style aliases."""
    return {**defaults, **normalize_aliases(values)}


class MapAxes(AxisComponents):
    """Longitude/latitude are always in degrees; coordinates are always lon first."""
    def __init__(self, figure, position, projection="equirectangular", projection_kw=None):
        Artist.__init__(self,figure)
        self.figure, self.position = figure, tuple(position)
        self._subplot_spec=None
        self._label=''
        self.projection = get_projection(projection, **(projection_kw or {}))
        self.layers = []
        self.insets = []
        self._extent = None
        self._bounds = None
        self._autoscale_on={'x':True,'y':True}
        self._margins={'x':rcParams['axes.xmargin'],'y':rcParams['axes.ymargin']}
        self._tight=False
        self._country = None
        self.facecolor = rcParams['axes.facecolor']
        self._title, self._subtitle = None, None
        self._left_title=self._right_title=None
        self._title_pads={loc:rcParams['axes.titlepad'] for loc in ('left','center','right')}
        self._xlabel, self._ylabel = None, None
        self._labelpad={name:rcParams['axes.labelpad'] for name in ('x','y')}
        self._overview = None
        self._plot_index = 0
        self._scatter_index=0
        self._prop_cycle=tuple(rcParams['axes.prop_cycle'])
        self._legend, self._scale_bar, self._north, self._colorbar = None, None, None, None
        self._compass=None
        self._frame = True
        self.visible=True
        self._grid_format=None
        self._grid_config=None
        self._grid_configs={'major':{},'minor':{}}
        self._axisbelow=rcParams['axes.axisbelow']
        self._colorbar_artist=None
        from .shared_axes import SharedGroup
        from .callbacks import CallbackRegistry
        self._shared_axes={name:SharedGroup(self) for name in ('x','y')}
        self._sharex=self._sharey=None
        self.callbacks=CallbackRegistry(('xlim_changed','ylim_changed'))
        self._init_components()
        if rcParams['axes.grid']:self.grid(True,which=rcParams['axes.grid.which'],axis=rcParams['axes.grid.axis'])

    def get_subplotspec(self):
        """Return the cell selection, or None for manually positioned axes."""
        return self._subplot_spec

    def get_gridspec(self):
        return self._subplot_spec.get_gridspec() if self._subplot_spec is not None else None

    def get_label(self):return self._label

    @artist_mutation
    def set_label(self,label):self._label='' if label is None else str(label)

    @artist_mutation
    def _add(self, kind, data, style=None, **options):
        style=style_dict(style)
        if kind in ('text','labels','annotation'):
            style={'fontfamily':rcParams['font.family'],'fontsize':rcParams['font.size'],'color':rcParams['text.color'],**style}
        cls=(ScatterCollection if kind=='scatter' else ScalarImage if kind=='mesh' and options.get('image') else
             MeshCollection if kind=='mesh' else VectorCollection if kind=='vectors' else
             MapText if kind=='text' else Annotation if kind=='annotation' else Layer)
        layer = cls(kind, data, style, options, _axes=self)
        self.layers.append(layer)
        return layer

    def _fit(self, collection):
        bounds = collection.bounds
        if bounds:
            current=self._get_extent()
            if self._bounds is None:
                self._bounds = bounds
            else:
                a, b = self._bounds, bounds
                self._bounds = min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])
            if self._extent is None and not self.get_autoscale_on():self._extent=current
            if (self._extent is not None or any(len(g.members)>1 for g in self._shared_axes.values())) and (self.get_autoscalex_on() or self.get_autoscaley_on()):self.autoscale_view()

    @artist_mutation
    def sharex(self,other):
        from .shared_axes import share
        share(self,other,'x')

    @artist_mutation
    def sharey(self,other):
        from .shared_axes import share
        share(self,other,'y')

    def get_shared_x_axes(self):
        from .shared_axes import SharedAxesView
        return SharedAxesView('x')

    def get_shared_y_axes(self):
        from .shared_axes import SharedAxesView
        return SharedAxesView('y')

    def _set_interval(self,name,low,high,*,emit=True,auto=False):
        low,high=float(low),float(high);bound=180 if name=='x' else 90
        if not math.isfinite(low+high) or not -bound<=low<high<=bound:
            raise ValueError('Geographic limits must be finite, increasing and within '+str(bound)+' degrees')
        members=[self,*[ax for ax in self._shared_axes[name].members if ax is not self]] if emit else [self]
        # Commit the whole group before notifying callbacks or requesting draws.
        for ax in members:
            w,s,e,n=ax._get_extent()
            ax._extent=(low,s,high,n) if name=='x' else (w,low,e,high)
            if auto is not None:ax._autoscale_on[name]=bool(auto)
        for ax in members:
            if emit:ax.callbacks.process(name+'lim_changed',ax)
            ax._changed()

    def geojson(self, data, *, style=None, fit=True, crs=None, **kwargs):
        """Read GeoJSON; style(feature) can override appearance per feature.

        Input must follow RFC 7946. To import projected coordinates, pass an
        explicit supported source CRS (currently EPSG:3857 or EPSG:4326).
        """
        if crs is not None:
            from .crs import transform_geojson
            data = transform_geojson(data, crs, "EPSG:4326")
        collection = data if isinstance(data, FeatureCollection) else read_geojson(data)
        if style is not None and not callable(style):
            raise TypeError("style must be a callable accepting a Feature")
        kwargs = style_dict(kwargs)
        if fit:
            self._fit(collection)
        return self._add("geometry", collection, kwargs, feature_style=style,fit=bool(fit))

    add_geometries = geojson

    def map(self, region="world", **kwargs):
        collection = read_geojson(datasets.country(region))
        layer = self.geojson(collection, **_defaults(kwargs, facecolor="#e9e7de", edgecolor="#768782", linewidth=.7, zorder=1))
        self._country = region if len(collection) == 1 else None
        if kwargs.get("fit", True) and collection.bounds:
            west, south, east, north = collection.bounds
            dx, dy = max((east-west)*.055, .1), max((north-south)*.055, .1)
            self.set_extent((max(-180,west-dx), min(180,east+dx), max(-89.5,south-dy), min(89.5,north+dy)))
        return layer

    def countries(self, **kwargs):
        return self.geojson(datasets.load("countries"),
                            **_defaults(kwargs, fit=False, facecolor="#e7e8e1", edgecolor="#a6b0aa", linewidth=.6, zorder=0))

    def states(self, country=None, **kwargs):
        fill=kwargs.get('fc',kwargs.get('facecolor','none'))
        default_order=2 if fill is None or str(fill).lower()=='none' else 1
        return self.geojson(datasets.load("states", country=country or self._country or "brazil"),
                            **_defaults(kwargs, facecolor="none", edgecolor="#778680", linewidth=.6, zorder=default_order))

    def state(self,name,**kwargs):
        """Draw and fit one Brazilian state by name, postal code or BR-XX."""
        collection=read_geojson(datasets.state(name))
        layer=self.geojson(collection,**_defaults(kwargs,facecolor='white',edgecolor='black',linewidth=.8))
        self._country='brazil'
        if kwargs.get('fit',True):
            w,s,e,n=collection.bounds
            dx,dy=max((e-w)*.08,.05),max((n-s)*.08,.05)
            self.set_extent((w-dx,e+dx,s-dy,n+dy))
        return layer

    def rivers(self, **kwargs):
        return self.geojson(datasets.load("rivers", country=self._country),
                            **_defaults(kwargs, fit=False, color="#4e9bb0", linewidth=.9, zorder=3))

    def lakes(self, **kwargs):
        return self.geojson(datasets.load("lakes", country=self._country),
                            **_defaults(kwargs, fit=False, facecolor="#b4d9e4", edgecolor="#7bb2c3", linewidth=.5, zorder=3))

    def coastlines(self, **kwargs):
        return self.geojson(datasets.load("coastlines", country=self._country),
                            **_defaults(kwargs, fit=False, color="#486c76", linewidth=.8, zorder=3))

    @artist_mutation
    def ocean(self, color="#e5f1f4"):
        self.facecolor = color
        return self

    set_facecolor = ocean
    def get_facecolor(self):return self.facecolor

    def borders(self, **kwargs):
        return self.countries(**_defaults(kwargs, facecolor="none"))

    def roads(self, data=None, **kwargs):
        if data is None:
            raise ValueError("Roads are not bundled. Supply road GeoJSON: ax.roads(data)")
        return self.geojson(data, **_defaults(kwargs, color="#cb9d6b", linewidth=1, zorder=4))

    def municipalities(self, data=None, **kwargs):
        if data is None:
            raise ValueError("Municipal boundaries are not bundled. Supply GeoJSON: ax.municipalities(data)")
        return self.geojson(data, **_defaults(kwargs, facecolor="none", edgecolor="#7a8589", linewidth=.4))

    def line(self, coordinates, **kwargs):
        return self.geojson(_collection("LineString", list(coordinates)), **_defaults(kwargs, zorder=2))

    @artist_mutation
    def set_prop_cycle(self,*args,**kwargs):
        """Set future line/scatter defaults; does not restyle existing Artists."""
        from .cycles import cycler
        cycle=rcParams['axes.prop_cycle'] if args==(None,) and not kwargs else cycler(*args,**kwargs)
        self._prop_cycle=tuple(cycle);self._plot_index=self._scatter_index=0

    @artist_mutation
    def plot(self,*args,data=None,**kwargs):
        """Plot one/many lon/lat series, columns and named data; return handles.

        Nx2 single input retains geographic coordinate-pair shorthand.
        Pass lon, lat_matrix for multiple columns. Numeric 1D single input uses
        row indices as longitude. Geographic finiteness/latitude rules apply.
        """
        from .plotting import groups,labels
        options=dict(kwargs)
        # Preserve the original geographic keyword spelling without allowing
        # keywords to disappear into a style dictionary.
        if 'lon' in options:
            if args:raise TypeError('Use positional data or lon/lat keywords')
            args=(options.pop('lon'),)
        if 'lat' in options:
            if len(args)!=1:raise TypeError('lat keyword requires one longitude input')
            lat=options.pop('lat')
            if lat is not None:args+=(lat,)
        if len(args)==3 and args[-1] is None:args=args[:2]
        if 'fmt' in options:
            fmt=options.pop('fmt')
            if len(args)>2:raise ValueError('fmt keyword supports one argument group')
            if fmt is not None:args+= (fmt,)
        label=options.pop('label',None);label_given=label is not None
        fit=bool(options.pop('fit',True));style_options=style_dict(options)
        if not args:return []
        prepared=[];index=self._plot_index;messages=[]
        for series,fmt,default_label in groups(args,data):
            parsed=_format_style(fmt)
            for key in ('color','marker','linestyle'):
                if key in parsed and parsed[key]!='None' and key in style_options:
                    messages.append(f'{key} is defined by fmt and keyword; keyword takes precedence')
            if parsed.get('linestyle')=='None' and parsed.get('marker') not in (None,'None') and 'linestyle' not in style_options:
                parsed['linewidth']=0
            base={**parsed,**style_options}
            for (x,y),name in zip(series,labels(label,len(series)) if label_given else [default_label]*len(series)):
                row=self._prop_cycle[index%len(self._prop_cycle)]
                style=dict(base)
                if any(style.get(key) is None for key in row):
                    for key,value in row.items():
                        if style.get(key) is None:style[key]=value
                    index=(index+1)%len(self._prop_cycle)
                # Explicit color does not advance a color-only cycle.
                if style.get('color') is None:style['color']='black'
                style.setdefault('linewidth',rcParams['lines.linewidth'])
                style.setdefault('markersize',rcParams['lines.markersize']);style.setdefault('marker','None')
                if 'linecap' not in style:style.setdefault('solid_capstyle','projecting');style.setdefault('dash_capstyle','butt')
                if 'linejoin' not in style:style.setdefault('solid_joinstyle','round');style.setdefault('dash_joinstyle','round')
                if name is not None:style['label']=str(name)
                style.setdefault('zorder',2);style=style_dict(style)
                coordinates=list(zip(x,y))
                collection=_collection('MultiPoint' if len(coordinates)==1 else 'LineString',coordinates)
                prepared.append((collection,style))
        # Validate all groups before attaching any handle or consuming the cycle.
        for message in messages:warnings.warn(message,UserWarning,stacklevel=2)
        result=[]
        for collection,style in prepared:
            if fit:self._fit(collection)
            result.append(self._add('geometry',collection,style,feature_style=None,fit=fit))
        self._plot_index=index
        return result

    def route(self, coordinates, *, geodesic=True, steps=64, **kwargs):
        coordinates = list(coordinates)
        if len(coordinates) < 2:
            raise ValueError("A route needs at least two coordinates")
        if geodesic:
            result = []
            for a, b in zip(coordinates, coordinates[1:]):
                segment = list(great_circle(a, b, steps=steps))
                result.extend(segment if not result else segment[1:])
            coordinates = result
        return self.line(coordinates, **_defaults(kwargs, arrow=True))

    def polygon(self, coordinates, *, holes=None, **kwargs):
        rings = [list(coordinates)] + [list(r) for r in holes or []]
        for ring in rings:
            if ring and tuple(ring[0]) != tuple(ring[-1]):
                ring.append(ring[0])
        return self.geojson(_collection("Polygon", rings), **kwargs)

    @artist_mutation
    def scatter(self, lon, lat, *, s=36, c=None,cmap='viridis',norm=None,vmin=None,vmax=None, **kwargs):
        coordinates = ScatterCollection._prepare_offsets(_zip_coordinates(lon, lat))
        collection = _collection("MultiPoint", coordinates)
        sizes = ScatterCollection._prepare_sizes([s] if isinstance(s,Real) else s)
        if len(sizes) not in (1,len(coordinates)):
            raise ValueError('s must be a scalar or have one marker area per point')
        colors = _broadcast(c, len(coordinates)) if c is not None else None
        numeric=colors is not None and all(v is None or isinstance(v,Real) for v in colors)
        style = style_dict(_defaults(kwargs, zorder=5))
        advance=c is None and style.get('color') is None and 'color' in self._prop_cycle[self._scatter_index%len(self._prop_cycle)]
        if c is None and style.get('color') is None:
            style['color']=self._prop_cycle[self._scatter_index%len(self._prop_cycle)].get('color','black')
        if numeric:
            from .colors import Normalize,get_cmap
            if norm is not None and (vmin is not None or vmax is not None):raise ValueError('Use norm or vmin/vmax')
            prepared_norm=norm if norm is not None else Normalize(vmin,vmax)
            if not isinstance(prepared_norm,Normalize):raise TypeError('norm must be an Azimlib Normalize')
            prepared_cmap=get_cmap(cmap)
            prepared_norm.autoscale_None(colors)
        self._fit(collection)
        layer=self._add("scatter", coordinates, style, sizes=sizes, colors=None if numeric else colors)
        if numeric:
            layer.set_cmap(prepared_cmap);layer.set_norm(prepared_norm);layer.set_array(colors)
        if advance:self._scatter_index=(self._scatter_index+1)%len(self._prop_cycle)
        return layer

    def text(self, lon, lat, text, *, transform="data", **kwargs):
        if transform not in ("data", "axes"):
            raise ValueError("transform must be 'data' or 'axes'")
        if not all(math.isfinite(float(v)) for v in (lon, lat)):
            raise ValueError("Text coordinates must be finite")
        if transform == "data":
            _collection("Point", [lon, lat])
        return self._add("text", (float(lon), float(lat), str(text)), _defaults(kwargs, zorder=8), transform=transform)

    def labels(self, data, field="name", *, avoid_overlap=True,padding=2,offsets=None,leader=False,
               placement='auto',priority_field='priority',min_span=0,max_span=None,**kwargs):
        """Place feature labels with collision avoidance and local line tangents.

        placement: auto, point or line. min/max_span filter the maximum lon/lat
        viewport span in degrees; offsets and padding are logical 100-dpi pixels.
        """
        if not math.isfinite(padding) or padding<0:raise ValueError('padding must be nonnegative')
        if placement not in ('auto','point','line'):raise ValueError('placement must be auto, point or line')
        if priority_field is not None and not isinstance(priority_field,str):raise TypeError('priority_field must be a field name or None')
        if not math.isfinite(float(min_span)) or min_span<0 or max_span is not None and (not math.isfinite(float(max_span)) or max_span<=0 or max_span<min_span):
            raise ValueError('Require finite 0<=min_span<=max_span, with max_span positive or None')
        if offsets is not None:
            offsets=tuple(tuple(float(v) for v in p) for p in offsets)
            if not offsets or any(len(p)!=2 or any(not math.isfinite(v) for v in p) for p in offsets):raise ValueError('offsets must be finite screen pairs')
        collection = read_geojson(data.data if isinstance(data, Layer) else data)
        if placement=='line' and any(f.geometry and f.geometry.type not in ('LineString','MultiLineString') for f in collection):
            raise ValueError('placement=line requires line geometries')
        if priority_field is not None:
            for feature in collection:
                value=feature.properties.get(priority_field)
                if value is not None and not math.isfinite(float(value)):raise ValueError('Feature label priority must be finite')
        return self._add("labels", collection, _defaults(kwargs, fontsize=10, ha="center", va="center", halo="white", zorder=8),
                         field=field, avoid_overlap=bool(avoid_overlap),padding=padding,offsets=offsets,leader=bool(leader),
                         placement=placement,priority_field=priority_field,min_span=float(min_span),max_span=None if max_span is None else float(max_span))

    def annotate(self, text, xy, xytext=None, *, textcoords="offset pixels", arrow=True, **kwargs):
        xy=coordinate_pair(xy,True)
        if textcoords not in ANNOTATION_COORDS:
            raise ValueError('Unsupported annotation coordinates')
        xytext = (20, -20) if xytext is None else xytext
        xytext=coordinate_pair(xytext,textcoords=='data')
        return self._add("annotation", (tuple(xy), tuple(xytext), str(text)), _defaults(kwargs, zorder=9, arrow=arrow), textcoords=textcoords)

    callout = annotate

    def info_box(self, text, *, position=(.025, .975), **kwargs):
        return self.text(*position, text, **_defaults(kwargs, transform="axes", fontsize=11, va="top", background="white"))

    def title(self, text, **kwargs):
        """Fluent geographic shorthand; set_title returns the text artist."""
        self.set_title(text,**kwargs)
        return self

    @artist_mutation
    def set_title(self, text, fontdict=None, loc=None, pad=None, **kwargs):
        """Set one of three independent titles; pad is measured in points."""
        loc=rcParams['axes.titlelocation'] if loc is None else loc
        if loc not in ('left','center','right'):raise ValueError('loc must be left, center or right')
        pad=rcParams['axes.titlepad'] if pad is None else float(pad)
        if not math.isfinite(pad):raise ValueError('title pad must be finite')
        options={**normalize_aliases(dict(fontdict or {})),**normalize_aliases(kwargs)}
        slot={'left':'_left_title','center':'_title','right':'_right_title'}[loc]
        artist=self._set_text_component(slot,text,options,fontsize=rcParams['axes.titlesize'],fontweight='normal',ha=loc,va='baseline')
        setattr(self,slot,artist);self._title_pads[loc]=pad
        return artist

    def _set_text_component(self,slot,text,kwargs,**defaults):
        artist=getattr(self,slot,None)
        if artist is None:return TextArtist(text,_owner=self,_slot=slot,**_defaults(kwargs,**defaults))
        artist.set(text=text,**kwargs)
        return artist

    def get_title(self,loc='center'):
        if loc not in ('left','center','right'):raise ValueError('loc must be left, center or right')
        artist=getattr(self,{'left':'_left_title','center':'_title','right':'_right_title'}[loc])
        return artist.text if artist is not None else ''

    @artist_mutation
    def set_xlabel(self, label, *,labelpad=None,**kwargs):
        """Set the horizontal geographic axis label."""
        if self._colorbar_artist is not None:return self._colorbar_artist.set_label(label,labelpad=labelpad,**kwargs)
        if labelpad is not None and not math.isfinite(float(labelpad)):raise ValueError('labelpad must be finite')
        self._xlabel = self._set_text_component('_xlabel',label,kwargs,fontsize=rcParams['axes.labelsize'],color=rcParams['axes.labelcolor'],ha='center',va='top')
        if labelpad is not None:self._labelpad['x']=float(labelpad)
        return self._xlabel

    def get_xlabel(self):
        if self._colorbar_artist is not None:return self._colorbar_artist.label_artist.text if self._colorbar_artist.orientation=='horizontal' else ''
        return self._xlabel[0] if self._xlabel is not None else ""

    @artist_mutation
    def set_ylabel(self, label, *,labelpad=None,**kwargs):
        """Set the vertical geographic axis label."""
        if self._colorbar_artist is not None:return self._colorbar_artist.set_label(label,labelpad=labelpad,**kwargs)
        if labelpad is not None and not math.isfinite(float(labelpad)):raise ValueError('labelpad must be finite')
        self._ylabel = self._set_text_component('_ylabel',label,kwargs,fontsize=rcParams['axes.labelsize'],color=rcParams['axes.labelcolor'],rotation=90,rotation_mode='anchor',ha='center',va='bottom')
        if labelpad is not None:self._labelpad['y']=float(labelpad)
        return self._ylabel

    def get_ylabel(self):
        if self._colorbar_artist is not None:return self._colorbar_artist.label_artist.text if self._colorbar_artist.orientation=='vertical' else ''
        return self._ylabel[0] if self._ylabel is not None else ""

    @artist_mutation
    def subtitle(self, text, **kwargs):
        self._subtitle = self._set_text_component('_subtitle',text,kwargs,fontsize=11,color='#657981')
        return self._subtitle

    @artist_mutation
    def set_extent(self, extent):
        """Set (west, east, south, north), matching common map plotting APIs."""
        if len(extent) != 4 or not all(math.isfinite(float(v)) for v in extent):
            raise ValueError("extent must contain four finite numbers: west,east,south,north")
        w, e, s, n = map(float, extent)
        if not (-180 <= w < e <= 180 and -90 <= s < n <= 90):
            raise ValueError("Require -180 <= west < east <= 180 and -90 <= south < north <= 90; seam-spanning viewports are not supported yet")
        self._set_interval('x',w,e)
        self._set_interval('y',s,n)
        return self

    def get_extent(self):
        w, s, e, n = self._get_extent()
        return w, e, s, n

    def get_xlim(self):
        """Return (west, east) geographic longitude limits in degrees."""
        west, east, _, _ = self.get_extent()
        return west, east

    @artist_mutation
    def set_xlim(self, left=None, right=None, *,emit=True,auto=False):
        """Set longitude limits; accept ``(left, right)`` or separate values."""
        if right is None and left is not None and not isinstance(left, Real):
            left, right = left
        west, east, south, north = self.get_extent()
        self._set_interval('x',west if left is None else left,east if right is None else right,emit=emit,auto=auto)
        return self.get_xlim()

    def get_ylim(self):
        """Return (south, north) geographic latitude limits in degrees."""
        _, _, south, north = self.get_extent()
        return south, north

    @artist_mutation
    def set_ylim(self, bottom=None, top=None, *,emit=True,auto=False):
        """Set latitude limits; accept ``(bottom, top)`` or separate values."""
        if top is None and bottom is not None and not isinstance(bottom, Real):
            bottom, top = bottom
        west, east, south, north = self.get_extent()
        self._set_interval('y',south if bottom is None else bottom,north if top is None else top,emit=emit,auto=auto)
        return self.get_ylim()

    def zoom(self, factor=2, center=None):
        """Zoom geographic limits by a positive factor (>1 zooms in).

        ``center`` is a (longitude, latitude) pair. Limits shift at the poles
        and antimeridian to preserve their span; seam-spanning limits are not
        supported by this initial viewport implementation.
        """
        factor = float(factor)
        if not math.isfinite(factor) or factor <= 0:
            raise ValueError("zoom factor must be finite and positive")
        west, east, south, north = self.get_extent()
        if center is None:
            cx, cy = (west+east)/2, (south+north)/2
        else:
            if len(center) != 2 or not all(math.isfinite(float(v)) for v in center):
                raise ValueError("zoom center must be a finite (longitude, latitude) pair")
            cx, cy = map(float, center)
            if not -180 <= cx <= 180 or not -90 <= cy <= 90:
                raise ValueError("zoom center must lie within longitude [-180,180], latitude [-90,90]")
        west, east = _bounded_interval(cx, min(360, (east-west)/factor), -180, 180)
        south, north = _bounded_interval(cy, min(180, (north-south)/factor), -90, 90)
        return self.set_extent((west, east, south, north))

    def pan(self, dlon, dlat):
        """Move the geographic viewport in degrees, preserving its size."""
        dlon, dlat = float(dlon), float(dlat)
        if not math.isfinite(dlon) or not math.isfinite(dlat):
            raise ValueError("pan offsets must be finite longitude/latitude degrees")
        west, east, south, north = self.get_extent()
        west, east = _bounded_interval((west+east)/2+dlon, east-west, -180, 180)
        south, north = _bounded_interval((south+north)/2+dlat, north-south, -90, 90)
        return self.set_extent((west, east, south, north))

    @artist_mutation
    def overview(self, visible=True, *, loc="upper right", context=None, extent=None, width=145, shade_alpha=.45):
        """Add a locator with a fixed context and highlighted current viewport.

        context='brazil' loads a country outline independently of the main map.
        Otherwise current geometry layers and their current extent are captured.
        """
        _validate_loc(loc)
        if not math.isfinite(width) or width<60:raise ValueError('Overview width must be at least 60 pixels')
        if not 0<=shade_alpha<=1:raise ValueError('shade_alpha must lie in [0,1]')
        from copy import copy
        clone=copy(self)
        from .shared_axes import SharedGroup
        from .callbacks import CallbackRegistry
        clone._shared_axes={name:SharedGroup(clone) for name in ('x','y')}
        clone._sharex=clone._sharey=None
        clone._autoscale_on=dict(self._autoscale_on)
        clone.callbacks=CallbackRegistry(('xlim_changed','ylim_changed'))
        clone.layers=list(self.layers);clone.insets=[]
        clone._overview=clone._legend=clone._scale_bar=clone._north=clone._compass=clone._colorbar=None
        clone._title=clone._subtitle=clone._xlabel=clone._ylabel=None
        clone._left_title=clone._right_title=None
        clone._frame=False
        if context is not None:
            clone.layers=[];clone._bounds=None;clone._extent=None
            clone.map(context,facecolor='#eeeeee',edgecolor='#555555',linewidth=.5)
            if str(context).lower() in ('brazil','brasil','bra'):clone.states(linewidth=.25)
        else:clone.layers=[layer for layer in clone.layers if layer.kind=='geometry']
        if extent is not None:clone.set_extent(extent)
        fixed=clone.get_extent();clone.set_extent(fixed)
        overview=MapComponent(axes=self,slot='_overview',loc=loc,width=float(width),shade_alpha=float(shade_alpha))
        overview.context_axes=clone
        overview['visible']=bool(visible)
        return self._replace_component('_overview',overview)

    def _get_extent(self):
        if self._extent:
            return self._extent
        if self._bounds:
            return self._data_extent()
        return -180, -80, 180, 84

    def _data_extent(self):
        w,s,e,n=self._bounds if self._bounds is not None else self._get_extent()
        def limits(low,high,margin,bound):
            if low==high:low,high=low-.5,high+.5
            padding=(high-low)*margin
            low,high=max(-bound,low-padding),min(bound,high+padding)
            # Unwrapped longitudes may sit entirely outside the display domain.
            return (-bound,bound) if low>=high else (low,high)
        for name in ('x','y'):
            bounds=[ax._bounds for ax in self._shared_axes[name].members if ax._bounds is not None]
            if not bounds:continue
            i,j=(0,2) if name=='x' else (1,3)
            low,high=limits(min(b[i] for b in bounds),max(b[j] for b in bounds),self._margins[name],180 if name=='x' else 90)
            if name=='x':w,e=low,high
            else:s,n=low,high
        return w,s,e,n

    def get_autoscalex_on(self):return self._autoscale_on['x']
    def get_autoscaley_on(self):return self._autoscale_on['y']
    def get_autoscale_on(self):return self.get_autoscalex_on() and self.get_autoscaley_on()
    @artist_mutation
    def set_autoscalex_on(self,value):self._autoscale_on['x']=bool(value)
    @artist_mutation
    def set_autoscaley_on(self,value):self._autoscale_on['y']=bool(value)
    @artist_mutation
    def set_autoscale_on(self,value):self._autoscale_on={'x':bool(value),'y':bool(value)}

    @artist_mutation
    def relim(self,visible_only=False):
        """Recompute geographic data bounds without moving the current view.

        Includes own geometry, scatter, mesh and vector layers. Background
        geometry added with fit=False stays excluded from automatic fitting.
        """
        current=self._get_extent();bounds=None
        for layer in self.layers:
            if visible_only and not layer.get_visible():continue
            candidate=None
            if layer.kind=='geometry' and layer.options.get('fit',True):candidate=layer.data.bounds
            elif layer.kind in ('scatter','vectors'):
                points=[p[:2] for p in layer.data]
                if points:candidate=_collection('MultiPoint',points).bounds
            elif layer.kind=='mesh':
                x,y,_=layer.data
                candidate=(x[0],y[0],x[-1],y[-1])
            if candidate is not None:
                bounds=candidate if bounds is None else (min(bounds[0],candidate[0]),min(bounds[1],candidate[1]),max(bounds[2],candidate[2]),max(bounds[3],candidate[3]))
        self._extent=current;self._bounds=bounds

    @artist_mutation
    def autoscale_view(self,tight=None,scalex=True,scaley=True):
        """Fit data bounds on automatic axes; explicit limits remain fixed."""
        if tight is not None:self._tight=bool(tight)
        if not any(ax._bounds is not None for group in self._shared_axes.values() for ax in group.members):return
        current=self._get_extent();fitted=self._data_extent()
        x=bool(scalex) and self.get_autoscalex_on()
        y=bool(scaley) and self.get_autoscaley_on()
        if x:self._set_interval('x',fitted[0],fitted[2],auto=None)
        if y:self._set_interval('y',fitted[1],fitted[3],auto=None)

    @artist_mutation
    def autoscale(self,enable=True,axis='both',tight=None):
        if axis not in ('x','y','both'):raise ValueError('axis must be x, y or both')
        axes=('x','y') if axis=='both' or enable is None else (axis,)
        if enable is not None:
            for name in axes:self._autoscale_on[name]=bool(enable)
        if tight:
            for name in axes:
                if enable is None or self._autoscale_on[name]:self._margins[name]=0.
        self.autoscale_view(tight=tight,scalex='x' in axes,scaley='y' in axes)

    @staticmethod
    def _margin(value):
        value=float(value)
        if not math.isfinite(value) or value<=-.5:raise ValueError('Margin must be finite and greater than -0.5')
        return value
    def get_xmargin(self):return self._margins['x']
    def get_ymargin(self):return self._margins['y']
    def set_xmargin(self,value):self.margins(x=value)
    def set_ymargin(self,value):self.margins(y=value)
    def margins(self,*margins,x=None,y=None,tight=True):
        if margins and (x is not None or y is not None):raise TypeError('Use positional margins or x/y')
        if len(margins)>2:raise TypeError('Use one or two positional margins')
        if margins:x,y=(margins[0],margins[0]) if len(margins)==1 else margins
        if x is None and y is None:return self.get_xmargin(),self.get_ymargin()
        updates={name:self._margin(value) for name,value in (('x',x),('y',y)) if value is not None}
        with self._mutation():
            self._margins.update(updates)
            self.autoscale_view(tight=tight)

    @artist_mutation
    def set_axisbelow(self,value):
        if value is not True and value is not False and value!='line':raise ValueError("axisbelow: True, False, or 'line'")
        self._axisbelow=value

    def get_axisbelow(self):return self._axisbelow

    @artist_mutation
    def grid(self, visible=None, which='major', axis='both', *, step=None, labels=None, **kwargs):
        """Toggle with no arguments; styling arguments imply visible=True."""
        if which not in ('major','minor','both') or axis not in ('x','y','both'):raise ValueError('which: major/minor/both; axis: x/y/both')
        if step is not None and (not math.isfinite(float(step)) or float(step) <= 0):
            raise ValueError("Grid step must be finite and positive")
        kwargs=style_dict(kwargs)
        # Validate all requested groups before replacing any layer.
        requests={}
        for kind in ('major','minor') if which=='both' else (which,):
            configs=dict(self._grid_configs[kind])
            existing=next((l for l in self.layers if l.kind=='grid' and l.options.get('which','major')==kind),None)
            for name in ('x','y') if axis=='both' else (axis,):
                previous=configs.get(name,{})
                shown=bool(existing and existing.visible and previous.get('visible'))
                enabled=True if kwargs else bool(visible) if visible is not None else True if step is not None or labels is not None else not shown
                style=style_dict(_defaults({**previous.get('style',{}),**kwargs},color=rcParams['grid.color'],linewidth=rcParams['grid.linewidth'],linestyle=rcParams['grid.linestyle'],alpha=rcParams['grid.alpha']))
                configs[name]=dict(visible=enabled,style=style,step=float(step) if step is not None else previous.get('step'),
                                   labels=bool(labels) if labels is not None else previous.get('labels',kind=='major'))
            requests[kind]=configs
        if kwargs and visible is False:
            import warnings
            warnings.warn('Grid style properties imply visible=True',UserWarning,stacklevel=2)
        result=None
        for kind,configs in requests.items():
            self._grid_configs[kind]=configs
            for layer in tuple(self.layers):
                if layer.kind=='grid' and layer.options.get('which','major')==kind:layer.remove()
            enabled={k:v for k,v in configs.items() if v['visible']}
            if enabled:
                latest=next(reversed(enabled.values()))
                result=self._add('grid',None,latest['style'],which=kind,axes_config=enabled,step=latest['step'],labels=latest['labels'])
                if kind=='major':
                    self._grid_config=latest
                    self._grid_format=dict(step=latest['step'],labels=latest['labels'])
        return result

    graticule = grid

    @artist_mutation
    def legend(self, handles=None, labels=None, *, title=None, loc=None, fontsize=None,
               frameon=True, facecolor=None, edgecolor=None, framealpha=None,
               title_fontsize=None, borderpad=.4, labelspacing=.5, handlelength=2,
               handletextpad=.8, borderaxespad=.5,ncols=None,ncol=None,columnspacing=2,
               bbox_to_anchor=None,bbox_transform='axes',mode=None):
        loc=rcParams['legend.loc'] if loc is None else loc
        fontsize=rcParams['legend.fontsize'] if fontsize is None else fontsize
        facecolor=rcParams['legend.facecolor'] if facecolor is None else facecolor
        if facecolor=='inherit':facecolor=self.facecolor
        edgecolor=rcParams['legend.edgecolor'] if edgecolor is None else edgecolor
        if edgecolor=='inherit':edgecolor=rcParams['axes.edgecolor']
        framealpha=rcParams['legend.framealpha'] if framealpha is None else framealpha
        if labels is not None and handles is None:raise ValueError('labels requires handles')
        handles=list(handles) if handles is not None else None
        labels=list(labels) if labels is not None else None
        if handles is not None and any(not isinstance(h,Layer) and not (isinstance(h,tuple) and h and all(isinstance(v,Layer) for v in h)) for h in handles):raise TypeError('Legend handles must be layers or nonempty tuples of layers')
        if labels is not None and len(labels)!=len(handles):raise ValueError('handles and labels must match')
        values=dict(fontsize=fontsize,title_fontsize=title_fontsize or fontsize,borderpad=borderpad,
                    labelspacing=labelspacing,handlelength=handlelength,handletextpad=handletextpad,borderaxespad=borderaxespad)
        if any(not math.isfinite(float(v)) or v<0 for v in values.values()) or fontsize<=0:raise ValueError('Legend dimensions must be nonnegative, fontsize positive')
        if not 0<=framealpha<=1:raise ValueError('framealpha must lie in [0,1]')
        self._legend = Legend(axes=self,slot='_legend',title=title,loc=loc,handles=handles,labels=labels,
            frameon=bool(frameon),facecolor=facecolor,edgecolor=edgecolor,framealpha=framealpha,
            ncols=ncols if ncols is not None else ncol if ncol is not None else 1,columnspacing=columnspacing,
            bbox_to_anchor=bbox_to_anchor,bbox_transform=bbox_transform,mode=mode,linewidth=rcParams['axes.linewidth'],**values)
        return self._legend

    def get_legend(self):return self._legend

    @artist_mutation
    def scale_bar(self, *, length=None, units="km", loc="lower left", fontsize=9,
                  frameon=True,facecolor='white',edgecolor='#cccccc',framealpha=.8,color='black'):
        _validate_loc(loc)
        if units not in ("km", "m", "mi"):
            raise ValueError("units must be km, m, or mi")
        if length is not None:
            length = float(length)
            if not math.isfinite(length) or length <= 0:
                raise ValueError("Scale bar length must be finite and positive")
        if not 0<=framealpha<=1:raise ValueError('framealpha must lie in [0,1]')
        style_dict(fontsize=fontsize)
        scale = ScaleBar(axes=self,slot='_scale_bar',length=length, units=units, loc=loc,
            fontsize=fontsize,frameon=frameon,facecolor=facecolor,edgecolor=edgecolor,framealpha=framealpha,color=color)
        return self._replace_component('_scale_bar',scale)

    @artist_mutation
    def north_arrow(self, *, loc="upper right", size=36, color="black"):
        """Add a north arrow without replacing the compass rose."""
        return self._orientation('_north',loc,size,color,False)

    def _orientation(self,slot,loc,size,color,compass):
        # Construct/validate before replacing another instance of the same kind.
        indicator=OrientationIndicator(axes=self,slot=slot,loc=loc,size=size,color=color,compass=compass)
        return self._replace_component(slot,indicator)

    def _replace_component(self,slot,component):
        previous=getattr(self,slot)
        setattr(self,slot,component)
        if previous is not None:
            previous._bind_parent(None)
            previous.remove()
        return component

    @artist_mutation
    def compass(self, *, loc="upper left", size=36, color="black"):
        """Add an eight-point compass rose independently of the north arrow."""
        return self._orientation('_compass',loc,size,color,True)

    @artist_mutation
    def inset(self, bounds=(.68, .66, .28, .28), *, projection="equirectangular", projection_kw=None):
        if len(bounds) != 4 or not all(math.isfinite(float(v)) for v in bounds):
            raise ValueError("inset bounds must be four finite fractions")
        x, y, w, h = map(float, bounds)
        if min(x,y) < 0 or min(w,h) <= 0 or x+w > 1 or y+h > 1:
            raise ValueError("inset must fit within axes: x,y,width,height in [0,1]")
        child = MapAxes(self.figure, (x, y, w, h), projection, projection_kw)
        child._parent_axes=self
        child._bind_parent(self)
        self.insets.append(child)
        return child

    inset_axes = inset

    def choropleth(self, data, values, *, key=None, cmap="ocean", vmin=None, vmax=None,
                   bins=5, scheme="equal_interval", missing_color="#dce1e0", norm=None, **kwargs):
        collection = read_geojson(data)
        raw = _feature_values(collection, values, key)
        numeric = []
        for value in raw:
            if value is None:
                numeric.append(None)
            else:
                number = float(value)
                numeric.append(number if math.isfinite(number) else None)
        valid = sorted(x for x in numeric if x is not None)
        if not valid:
            raise ValueError("No finite choropleth values")
        low, high = min(valid) if vmin is None else float(vmin), max(valid) if vmax is None else float(vmax)
        if not math.isfinite(low) or not math.isfinite(high) or low > high:
            raise ValueError("vmin and vmax must be finite with vmin <= vmax")
        if scheme not in ("equal_interval", "quantile"):
            raise ValueError("scheme must be equal_interval or quantile")
        if bins is not None and (isinstance(bins, bool) or not isinstance(bins, int) or not 1 <= bins <= 20):
            raise ValueError("bins must be an integer in [1,20]")
        continuous=bins is None
        if continuous:bins=256
        if scheme == "quantile":
            edges = sorted(set([low] + [max(low,min(high,valid[round(i*(len(valid)-1)/bins)])) for i in range(1,bins)] + [high]))
        else:
            edges = [low*(1-i/bins)+high*(i/bins) for i in range(bins+1)]
        if high == low:
            edges = [low, high]
        count = len(edges)-1
        from .colors import get_cmap
        colors = [get_cmap(cmap)((i+.5)/count) for i in range(count)]
        feature_styles = []
        for value in numeric:
            index = min(count-1, sum(value >= e for e in edges[1:])) if value is not None else 0
            feature_styles.append(dict(facecolor=missing_color if value is None else colors[index]))
        # Prepare every built-in mapping validation while still detached.
        # Invalid norm/limits must not leave a fitted, half-created layer.
        from .colors import Normalize
        if norm is not None and (vmin is not None or vmax is not None):raise ValueError('Use norm or vmin/vmax')
        prototype=Layer('geometry',collection)
        prepared=prototype._prepare_set(dict(norm=norm if norm is not None else Normalize(low,high),cmap=cmap,array=numeric))
        layer = self.geojson(collection, **_defaults(kwargs, edgecolor="white", linewidth=.7, zorder=2))
        layer.options.update(feature_styles=feature_styles, color_scale=dict(vmin=low, vmax=high, cmap=cmap, edges=edges, colors=colors))
        layer._apply_set(prepared)
        layer.options.update(mapped=True,continuous=continuous,missing_color=missing_color,bins=count,scheme=scheme)
        layer.legend_entries = [(f"{edges[i]:,.3g} – {edges[i+1]:,.3g}", dict(facecolor=colors[i], edgecolor="none"), "polygon") for i in range(count)]
        if any(x is None for x in numeric):
            layer.legend_entries.append(("Sem dados", dict(facecolor=missing_color, edgecolor="none"), "polygon"))
        return layer

    def categorical(self, data, values, *, key=None, colors=None, missing_color="#dce1e0", **kwargs):
        collection = read_geojson(data)
        categories = _feature_values(collection, values, key)
        unique = list(dict.fromkeys(str(x) if x is not None else "Sem dados" for x in categories))
        if colors is None:
            colors = CATEGORY_COLORS
        if not isinstance(colors, Mapping):
            if isinstance(colors, str):
                raise ValueError("colors must be a nonempty sequence or a category-to-color mapping")
            colors = tuple(colors)
            if not colors:
                raise ValueError("colors must be a nonempty sequence or a category-to-color mapping")
        color_map = {}
        for index, name in enumerate(unique):
            if name == "Sem dados" and any(value is None for value in categories):
                color_map[name] = missing_color
            elif isinstance(colors, Mapping):
                source = next(value for value in categories if str(value) == name)
                if source in colors:
                    color_map[name] = colors[source]
                elif name in colors:
                    color_map[name] = colors[name]
                else:
                    raise ValueError(f"No color supplied for category {name!r}")
            else:
                color_map[name] = colors[index % len(colors)]
        layer = self.geojson(collection, **_defaults(kwargs, edgecolor="white", linewidth=.7))
        layer.options["feature_styles"] = [dict(facecolor=color_map[str(x) if x is not None else "Sem dados"]) for x in categories]
        layer.legend_entries = [(name, dict(facecolor=color, edgecolor="none"), "polygon") for name, color in color_map.items()]
        return layer

    def density(self, lon, lat, *, bins=24, smoothing=1, cmap="sunset", **kwargs):
        """A regular lon/lat count grid with optional Gaussian cell smoothing.

        Values are weighted counts per angular cell, not people per km².
        """
        coordinates = _zip_coordinates(lon, lat)
        _collection("MultiPoint", coordinates)
        if not coordinates:
            raise ValueError("density needs at least one point")
        if not isinstance(bins, int) or not 2 <= bins <= 100:
            raise ValueError("bins must be an integer in [2,100]")
        smoothing = float(smoothing)
        if not math.isfinite(smoothing) or not 0 <= smoothing <= 5:
            raise ValueError("smoothing must be in [0,5] cells")
        w, s = min(x for x,y in coordinates), min(y for x,y in coordinates)
        e, n = max(x for x,y in coordinates), max(y for x,y in coordinates)
        dx, dy = max((e-w)*.08,.1), max((n-s)*.08,.1)
        w,e,s,n = max(-180,w-dx),min(180,e+dx),max(-90,s-dy),min(90,n+dy)
        sx, sy = (e-w)/bins, (n-s)/bins
        grid = [[0. for _ in range(bins)] for _ in range(bins)]
        for x,y in coordinates:
            i,j = min(bins-1,int((x-w)/sx)),min(bins-1,int((y-s)/sy))
            grid[j][i] += 1
        if smoothing:
            radius = math.ceil(3*smoothing)
            kernel = [math.exp(-i*i/(2*smoothing*smoothing)) for i in range(-radius,radius+1)]
            total = sum(kernel)
            kernel = [v/total for v in kernel]
            for axis in (0,1):
                result = [[0. for _ in range(bins)] for _ in range(bins)]
                for j in range(bins):
                    for i in range(bins):
                        for k,weight in enumerate(kernel):
                            xx,yy = (i+k-radius,j) if axis == 0 else (i,j+k-radius)
                            if 0 <= xx < bins and 0 <= yy < bins:
                                result[j][i] += grid[yy][xx]*weight
                grid = result
        features, values = [], []
        for j in range(bins):
            for i in range(bins):
                if grid[j][i] <= 0:
                    continue
                x,y = w+i*sx,s+j*sy
                right, top = min(e, x+sx), min(n, y+sy)
                ring = [[x,y],[right,y],[right,top],[x,top],[x,y]]
                features.append({"type":"Feature", "properties":{}, "geometry":{"type":"Polygon","coordinates":[ring]}})
                values.append(grid[j][i])
        return self.choropleth({"type":"FeatureCollection","features":features}, values, cmap=cmap, **_defaults(kwargs, edgecolor="none", linewidth=0))

    @artist_mutation
    def colorbar(self, layer, **kwargs):
        from .colorbar import Colorbar
        bar=Colorbar(self,layer,**kwargs)
        return self._replace_component('_colorbar',bar)

    def pcolormesh(self,lon,lat,values,*,cmap='viridis',norm=None,vmin=None,vmax=None,shading='flat',antialiased=False,**kwargs):
        """Lon/lat edges and scalar cells; own projected quadrilateral mesh."""
        if shading!='flat':raise ValueError('Currently shading=flat; x/y are cell edges')
        return self._scalar_mesh(lon,lat,values,cmap,norm,vmin,vmax,antialiased,kwargs)

    def _scalar_mesh(self,lon,lat,values,cmap,norm,vmin,vmax,antialiased,kwargs,**options):
        lon,lat=tuple(float(v) for v in lon),tuple(float(v) for v in lat)
        rows=scalar_rows(values)
        if len(lon)<2 or len(lat)<2 or len(rows)!=len(lat)-1 or any(len(row)!=len(lon)-1 for row in rows):raise ValueError('Z shape must be (len(lat)-1,len(lon)-1)')
        if any(not math.isfinite(v) for v in lon+lat) or any(a>=b for a,b in zip(lon,lon[1:])) or any(a>=b for a,b in zip(lat,lat[1:])):raise ValueError('Edges must be finite and increasing')
        bounds=_collection('MultiPoint',[(lon[0],lat[0]),(lon[-1],lat[-1])])
        styles=style_dict(_defaults(kwargs,zorder=1,edgecolor='none',linewidth=0,antialiased=antialiased))
        flat=[v for row in rows for v in row]
        prepared_norm,prepared_cmap=_field_mapping(flat,cmap,norm,vmin,vmax)
        layer=self._add('mesh',(lon,lat,rows),styles,**options)
        layer.set_cmap(prepared_cmap);layer.set_norm(prepared_norm)
        # The initial data already follows geographic south-to-north row order.
        Layer.set_array(layer,flat)
        self._fit(bounds)
        return layer

    def imshow(self,values,*,extent,origin='upper',cmap='viridis',norm=None,vmin=None,vmax=None,**kwargs):
        """Scalar geographic image; extent=(west,east,south,north)."""
        if origin not in ('upper','lower'):raise ValueError('origin must be upper or lower')
        rows=scalar_rows(values);extent=image_extent(extent)
        x,y=image_edges(extent,len(rows[0]),len(rows))
        if origin=='upper':rows=rows[::-1]
        automatic=dict(self._autoscale_on)
        layer=self._scalar_mesh(x,y,rows,cmap,norm,vmin,vmax,False,kwargs,image=True,origin=origin,image_extent=extent)
        # An image must not override limits explicitly set by the caller.
        # Keep the existing exact/fixed image extent policy on automatic axes.
        if automatic['x'] and automatic['y']:self.set_extent(extent)
        elif automatic['x']:self.set_xlim(extent[0],extent[1])
        elif automatic['y']:self.set_ylim(extent[2],extent[3])
        return layer

    def contour(self,lon,lat,values,levels=7,*,cmap='viridis',norm=None,vmin=None,vmax=None,colors=None,linewidths=None,linestyles=None,**kwargs):
        if norm is not None and (vmin is not None or vmax is not None):raise ValueError('Use norm or vmin/vmax')
        from .fields import grid_data,contour_segments,contour_levels
        from .colors import Normalize
        x,y,z=grid_data(lon,lat,values);valid=[v for row in z for v in row if v is not None]
        if not valid:raise ValueError('No finite contour values')
        levels=contour_levels(valid,levels)
        features=[]
        for level in levels:
            for line in contour_segments(x,y,z,level):
                features.append({'type':'Feature','properties':{'level':level},'geometry':{'type':'LineString','coordinates':line}})
        from .contours import ContourSet,_colors
        from .colors import NoNorm,ListedColormap
        explicit=_colors(colors)
        if explicit:
            cmap=ListedColormap([explicit[i%len(explicit)] for i in range(len(levels))],name='contour_colors')
            norm=NoNorm(vmin if vmin is not None else levels[0],vmax if vmax is not None else levels[-1])
            color_values=list(range(len(levels)))
        else:color_values=list(levels)
        style=style_dict(_defaults(kwargs,linewidth=1,zorder=2))
        edits=dict(norm=norm if norm is not None else Normalize(vmin if vmin is not None else levels[0],vmax if vmax is not None else levels[-1]),cmap=cmap,array=color_values)
        if linewidths is not None:
            if 'linewidth' in kwargs or 'lw' in kwargs:raise ValueError('Use linewidth or linewidths, not both')
            edits['linewidths']=linewidths
        if linestyles is not None:
            if 'linestyle' in kwargs or 'ls' in kwargs:raise ValueError('Use linestyle or linestyles, not both')
            edits['linestyles']=linestyles
        layer=ContourSet('geometry',read_geojson({'type':'FeatureCollection','features':features}),style,dict(contour=True,levels=levels,fit=True,initial_cvalues=tuple(color_values)))
        layer.set(**edits)
        layer._axes=self;layer._bind_parent(self);self.layers.append(layer);self._changed()
        self._fit(_collection('MultiPoint',[(x[0],y[0]),(x[-1],y[-1])]))
        return layer

    def clabel(self,contour,levels=None,*,fmt='%g',**kwargs):
        """Return editable line-label handles; inline=True cuts the displayed path."""
        from .contours import make_labels
        return make_labels(self,contour,levels,fmt,kwargs)

    def quiver(self,lon,lat,u,v,C=None,*,scale=None,cmap='viridis',norm=None,vmin=None,vmax=None,**kwargs):
        """East/north vectors; scale is data units per axes width."""
        if norm is not None and (vmin is not None or vmax is not None):raise ValueError('Use norm or vmin/vmax')
        origins=ScatterCollection._prepare_offsets(_zip_coordinates(lon,lat));count=len(origins)
        u=VectorCollection._values(u,count);v=VectorCollection._values(v,count);scale=VectorCollection._scale(scale)
        bounds=_collection('MultiPoint',origins)
        styles=style_dict(_defaults(kwargs,zorder=2,linewidth=.8))
        if C is not None:
            values=VectorCollection._values(C,count,colors=True)
            prepared_norm,prepared_cmap=_field_mapping(values,cmap,norm,vmin,vmax)
        layer=self._add('vectors',tuple((*p,a,b) for p,a,b in zip(origins,u,v)),styles,scale=scale)
        if C is not None:
            layer.set_cmap(prepared_cmap);layer.set_norm(prepared_norm);layer.set_array(values)
        self._fit(bounds);return layer

    @artist_mutation
    def set_axis_off(self):
        self._frame = False
        return self

    @artist_mutation
    def set_visible(self,visible):self.visible=bool(visible)
    def get_visible(self):return self.visible

    def remove(self):
        if self._colorbar_artist is not None:return self._colorbar_artist.remove()
        parent=getattr(self,'_parent_axes',None)
        collection=parent.insets if parent is not None else self.figure.axes
        if self in collection:collection.remove(self)
        if parent is None:self.figure._forget_axes(self)
        from .shared_axes import detach
        detach(self)
        self._changed()
        self.visible=False
        self._bind_parent(None)

    def get_children(self):
        decorations=[getattr(self,name,None) for name in ('_title','_left_title','_right_title','_subtitle','_xlabel','_ylabel','_legend','_scale_bar','_north','_compass','_overview','_colorbar')]
        labels=[a for store in (self._tick_labels,self._minor_tick_labels) for values in store.values() for a in values or []]
        return [*self.layers,*self.insets,*self.spines.values(),self.xaxis.offsetText,self.yaxis.offsetText,*labels,*[a for a in decorations if a is not None]]

    @artist_mutation
    def clear(self):
        """Remove artists and decoration while preserving projection and position."""
        if self._colorbar is not None:
            self._colorbar._bind_parent(None)
            self._colorbar.remove()
        for child in self.get_children():child._bind_parent(None)
        for layer in self.layers:
            layer._axes = None
        self.layers.clear()
        self.insets.clear()
        self._extent = self._bounds = self._country = None
        self._autoscale_on={'x':True,'y':True}
        self._margins={'x':rcParams['axes.xmargin'],'y':rcParams['axes.ymargin']}
        self._tight=False
        self._title = self._subtitle = self._legend = self._scale_bar = self._north = self._colorbar = None
        self._left_title=self._right_title=None
        self._title_pads={loc:rcParams['axes.titlepad'] for loc in ('left','center','right')}
        self._compass=None
        self._xlabel = self._ylabel = self._overview = None
        self._plot_index = 0
        self._scatter_index=0
        self._prop_cycle=tuple(rcParams['axes.prop_cycle'])
        self._frame = True
        self.visible=True
        self._grid_format=None
        self.facecolor = rcParams['axes.facecolor']
        self._grid_config=None
        self._grid_configs={'major':{},'minor':{}}
        self._axisbelow=rcParams['axes.axisbelow']
        self._init_components()
        from .shared_axes import copy_tickers,sync_tickers
        for name in ('x','y'):
            other=getattr(self,'_share'+name)
            if other is not None:
                copy_tickers(self,other,name)
                limits=other.get_xlim() if name=='x' else other.get_ylim()
                self._set_interval(name,*limits,auto=other._autoscale_on[name])
            elif len(self._shared_axes[name].members)>1:
                for minor in (False,True):
                    for locator in (False,True):sync_tickers(self,name,minor=minor,locator=locator)
                limits=self.get_xlim() if name=='x' else self.get_ylim()
                self._set_interval(name,*limits,auto=True)
        if rcParams['axes.grid']:self.grid(True,which=rcParams['axes.grid.which'],axis=rcParams['axes.grid.axis'])
        return self


def _zip_coordinates(lon, lat):
    if isinstance(lon, Real) and isinstance(lat, Real):
        return [(lon,lat)]
    lon,lat = list(lon),list(lat)
    if len(lon) != len(lat):
        raise ValueError("lon and lat must have equal lengths")
    return list(zip(lon,lat))


def _bounded_interval(center, span, low, high):
    left = max(low, min(high-span, center-span/2))
    return left, left+span


def _format_style(fmt):
    if fmt is None:return {}
    if fmt=='':return {'linestyle':'-','marker':'None'}
    if not isinstance(fmt, str):
        raise ValueError("plot format must be a string such as 'r--' or 'bo-'")
    if fmt.startswith('#'):
        from .cycles import _color
        return {'color':_color(fmt)}
    if fmt in ('red','blue','green','black','white','cyan','magenta','yellow','orange','purple','gray','grey','brown','pink','lime','navy','teal','gold'):
        return {'color':fmt}
    if fmt in ('None','none'):return {'color':'none'}
    style = {}
    match = re.search(r"--|-\.|-|:", fmt)
    if match:
        style["linestyle"] = match.group()
        fmt = fmt[:match.start()] + fmt[match.end():]
    colors = {"b": "#0000ff", "g": "#008000", "r": "#ff0000", "c": "#00bfbf", "m": "#bf00bf", "y": "#bfbf00", "k": "#000000", "w": "#ffffff"}
    for token in fmt:
        if token in colors and "color" not in style:
            style["color"] = colors[token]
        elif token in "os^vD*ph+x.dH" and "marker" not in style:
            style["marker"] = {".": "o", "H": "h"}.get(token, token)
            if token == ".":
                style["markersize"] = 2
        else:
            raise ValueError(f"Unsupported or repeated plot format token {token!r}; use e.g. 'r--', 'bo-' or explicit styles")
    if 'linestyle' in style:style.setdefault('marker','None')
    elif 'marker' in style:style['linestyle']='None'
    return style


def _field_mapping(values,cmap,norm,vmin,vmax):
    from .colors import Normalize,get_cmap
    if norm is not None and (vmin is not None or vmax is not None):raise ValueError('Use norm or vmin/vmax')
    norm=Normalize(vmin,vmax) if norm is None else norm
    if not isinstance(norm,Normalize):raise TypeError('norm must be an Azimlib Normalize')
    palette=get_cmap(cmap);norm.autoscale_None(values)
    return norm,palette

def _broadcast(value, count):
    if isinstance(value, (str, Real)) or value is None:
        return [value]*count
    result = list(value)
    if len(result) != count:
        raise ValueError(f"Expected {count} values, received {len(result)}")
    return result


def _feature_values(collection, values, key):
    if isinstance(values, str):
        return [f.properties.get(values) for f in collection]
    if isinstance(values, Mapping):
        return [values.get(f.properties.get(key) if key is not None else f.id) for f in collection]
    result = list(values)
    if len(result) != len(collection):
        raise ValueError("values must have one entry per feature")
    return result


def _validate_loc(loc):
    if loc not in ("lower left", "lower right", "upper left", "upper right"):
        raise ValueError("loc must be lower left, lower right, upper left, or upper right")

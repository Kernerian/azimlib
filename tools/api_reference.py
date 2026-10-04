"""Generate the public signature reference from Azimlib, without Matplotlib."""
import inspect
from pathlib import Path
import azimlib
from azimlib import pyplot,colors,cm,fields,components,colorbar,geometry,io,projections,crs,datasets,ticker
from azimlib.axis import Axis
from azimlib.artist import Artist
from azimlib.callbacks import CallbackRegistry
from azimlib.figure import Figure,FigureCanvas,AxesGrid
from azimlib.axes import MapAxes
from azimlib.layers import Layer
from azimlib.collections import ScatterCollection
from azimlib.field_artists import MeshCollection,ScalarImage,VectorCollection
from azimlib.contours import ContourSet,ContourLabel,ContourLabels
from azimlib.text_artists import MapText,Annotation
from azimlib.figure_text import FigureTextArtist
from azimlib.cycles import Cycler
from azimlib.gridspec import GridSpec,GridSpecFromSubplotSpec,SubplotSpec,SubplotBox
from azimlib.spatial import BoundsIndex
from azimlib.layout_engine import LayoutEngine,TightLayoutEngine,ConstrainedLayoutEngine,PlaceHolderLayoutEngine

modules=(azimlib,pyplot,colors,cm,fields,io,projections,crs,datasets)
classes=(Artist,CallbackRegistry,BoundsIndex,Figure,GridSpec,GridSpecFromSubplotSpec,SubplotSpec,SubplotBox,FigureCanvas,MapAxes,AxesGrid,Layer,ScatterCollection,MeshCollection,ScalarImage,VectorCollection,ContourSet,ContourLabel,ContourLabels,Axis,components.AxisComponents,components.TextArtist,MapText,Annotation,FigureTextArtist,Cycler,
         components.MapComponent,components.Spine,components.Legend,components.LegendFrame,
         components.OrientationIndicator,components.ScaleBar,
         colorbar.Colorbar,colorbar.ColorbarAxes,cm.ScalarMappable,
         colors.Normalize,colors.NoNorm,colors.LogNorm,colors.TwoSlopeNorm,colors.BoundaryNorm,
         colors.Colormap,colors.ListedColormap,geometry.Geometry,
         geometry.Feature,geometry.FeatureCollection,crs.CRS,crs.Transformer,
         ticker.Locator,ticker.FixedLocator,ticker.NullLocator,ticker.MultipleLocator,
         ticker.MaxNLocator,ticker.AutoLocator,ticker.LogLocator,ticker.Formatter,
         ticker.AutoMinorLocator,
         ticker.ScalarFormatter,ticker.EngFormatter,ticker.NullFormatter,ticker.FixedFormatter,
         ticker.FuncFormatter,ticker.FormatStrFormatter,ticker.StrMethodFormatter,
         ticker.LongitudeFormatter,ticker.LatitudeFormatter,
         projections.Projection,projections.Equirectangular,projections.Mercator,
         projections.EqualEarth,projections.Orthographic,projections.LambertConformalConic,
         projections.AlbersEqualArea,LayoutEngine,TightLayoutEngine,ConstrainedLayoutEngine,PlaceHolderLayoutEngine)

def signature(obj):
    try:return str(inspect.signature(obj))
    except (ValueError,TypeError):return '(...)'

lines=['# Referência pública da Azimlib', '',
       'Gerada por `python tools/api_reference.py` a partir dos objetos reais.',
       'Assinaturas descrevem a implementação atual, não compatibilidade integral',
       'com Matplotlib. Veja [guia científico](scientific.md),',
       '[componentes](components.md), [limites de compatibilidade](compatibility.md)',
       'e [matemática](math.md).', '',
       'Coordenadas: longitude/latitude em graus. figsize: polegadas; linewidth,',
       'fontes e espaçamentos: pontos; s: pontos². set_extent/extent:',
       '(west, east, south, north). Arquivos PNG/SVG não incluem controles de UI.', '']
for module in modules:
    lines.extend([f'## {module.__name__}', ''])
    for name,obj in inspect.getmembers(module,inspect.isfunction):
        if name.startswith('_'):continue
        if not getattr(obj,'__module__','').startswith('azimlib'):continue
        lines.extend([f'### `{name}{signature(obj)}`', ''])
        doc=inspect.getdoc(obj)
        if doc:lines.extend([doc.split('\n\n')[0], ''])
for cls in classes:
    lines.extend([f'## {cls.__module__}.{cls.__name__}', '',f'`{cls.__name__}{signature(cls)}`', ''])
    for name,obj in inspect.getmembers(cls):
        if name.startswith('_') or not inspect.isfunction(obj):continue
        sig=signature(obj).replace('(self, ', '(').replace('(self)', '()')
        lines.extend([f'### `{name}{sig}`', ''])
        doc=inspect.getdoc(obj)
        if doc:lines.extend([doc.split('\n\n')[0], ''])
        if len(sig)>1000:raise RuntimeError('Unexpected oversized signature')
target=Path(__file__).resolve().parents[1]/'docs/api.md'
target.write_text('\n'.join(lines),encoding='utf-8')
print(target)

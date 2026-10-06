"""Azimlib: independent Python cartography with familiar plotting syntax.

>>> import azimlib as azl
>>> fig, ax = azl.subplots()
>>> ax.map("brazil")
>>> ax.states()
>>> ax.rivers()
>>> ax.title("Brasil")
>>> fig.save("brasil.svg")
"""
from __future__ import annotations

from .figure import Figure,AxesGrid
from .gridspec import GridSpec,SubplotSpec,GridSpecFromSubplotSpec
from .axes import MapAxes
from .geometry import Geometry,Feature,FeatureCollection,haversine,great_circle,destination
from .io import read_geojson,write_geojson,read_csv
from .projections import (Projection,Equirectangular,Mercator,EqualEarth,Orthographic,
                          LambertConformalConic,AlbersEqualArea,get_projection,register_projection)
from .crs import CRS,Transformer,transform
from .layers import Layer
from .collections import ScatterCollection
from .text_artists import MapText,Annotation
from .field_artists import MeshCollection,ScalarImage,VectorCollection
from .contours import ContourSet,ContourLabel,ContourLabels
from . import datasets
from .config import rcParams,rc,rc_context,rcdefaults
from . import style
from . import colors,cm,ticker
from .artist import Artist,setp,getp,ion,ioff,isinteractive
from .cycles import cycler,Cycler

__version__="0.3.0.dev0"
__all__=["Artist","setp","getp","ion","ioff","isinteractive","Figure","GridSpec","SubplotSpec","MapAxes","AxesGrid","Layer","ScatterCollection","MeshCollection","ScalarImage","VectorCollection","ContourSet","ContourLabel","ContourLabels","Geometry","Feature","FeatureCollection",
         "Projection","Equirectangular","Mercator","EqualEarth","Orthographic","LambertConformalConic",
         "AlbersEqualArea","get_projection","register_projection","CRS","Transformer","transform",
         "haversine","great_circle","destination","read_geojson","write_geojson","read_csv","datasets",
         "figure","subplots","subplot_mosaic","subplot","show","savefig","gcf","gca","sca",
         "get_fignums","get_figlabels","fignum_exists","clf","cla","close",
         "rcParams","rc","rc_context","rcdefaults","style","colors","cm","ticker"]
__all__.append('GridSpecFromSubplotSpec')
__all__.extend(('MapText','Annotation'))
__all__.extend(('cycler','Cycler'))
from ._state import (figure,subplots,subplot_mosaic,subplot,show,savefig,gcf,gca,sca,
                     get_fignums,get_figlabels,fignum_exists,clf,cla,close,_figures)

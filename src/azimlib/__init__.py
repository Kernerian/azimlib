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
from .shapefile import read_shapefile, read_dbf, DBFRecord
from .xmlio import read_kml, read_osm
from .raster import GeoRaster, read_raster, read_geotiff, read_world_file
from .catalog import DatasetCatalog

from .projections import (Projection,Equirectangular,Mercator,EqualEarth,Orthographic,
                          LambertConformalConic,AlbersEqualArea,TransverseMercator,Stereographic,AzimuthalEquidistant,get_projection,register_projection)
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

from . import transforms,dates,scale
from .path import Path
from .patches import PathPatch,Symbol

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

__all__.extend(("read_shapefile", "read_dbf", "DBFRecord", "read_kml", "read_osm", "GeoRaster", "read_raster", "read_geotiff", "read_world_file", "DatasetCatalog"))

from .geodesy import (Unit, METRE, KILOMETRE, DEGREE, RADIAN, Ellipsoid, Datum,
                      WGS84, GRS80, WGS84_DATUM, Geodesic, GeodesicResult)
from .transverse import utm_zone, utm_crs
__all__.extend(('Unit','METRE','KILOMETRE','DEGREE','RADIAN','Ellipsoid','Datum','WGS84','GRS80','WGS84_DATUM','Geodesic','GeodesicResult','utm_zone','utm_crs','TransverseMercator','Stereographic','AzimuthalEquidistant'))

from .topology import (orientation, segment_intersection, ring_orientation, validate_ring, validate_geometry, Intersection, ValidationIssue, TopologyReport)
from .geometry import longitude_bounds, clip_orthographic_line, clip_orthographic_polygon
__all__.extend(('orientation','segment_intersection','ring_orientation','validate_ring','validate_geometry','Intersection','ValidationIssue','TopologyReport','longitude_bounds','clip_orthographic_line','clip_orthographic_polygon'))

__all__.extend(('transforms','dates','scale','Path','PathPatch','Symbol'))

from .collections import LineCollection
__all__.append('LineCollection')

from .subfigure import SubFigure
__all__.append('SubFigure')

from . import legend_handler
__all__.append('legend_handler')

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

from .bodies import (Body,BodySource,BodyRegistry,BODIES,EARTH,MOON,MARS,VENUS,MERCURY,
                     SurfaceMesh,LongitudeConvention,Capability,CapabilityStatus,UnsupportedBodyOperation)
from .planetary import PlanetaryContext,PlanetaryData
from .groups import ArtistGroup
from ._frames import ReferenceFrame,Coordinates,RigidTransform,GeodeticFrame
from .figure import Figure,AxesGrid
from .gridspec import GridSpec,SubplotSpec,GridSpecFromSubplotSpec
from .axes import MapAxes
from .geometry import Geometry,Feature,FeatureCollection,haversine,great_circle,destination
from .io import read_geojson,write_geojson,read_csv
from .shapefile import read_shapefile, read_dbf, DBFRecord
from .xmlio import read_kml, read_osm
from .pbf import read_osm_pbf, iter_osm_pbf, OSMIndex, OSMRecord, OSMMember
from .raster import GeoRaster, read_raster, read_geotiff, read_world_file
from .catalog import DatasetCatalog

from .projections import (Projection,Equirectangular,Mercator,EqualEarth,Orthographic,
                          LambertConformalConic,AlbersEqualArea,TransverseMercator,Stereographic,AzimuthalEquidistant,LambertAzimuthalEqualArea,get_projection,register_projection)
from .crs import CRS,Transformer,transform,CRSCatalog,CRSDefinition,crs_catalog
from .coordinate_operations import CoordinateFrame,GeodeticConversion,Helmert,CoordinatePipeline
from .datum_grids import ShiftGrid,GridTile,GridCoverageError,GridNoDataError,read_ntv2,read_gtx
from .grid_operations import GridOperation,OperationSet
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

from .patterns import Provenance,HatchPattern
from .icons import read_svg_symbol

__version__="0.5.0.dev0"
from .text_engine import register_font, text_context, TextEngineError, MissingGlyphError, FontPermissionError
__all__=["Artist","setp","getp","ion","ioff","isinteractive","Figure","GridSpec","SubplotSpec","MapAxes","AxesGrid","Layer","ScatterCollection","MeshCollection","ScalarImage","VectorCollection","ContourSet","ContourLabel","ContourLabels","Geometry","Feature","FeatureCollection",
         "Projection","Equirectangular","Mercator","EqualEarth","Orthographic","LambertConformalConic",
         "AlbersEqualArea","get_projection","register_projection","CRS","Transformer","transform",
         "haversine","great_circle","destination","read_geojson","write_geojson","read_csv","datasets",
         "figure","subplots","subplot_mosaic","subplot","show","savefig","gcf","gca","sca",
         "get_fignums","get_figlabels","fignum_exists","clf","cla","close",
         "rcParams","rc","rc_context","rcdefaults","style","colors","cm","ticker"]
__all__.append('GridSpecFromSubplotSpec')
__all__.extend(('register_font','text_context','TextEngineError','MissingGlyphError','FontPermissionError'))
__all__.extend(('MapText','Annotation'))
__all__.extend(('cycler','Cycler'))
from ._state import (figure,subplots,subplot_mosaic,subplot,show,savefig,gcf,gca,sca,
                     get_fignums,get_figlabels,fignum_exists,clf,cla,close,_figures)

__all__.extend(("read_shapefile", "read_dbf", "DBFRecord", "read_kml", "read_osm", "GeoRaster", "read_raster", "read_geotiff", "read_world_file", "DatasetCatalog"))
__all__.extend(('read_osm_pbf', 'iter_osm_pbf', 'OSMIndex', 'OSMRecord', 'OSMMember'))
__all__.extend(('CRSCatalog','CRSDefinition','crs_catalog','CoordinateFrame',
                'GeodeticConversion','Helmert','CoordinatePipeline','LambertAzimuthalEqualArea'))
__all__.extend(('ShiftGrid','GridTile','GridCoverageError','GridNoDataError',
                'read_ntv2','read_gtx','GridOperation','OperationSet'))

from .geodesy import (Unit, METRE, KILOMETRE, DEGREE, RADIAN, SECOND, DAY, Ellipsoid, Datum,
                      WGS84, GRS80, WGS84_DATUM, Geodesic, GeodesicResult)
from .transverse import utm_zone, utm_crs
__all__.extend(('Unit','METRE','KILOMETRE','DEGREE','RADIAN','SECOND','DAY','Ellipsoid','Datum','WGS84','GRS80','WGS84_DATUM','Geodesic','GeodesicResult','utm_zone','utm_crs','TransverseMercator','Stereographic','AzimuthalEquidistant'))

from .topology import (orientation, segment_intersection, ring_orientation, validate_ring, validate_geometry, Intersection, ValidationIssue, TopologyReport)
from .geometry import longitude_bounds, clip_orthographic_line, clip_orthographic_polygon
__all__.extend(('orientation','segment_intersection','ring_orientation','validate_ring','validate_geometry','Intersection','ValidationIssue','TopologyReport','longitude_bounds','clip_orthographic_line','clip_orthographic_polygon'))

from .overlay import (overlay,intersection,union,difference,symmetric_difference,
                      overlay_features,SphericalRegion,OverlayResult,TopologyGraph,
                      TopologyEdge,TopologyError,TopologyPrecisionError,validate_topology,
                      repair_geometry,RepairResult)
__all__.extend(('overlay','intersection','union','difference','symmetric_difference',
                'overlay_features','SphericalRegion','OverlayResult','TopologyGraph',
                'TopologyEdge','TopologyError','TopologyPrecisionError','validate_topology',
                'repair_geometry','RepairResult'))

__all__.extend(('transforms','dates','scale','Path','PathPatch','Symbol'))

from .collections import LineCollection
__all__.append('LineCollection')

from .geocoding import (Address,GeocodingSource,GeocodingRecord,AddressRange,
                       GeocodingResult,GeocodingResults,LocalGeocoder,
                       ExternalGeocoder,GeocodingLimitError,records_from_features)
__all__.extend(('Address','GeocodingSource','GeocodingRecord','AddressRange',
                'GeocodingResult','GeocodingResults','LocalGeocoder',
                'ExternalGeocoder','GeocodingLimitError','records_from_features'))

from .subfigure import SubFigure
__all__.append('SubFigure')

from .routing import (RoadGraph,RoadNode,RoadEdge,RoutingSource,RoutingProfile,
                      NetworkSnap,RoadRoute,RouteStep,RouteInstruction,RoutingTask,
                      RoutingError,RoutingLimitError,UnsupportedRoutingRule)
__all__.extend(('RoadGraph','RoadNode','RoadEdge','RoutingSource','RoutingProfile',
                'NetworkSnap','RoadRoute','RouteStep','RouteInstruction','RoutingTask',
                'RoutingError','RoutingLimitError','UnsupportedRoutingRule'))

from . import legend_handler
__all__.append('legend_handler')

from .tri import Triangulation,LinearTriInterpolator
from .scientific_artists import ColorImage,FilledContourSet,FlowCollection
__all__.extend(('Triangulation','LinearTriInterpolator','ColorImage','FilledContourSet','FlowCollection'))

__all__.extend(('Provenance','HatchPattern','read_svg_symbol'))
from . import widgets
__all__.append('widgets')
from .simplify import simplify_path,simplify_boundaries
__all__.extend(('simplify_path','simplify_boundaries'))

from .temporal import TemporalSeries,Frame,ScalarBinding
from .atlas import Atlas,Region
from . import animation
__all__.extend(('TemporalSeries','Frame','ScalarBinding','Atlas','Region','animation'))

from .tex import TexConfig,tex_context,TexError,TexUnavailableError,TexResourceError,clear_tex_cache
__all__.extend(('TexConfig','tex_context','TexError','TexUnavailableError','TexResourceError','clear_tex_cache'))

from .volume import VolumeField,VolumeBudget,read_volume,write_volume
from .volume_render import OpacityTransfer,VolumeLight
__all__.extend(('VolumeField','VolumeBudget','read_volume','write_volume','OpacityTransfer','VolumeLight'))

from .solar import (SolarModel,SunPosition,SunDirection,SolarObserver,SolarTimeOffsets,
                    SolarRefraction,SolarPath,SolarEvents,solar_events)
__all__.extend(('SolarModel','SunPosition','SunDirection','SolarObserver','SolarTimeOffsets',
                'SolarRefraction','SolarPath','SolarEvents','solar_events'))

from .lunar import LunarModel,MoonPosition,MoonDirection,LunarPath
__all__.extend(('LunarModel','MoonPosition','MoonDirection','LunarPath'))

from .lighting import SolarLighting,ShadowBudget
from .eclipse import EclipseGeometry,ShadowSphere,ShadowCone,Occultation,occultation
from .solar_disk import SolarDiskConvention,SolarDiskComparison,IAU2015_NOMINAL,NASA_SVS_696000
__all__.extend(('SolarDiskConvention','SolarDiskComparison','IAU2015_NOMINAL','NASA_SVS_696000'))
__all__.extend(('SolarLighting','ShadowBudget','EclipseGeometry','ShadowSphere','ShadowCone','Occultation','occultation'))

__all__.extend(('Body','BodySource','BodyRegistry','BODIES','EARTH','MOON','MARS','VENUS','MERCURY','SurfaceMesh','LongitudeConvention','Capability','CapabilityStatus','UnsupportedBodyOperation','PlanetaryContext','PlanetaryData','ArtistGroup'))
__all__.extend(('ReferenceFrame','Coordinates','RigidTransform','GeodeticFrame'))

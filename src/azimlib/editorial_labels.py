"""Body-aware label adapters to the existing deterministic label engine."""
import weakref
from .geometry import Geometry,Feature,FeatureCollection
from .planetary import PlanetaryData

def prepare(ax,data,field):
 from .layers import Layer
 from .thematic import RegionDefinition,CartographicPath
 source=None
 if isinstance(data,Layer):
  if data.axes is not ax:raise ValueError('Labels and source Artist must share Axes ownership')
  source=data
  if data.kind=='thematic_symbols':
   values=data.labels
   return FeatureCollection(tuple(Feature(Geometry('Point',p),{field:values[i] or data.options.get('category','')}) for i,p in enumerate(data.data))),source
  if data.kind=='thematic_region':data=data.definition
  elif data.kind=='thematic_path':data=data.definition
  else:data=data.data
 if isinstance(data,RegionDefinition):
  if data.context!=ax.get_context():raise ValueError('Label region context mismatch')
  return FeatureCollection((Feature(data.geometry,{field:data.category}),)),source
 if isinstance(data,CartographicPath):
  if data.context!=ax.get_context():raise ValueError('Label path context mismatch')
  label='' if source is None else source.style.get('label','')
  return FeatureCollection((Feature(data.geometry,{field:label}),)),source
 if isinstance(data,PlanetaryData):
  if data.context!=ax.get_context():raise ValueError('Label data Body/frame mismatch')
  return data.features,source
 from .io import read_geojson
 if ax.get_body().identifier!='earth' and source is None:raise ValueError('Non-Earth labels require PlanetaryData or owned contextual Artist/definition')
 return read_geojson(data),source

def associated_labels(source,text,**options):
 if source.axes is None:raise ValueError('Source is detached')
 from .thematic import RegionArtist,CartographicPathArtist,SymbolArtist
 from .geometry import Feature,FeatureCollection
 from .planetary import PlanetaryData
 if isinstance(source,SymbolArtist):
  values=[str(text)]*len(source.data) if isinstance(text,str) else tuple(text)
  if len(values)!=len(source.data):raise ValueError('Label count mismatch')
  features=FeatureCollection(tuple(Feature(Geometry('Point',p),{'name':str(v)}) for p,v in zip(source.data,values)))
 elif isinstance(source,(RegionArtist,CartographicPathArtist)):
  features=FeatureCollection((Feature(source.definition.geometry,{'name':str(text)}),))
 else:raise TypeError('Associated labels require thematic source')
 artist=source.axes.labels(PlanetaryData(features,source.get_context()),**options)
 artist.options['associated_source']=weakref.ref(source);artist._changed();return artist

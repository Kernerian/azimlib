"""Explicitly sourced surface nomenclature and thematic geology, no built-in truth."""
from dataclasses import dataclass
import hashlib,json
from pathlib import Path
from .geometry import Geometry,Feature,FeatureCollection,_number
from .planetary import PlanetaryContext,PlanetaryData
from .thematic_assets import AssetSource
KINDS=frozenset(('crater','volcano','mountain','canyon','mare','cap','fault','region','geological-unit','landing','rover','probe','instrument','waypoint','scientific-point'))
@dataclass(frozen=True)
class FeatureName:
 text:str
 language:str
 authority:str
 def __post_init__(self):
  if any(not isinstance(s,str) or not s.strip() for s in (self.text,self.language,self.authority)):raise ValueError('Name,language,authority are explicit')
@dataclass(frozen=True)
class SurfaceFeature:
 identifier:str
 kind:str
 geometry:Geometry
 names:tuple
 source:AssetSource
 epoch:str
 status:str
 classification:str=''
 uncertainty_m:float | None=None
 def __post_init__(self):
  if not isinstance(self.identifier,str) or not self.identifier or self.kind not in KINDS or not isinstance(self.geometry,Geometry):raise ValueError('Invalid surface feature identity/type/geometry')
  if self.geometry.type not in ('Point','MultiPoint','LineString','MultiLineString','Polygon','MultiPolygon'):raise ValueError('Unsupported surface geometry')
  names=tuple(self.names)
  if not names or any(not isinstance(n,FeatureName) for n in names) or len(names)>32:raise ValueError('Require bounded explicit nomenclature')
  if not isinstance(self.source,AssetSource) or not isinstance(self.epoch,str) or not self.epoch.strip():raise ValueError('Feature requires source/license/epoch')
  if self.status not in ('observation','reconstruction','synthetic','illustrative-plan'):raise ValueError('Declare feature evidential status')
  if self.uncertainty_m is not None and _number(self.uncertainty_m)<0:raise ValueError('Uncertainty must be nonnegative metres')
  if not isinstance(self.classification,str):raise ValueError('Classification is an explicit string')
  object.__setattr__(self,'names',names)
@dataclass(frozen=True)
class FeatureCatalog:
 context:PlanetaryContext
 features:tuple
 source:AssetSource
 def __post_init__(self):
  if not isinstance(self.context,PlanetaryContext) or not isinstance(self.source,AssetSource):raise TypeError('Require Body context and dataset source')
  features=tuple(self.features)
  if not len(features)<=2048 or any(not isinstance(f,SurfaceFeature) for f in features) or len({f.identifier for f in features})!=len(features):raise ValueError('Duplicate IDs/feature budget/type')
  count=0
  for f in features:
   for p in f.geometry.iter_positions():self.context.canonical(*p[:2]);count+=1
  if count>65536:raise ValueError('Catalog vertex budget exceeded')
  object.__setattr__(self,'features',features)
 def data(self,*,language=None):
  features=[]
  for item in self.features:
   name=next((n for n in item.names if n.language==language),item.names[0])
   features.append(Feature(item.geometry,dict(name=name.text,language=name.language,authority=name.authority,kind=item.kind,classification=item.classification,epoch=item.epoch,status=item.status,uncertainty_m=item.uncertainty_m,source=item.source.origin,license=item.source.license),item.identifier))
  return PlanetaryData(FeatureCollection(tuple(features)),self.context)
 @classmethod
 def from_file(cls,path,*,context,source,max_bytes=1048576):
  if not isinstance(source,AssetSource) or not source.sha256:raise ValueError('Local feature file requires frozen SHA-256/provenance')
  if type(max_bytes) is not int or not 1<=max_bytes<=8*1048576:raise ValueError('Feature input budget1..8MiB')
  p=Path(path)
  if p.stat().st_size>max_bytes:raise ValueError('Feature input exceeds budget')
  raw=p.read_bytes()
  if len(raw)>max_bytes or hashlib.sha256(raw).hexdigest()!=source.sha256:raise ValueError('Feature source hash/budget mismatch')
  value=json.loads(raw)
  from .io import read_geojson
  geo=read_geojson(value);items=[]
  for f in geo:
   if f.id is None:raise ValueError('Feature requires an explicit stable identifier')
   q=f.properties;name=FeatureName(q['name'],q['language'],q['authority'])
   items.append(SurfaceFeature(str(f.id),q['kind'],f.geometry,(name,),source,q['epoch'],q['status'],q.get('classification',''),q.get('uncertainty_m')))
  return cls(context,tuple(items),source)
 def draw(self,axes,*,language=None,labels=True,style=None,symbols=None,name='Surface features'):
  if axes.get_context()!=self.context:raise ValueError('Feature catalog Body/frame mismatch')
  default_symbols=dict(crater='circle',volcano='mountain',mountain='mountain',canyon='route',landing='flag',rover='bot',probe='satellite',instrument='microscope',waypoint='map-pin',**{'scientific-point':'crosshair'})
  default_symbols.update(symbols or {});prepared=[]
  # Validate styles/symbols/areas before attaching any Artist.
  from .thematic import RegionDefinition,CartographicPath
  from .thematic_assets import get_symbol
  from .styles import style_dict
  for item in self.features:
   appearance=style_dict(style(item) if callable(style) else style or {})
   if item.geometry.type in ('Polygon','MultiPolygon'):value=RegionDefinition(item.geometry,self.context,category=item.classification or item.kind);kind='area'
   elif item.geometry.type in ('LineString','MultiLineString'):
    lines=(item.geometry.coordinates,) if item.geometry.type=='LineString' else item.geometry.coordinates
    value=tuple(CartographicPath.polyline(line,context=self.context) for line in lines);kind='path'
   else:value=get_symbol(default_symbols.get(item.kind,'map-pin'));kind='symbol'
   prepared.append((item,appearance,kind,value))
  group=axes.group(name=name)
  for item,appearance,kind,value in prepared:
   label=next((n.text for n in item.names if n.language==language),item.names[0].text)
   if kind=='area':artists=[axes.region(value,**appearance)]
   elif kind=='path':artists=[axes.cartographic_path(p,**appearance) for p in value]
   else:
    points=(item.geometry.coordinates,) if item.geometry.type=='Point' else item.geometry.coordinates
    artists=[axes.symbols(points,value,category=item.kind,**appearance)]
   for artist in artists:
    group.add(artist);artist.options['surface_feature']=item
    if labels:
     text=artist.labels_for(label,fontsize=8,priority=1,**({'placement':'line'} if kind=='path' else {}));group.add(text)
  return group

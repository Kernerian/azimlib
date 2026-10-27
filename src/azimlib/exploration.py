"""Sourced finite exploration frames using the existing temporal/playback system."""
from dataclasses import dataclass
from .planetary import PlanetaryContext
from .thematic_assets import AssetSource
from .temporal import TemporalSeries
from .bodies import UnsupportedBodyOperation
@dataclass(frozen=True)
class ExplorationSequence:
 series:TemporalSeries
 context:PlanetaryContext
 source:AssetSource
 mode:str
 quantity:str
 unit:str
 def __post_init__(self):
  if not isinstance(self.series,TemporalSeries) or not isinstance(self.context,PlanetaryContext) or not isinstance(self.source,AssetSource):raise TypeError('Require finite TemporalSeries,Body context and provenance')
  if self.mode not in ('observation','reconstruction','visual-interpolation','simulation','illustrative-plan'):raise UnsupportedBodyOperation('No implicit prediction/operational/orbital propagation')
  if not isinstance(self.quantity,str) or not self.quantity.strip() or not isinstance(self.unit,str) or not self.unit.strip():raise ValueError('Declare observed/simulated quantity and unit')
 def bind(self,artist):return ExplorationBinding(self,artist)
class ExplorationBinding:
 def __init__(self,sequence,artist):
  from .thematic import SymbolArtist,CartographicPathArtist,RegionArtist,CartographicPath,RegionDefinition,_points
  from .planetary_light import GeometricLight
  from collections.abc import Mapping
  if artist.axes is None or artist.get_context()!=sequence.context:raise ValueError('Sequence and Artist require one live Body/context')
  self.sequence,self.series,self.artist=sequence,sequence.series,artist;self.index=None;prepared=[]
  for frame in self.series:
   payload=frame.data
   if isinstance(artist,(SymbolArtist,CartographicPathArtist,RegionArtist)) and sequence.unit not in ('degree','deg'):raise ValueError('Angular thematic frames require explicit degree units')
   if isinstance(artist,SymbolArtist):
    if payload is None:prepared.append(None);continue
    value=_points(payload,sequence.context,limit=2048)
    if len(value)!=len(artist.data):raise ValueError('Temporal symbol cardinality must be invariant')
    prepared.append(value)
   elif isinstance(artist,CartographicPathArtist):prepared.append(None if payload is None else CartographicPath.polyline(payload,context=sequence.context))
   elif isinstance(artist,RegionArtist):
    from .geometry import Geometry
    prepared.append(None if payload is None else RegionDefinition(Geometry('Polygon',payload),sequence.context,category=artist.definition.category,semantics=artist.definition.semantics,meaning=artist.definition.meaning))
   else:
    # Existing scalar/lighting binders retain their own complete validation.
    prepared=None;self.delegate=self.series.bind(artist);break
  self.prepared=None if prepared is None else tuple(prepared)
  self.region_slices=tuple(artist.gradient.slices(v) if v is not None and artist.gradient else () for v in self.prepared) if isinstance(artist,RegionArtist) else ()
 def apply(self,index):
  from .animation import frame_index
  from .thematic import SymbolArtist,CartographicPathArtist
  index=frame_index(index,len(self.series))
  if self.artist.axes is None:raise ValueError('Sequence Artist was removed')
  if self.prepared is None:self.delegate.apply(index)
  else:
   value=self.prepared[index]
   if value is None:self.artist.set_visible(False)
   else:
    if isinstance(self.artist,SymbolArtist):self.artist.set_positions(value)
    elif isinstance(self.artist,CartographicPathArtist):self.artist.set_definition(value)
    else:
     # Region replacement is an explicit data edit, not interpolation of history.
     self.artist.definition=value;self.artist.data=value.geometry;self.artist.slices=self.region_slices[index];self.artist._changed()
    self.artist.set_visible(True)
  self.index=index;return self.series[index]
 def at(self,time,*,method='exact'):return self.apply(self.series.index_at(time,method=method))
 def animation(self,**kwargs):
  from .animation import FuncAnimation
  return FuncAnimation(self.artist.figure,lambda i:self.apply(i),len(self.series),**kwargs)

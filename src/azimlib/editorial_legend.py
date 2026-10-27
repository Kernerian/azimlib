"""Sections and explicit quantitative flow keys using the existing Legend."""
from dataclasses import dataclass
from .geometry import _number
from .styles import style_dict
@dataclass(frozen=True)
class LegendSection:
 title:str
 handles:tuple
 labels:tuple | None=None
 def __post_init__(self):
  handles=tuple(self.handles);labels=None if self.labels is None else tuple(str(x) for x in self.labels)
  if not isinstance(self.title,str) or not self.title.strip() or not handles or len(handles)>256:raise ValueError('Section needs title and1..256 handles')
  if labels is not None and len(labels)!=len(handles):raise ValueError('Section labels must match handles')
  object.__setattr__(self,'handles',handles);object.__setattr__(self,'labels',labels)
 @classmethod
 def from_group(cls,group,*,title=None):
  from .groups import ArtistGroup
  def leaves(g):
   result=[]
   for child in g.get_children():result.extend(leaves(child) if isinstance(child,ArtistGroup) else [child])
   return result
  return cls(title or group.name,tuple(leaves(group)))
@dataclass(frozen=True)
class _Heading:
 text:str
class _HeadingHandler:
 def legend_artist(self,legend,handle,fontsize,box):return None
@dataclass(frozen=True)
class FlowScale:
 minimum:float
 maximum:float
 unit:str
 widths:tuple=(.5,4.)
 def __post_init__(self):
  lo,hi=_number(self.minimum),_number(self.maximum);w=tuple(_number(v) for v in self.widths)
  if lo<0 or hi<=lo or not isinstance(self.unit,str) or not self.unit.strip() or len(w)!=2 or min(w)<=0 or max(w)>20 or w[1]<w[0]:raise ValueError('Invalid authored flow range/unit/point widths')
  object.__setattr__(self,'widths',w)
 def width(self,value):
  value=_number(value)
  if not self.minimum<=value<=self.maximum:raise ValueError('Flow value outside declared range; no silent clipping')
  t=(value-self.minimum)/(self.maximum-self.minimum);return self.widths[0]*(1-t)+self.widths[1]*t
 def keys(self,values,*,color='#286e82'):return tuple(FlowKey(self,_number(v),color) for v in values)
@dataclass(frozen=True)
class FlowKey:
 scale:FlowScale
 value:float
 color:str
 def __post_init__(self):
  from .colors import to_rgba
  self.scale.width(self.value);to_rgba(self.color)
 @property
 def label(self):return f'{self.value:g} {self.scale.unit}'
class _FlowHandler:
 def legend_artist(self,legend,handle,fontsize,box):
  from .scene import Path
  from .styles import path_style
  box.scene.add(Path([[(box.x,box.y+box.height/2),(box.x+box.width,box.y+box.height/2)]],False,path_style(dict(color=handle.color,linewidth=handle.scale.width(handle.value)))))
def prepare(sections,handles,labels,handler_map):
 handlers=dict(handler_map or {});handlers.setdefault(FlowKey,_FlowHandler());handlers.setdefault(_Heading,_HeadingHandler())
 if sections is None:return handles,labels,handlers,None
 if handles is not None or labels is not None:raise ValueError('Use sections or flat handles/labels, not both')
 sections=tuple(sections)
 if not 1<=len(sections)<=32 or any(not isinstance(s,LegendSection) for s in sections):raise ValueError('Require1..32 LegendSections')
 output=[];names=[];lengths=[]
 for section in sections:
  output.append(_Heading(section.title));names.append(section.title)
  for i,handle in enumerate(section.handles):
   output.append(handle);names.append(section.labels[i] if section.labels is not None else getattr(handle,'label',None) or getattr(handle,'style',{}).get('label') or getattr(handle,'options',{}).get('category') or getattr(handle,'kind','Item'))
  lengths.append(len(section.handles)+1)
 return output,names,handlers,tuple(lengths)

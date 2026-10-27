"""Explicit physical scale versus visual normalization in one Figure."""
from dataclasses import dataclass
from .bodies import Body
@dataclass(frozen=True)
class WorldComparison:
 figure:object
 axes:tuple
 mode:str

def compare_worlds(bodies,*,mode='normalized',figsize=(11,5),dpi=100):
 from .figure import Figure
 from .pyplot import figure
 bodies=tuple(bodies)
 if not 2<=len(bodies)<=6 or any(not isinstance(b,Body) for b in bodies):raise ValueError('Compare2..6 declared Bodies')
 if mode not in ('physical','normalized'):raise ValueError('Declare physical or normalized visual size')
 if any(b.shape not in ('sphere','ellipsoid') for b in bodies):raise ValueError('Comparison only demonstrated for sphere/oblate reference surfaces')
 f=figure(figsize=figsize,dpi=dpi);axes=[];largest=max(b.axes[0] for b in bodies);slot=.92/len(bodies);fw,fh=figsize
 for i,b in enumerate(bodies):
  factor=b.axes[0]/largest if mode=='physical' else 1.;size=min(slot*.85*fw,.72*fh);width=size/fw*factor;height=size/fh*factor;cx=.04+slot*(i+.5);cy=.53
  from .surfaces import BodySurface
  from .planetary import axis_context
  context=axis_context(b);projection=BodySurface(context).projection('orthographic')
  ax=f.add_axes((cx-width/2,cy-height/2,width,height),context=context,projection=projection);ax.set_extent((-180,180,-90,90));ax.set_axis_off();ax.grid(True,step=45,linewidth=.35,color='#a1b0b8');f.text(cx,.11,b.name,ha='center',fontsize=12);f.text(cx,.065,f'a={b.axes[0]/1000:,.1f} km',ha='center',fontsize=8);axes.append(ax)
 f.suptitle('Common physical reference-surface scale' if mode=='physical' else 'Visually normalized bodies | not a common physical scale',fontsize=15)
 f.text(.5,.02,'Ideal reference surfaces, static declared frames; no orbital positions or hidden vertical exaggeration',ha='center',fontsize=8)
 return WorldComparison(f,tuple(axes),mode)

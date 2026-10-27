"""Pure presentation themes: defaults < theme < group < local Artist."""
from dataclasses import dataclass
from .styles import style_dict
@dataclass(frozen=True)
class CartographicTheme:
 name:str
 roles:tuple
 def __post_init__(self):
  if not isinstance(self.name,str) or not self.name.strip():raise ValueError('Theme needs name')
  allowed={'base','symbols','region','path','labels','legend','inset','background','frame','orientation','raster'};result=[]
  for role,style in self.roles:
   if role not in allowed or any(r==role for r,_ in result):raise ValueError('Unknown/duplicate theme role')
   result.append((role,tuple(style_dict(dict(style)).items())))
  object.__setattr__(self,'roles',tuple(result))
 def style(self,role):return dict(next((s for r,s in self.roles if r==role),()))

def _theme(name,accent,region,background):
 return CartographicTheme(name,tuple((r,tuple(s.items())) for r,s in dict(symbols=dict(color=accent),region=dict(facecolor=region,edgecolor=accent,alpha=.4),path=dict(color=accent,linewidth=1.4),labels=dict(color='#293e48',halo='white',halo_width=1),base=dict(facecolor='#e9e7db',edgecolor='#9aa9ac',linewidth=.4),background=dict(facecolor=background),legend=dict(facecolor='white',edgecolor='#c3cdd1'),inset=dict(facecolor=background),frame=dict(edgecolor='#52646c'),orientation=dict(color=accent),raster=dict(alpha=1)).items()))
PRESETS={name:_theme(name,*colors) for name,colors in dict(atlas=('#23677f','#d8b36c','#e6f0f3'),historical=('#7b5740','#d4a45e','#eee9da'),political=('#6b6099','#bbaed6','#e4edf3'),physical=('#4d7c64','#adc19b','#e1edf1'),scientific=('#26798b','#8eb9c1','#f1f5f6'),geological=('#8e6c47','#d0b17b','#f1eade'),**{'planetary-exploration':('#286c80','#cf9e6f','#e9ded1')}).items()}
def get_theme(value):
 if isinstance(value,CartographicTheme):return value
 if value not in PRESETS:raise ValueError('Unknown cartographic theme')
 return PRESETS[value]
def role(artist):return {'thematic_symbols':'symbols','thematic_region':'region','thematic_path':'path','geometry':'base','labels':'labels','locator':'path','mesh':'raster'}.get(getattr(artist,'kind',''),'')
def defaults(artist):
 ax=getattr(artist,'axes',None);theme=getattr(ax,'_cartographic_theme',None)
 return theme.style(role(artist)) if theme else {}
def set_theme(ax,value):
 theme=None if value is None else get_theme(value)
 if not hasattr(ax,'_theme_original_facecolor'):ax._theme_original_facecolor=ax.facecolor
 ax._cartographic_theme=theme
 ax.set_facecolor(theme.style('background').get('facecolor',ax._theme_original_facecolor) if theme else ax._theme_original_facecolor)
 for artist in ax.layers:artist._changed()
 ax._changed();return theme

"""A programmatic map/legend/note page over existing Figure/Axes Artists."""
import math,textwrap
from .artist import Artist
class CartographicPage(Artist):
 def __init__(self,figure,*,body=None,context=None,title='',subtitle='',credits='',orientation='auto',margin=28,sidebar=.25,gap=18):
  if figure.axes:raise ValueError('CartographicPage owns allocation on an initially empty Figure')
  if orientation not in ('auto','landscape','portrait'):raise ValueError('Unknown editorial orientation')
  if not all(math.isfinite(float(v)) for v in (margin,sidebar,gap)) or margin<8 or not .15<=sidebar<=.45 or gap<4:raise ValueError('Invalid editorial dimensions')
  Artist.__init__(self,figure);self.figure=figure;self.orientation=orientation;self.margin=margin;self.sidebar=sidebar;self.gap=gap;self.notes=[];self._note_artists=[]
  self.axes=figure.add_axes((.1,.2,.6,.6),body=body,context=context)
  self.title_artist=figure.text(.05,.96,title,fontsize=22,fontweight='bold',va='top');self.subtitle_artist=figure.text(.05,.90,subtitle,fontsize=11,va='top',color='#526a76');self.credit_artist=figure.text(.05,.04,credits,fontsize=8,va='bottom',color='#526a76')
  figure._editorial_pages=[self];self.reflow()
 def reflow(self):
  key=(self.figure.figsize,tuple(self.notes),id(self.axes._legend),self.orientation,self.margin,self.sidebar,self.gap)
  if key==getattr(self,'_layout_key',None):return
  w,h=(v*72 for v in self.figure.figsize);m=self.margin;g=self.gap;header=75;footer=45
  if min(w,h)<320 or h-header-footer-2*m<150:raise ValueError('Editorial page too small; minimum side320pt')
  landscape=w>=h if self.orientation=='auto' else self.orientation=='landscape'
  width=w-2*m;height=h-2*m-header-footer
  if landscape:
   side=width*self.sidebar;mw=width-side-g;mapbox=(m,m+footer,mw,height);self.sidebar_box=((m+mw+g)/w,(m+footer)/h,side/w,height/h)
  else:
   side=height*.31;mapbox=(m,m+footer+side+g,width,height-side-g);self.sidebar_box=(m/w,(m+footer)/h,width/w,side/h)
  x,y,mw,mh=mapbox;self.axes.position=(x/w,y/h,mw/w,mh/h)
  self.title_artist.set_position((m/w,1-m/h));self.subtitle_artist.set_position((m/w,1-(m+34)/h));self.credit_artist.set_position((m/w,m/h))
  if self.axes._legend:
   bx,by,bw,bh=self.sidebar_box;self.axes._legend['bbox_to_anchor']=(bx,by,bw,bh);self.axes._legend['bbox_transform']='figure';self.axes._legend['loc']='upper left'
  for artist in self._note_artists:artist.remove()
  self._note_artists=[];bx,by,bw,bh=self.sidebar_box;cursor=by+bh
  if self.axes._legend:
   from .legend_layout import layout
   from .locators import _viewport
   x0,y0,lw,lh=layout(self.axes._legend,_viewport(self.axes))['box']
   cursor=min(cursor,1-(y0+lh)/(self.figure.figsize[1]*100)-14/h)
  for note in self.notes:
   chars=max(18,int(bw*w/4.8));wrapped=textwrap.fill(note,chars);self._note_artists.append(self.figure.text(bx,cursor,wrapped,fontsize=8,va='top',color='#526a76'));cursor-=len(wrapped.splitlines())*11/h+8/h
   if cursor<by:raise ValueError('Notes exceed editorial sidebar; reduce notes/font or enlarge page')
  self._layout_key=key
 def legend(self,**kwargs):
  kwargs.setdefault('fontsize',9);kwargs.setdefault('frameon',False);kwargs.setdefault('loc','upper left');kwargs.setdefault('bbox_transform','figure');kwargs.setdefault('borderaxespad',0)
  result=self.axes.legend(**kwargs);self.reflow();return result
 def note(self,text):
  if len(self.notes)>=8 or len(str(text))>1500:raise ValueError('Editorial note budget exceeded')
  self.notes.append(str(text));self.reflow();self._changed();return self
 def locator(self,*,bounds=(.68,.04,.28,.25),projection='equirectangular',extent=(-180,180,-90,90),**options):
  child=self.axes.inset(bounds,projection=projection);child.set_extent(extent);child.set_axis_off();child.locator(self.axes,**options);return child
 def remove(self):
  self.figure._editorial_pages=[]
  for artist in (self.title_artist,self.subtitle_artist,self.credit_artist,*self._note_artists):artist.remove()
  self.axes.remove();self._bind_parent(None)

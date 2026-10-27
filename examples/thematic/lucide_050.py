"""Official pinned Lucide plus optional Azimlib effects; no network."""
import argparse,json,subprocess,hashlib
from pathlib import Path
import azimlib as a

def catalog():
 f,ax=a.subplots(figsize=(12,9),dpi=120);ax.set_extent((0,30,0,25));ax.set_axis_off()
 for i,(name,icon) in enumerate(a.lucide_catalog().items()):
  x=2+(i%6)*5;y=23-(i//6)*5;ax.symbols([(x,y)],icon,size=24,color=('#256779','#9d5a3f','#717f42')[i%3]);ax.text(x,y-1.6,name,fontsize=8,ha='center')
 ax.set_title('Lucide 1.61.0 | cartographic subset',fontsize=18);f.text(.5,.025,'Official unmodified SVG assets | ISC / applicable Feather MIT terms | names shown are upstream names',ha='center',fontsize=9)
 return f

def effects():
 f,axes=a.subplots(3,4,figsize=(12,8),dpi=120);f.subplots_adjust(left=.03,right=.97,top=.87,bottom=.08,wspace=.12,hspace=.27)
 labels=['Original','Light/dark halo','Soft shadow','Halo + shadow']
 for r,row in enumerate(axes):
  for c,ax in enumerate(row):
   ax.set_extent((-5,5,-4,4));ax.set_axis_off();ax.set_facecolor('#f3eee3' if r!=1 else '#15303c')
   if r==2:ax.imshow([[i+j for i in range(16)] for j in range(12)],extent=(-5,5,-4,4),cmap='terrain')
   halo=a.IconHalo(color='#182b34' if r==1 else 'white',width=1) if c in (1,3) else None
   shadow=a.IconShadow(alpha=.3,offset=(1,1),blur=1) if c in (2,3) else None
   for k,(name,size) in enumerate(zip(('anchor','bot','gem'),(11,20,30))):ax.symbols([(-3+k*3,0)],'lucide:'+name,size=size,color='#edb767' if r==1 else '#276d7e',stroke_width=1.5+k*.5,halo=halo,shadow=shadow)
   if r==0:ax.set_title(labels[c],fontsize=12)
 f.suptitle('Cartographic icons | optional effects in physical points',fontsize=17);f.text(.5,.025,'11/20/30pt | source stroke 1.5/2/2.5 viewBox units | original vectors preserved; only soft shadow uses a local alpha tile',ha='center',fontsize=8)
 return f

def main(out):
 out.mkdir(parents=True,exist_ok=True)
 for name,create in (('lucide-catalog',catalog),('lucide-effects',effects)):
  f=create()
  for fmt in ('png','svg','pdf'):f.savefig(out/(name+'.'+fmt))
  a.close(f)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)

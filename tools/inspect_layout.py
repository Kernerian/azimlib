"""Development-only Matplotlib reference, never imported by the library."""
import json,warnings
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.ticker import MultipleLocator as ReferenceLocator
import azimlib as azl
from azimlib.layout_engine import item_bounds
from PIL import Image,ImageDraw

root=Path(__file__).resolve().parents[1]
reference={'matplotlib_version':matplotlib.__version__,'checks':[]}

def behavior(module):
    f,a=module.subplots(layout='constrained')
    a.set_xlim(-54,-42);a.set_ylim(-28,-16);a.set_title('Reference')
    f.canvas.draw()
    before=dict(left=f.subplotpars.left) if module is plt else dict(left=f.subplotpars['left'])
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter('always');f.subplots_adjust(left=.3)
    after=f.subplotpars.left if module is plt else f.subplotpars['left']
    result={'manual_adjust_ignored':before['left']==after,'warns':bool(recorded),'engine':type(f.get_layout_engine()).__name__}
    f.set_layout_engine('none')
    result['none_retains_adjust_policy']=not f.get_layout_engine().adjust_compatible
    f.set_layout_engine(None);f.subplots_adjust(left=.3)
    result['manual_adjust_after_disable']=(f.subplotpars.left if module is plt else f.subplotpars['left'])==.3
    f.tight_layout();result['tight_stops_continuous_layout']=f.get_layout_engine() is None or type(f.get_layout_engine()).__name__=='PlaceHolderLayoutEngine'
    module.close(f);return result

reference['behavior']={'matplotlib':behavior(plt),'azimlib':behavior(azl)}
assert reference['behavior']['matplotlib']==reference['behavior']['azimlib']

data=azl.datasets.load('states',country='brazil')
for module,name in ((plt,'matplotlib'),(azl,'azimlib')):
    f,a=module.subplots(figsize=(6.4,4.8),layout='tight')
    if module is plt:
        for feature in data['features']:
            geo=feature['geometry'];polys=[geo['coordinates']] if geo['type']=='Polygon' else geo['coordinates']
            for polygon in polys:
                a.add_patch(Polygon(polygon[0],facecolor='#f1f1f1',edgecolor='#888888',linewidth=.4))
        a.set_aspect('equal')
    else:a.states(facecolor='#f1f1f1',edgecolor='#888888',linewidth=.4)
    a.set_xlim(-54,-42);a.set_ylim(-28,-16)
    locator=ReferenceLocator if module is plt else azl.ticker.MultipleLocator
    a.xaxis.set_major_locator(locator(2));a.yaxis.set_major_locator(locator(2))
    a.plot([-52,-48,-44],[-24,-21,-20],color='#d65f45',linestyle='--',linewidth=1.5,label='Rota demonstrativa')
    a.set_title('Título em duas linhas\nFoco geográfico',fontsize=14)
    a.tick_params(labelsize=11,labelrotation=25)
    a.set_xlabel('Longitude',labelpad=6);a.set_ylabel('Latitude',labelpad=6)
    a.legend(loc='center left',bbox_to_anchor=(1.02,.5),fontsize=9)
    f.savefig(root/'gallery'/f'layout-reference-{name}.png',dpi=100)
    if module is plt:
        f.canvas.draw();renderer=f.canvas.get_renderer();b=a.get_tightbbox(renderer)
        box=(b.x0,480-b.y1,b.width,b.height)
    else:
        s=f.to_scene();_,start,end,_=s._layout_groups[0];box=item_bounds(s,start,end)
    x,y,w,h=box
    assert x>=-.2 and y>=-.2 and x+w<=640.2 and y+h<=480.2
    reference['checks'].append({'library':name,'decorations_inside_canvas':True,'bounds_px':box})
    module.close(f)

images=[Image.open(root/'gallery'/f'layout-reference-{name}.png').convert('RGB') for name in ('matplotlib','azimlib')]
combined=Image.new('RGB',(1280,514),'white');draw=ImageDraw.Draw(combined)
draw.text((12,10),'Matplotlib 3.11.2 / Agg',fill='black');draw.text((652,10),'Azimlib / renderer proprio',fill='black')
for i,im in enumerate(images):combined.paste(im,(i*640,34))
combined.save(root/'gallery/layout-reference.png')
(root/'docs/layout-reference.json').write_text(json.dumps(reference,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(reference,indent=2,ensure_ascii=False))

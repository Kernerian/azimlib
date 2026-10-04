"""Development-only Agg reference for figure history and rectangle navigation."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backend_bases import NavigationToolbar2

fig,axes=plt.subplots(1,2,sharex=True,figsize=(8,4),dpi=100)
for ax in axes:ax.set_xlim(-60,-40);ax.set_ylim(-30,-10);ax.set_aspect('equal')
axes[1].set_ylim(-20,0)
toolbar=NavigationToolbar2(fig.canvas);toolbar.push_current();cases=[]

def record(name,action=None):
    fig.canvas.draw()
    cases.append(dict(name=name,action=action,
        extents=[[*map(float,ax.get_xlim()),*map(float,ax.get_ylim())] for ax in axes],
        boxes=[[float(b.x0),float(fig.bbox.height-b.y1),float(b.width),float(b.height)] for ax in axes for b in [ax.get_window_extent()]],
        cursor=toolbar._nav_stack._pos,history=len(toolbar._nav_stack._elements)))

def rectangle(index,out=False):
    fig.canvas.draw();ax=axes[index];b=ax.get_window_extent()
    bounds=ax._prepare_view_from_bbox([b.x0+b.width*.25,b.y0+b.height*.25,b.x0+b.width*.75,b.y0+b.height*.75],direction='out' if out else 'in')
    ax.set_xlim(*bounds[0]);ax.set_ylim(*bounds[1]);toolbar.push_current()
    record('rectangle out' if out else 'rectangle in',dict(kind='rectangle',index=index,out=out))

record('initial');rectangle(0);rectangle(1,out=True)
toolbar.home();record('home',dict(kind='home'))
toolbar.back();record('back from home',dict(kind='navigate',delta=-1))
toolbar.back();record('back again',dict(kind='navigate',delta=-1))
rectangle(1);toolbar.forward();record('forward after branch',dict(kind='navigate',delta=1))
plt.close(fig)
path=Path(__file__).resolve().parents[1]/'docs/portable-navigation-reference.json'
path.write_text(json.dumps(dict(version=matplotlib.__version__,backend=matplotlib.get_backend(),cases=cases),indent=2)+'\n',encoding='utf-8')
print(path)

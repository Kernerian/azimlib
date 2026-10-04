"""Development-only Matplotlib reference for grouped mappable properties.

Records observable final state, not private implementation or signal counts.
Azimlib retains its own batch validation/notifications and list/geographic API.
"""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize,LogNorm
from matplotlib.ticker import FixedLocator
import numpy as np


cases=[]
for kind in ('image','mesh','scatter','vectors'):
    fig,ax=plt.subplots()
    if kind=='image':item=ax.imshow([[1,2],[3,4]],extent=(-54,-44,-26,-18),origin='lower',norm=Normalize(0,10))
    elif kind=='mesh':item=ax.pcolormesh([-54,-49,-44],[-26,-22,-18],[[1,2],[3,4]],norm=Normalize(0,10))
    elif kind=='scatter':item=ax.scatter([-52,-50,-48,-46],[-25,-23,-21,-19],c=[1,2,3,4],norm=Normalize(0,10))
    else:item=ax.quiver([-52,-50,-48,-46],[-25,-23,-21,-19],[1]*4,[1]*4,[1,2,3,4],norm=Normalize(0,10))
    bar=fig.colorbar(item);bar.locator=FixedLocator([0,5,10]);bar.update_ticks()
    locator=bar.locator
    def snapshot(name):
        cases.append(dict(kind=kind,name=name,array=item.get_array().ravel().tolist(),
            norm=type(item.norm).__name__,clim=list(item.get_clim()),cmap=item.cmap.name,
            alpha=item.get_alpha(),visible=item.get_visible(),bar_norm_shared=bar.norm is item.norm,
            locator_retained=bar.locator is locator))
    snapshot('initial')
    values=np.array([[10,20],[30,40]]) if kind in ('image','mesh') else np.array([10,20,30,40])
    plt.setp(item,array=values,cmap='plasma',clim=(0,50),alpha=.6,visible=False)
    snapshot('mapping-batch')
    values=np.array([[1,5],[20,80]]) if kind in ('image','mesh') else np.array([1,5,20,80])
    item.set(array=values,norm=LogNorm(1,100),cmap='viridis',visible=True)
    snapshot('norm-replaced')
    item.cmap='plasma';snapshot('palette-assigned')
    item.set(cmap=None,clim=(2,200));snapshot('default-palette')
    plt.close(fig)
target=Path(__file__).resolve().parents[1]/'docs/mappable-batches-reference.json'
target.write_text(json.dumps(dict(matplotlib=matplotlib.__version__,cases=cases),indent=2),encoding='utf-8')
print(target)

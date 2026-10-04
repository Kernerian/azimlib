"""Development-only hierarchy/allocation oracle using installed Matplotlib/Agg."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

cases=[]
for options in ({},{'wspace':.35,'hspace':.42,'width_ratios':[2,1],'height_ratios':[1,3]}):
    fig=plt.figure();root=fig.add_gridspec(2,2,width_ratios=[1,2],height_ratios=[2,1])
    nested=root[:,1].subgridspec(2,2,**options);deep=nested[1,0].subgridspec(1,2,wspace=.1)
    for name,spec in [('parent',root[:,1]),('first',nested[0,0]),('span',nested[:,1]),('deep first',deep[0,0]),('deep last',deep[0,1])]:
        cases.append(dict(options=options,name=name,bounds=spec.get_position(fig).bounds,
                          params=vars(spec.get_gridspec().get_subplot_params(fig)),
                          top=list(map(int,spec.get_topmost_subplotspec().get_geometry()))))
    plt.close(fig)
fig=plt.figure();root=fig.add_gridspec(1,2,width_ratios=[1,2]);child=root[1].subgridspec(2,1)
axes=[fig.add_subplot(root[0]),fig.add_subplot(child[0]),fig.add_subplot(child[1])]
updates=[]
for name,action in [('initial',lambda:None),('margins',lambda:fig.subplots_adjust(left=.2,right=.95,wspace=.4,hspace=.3)),
                    ('parent weights',lambda:root.set_width_ratios([3,1])),('apply weights',lambda:root.update())]:
    action();updates.append(dict(name=name,positions=[ax.get_position(original=True).bounds for ax in axes]))
plt.close(fig)
mosaics=[]
for layout in ([['A',[['B','C'],['D','C']]]],[[[['A','B']],'C'],['D','D']],
               [['A',[['B', [['C'],['D']]]]]]):
    fig,axes=plt.subplot_mosaic(layout,gridspec_kw={'wspace':.3,'hspace':.4})
    mosaics.append(dict(layout=layout,axes=[dict(key=key,bounds=ax.get_position(original=True).bounds,
                       top=list(map(int,ax.get_subplotspec().get_topmost_subplotspec().get_geometry()))) for key,ax in axes.items()]))
    plt.close(fig)
target=Path(__file__).resolve().parents[1]/'docs/nested-layout-reference.json'
target.write_text(json.dumps(dict(matplotlib_version=matplotlib.__version__,cases=cases,updates=updates,mosaics=mosaics),indent=2),encoding='utf-8')
print(target)

"""Development-only GridSpec reference from installed Matplotlib/Agg."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

cases=[]
selections=[('first',lambda g:g[0]),('last',lambda g:g[-1]),
            ('column',lambda g:g[:,0]),('row',lambda g:g[0,:]),
            ('block',lambda g:g[1:,1:]),('negative',lambda g:g[-1,-2:]),
            ('flat span',lambda g:g[2:5]),('all',lambda g:g[:,:])]
for options in ({},{'width_ratios':[3,1,2],'height_ratios':[1,2]},
                {'left':.18,'right':.86,'bottom':.16,'top':.92,'wspace':.35,'hspace':.42,
                 'width_ratios':[2,3,1],'height_ratios':[4,1]}):
    fig=plt.figure()
    gs=fig.add_gridspec(2,3,**options)
    for name,select in selections:
        spec=select(gs)
        cases.append({'options':options,'selection':name,'geometry':spec.get_geometry(),
                      'rows':list(spec.rowspan),'cols':list(spec.colspan),
                      'bounds':spec.get_position(fig).bounds,
                      'edges':[list(v) for v in gs.get_grid_positions(fig)]})
    plt.close(fig)

fig=plt.figure();gs=fig.add_gridspec(2,3,width_ratios=[3,1,2],height_ratios=[1,2])
axes=[fig.add_subplot(gs[:,0]),fig.add_subplot(gs[0,1:]),fig.add_subplot(gs[1,1:])]
states=[]
def record(name):states.append({'name':name,'positions':[a.get_position(original=True).bounds for a in axes]})
record('initial')
fig.subplots_adjust(left=.2,right=.95,bottom=.08,top=.9,wspace=.4,hspace=.3);record('figure adjustment')
gs.update(left=.25,wspace=.15);record('grid adjustment')
gs.set_width_ratios([1,2,4]);gs.set_height_ratios([2,1]);record('ratios before update')
gs.update();record('ratios applied')
gs.update(left=None,wspace=None);record('overrides reset')
plt.close(fig)

fig=plt.figure()
numeric=[]
for args in ((231,),(2,3,4),(2,3,(2,6))):
    ax=fig.add_subplot(*args);spec=ax.get_subplotspec()
    numeric.append({'args':args,'geometry':spec.get_geometry(),'bounds':ax.get_position(original=True).bounds})
plt.close(fig)
output={'matplotlib_version':matplotlib.__version__,'cases':cases,'updates':states,'numeric':numeric}
target=Path(__file__).resolve().parents[1]/'docs/gridspec-reference.json'
target.write_text(json.dumps(output,ensure_ascii=False,indent=2,default=lambda v:v.item()),encoding='utf-8')
print(f'{target}: {len(cases)} selections, {len(states)} update states, {len(numeric)} numeric selections')

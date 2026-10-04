"""Development-only pyplot lifecycle and flat mosaic oracle from Matplotlib."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

states=[]
def record(name):
    states.append(dict(name=name,numbers=plt.get_fignums(),labels=plt.get_figlabels(),
                       current=plt.gcf().number,label=plt.gcf().get_label(),
                       axes=[a.get_label() for a in plt.gcf().axes],
                       current_axes=plt.gca().get_label() if plt.gcf().axes else None))
plt.close('all')
a=plt.figure(7);a.add_subplot().set_label('A');record('number')
b=plt.figure('atlas');b.add_subplot().set_label('B');record('label')
plt.figure(7);record('reactivate')
c=plt.figure();record('next number')
plt.figure('atlas');record('label reuse')
plt.close(7);record('close inactive')
plt.close('atlas');record('close active')
plt.close('all')
fig,axes=plt.subplots(1,3)
for ax,label in zip(axes,['A','B','C']):ax.set_label(label)
current=[]
def selected(name):current.append(dict(name=name,axes=[a.get_label() for a in fig.axes],active=fig.gca().get_label()))
selected('created');fig.sca(axes[0]);selected('first');fig.sca(axes[1]);selected('second')
axes[1].remove();selected('removed second');axes[0].remove();selected('removed first')
plt.close('all')
cases=[]
for layout in ('AA;BC','A.;BB',[['country','country'],['state','detail']],[['A',0],[None,'B']]):
    for options in ({},{'width_ratios':[2,1],'height_ratios':[1,2],'gridspec_kw':{'wspace':.3,'hspace':.4}}):
        fig,axes=plt.subplot_mosaic(layout,**options)
        cases.append(dict(layout=layout,options=options,
                          axes=[dict(key=key,label=ax.get_label(),bounds=ax.get_position(original=True).bounds,
                                     geometry=[int(v) for v in ax.get_subplotspec().get_geometry()]) for key,ax in axes.items()]))
        plt.close(fig)
target=Path(__file__).resolve().parents[1]/'docs/figure-state-reference.json'
target.write_text(json.dumps(dict(matplotlib_version=matplotlib.__version__,states=states,selection=current,mosaics=cases),indent=2),encoding='utf-8')
print(target)

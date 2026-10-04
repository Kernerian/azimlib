"""Development-only Matplotlib oracle for norm signals and data/view limits."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize,TwoSlopeNorm
from matplotlib.cm import ScalarMappable

norm=Normalize(0,10);first=ScalarMappable(norm);second=ScalarMappable(norm)
events=[]
for name,mapping in (('first',first),('second',second)):
    mapping.callbacks.connect('changed',lambda m,name=name:events.append([name,list(m.get_clim()),bool(m.norm.clip)]))
norm.vmax=20;norm.vmax=20
norm.clip=True;norm.clip=True
first.set_clim(30,50)
first.set_norm(Normalize(-1,1));first.norm=first.norm
norm.vmax=60
signal_protocol=events
norm=Normalize(0,10);mapping=ScalarMappable(norm)
mapping.set_array([32,35,45]);events=[]
mapping.callbacks.connect('changed',lambda m:events.append(list(m.get_clim())))
mapping.autoscale()
slope=TwoSlopeNorm(0,-2,5);slope.vcenter=1
normalization=dict(signals=signal_protocol,autoscale=events,
                   slope=[float(v) for v in slope([-2,0,1,3,5])])

fig,ax=plt.subplots();line,=ax.plot([-52,-48],[-25,-21])
cases=[]
def snapshot(name):
    cases.append(dict(name=name,extent=[*ax.get_xlim(),*ax.get_ylim()],
                      flags=[ax.get_autoscalex_on(),ax.get_autoscaley_on()],margins=list(ax.margins())))
snapshot('initial')
line.set_data([-50,-42],[-24,-18]);snapshot('edit-preserves-view')
ax.relim();snapshot('relim-preserves-view')
ax.autoscale_view();snapshot('fit-edited-data')
ax.set_xlim(-54,-44)
line.set_data([-50,-40],[-24,-16]);ax.relim();ax.autoscale_view();snapshot('manual-x-auto-y')
ax.autoscale(axis='x',tight=True);snapshot('tight-x')
ax.margins(x=.1,y=-.1);snapshot('positive-and-negative-margins')
ax.autoscale(False,tight=True);snapshot('disabled')
hidden,=ax.plot([-60,-55],[-32,-28]);hidden.set_visible(False)
ax.relim(visible_only=True);ax.autoscale(tight=True);snapshot('visible-only')
plt.close(fig)
target=Path(__file__).resolve().parents[1]/'docs/norm-limits-reference.json'
target.write_text(json.dumps(dict(matplotlib=matplotlib.__version__,backend='Agg',normalization=normalization,limits=cases),indent=2)+'\n',encoding='utf-8')
print(target)

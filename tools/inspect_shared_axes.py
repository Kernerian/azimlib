"""Development oracle only: installed Matplotlib, never a runtime dependency."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator,FixedFormatter

cases=[]
for sx in (False,True,'all','none','row','col'):
    for sy in (False,True,'all','none','row','col'):
        fig,axes=plt.subplots(2,3,sharex=sx,sharey=sy)
        flat=list(axes.flat)
        cases.append(dict(sharex=sx,sharey=sy,
            xgroups=[[i for i,b in enumerate(flat) if a.get_shared_x_axes().joined(a,b)] for a in flat],
            ygroups=[[i for i,b in enumerate(flat) if a.get_shared_y_axes().joined(a,b)] for a in flat],
            labels=[[bool(a.xaxis.get_major_ticks()[0].label1.get_visible()),bool(a.yaxis.get_major_ticks()[0].label1.get_visible())] for a in flat]))
        plt.close(fig)
fig,axes=plt.subplots(2,2,sharex='col',sharey='row')
axes[0,0].plot([1,2],[3,4]);axes[1,0].plot([8,9],[20,30]);fig.canvas.draw()
data=[dict(x=list(a.get_xlim()),y=list(a.get_ylim())) for a in axes.flat]
axes[0,0].set_autoscalex_on(False)
flags_local=[a.get_autoscalex_on() for a in axes.flat]
axes[0,0].set_xlim(0,12)
flags_limits=[a.get_autoscalex_on() for a in axes.flat]
plt.close(fig)
fig,axes=plt.subplot_mosaic([['A',[['B','C'],['D','E']]]],sharex=True,sharey=True)
nested={key:[bool(a.xaxis.get_major_ticks()[0].label1.get_visible()),bool(a.yaxis.get_major_ticks()[0].label1.get_visible())] for key,a in axes.items()}
plt.close(fig)
result=dict(version=matplotlib.__version__,backend=matplotlib.get_backend(),cases=cases,data=data,
            flags_local=flags_local,flags_limits=flags_limits,nested=nested)
path=Path(__file__).resolve().parents[1]/'docs/shared-axes-reference.json'
path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(path)

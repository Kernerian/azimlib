"""Development-only final-state reference using installed Matplotlib/Agg."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


fig,ax=plt.subplots()
line,=ax.plot([-52,-48,-44],[-25,-22,-20],color='red',marker='o',label='Route')
line_cases=[]
def snapshot(name):
    keys=('color','linewidth','linestyle','marker','markersize','markerfacecolor',
          'markeredgecolor','markeredgewidth','solid_capstyle','dash_capstyle',
          'solid_joinstyle','dash_joinstyle','antialiased','alpha','visible','label')
    line_cases.append(dict(name=name,data=[[float(v) for v in line.get_xdata()],[float(v) for v in line.get_ydata()]],
                           **{key:getattr(line,'get_'+key)() for key in keys}))
snapshot('initial')
plt.setp(line,data=([-51,-47,-43],[-26,-23,-19]),color='blue',linewidth=.9,
         linestyle='--',marker='s',markersize=4,markerfacecolor='white',
         markeredgecolor='black',markeredgewidth=.4,solid_capstyle='butt',
         dash_capstyle='round',solid_joinstyle='miter',dash_joinstyle='bevel',
         antialiased=False,alpha=.7,visible=False,label='Edited route')
snapshot('grouped')
line.set(xdata=[-50,-46,-42],ydata=[-25,-22,-18],marker='None',linestyle='None',
         markerfacecolor='auto',markeredgecolor='auto',alpha=None,visible=True)
snapshot('no-symbols')
line.set_data([],[]);snapshot('empty')
plt.close(fig)

fig,ax=plt.subplots()
contour=ax.contour([-54,-49,-44],[-26,-22,-18],[[0,1,2]]*3,
                   levels=[.5,1.5],linewidths=[.4,.8])
contour_cases=[]
def contour_snapshot(name):
    contour_cases.append(dict(name=name,levels=contour.levels.tolist(),array=contour.get_array().tolist(),
        linewidths=contour.get_linewidths().tolist(),alpha=contour.get_alpha(),
        visible=contour.get_visible(),clim=[float(v) for v in contour.get_clim()],cmap=contour.cmap.name))
contour_snapshot('initial')
contour.set(linewidth=[1,2],linestyle=['--',':'],alpha=.5,cmap='plasma',clim=(0,2))
contour_snapshot('grouped')
labels=ax.clabel(contour,levels=[.5,1.5],fmt={.5:'Low',1.5:'High'},inline=False)
label_protocol=dict(is_list=isinstance(labels,list),texts=[label.get_text() for label in labels])
plt.setp(labels,fontsize=9,color='black')
labels[0].set_text('Edited');labels[1].set_visible(False)
label_protocol.update(texts_after=[label.get_text() for label in labels],
    visibility_after=[label.get_visible() for label in labels],fontsize=[label.get_fontsize() for label in labels])
contour.set_visible(False)
label_protocol['visibility_after_hidden_contour']=[label.get_visible() for label in labels]
contour_snapshot('hidden')
contour.remove()
label_protocol['removed_with_contour']=all(label.axes is None and label.get_figure() is None for label in labels)
plt.close(fig)
target=Path(__file__).resolve().parents[1]/'docs/lines-contours-reference.json'
target.write_text(json.dumps(dict(matplotlib=matplotlib.__version__,lines=line_cases,
    contours=contour_cases,label_protocol=label_protocol),indent=2),encoding='utf-8')
print(target)

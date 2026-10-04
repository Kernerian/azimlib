"""Development-only Matplotlib oracle; the library/tests never import it."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

fig,ax=plt.subplots();line,=ax.plot([-52,-48,-44],[-25,-22,-20])
fig.canvas.draw()
protocol={'after_draw':[line.stale,ax.stale,fig.stale]}
line.set_visible(False);protocol['after_edit']=[line.stale,ax.stale,fig.stale]
line.stale=False;protocol['after_child_clean']=[line.stale,ax.stale,fig.stale]
line.set_alpha(None);protocol['alpha_none']=line.get_alpha()
title=ax.set_title('A');protocol['title_reused']=title is ax.set_title('B')
line.remove();protocol['removed_figure']=line.get_figure() is None
target=Path(__file__).resolve().parents[1]/'docs/artist-reference.json'
target.write_text(json.dumps({'matplotlib':matplotlib.__version__,'backend':'Agg','protocol':protocol},indent=2)+'\n',encoding='utf-8')
plt.close(fig);print(target)

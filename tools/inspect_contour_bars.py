"""Development-only contours/colorbars/inline defaults from Matplotlib/Agg."""
import inspect,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm,NoNorm
from matplotlib.contour import ContourLabeler


cases=[]
for kind in ('mapped','explicit','log'):
    for orientation in ('vertical','horizontal'):
        for spacing in ('uniform','proportional'):
            fig,ax=plt.subplots()
            options=dict(levels=[.2,.7,1.8],linewidths=[.4,.8,1.2])
            z=[[0,1,2]]*3
            if kind=='explicit':options['colors']=['red','blue']
            if kind=='log':options.update(levels=[1,10,100],norm=LogNorm(1,100));z=[[1,10,100]]*3
            cs=ax.contour([0,1,2],[0,1,2],z,**options)
            bar=fig.colorbar(cs,orientation=orientation,spacing=spacing);fig.canvas.draw()
            positions=[]
            for value in cs.levels:
                point=(.5,value) if orientation=='vertical' else (value,.5)
                pos=bar.ax.transAxes.inverted().transform(bar.ax.transData.transform(point))
                positions.append(float(pos[1 if orientation=='vertical' else 0]))
            cases.append(dict(kind=kind,orientation=orientation,spacing=spacing,
                array=[float(v) for v in cs.get_array()],norm=type(cs.norm).__name__,
                clim=[float(v) for v in cs.get_clim()],boundaries=bar.boundaries.tolist(),
                values=[float(v) for v in bar.values],ticks=bar.get_ticks().tolist(),positions=positions,
                linewidths=[float(v) for v in bar.lines[0].get_linewidths()],solids=bar.solids is not None))
            plt.close(fig)
signature=inspect.signature(ContourLabeler.clabel)
defaults={key:signature.parameters[key].default for key in ('inline','inline_spacing')}
target=Path(__file__).resolve().parents[1]/'docs/contour-bars-reference.json'
target.write_text(json.dumps(dict(matplotlib=matplotlib.__version__,cases=cases,
    defaults=defaults,no_norm=[NoNorm()(v) for v in (-1,0,1,2)]),indent=2),encoding='utf-8')
print(target)

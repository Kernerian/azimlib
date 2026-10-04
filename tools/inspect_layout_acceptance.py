"""Development-only direct Agg reference for colorbar padding/manual globals."""
import json,hashlib
from pathlib import Path
import azimlib as azl
from azimlib.scene import Text
from azimlib.layout_engine import primitive_bounds,union_bounds

ROOT=Path(__file__).resolve().parents[1]


def inspect(module,*,native=False):
    if native:
        from matplotlib.colors import Normalize
        from matplotlib.cm import ScalarMappable
    else:
        from azimlib.colors import Normalize
        from azimlib.cm import ScalarMappable
    rows=[]
    for location in ('left','right','top','bottom'):
        for rotation in (0,35,75):
            for dpi in (100,200):
                fig,ax=module.subplots(figsize=(6,6),dpi=dpi,layout='constrained')
                ax.set_xlim(-54,-42);ax.set_ylim(-28,-16)
                bar=fig.colorbar(ScalarMappable(norm=Normalize(0,100)),ax=ax,location=location)
                bar.set_ticks([0,50,100],labels=['Baixo','Médio','Muito alto'],rotation=rotation)
                bar.set_label('Índice sintético',fontsize=14,labelpad=8)
                if native:
                    fig.canvas.draw();renderer=fig.canvas.get_renderer()
                    ticks=[label.get_window_extent(renderer) for label in (bar.ax.get_yticklabels() if location in ('left','right') else bar.ax.get_xticklabels())]
                    label=(bar.ax.yaxis.label if location in ('left','right') else bar.ax.xaxis.label).get_window_extent(renderer)
                    gap={'left':min(b.x0 for b in ticks)-label.x1,'right':label.x0-max(b.x1 for b in ticks),
                         'top':label.y0-max(b.y1 for b in ticks),'bottom':min(b.y0 for b in ticks)-label.y1}[location]
                else:
                    items=[p for p in fig.to_scene().items if isinstance(p,Text)]
                    ticks=union_bounds(primitive_bounds(p) for p in items if p.text in ('Baixo','Médio','Muito alto'))
                    label=next(primitive_bounds(p) for p in items if p.text=='Índice sintético')
                    gap={'left':ticks[0]-label[0]-label[2],'right':label[0]-ticks[0]-ticks[2],
                         'top':ticks[1]-label[1]-label[3],'bottom':label[1]-ticks[1]-ticks[3]}[location]
                rows.append(dict(location=location,rotation=rotation,dpi=dpi,labelpad=bar.ax.yaxis.labelpad if native and location in ('left','right') else bar.ax.xaxis.labelpad if native else bar.labelpad,gap_points=round(gap*72/dpi,8)))
                module.close(fig)
    fig,ax=module.subplots(figsize=(6,6),layout='constrained')
    x=fig.supxlabel('Longitude',x=.4,y=.015);y=fig.supylabel('Latitude',x=.015,y=.4)
    fig.canvas.draw()
    manual=[list(x.get_position()),list(y.get_position())]
    module.close(fig)
    fig,ax=module.subplots(figsize=(6,6),layout='constrained')
    x=fig.supxlabel('Longitude');y=fig.supylabel('Latitude')
    x.set_position((.4,.015));y.set_position((.015,.4))
    fig.canvas.draw()
    setters=[list(x.get_position()),list(y.get_position())]
    module.close(fig)
    return dict(padding=rows,explicit_global_positions=manual,automatic_globals_after_position_setter=setters)


if __name__=='__main__':
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    reference=inspect(plt,native=True);own=inspect(azl)
    assert all(a['labelpad']==b['labelpad'] and a['gap_points']>0 and b['gap_points']>0 for a,b in zip(own['padding'],reference['padding']))
    assert all(a==b for a,b in zip(own['padding'],reference['padding']) if a['location']!='top')
    assert own['explicit_global_positions']==reference['explicit_global_positions']
    report=dict(matplotlib=matplotlib.__version__,reference=reference,azimlib=own,
                tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                scope='24 labelpad values and explicit Figure label coordinates match. 18 physical gap states match; top has native baseline/descent difference (recorded). No all-pixel equality.')
    (ROOT/'docs/layout-acceptance-reference.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('24 labelpad controls/18 physical gaps and explicit Figure coordinates match; top baseline difference recorded')

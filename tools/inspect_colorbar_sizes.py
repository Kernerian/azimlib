"""Development-only colorbar dimensions against installed Matplotlib Agg."""
import json
from pathlib import Path
import azimlib as azl
from azimlib.scene import Rect

ROOT=Path(__file__).resolve().parents[1]


def inspect(module,location,layout,shrink):
    fig,ax=module.subplots(figsize=(6.4,4.8),layout=layout)
    try:
        ax.set_xlim(-54,-42);ax.set_ylim(-28,-16)
        if module is not azl:ax.set_aspect('equal')
        ax.set_xlabel('Longitude');ax.set_ylabel('Latitude');ax.set_title('Colorbar')
        point=ax.scatter([-52,-48,-44],[-26,-22,-18],c=[0,1,2],cmap='viridis',s=36)
        bar=fig.colorbar(point,ax=ax,location=location,shrink=shrink,label='Valor')
        if module is azl:
            scene=fig.to_scene()
            cells=[p for p in scene.items if isinstance(p,Rect) and p.style.get('shape_rendering')=='crispEdges']
            x=min(p.x for p in cells);y=min(p.y for p in cells)
            return [x,y,max(p.x+p.width for p in cells)-x,max(p.y+p.height for p in cells)-y]
        fig.canvas.draw();b=bar.ax.get_window_extent()
        return [b.x0,fig.get_figheight()*fig.dpi-b.y1,b.width,b.height]
    finally:module.close(fig)


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as mpl
    cases=[]
    for location in ('left','right','top','bottom'):
        for layout in (None,'constrained'):
            for shrink in (1,.75):
                own=inspect(azl,location,layout,shrink);reference=inspect(mpl,location,layout,shrink)
                cases.append(dict(location=location,layout=layout,shrink=shrink,azimlib_box=own,matplotlib_box=reference,
                                  size_difference_pixels=[own[i]-reference[i] for i in (2,3)]))
    report=dict(matplotlib=matplotlib.__version__,dpi=100,figsize=[6.4,4.8],fraction=.15,aspect=20,cases=cases,
                scope='Actual gradient dimensions; own constrained layout can reserve different decoration space. No pixel equality claim.')
    (ROOT/'docs/colorbar-size-reference.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for case in cases:print(case['location'],case['layout'],case['shrink'],case['size_difference_pixels'])


if __name__=='__main__':main()

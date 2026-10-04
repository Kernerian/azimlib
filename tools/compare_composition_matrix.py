"""Own composition versus actual Matplotlib Axes, across sizes/DPI/layouts."""
import argparse,importlib.util,json,platform,warnings
from pathlib import Path
import azimlib as azl
from azimlib.layout_engine import item_bounds

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('composition_examples',ROOT/'examples/composition_matrix.py')
example=importlib.util.module_from_spec(spec);spec.loader.exec_module(example)


def inspect(module,kind,layout,size,dpi):
    fig,axes,bar=example.build(kind,layout,size,dpi,module=module)
    try:
        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter('always')
            if module is azl:
                scene=fig.to_scene();boxes=[item_bounds(scene,start,end) for _,start,end,_ in scene._layout_groups]
                boxes=[*boxes,*[getattr(scene,'_layout'+slot) for slot in ('_suptitle','_supxlabel','_supylabel')]]
                width,height=scene.width,scene.height
                positions=[list(ax.position) for ax in axes]
            else:
                fig.canvas.draw();renderer=fig.canvas.get_renderer();width,height=fig.get_size_inches()*dpi
                raw=[ax.get_tightbbox(renderer) for ax in axes]
                raw += [a.get_window_extent(renderer) for a in (fig._suptitle,fig._supxlabel,fig._supylabel)]
                raw += [bar.ax.get_tightbbox(renderer)]
                boxes=[(b.x0,height-b.y1,b.width,b.height) for b in raw]
                positions=[list(ax.get_position().bounds) for ax in axes]
        # Raw pixel boxes are retained; logical bounds permit DPI comparisons.
        boxes=[list(b) for b in boxes if b is not None]
        overflow=max([0.]+[max(-x,-y,x+w-width,y+h-height) for x,y,w,h in boxes])
        return dict(canvas=[float(width),float(height)],positions=positions,
                    logical_bounds=[[float(v*100/dpi) for v in b] for b in boxes],
                    overflow_logical=float(overflow*100/dpi),warnings=[str(w.message) for w in recorded],error=None)
    except Exception as error:
        return dict(error=dict(type=type(error).__name__,message=str(error)))
    finally:module.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'docs/composition-matrix-reference.json')
    args=parser.parse_args()
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as mpl
    report=dict(matplotlib=matplotlib.__version__,python=platform.python_version(),platform=platform.platform(),
        notes=['54 paired configurations, synthetic polygons/station values; actual Matplotlib Axes, no GIS backend.',
               'Own examples explicitly add scale/north; Matplotlib has no corresponding core ornament.',
               'Each own box uses emitted primitives; reference uses native tight bboxes. Bounds and solvers differ.',
               'No pixel-identity/latency claim. Raw logical bounds and warnings retained.'],cases=[])
    for kind,sizes in example.SIZES.items():
        for layout in ('tight','constrained'):
            for size in sizes:
                for dpi in (100,150,200):
                    row=dict(kind=kind,layout=layout,size=list(size),dpi=dpi,
                             azimlib=inspect(azl,kind,layout,size,dpi),matplotlib=inspect(mpl,kind,layout,size,dpi))
                    report['cases'].append(row)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Paired cases:',len(report['cases']))
    for name in ('azimlib','matplotlib'):
        complete=[c[name] for c in report['cases'] if not c[name]['error']]
        print(name,'errors:',len(report['cases'])-len(complete),'warnings:',sum(bool(c['warnings']) for c in complete),
              'maximum logical overflow:',max([0]+[c['overflow_logical'] for c in complete]))


if __name__=='__main__':main()

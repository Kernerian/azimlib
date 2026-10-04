"""Direct development-only Matplotlib Text reference; own production layout."""
import hashlib,itertools,json
from pathlib import Path
from azimlib.scene import Scene
from azimlib.styles import text_style
from azimlib.render_map import _text
from azimlib.layout_engine import item_bounds

ROOT=Path(__file__).resolve().parents[1]


def own(case):
    scene=Scene(400,400)
    _text(scene,200,200,case['text'],text_style({key:case[key] for key in ('fontsize','rotation','rotation_mode','ha','va')}))
    x,y,w,h=item_bounds(scene)
    return [x-200,y-200,w,h]


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig=plt.figure(figsize=(4,4),dpi=100);fig.canvas.draw();renderer=fig.canvas.get_renderer()
    rows=[]
    try:
        for mode,angle,ha,va,value in itertools.product(('default','anchor','xtick','ytick'),
                (0,35,90,135,180,225,300,-35),('left','center','right'),('top','center','bottom','baseline'),
                ('Latitude','Título\nFoco')):
            case=dict(fontsize=12,rotation=angle,rotation_mode=mode,ha=ha,va=va,text=value)
            text=fig.text(.5,.5,value,fontfamily='DejaVu Sans',**{k:v for k,v in case.items() if k!='text'})
            box=text.get_window_extent(renderer);native=[float(box.x0-200),float(200-box.y1),float(box.width),float(box.height)]
            text.remove();actual=own(case);error=max(abs(a-b) for a,b in zip(native,actual))
            rows.append(dict(case=case,matplotlib=native,azimlib=actual,max_error_pixels=error))
    finally:plt.close(fig)
    report=dict(matplotlib=matplotlib.__version__,dpi=100,cases=rows,max_error_pixels=max(r['max_error_pixels'] for r in rows),
                tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                scope='768 Latin/DejaVu text bounds: four rotation modes, eight angles, three horizontal and four vertical alignments, one/two lines. Own font advances are fractional; Agg rounds some glyph advances. Not MathText/TeX/shaping or pixel identity.')
    (ROOT/'docs/text-rotation-reference.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Cases:',len(rows),'max bbox difference:',report['max_error_pixels'],'pixels at 100 DPI')


if __name__=='__main__':main()

"""Dev-only style/clip matrices: the same own Scene rasterized by own PNG/Agg.

Not an independent Matplotlib Axes/layout/hatch-engine comparison. Matplotlib
is a direct reference only here, never a runtime/backend dependency of Azimlib.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path as FilePath
import platform
import sys
from PIL import Image,ImageDraw,ImageChops,__version__ as pillow_version
import matplotlib
import azimlib as azl
from azimlib.scene import Scene,Rect,Path,Circle,Text
from azimlib.renderers import render_png,render_svg
from compare_map_quality import reference,differences

ROOT=FilePath(__file__).resolve().parents[1]

def strokes():
    scene=Scene(720,520)
    scene.add(Text(360,27,'Traços: larguras físicas, extremidades e junções',dict(anchor='middle',font_size=17,fill='black')))
    for row,cap in enumerate(('butt','round','square')):
        for col,join in enumerate(('miter','round','bevel')):
            x,y=18+col*234,52+row*148
            scene.add(Rect(x,y,218,134,dict(fill='#f8f8f8',stroke='#aaaaaa',stroke_width=.5)))
            scene.add(Text(x+8,y+18,f'{cap} / {join}',dict(font_size=11,fill='black')))
            for i,width in enumerate((.25,.5,1.5)):
                points=[(x+13,y+35+i*27),(x+54,y+29+i*27),(x+101,y+51+i*27),(x+150,y+28+i*27),(x+204,y+42+i*27)]
                scene.add(Path([points],style=dict(stroke=('#1f77b4','#d62728','#222222')[i],stroke_width=width*100/72,
                    linecap=cap,linejoin=join,dash=None if i==0 else [5,2] if i==1 else [1.2,1.8,5,2],opacity=.75 if i==1 else 1)))
            scene.add(Text(x+8,y+125,'0.25 / 0.5 / 1.5 pt · sólido / dashes',dict(font_size=9,fill='#444444')))
    scene.add(Text(360,510,'Mesma geometria de tela nos dois rasterizadores',dict(anchor='middle',font_size=10,fill='#555555')))
    return scene

def clipping():
    scene=Scene(720,520)
    scene.add(Text(360,27,'Recortes fracionários: traços, buracos, texto e alpha',dict(anchor='middle',font_size=16,fill='black')))
    labels=('traço fino','caps + tracejado','buraco + alpha','texto rotacionado','marcadores','z-order + alpha')
    for i,label in enumerate(labels):
        x,y=18+(i%3)*234,60+(i//3)*218
        clip=(x+12.3,y+27.7,193.4,157.8)
        scene.add(Text(x+12,y+16,label,dict(font_size=12,fill='black')))
        scene.add(Rect(*clip,dict(fill='#f4f4f4',stroke='#999999',stroke_width=.5)))
        if i in (0,1):
            points=[(x-40,y+60),(x+44,y+47),(x+70,y+151),(x+144,y+61),(x+270,y+127)]
            scene.add(Path([points],style=dict(stroke='#1f77b4',stroke_width=.4 if i==0 else 2.5,linecap='round',
                linejoin='miter',dash=None if i==0 else [7,3]),clip=clip))
        elif i==2:
            scene.add(Path([[(x-5,y+16),(x+221,y+18),(x+220,y+201),(x-4,y+190)],
                            [(x+56,y+66),(x+56,y+132),(x+151,y+132),(x+151,y+66)]],True,
                dict(fill='#ffcc00',stroke='#224466',stroke_width=1.2,opacity=.55),clip=clip))
        elif i==3:
            scene.add(Text(x+106,y+120,'São Paulo · 20°',dict(anchor='middle',font_size=25,rotation=31,fill='#115577',
                background='#ffeebb88',stroke='white',stroke_width=2,opacity=.8),clip=clip))
        elif i==4:
            for j in range(8):
                scene.add(Circle(x+8+j*29,y+52+j*17,2+j,dict(fill='#d6272880',stroke='#222222',stroke_width=.6),clip=clip))
        else:
            scene.add(Rect(x-4,y+50,153,126,dict(fill='#1f77b4',stroke='black',stroke_width=2,opacity=.45),clip=clip))
            scene.add(Rect(x+70,y+12,144,132,dict(fill='#ffcc00',stroke='#d62728',stroke_width=3,opacity=.55),clip=clip))
    scene.add(Text(360,510,'Molduras cinzas mostram limites; clip retangular em coordenadas de tela',dict(anchor='middle',font_size=10,fill='#555555')))
    return scene

def create(name,dpi):
    if name=='hatches':
        sys.path.insert(0,str(ROOT/'examples'))
        from scientific import hatch_catalog
        fig=hatch_catalog();fig.dpi=dpi
        try:return fig.to_scene(cull=True)
        finally:azl.close(fig)
    return (strokes() if name=='strokes' else clipping()).scaled(dpi/100)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases',nargs='+',choices=('strokes','clipping','hatches'),default=['strokes','clipping','hatches'])
    parser.add_argument('--dpi',nargs='+',type=int,default=[100,150,200])
    parser.add_argument('--output',type=FilePath,default=ROOT/'docs/style-quality.json')
    parser.add_argument('--gallery',type=FilePath,default=ROOT/'gallery')
    args=parser.parse_args()
    if any(v<1 for v in args.dpi):parser.error('dpi must be positive')
    folder=ROOT/'src/azimlib/renderers'
    report=dict(python=platform.python_version(),platform=platform.platform(),pillow=pillow_version,
        matplotlib=matplotlib.__version__,azimlib=azl.__version__,
        renderer_source_sha256={n:hashlib.sha256((folder/n).read_bytes()).hexdigest() for n in ('coverage.py','pillow.py')},
        notes=['Same own Scene/physical sizes/fonts sent to both rasterizers, not independent Matplotlib Axes/layout/cartography.',
               'Hatch paths are composed by Azimlib; this does not compare spacing/shapes against Matplotlib native hatch generation.',
               'Fractional clips, hinted text, supersampling, cap/join/dash rasterization can differ. No pixel equality/perceptual score claimed.',
               'Text halo is vector outline under hinted fill in the dev adapter; complex self-intersecting even-odd paths are outside its contract.',
               'Diagnostic image comparison only, not a timing/memory benchmark.'],cases=[])
    args.gallery.mkdir(parents=True,exist_ok=True)
    for name in args.cases:
        for dpi in args.dpi:
            scene=create(name,dpi);buffer=io.BytesIO();render_png(scene,buffer)
            own=Image.open(buffer).convert('RGBA');agg=reference(scene,dpi);prefix=f'style-quality-{name}-{dpi}'
            own.save(args.gallery/f'{prefix}-azimlib.png');agg.save(args.gallery/f'{prefix}-agg.png')
            (args.gallery/f'{prefix}.svg').write_text(render_svg(scene),encoding='utf-8')
            canvas=Image.new('RGB',(own.width*2,own.height+30),'white');canvas.paste(own,(0,30));canvas.paste(agg,(own.width,30))
            draw=ImageDraw.Draw(canvas);draw.text((10,8),f'Azimlib / own PNG / {dpi} DPI',fill='black')
            draw.text((own.width+10,8),f'Same Scene -> Matplotlib {matplotlib.__version__} / Agg',fill='black')
            canvas.save(args.gallery/f'{prefix}-comparison.png')
            ImageChops.difference(own.convert('RGB'),agg.convert('RGB')).save(args.gallery/f'{prefix}-difference.png')
            entry=dict(name=name,dpi=dpi,pixels=list(own.size),items=len(scene.items),metrics=differences(own,agg),
                png_sha256={key:hashlib.sha256((args.gallery/f'{prefix}-{suffix}.png').read_bytes()).hexdigest() for key,suffix in (('azimlib','azimlib'),('agg','agg'))},
                files=dict(comparison=f'{prefix}-comparison.png',svg=f'{prefix}.svg'))
            report['cases'].append(entry);args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
            print(f'{name} {dpi}: {entry["metrics"]}',flush=True)

if __name__=='__main__':main()

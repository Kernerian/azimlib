"""Development-only visual reference, independently authored from common inputs.

Matplotlib is optional here, never imported by Azimlib. No reference code,
icons or image assets are copied. Both compositions use the same original
routes, Natural Earth geometry and the licensed bundled DejaVu font.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import azimlib as azl

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=True)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as mpl
    from matplotlib.font_manager import FontProperties
    from azimlib.typography import font_path
    font=FontProperties(fname=str(font_path({})))
    points=[(-52,-25),(-50,-24.5),(-48,-23),(-46,-21.5),(-44,-20)]
    def configure(a):
        a.set_xlim(-54,-42);a.set_ylim(-28,-16)
        if hasattr(a,'set_aspect'):a.set_aspect('equal')  # Azimlib map aspect is always geographic/equal.
        a.set_title('Paths and cartographic context',fontsize=12,pad=6)
        a.set_xlabel('Longitude',labelpad=4);a.set_ylabel('Latitude',labelpad=4)
        a.set_xticks([-54,-52,-50,-48,-46,-44,-42]);a.set_yticks([-28,-26,-24,-22,-20,-18,-16])
        if isinstance(a,azl.MapAxes):
            a.xaxis.set_major_formatter(azl.ticker.ScalarFormatter())
            a.yaxis.set_major_formatter(azl.ticker.ScalarFormatter())
        a.grid(True,color='#d0d0d0',linewidth=.5,linestyle='--')
        for color,marker,ls,dy,label in (('#d34c46','o','-',0,'Route A'),('#9360a8','D','--',1.5,'Route B'),('#258bb0','^',':',3,'Route C')):
            a.plot([p[0] for p in points],[p[1]+dy for p in points],color=color,marker=marker,markersize=5,linewidth=1,linestyle=ls,label=label)
        a.legend(loc='upper left',fontsize=9,framealpha=.8)
    own,a=azl.subplots(figsize=(6.4,4.8),dpi=120);a.states(facecolor='#f1f2f3',edgecolor='#9ba4ab',linewidth=.4)
    configure(a)
    for ext in ('png','svg','pdf'):own.savefig(out/f'azimlib-reference.{ext}')
    ref,r=mpl.subplots(figsize=(6.4,4.8),dpi=120)
    # Only geographic coordinates are shared; no cartographic renderer used.
    layer=a.layers[0]
    for feature in layer.data:
        g=feature.geometry
        if g is None:continue
        polygons=[g.coordinates] if g.type=='Polygon' else g.coordinates
        for polygon in polygons:
            xs,ys=zip(*[p[:2] for p in polygon[0]])
            r.fill(xs,ys,facecolor='#f1f2f3',edgecolor='#9ba4ab',linewidth=.4)
    configure(r)
    for text in (r.title,r.xaxis.label,r.yaxis.label,*r.get_xticklabels(),*r.get_yticklabels(),*r.get_legend().get_texts()):
        size=text.get_fontsize();text.set_fontproperties(font);text.set_fontsize(size)
    ref.savefig(out/'matplotlib-reference.png');mpl.close(ref);azl.close(own)
    from PIL import Image,ImageDraw,ImageFont
    first=Image.open(out/'azimlib-reference.png').convert('RGB');second=Image.open(out/'matplotlib-reference.png').convert('RGB')
    canvas=Image.new('RGB',(first.width+second.width,first.height+30),'white');canvas.paste(first,(0,30));canvas.paste(second,(first.width,30))
    draw=ImageDraw.Draw(canvas);fnt=ImageFont.truetype(str(font_path({})),14)
    draw.text((10,8),'Azimlib / own renderer',fill='black',font=fnt);draw.text((first.width+10,8),f'Matplotlib {matplotlib.__version__} / Agg (reference only)',fill='black',font=fnt)
    canvas.save(out/'finishing-comparison.png');first.close();second.close();canvas.close()
    names=('finishing-comparison.png','azimlib-reference.png','matplotlib-reference.png')
    report=dict(schema_version=1,reference_version=matplotlib.__version__,runtime_version=azl.__version__,
        scope='Common simple cartographic paths, markers, legend, titles, grid and axis labels at 120 DPI; visual comparison, not pixel equality or full API parity.',
        provenance=['Original synthetic routes and composition, BSD-3-Clause','Natural Earth administrative geometry, public domain','Bundled DejaVu font; font notice shipped','Matplotlib used only to generate development reference; no source/assets copied'],
        files={name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in names})
    (out/'reference-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()

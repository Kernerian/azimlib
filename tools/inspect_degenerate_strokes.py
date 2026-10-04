"""Development-only direct Agg/SVG comparison of collapsed line and markers."""
import argparse
import io
import json
from pathlib import Path
import platform
import xml.etree.ElementTree as ET
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as mpl
from PIL import Image
import azimlib as azl

def red_count(stream):
    stream.seek(0)
    with Image.open(stream) as source:
        with source.convert('RGB') as image:
            return sum(image.getpixel((x,y))[0]>180 and image.getpixel((x,y))[1]<100 and image.getpixel((x,y))[2]<100
                       for y in range(image.height) for x in range(image.width))

def inspect():
    cases=[]
    for cap in ('butt','round','projecting'):
        for count in (1,2,4):
            for marker in ('None','o'):
                record=dict(cap=cap,count=count,marker=marker)
                for mode,library in (('matplotlib',mpl),('azimlib',azl)):
                    fig,ax=library.subplots(figsize=(2,2),dpi=100)
                    try:
                        ax.set_xlim(-1,1);ax.set_ylim(-1,1)
                        ax.plot([0]*count,[0]*count,color='red',linewidth=6,solid_capstyle=cap,marker=marker)
                        png=io.BytesIO();svg=io.StringIO();fig.savefig(png,format='png');fig.savefig(svg,format='svg')
                        paths=[node.attrib.get('d','') for node in ET.fromstring(svg.getvalue()).iter()
                               if node.tag.endswith('path') and ('#ff0000' in node.attrib.get('style','') or node.attrib.get('stroke')=='red')]
                        record[mode]=dict(red_pixels=red_count(png),line_visible=red_count(png)>0,red_svg_paths=paths)
                    finally:library.close(fig)
                assert record['matplotlib']['line_visible']==record['azimlib']['line_visible']==(marker!='None')
                cases.append(record)
    return dict(python=platform.python_version(),matplotlib=matplotlib.__version__,azimlib=azl.__version__,cases=cases,
                scope='Selected Agg visibility contract; red counts are diagnostic, not pixel equality. SVG paths recorded separately.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();report=inspect();args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'{len(report["cases"])} native visibility cases recorded')

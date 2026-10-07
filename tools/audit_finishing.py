"""Audit original curve accuracy, bundled outline provenance and PNG/SVG/PDF.

Optional --font-reference uses fontTools only as an independent development
oracle, never as a renderer/runtime dependency. Reports contain no local paths.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import azimlib as azl
from azimlib.scene import Scene,Text,Path as ScreenPath,Rect,Circle
from azimlib.font_outline import contours
from azimlib.typography import font_path,_metrics

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--font-reference',action='store_true')
    args=p.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=True)
    report=dict(schema_version=1,version=azl.__version__,scope='Local numeric/export checks; no native visual approval or remote CI claim',font_reference=None,
                installed_runtime=Path(azl.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()))
    cases=0;max_error=0
    for tolerance in (.02,.1,.4):
        path=azl.Path([(0,0),(0,100),(100,100),(100,0)],[1,4,4,4]);line=path.to_polylines(tolerance=tolerance)[0][0]
        for i in range(1001):
            t=i/1000;x=300*t*t-200*t**3;y=300*t*(1-t)
            errors=[]
            for a,b in zip(line,line[1:]):
                dx,dy=b[0]-a[0],b[1]-a[1];u=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy)))
                errors.append(math.hypot(x-a[0]-u*dx,y-a[1]-u*dy))
            error=min(errors);assert error<=tolerance;cases+=1;max_error=max(max_error,error)
    report['bezier']=dict(cases=cases,max_error=max_error,tolerances=[.02,.1,.4],oracle='Analytic cubic (300t²-200t³,300t(1-t)), Euclidean segment distance')
    if args.font_reference:
        import fontTools
        from fontTools.ttLib import TTFont
        faces=[];cases=0;max_delta=0
        for weight,slant in (('normal','normal'),('bold','normal'),('normal','italic'),('bold','italic')):
            style=dict(font_weight=weight,font_style=slant);path=font_path(style);font=TTFont(path);metrics=_metrics()[path.stem]
            glyphs=sorted({row[0] for row in metrics['chars'].values()});checked=0
            for glyph in glyphs:
                own=contours(path,glyph);reference=font['glyf'][font.getGlyphOrder()[glyph]]
                coords,ends,flags=reference.getCoordinates(font['glyf'])
                expected=[];start=0
                for end in ends:
                    expected.append(tuple((coords[i][0],coords[i][1],bool(flags[i]&1)) for i in range(start,end+1)));start=end+1
                assert len(own)==len(expected),(path.name,glyph)
                for a,b in zip(own,expected):
                    assert len(a)==len(b),(path.name,glyph)
                    for first,second in zip(a,b):
                        assert first[2]==second[2]
                        delta=max(abs(first[i]-second[i]) for i in range(2));max_delta=max(max_delta,delta)
                        assert delta<=1e-8,(path.name,glyph,first,second)
                cases+=1;checked+=1
            font.close();faces.append(dict(face=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),glyphs=checked))
        report['font_reference']=dict(tool='fontTools',version=fontTools.__version__,faces=faces,glyphs=cases,max_coordinate_delta=max_delta,scope='Unhinted static glyph points, simple/composite; no rasterization or shaping claim')
    from azimlib.renderers import render_pdf,render_svg,render_image
    exports=[]
    for dpi in (100,150,200):
        s=Scene(400,200,None);s.add(Rect(.25,.5,150,150,dict(fill='#258bb080',stroke='#00000080',stroke_width=.8)))
        s.add(Circle(180.25,75.5,28.25,dict(fill='#db6c6980')))
        s.add(ScreenPath([[(20.25,140.5),(80.25,75.5),(160.25,140.5)]],False,dict(stroke='#9360a8',stroke_width=1.5,linecap='round',linejoin='bevel',dash=(5,3)),(.25,.5,250.75,170.25)))
        s.add(Text(240.25,80.5,'São Paulo',dict(fill='black',font_size=14,rotation=-25)))
        s.add(Text(240.25,120.5,r'$\sigma^2=\frac{x_0^2}{2}$',dict(fill='black',font_size=18)))
        scaled=s.scaled(dpi/100);stem=f'backend-{dpi}'
        (out/(stem+'.svg')).write_text(render_svg(scaled),encoding='utf8');render_pdf(scaled,out/(stem+'.pdf'),dpi=dpi)
        image=render_image(scaled);assert image.size==(dpi*4,dpi*2);image.save(out/(stem+'.png'));image.close()
        exports.append(dict(dpi=dpi,page_inches=[4,2],files={ext:hashlib.sha256((out/(stem+'.'+ext)).read_bytes()).hexdigest() for ext in ('png','svg','pdf')}))
    report['exports']=exports;report['passed']=True
    (out/'audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps(report,indent=2))

if __name__=='__main__':main()

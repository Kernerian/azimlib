"""Development-only comparison with Matplotlib/Agg; never a runtime backend.

Requires Matplotlib and Pillow in the reference environment. Both renderers
receive identical screen geometry, DejaVu fonts and 100 DPI. --tag preserves
before/after artifacts. The measured ink areas are independent of Matplotlib.
"""
import argparse,io,json,math
from pathlib import Path as FilePath
from PIL import Image,ImageColor,ImageDraw
import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_agg import RendererAgg
from matplotlib.path import Path as MplPath
from matplotlib.transforms import Affine2D
from matplotlib.font_manager import FontProperties
from azimlib.scene import Scene,Path,Circle,Rect,Text
from azimlib.renderers import render_png,render_svg
from azimlib.typography import font_path,text_width,text_baseline_offset

def samples():
    scene=Scene(640,440)
    for i,r in enumerate((2.5,4,7,12)):
        scene.add(Circle(50+i*70+.23,55.37,r,dict(fill='#1f77b4',stroke='black',stroke_width=.8*100/72)))
    for i,cap in enumerate(('butt','round','square')):
        scene.add(Path([[(340,35+i*22),(470,42+i*22),(525,28+i*22)]],False,
                       dict(stroke='#d94a48',stroke_width=1.5*100/72,linecap=cap,linejoin='round')))
    for i,join in enumerate(('miter','round','bevel')):
        scene.add(Path([[(45+i*95,155),(75+i*95,100),(105+i*95,155)]],False,
                       dict(stroke='black',stroke_width=5*100/72,linecap='butt',linejoin=join)))
    # Opposite ring winding also describes this hole for Agg's nonzero fill.
    scene.add(Path([[(350.2,110.4),(465.6,104.8),(490.3,167.7),(357.4,168.6)],
                    [(382,123),(382,149),(423,149),(423,123)]],True,
                   dict(fill='#2ca02c',stroke='black',stroke_width=.6*100/72)))
    for i,rotation in enumerate((0,25,90)):
        scene.add(Text(90+i*200,240,'São Paulo · 1.250',dict(fill='#222222',font_family='DejaVu Sans',
                       font_size=10*100/72,anchor='middle',baseline='middle',rotation=rotation,background='#eef2f6')))
    for i,weight in enumerate(('normal','bold')):
        scene.add(Text(30,345+i*30,'Geografia: águas, curvas e territórios',
                       dict(fill='black',font_family='DejaVu Sans',font_size=12*100/72,font_weight=weight)))
    scene.add(Path([[(340,370),(390,320),(440,355),(500,310),(580,350)]],False,
                   dict(stroke='#1f77b4',stroke_width=.8*100/72,dash=[5,3],linecap='butt',linejoin='round')))
    return scene

def reference(scene):
    renderer=RendererAgg(int(scene.width),int(scene.height),100)
    transform=Affine2D().scale(1,-1).translate(0,scene.height)
    def path(parts,closed,style,transform=transform):
        vertices=[];codes=[]
        for part in parts:
            vertices.extend(part);codes.extend([MplPath.MOVETO]+[MplPath.LINETO]*(len(part)-1))
            if closed:vertices.append(part[0]);codes.append(MplPath.CLOSEPOLY)
        gc=renderer.new_gc();gc.set_antialiased(True);gc.set_snap(False)
        gc.set_linewidth(style.get('stroke_width',1)*72/100 if style.get('stroke') else 0)
        gc.set_capstyle({'square':'projecting'}.get(style.get('linecap'),style.get('linecap','butt')))
        gc.set_joinstyle(style.get('linejoin','round'))
        if style.get('stroke'):gc.set_foreground(style['stroke'])
        if style.get('dash'):gc.set_dashes(0,[v*72/100 for v in style['dash']])
        fill=style.get('fill');rgba=None if not fill or fill=='none' else tuple(v/255 for v in ImageColor.getcolor(fill,'RGBA'))
        renderer.draw_path(gc,MplPath(vertices,codes),transform,rgba)
    path([[(0,0),(scene.width,0),(scene.width,scene.height),(0,scene.height)]],True,dict(fill='white'))
    for item in scene.items:
        if isinstance(item,Path):path(item.paths,item.closed,item.style)
        elif isinstance(item,Rect):path([[(item.x,item.y),(item.x+item.width,item.y),(item.x+item.width,item.y+item.height),(item.x,item.y+item.height)]],True,item.style)
        elif isinstance(item,Circle):
            gc=renderer.new_gc();gc.set_snap(False);gc.set_foreground(item.style.get('stroke','black'))
            gc.set_linewidth(item.style.get('stroke_width',1)*72/100 if item.style.get('stroke') else 0)
            fill=tuple(v/255 for v in ImageColor.getcolor(item.style['fill'],'RGBA'))
            renderer.draw_path(gc,MplPath.unit_circle(),Affine2D().scale(item.r).translate(item.x,item.y)+transform,fill)
        elif isinstance(item,Text):
            style=item.style;offset=text_baseline_offset(item.text,style)
            x=-{'start':0,'middle':.5,'end':1}[style.get('anchor','start')]*text_width(item.text,style)
            angle=math.radians(style.get('rotation',0))
            tx=item.x+x*math.cos(angle)-offset*math.sin(angle)
            ty=item.y+x*math.sin(angle)+offset*math.cos(angle)
            if style.get('background'):
                from azimlib.typography import text_vertical_bounds
                low,high=text_vertical_bounds(item.text,style);w=text_width(item.text,style)
                local=[(x-3,offset-high-3),(x+w+3,offset-high-3),(x+w+3,offset-low+3),(x-3,offset-low+3)]
                corners=[(item.x+a*math.cos(angle)-b*math.sin(angle),item.y+a*math.sin(angle)+b*math.cos(angle)) for a,b in local]
                path([corners],True,dict(fill=style['background']))
            gc=renderer.new_gc();gc.set_foreground(style['fill'])
            renderer.draw_text(gc,tx,ty,item.text,FontProperties(fname=str(font_path(style)),size=style['font_size']*72/100),-style.get('rotation',0))
    return Image.frombytes('RGBA',(int(scene.width),int(scene.height)),bytes(renderer.buffer_rgba()))

def ink_metrics():
    results=[]
    for r in (2.5,4,7,12):
        scene=Scene(60,60,None);scene.add(Circle(30.23,30.37,r,dict(fill='black')))
        stream=io.BytesIO();render_png(scene,stream)
        image=Image.open(stream).convert('RGBA');area=sum(image.getchannel('A').tobytes())/255
        results.append(dict(radius=r,measured_area=area,expected_area=math.pi*r*r,relative_error=(area/(math.pi*r*r)-1)))
    for x,y,w,h in ((10.23,12.37,13.2,9.6),(10.2,12.4,.8,12.7)):
        scene=Scene(60,60,None);scene.add(Rect(x,y,w,h,dict(fill='black')))
        stream=io.BytesIO();render_png(scene,stream)
        image=Image.open(stream).convert('RGBA');area=sum(image.getchannel('A').tobytes())/255
        results.append(dict(rect=[x,y,w,h],measured_area=area,expected_area=w*h,relative_error=area/(w*h)-1))
    return results

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--tag',default='after');args=parser.parse_args()
    root=FilePath(__file__).resolve().parents[1];gallery=root/'gallery';scene=samples()
    output=io.BytesIO();render_png(scene,output);own=Image.open(output).convert('RGBA');agg=reference(scene)
    own.save(gallery/f'render-quality-azimlib-{args.tag}.png');agg.save(gallery/'render-quality-matplotlib.png')
    (gallery/'render-quality.svg').write_text(render_svg(scene),encoding='utf-8')
    combined=Image.new('RGB',(1280,470),'white');combined.paste(own,(0,30));combined.paste(agg,(640,30))
    draw=ImageDraw.Draw(combined);draw.text((15,8),'Azimlib / own renderer / 100 DPI',fill='black');draw.text((655,8),f'Matplotlib {matplotlib.__version__} / Agg / 100 DPI',fill='black')
    combined.save(gallery/f'render-quality-{args.tag}.png')
    metrics=dict(reference=matplotlib.__version__,dpi=100,canvas=[640,440],ink=ink_metrics())
    (root/'docs'/f'fill-validation-{args.tag}.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    print(json.dumps(metrics,indent=2))

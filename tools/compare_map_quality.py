"""Dev-only full-scene PNG comparison with Agg at identical screen geometry.

This measures rasterization differences, not Matplotlib Axes/cartographic layout.
No part of this adapter is imported by Azimlib's runtime or used as its backend.
"""
import argparse
import hashlib
import io
import json
import math
import platform
import time
from pathlib import Path as FilePath
import numpy as np
from PIL import Image, ImageChops, ImageDraw, __version__ as pillow_version
import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_agg import RendererAgg
from matplotlib.colors import to_rgba
from matplotlib.font_manager import FontProperties
from matplotlib.path import Path as AggPath
from matplotlib.textpath import TextPath
from matplotlib.transforms import Affine2D, Bbox
import azimlib as azl
from azimlib.scene import Scene, Path, Rect, Circle, Text
from azimlib.renderers import render_png, render_svg
from azimlib.typography import font_path, text_width, text_baseline_offset, text_bounds
from benchmark_maps import create

ROOT=FilePath(__file__).resolve().parents[1]

def winding(parts):
    """Convert simple nested even-odd rings to Agg's nonzero convention."""
    def inside(p,ring):
        x,y=p;result=False
        for a,b in zip(ring,ring[1:]+ring[:1]):
            if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:result=not result
        return result
    result=[]
    for i,ring in enumerate(parts):
        if not ring:continue
        depth=sum(inside(ring[0],other) for j,other in enumerate(parts) if i!=j and other)
        area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(ring,ring[1:]+ring[:1]))
        result.append(list(reversed(ring)) if (area>0)!=(depth%2==0) else ring)
    return result

def reference(scene,dpi):
    size=(round(scene.width),round(scene.height));screen=Affine2D().scale(1,-1).translate(0,scene.height)
    def rgba(value,opacity=1):
        c=to_rgba(value or 'none');return (*c[:3],c[3]*opacity)
    def graphics(renderer,style,clip):
        gc=renderer.new_gc();gc.set_antialiased(style.get('shape_rendering')!='crispEdges');gc.set_snap(False)
        gc.set_linewidth(style.get('stroke_width',1)*72/dpi if style.get('stroke') not in (None,'none') else 0)
        gc.set_foreground(rgba(style.get('stroke','none'),style.get('stroke_opacity',1)))
        gc.set_capstyle({'square':'projecting'}.get(style.get('linecap'),style.get('linecap','butt')))
        gc.set_joinstyle(style.get('linejoin','round'))
        if style.get('dash'):gc.set_dashes(0,[v*72/dpi for v in style['dash']])
        if clip is not None:
            x,y,w,h=clip;gc.set_clip_rectangle(Bbox.from_bounds(x,scene.height-y-h,w,h))
        return gc
    def path(renderer,parts,closed,style,clip=None):
        parts=winding(parts) if closed and len(parts)>1 else parts
        vertices=[];codes=[]
        for part in parts:
            if not part:continue
            vertices.extend(part);codes.extend([AggPath.MOVETO]+[AggPath.LINETO]*(len(part)-1))
            if closed:vertices.append(part[0]);codes.append(AggPath.CLOSEPOLY)
        if not vertices:return
        gc=graphics(renderer,style,clip)
        fill=rgba(style.get('fill','none'),style.get('fill_opacity',1))
        renderer.draw_path(gc,AggPath(vertices,codes),screen,fill if fill[3] else None);gc.restore()
    def paint(renderer,item):
        s=item.style
        if isinstance(item,Path):path(renderer,item.paths,item.closed,s,item.clip)
        elif isinstance(item,Rect):
            x,y,w,h=item.x,item.y,item.width,item.height
            path(renderer,[[(x,y),(x+w,y),(x+w,y+h),(x,y+h)]],True,s,item.clip)
        elif isinstance(item,Circle):
            gc=graphics(renderer,s,item.clip);fill=rgba(s.get('fill','none'),s.get('fill_opacity',1))
            renderer.draw_path(gc,AggPath.unit_circle(),Affine2D().scale(item.r).translate(item.x,item.y)+screen,fill if fill[3] else None);gc.restore()
        elif isinstance(item,Text):
            angle=math.radians(s.get('rotation',0));offset=text_baseline_offset(item.text,s)
            shift=-{'start':0,'middle':.5,'end':1}[s.get('anchor','start')]*text_width(item.text,s)
            if s.get('background'):
                bx,by,w,h=text_bounds(item.text,s)
                corners=[(bx-3,by-3),(bx+w+3,by-3),(bx+w+3,by+h+3),(bx-3,by+h+3)]
                path(renderer,[[(item.x+x*math.cos(angle)-y*math.sin(angle),item.y+x*math.sin(angle)+y*math.cos(angle)) for x,y in corners]],True,dict(fill=s['background']),item.clip)
            fname=font_path(s)
            if fname is None:raise ValueError('This comparison requires the bundled DejaVu fonts')
            if s.get('stroke') not in (None,'none') and s.get('stroke_width',0)>0:
                prop=FontProperties(fname=str(fname))
                glyphs=TextPath((0,0),item.text,size=s.get('font_size',12),prop=prop)
                transform=Affine2D().scale(1,-1).translate(shift,offset).rotate(angle).translate(item.x,item.y)+screen
                gc=graphics(renderer,s,item.clip);renderer.draw_path(gc,glyphs,transform,None);gc.restore()
            gc=graphics(renderer,s,item.clip);gc.set_foreground(rgba(s.get('fill','black'),s.get('fill_opacity',1)))
            tx=item.x+shift*math.cos(angle)-offset*math.sin(angle);ty=item.y+shift*math.sin(angle)+offset*math.cos(angle)
            renderer.draw_text(gc,tx,ty,item.text,FontProperties(fname=str(fname),size=s.get('font_size',12)*72/dpi),-s.get('rotation',0));gc.restore()
    renderer=RendererAgg(*size,dpi)
    if scene.background is not None:path(renderer,[[(0,0),(scene.width,0),(scene.width,scene.height),(0,scene.height)]],True,dict(fill=scene.background))
    for item in scene.items:
        opacity=item.style.get('opacity',1)
        if opacity==1:paint(renderer,item);continue
        # Own Scene opacity applies after fill+stroke have been composed.
        temp=RendererAgg(*size,dpi);paint(temp,item)
        overlay=Image.frombytes('RGBA',size,bytes(temp.buffer_rgba()))
        overlay.putalpha(overlay.getchannel('A').point([round(v*opacity) for v in range(256)]))
        base=Image.frombytes('RGBA',size,bytes(renderer.buffer_rgba()));base.alpha_composite(overlay)
        gc=renderer.new_gc();renderer.clear();renderer.draw_image(gc,0,0,np.asarray(base)[::-1]);gc.restore()
    return Image.frombytes('RGBA',size,bytes(renderer.buffer_rgba()))

def differences(own,agg):
    a=np.asarray(own.convert('RGB'),dtype=np.int16);b=np.asarray(agg.convert('RGB'),dtype=np.int16)
    delta=np.abs(a-b);occupied=(a.min(axis=2)<250)|(b.min(axis=2)<250)
    return dict(mean_absolute_rgb=float(delta.mean()),occupied_mean_absolute_rgb=float(delta[occupied].mean()) if occupied.any() else 0,
                occupied_fraction=float(occupied.mean()),fraction_pixels_max_difference_gt16=float((delta.max(axis=2)>16).mean()),
                identical_pixels=bool(np.array_equal(a,b)))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases',nargs='+',choices=('state','brazil','atlas'),default=['state','brazil','atlas'])
    parser.add_argument('--dpi',nargs='+',type=int,default=[100,150,200])
    parser.add_argument('--output',type=FilePath,default=ROOT/'docs/map-quality.json')
    parser.add_argument('--gallery',type=FilePath,default=ROOT/'gallery')
    args=parser.parse_args()
    if any(v<1 for v in args.dpi):parser.error('dpi must be positive')
    report=dict(python=platform.python_version(),platform=platform.platform(),pillow=pillow_version,matplotlib=matplotlib.__version__,
        azimlib=azl.__version__,notes=['Same own cartographic Scene sent to both rasterizers; does not compare Axes layout or cartographic algorithms.',
        'Bundled fonts, physical sizes, clip rectangles, colors, global opacity and simple nested holes preserved.',
        'Agg uses hinted font rasterization; own renderer uses its existing supersampling; pixel equality is not expected.',
        'Text halo uses vector outlines beneath hinted fill in this development adapter; complex self-intersecting even-odd paths are not covered.',
        'Metrics are descriptive diagnostics, not perceptual scores or performance comparisons.'],cases=[])
    args.gallery.mkdir(parents=True,exist_ok=True)
    for name in args.cases:
        for dpi in args.dpi:
            fig,_=create(name,1500);fig.dpi=dpi;scene=fig.to_scene(cull=True)
            start=time.perf_counter();buffer=io.BytesIO();render_png(scene,buffer);own_seconds=time.perf_counter()-start
            own=Image.open(buffer).convert('RGBA');start=time.perf_counter();agg=reference(scene,dpi);agg_seconds=time.perf_counter()-start
            prefix=f'map-quality-{name}-{dpi}';own.save(args.gallery/f'{prefix}-azimlib.png');agg.save(args.gallery/f'{prefix}-agg.png')
            (args.gallery/f'{prefix}.svg').write_text(render_svg(scene),encoding='utf-8')
            canvas=Image.new('RGB',(own.width*2,own.height+30),'white');canvas.paste(own,(0,30));canvas.paste(agg,(own.width,30))
            draw=ImageDraw.Draw(canvas);draw.text((10,8),f'Azimlib / own raster / {dpi} DPI',fill='black');draw.text((own.width+10,8),f'Same Scene -> Matplotlib {matplotlib.__version__} / Agg',fill='black')
            canvas.save(args.gallery/f'{prefix}-comparison.png')
            diff=ImageChops.difference(own.convert('RGB'),agg.convert('RGB'));diff.save(args.gallery/f'{prefix}-difference.png')
            result=dict(name=name,dpi=dpi,pixels=[own.width,own.height],items=len(scene.items),metrics=differences(own,agg),
                        png_sha256=dict(azimlib=hashlib.sha256((args.gallery/f'{prefix}-azimlib.png').read_bytes()).hexdigest(),agg=hashlib.sha256((args.gallery/f'{prefix}-agg.png').read_bytes()).hexdigest()),
                        observed_seconds=dict(own=own_seconds,agg_adapter=agg_seconds),files=dict(comparison=f'{prefix}-comparison.png',svg=f'{prefix}.svg'))
            report['cases'].append(result);args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
            print(f'{name} {dpi} DPI: {result["metrics"]}',flush=True);azl.close(fig)

if __name__=='__main__':main()

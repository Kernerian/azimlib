"""Own synthetic visual/numeric/performance gates; no external plotter or FPS claim."""
import argparse,dataclasses,hashlib,json,math,statistics,sys,time
from pathlib import Path
import azimlib as azl
from azimlib.renderers import render_image
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'tools/baselines/release030'

def create(name):
    fig,ax=azl.subplots(figsize=(3.2,2.8),dpi=100,projection='3d' if name=='depth' else 'equirectangular')
    if name=='depth':
        xy=[i*10 for i in range(8)]
        ax.plot_surface(xy,xy,[[10+20*math.sin(i/3)*math.cos(j/4) for i in range(8)] for j in range(8)],color='#267f96')
        ax.set_title('Metric terrain');ax.set_xlabel('East (m)');ax.set_ylabel('North (m)')
    else:
        ax.set_extent((-5,5,-4,4));ax.set_xlabel('Longitude',labelpad=4);ax.set_ylabel('Latitude',labelpad=4)
        ax.set_title('Scalar cells' if name=='cells' else 'Styles and components')
        if name=='cells':
            field=ax.imshow([[1,2,3],[4,None,6],[7,8,9]],extent=(-5,5,-4,4),origin='lower',cmap='viridis')
            cax=fig.add_axes([.35,.11,.42,.035]);fig.colorbar(field,cax=cax,orientation='horizontal',label='Value')
        else:
            ax.plot([-4,-1,3],[-2,2,1],color='#9562a8',linestyle='--',marker='D',linewidth=1,label='Route')
            ax.geojson({'type':'Polygon','coordinates':[[[-3,-2],[-1,-2],[-1,0],[-3,0],[-3,-2]]]},facecolor='#ecf1f4',edgecolor='#506470',hatch='//',linewidth=.6)
            ax.grid(linestyle=':',linewidth=.4);ax.legend(loc='upper right',fontsize=6)
    fig.subplots_adjust(left=.23,right=.94,bottom=.33 if name=='cells' else .21,top=.83)
    return fig

def primitive_key(scene):
    # Round geometric results, never font/dataset/PNG bytes, for libm tolerance.
    def normalize(value):
        if dataclasses.is_dataclass(value):return normalize(dataclasses.asdict(value))
        if isinstance(value,dict):return {k:normalize(v) for k,v in value.items()}
        if isinstance(value,(list,tuple)):return [normalize(v) for v in value]
        if isinstance(value,float):return round(value,5)
        if isinstance(value,bytes):return hashlib.sha256(value).hexdigest()
        return value
    rows=[dict(type=type(item).__name__,value=normalize(item)) for item in scene.items]
    return hashlib.sha256(json.dumps(rows,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def text_mask(scene, size):
    """Only font ink boxes may tolerate optional FreeType/RAQM raster differences."""
    from PIL import Image, ImageDraw
    from azimlib.typography import text_bounds, text_rotation_offset
    mask=Image.new('L',size);draw=ImageDraw.Draw(mask)
    for item in scene.items:
        if type(item).__name__!='Text':continue
        x,y,w,h=text_bounds(item.text,item.style)
        angle=math.radians(item.style.get('rotation',0));c,s=math.cos(angle),math.sin(angle)
        dx,dy=text_rotation_offset(item.text,item.style)
        points=[(item.x+dx+px*c-py*s,item.y+dy+px*s+py*c) for px,py in ((x,y),(x+w,y),(x+w,y+h),(x,y+h))]
        draw.rectangle((math.floor(min(p[0] for p in points)-4),math.floor(min(p[1] for p in points)-4),math.ceil(max(p[0] for p in points)+4),math.ceil(max(p[1] for p in points)+4)),fill=255)
    return mask


def pixels(actual,expected,mask=None):
    from PIL import Image,ImageChops
    assert actual.size==expected.size,'Baseline dimensions changed'
    a,b=actual.convert('RGB'),expected.convert('RGB')
    raw=ImageChops.difference(a,b);n=actual.width*actual.height*3
    def metrics(diff):
        hist=diff.histogram()
        return (math.sqrt(sum((i%256)**2*v for i,v in enumerate(hist))/n),sum(v for i,v in enumerate(hist) if i%256>24)/n)
    diff=raw
    if mask is not None:
        # Both directions catch erased/new text. Geometry and all text/style
        # properties still require the independent exact primitive hash gate.
        def nearest(left,right):
            best=ImageChops.difference(left,right)
            for dx in range(-2,3):
                for dy in range(-2,3):
                    shifted=Image.new('RGB',right.size,'white');shifted.paste(right,(dx,dy))
                    candidate=ImageChops.difference(left,shifted)
                    updated=ImageChops.darker(best,candidate)
                    best.close();shifted.close();candidate.close();best=updated
            return best
        forward,reverse=nearest(a,b),nearest(b,a)
        diff=Image.composite(forward,raw,mask)
        backward=Image.composite(reverse,raw,mask)
        backward_rms,backward_changed=metrics(backward)
        backward.close();forward.close();reverse.close()
    rms,changed=metrics(diff)
    if mask is not None:rms,changed=max(rms,backward_rms),max(changed,backward_changed)
    raw_rms,raw_changed=metrics(raw)
    a.close();b.close()
    if diff is not raw:diff.close()
    raw.close()
    assert rms<=3 and changed<=.025,('Visual regression',rms,changed)
    return dict(rms=rms,fraction_channels_over_24=changed,raw_rms=raw_rms,raw_fraction_channels_over_24=raw_changed,tolerance_rms=3,tolerance_fraction=.025,text_neighbourhood_pixels=2 if mask is not None else 0)

def main():
    from PIL import Image
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--record',action='store_true',help='Explicitly create previously absent reviewed baselines; never overwrite')
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    if a.record and BASE.exists():raise FileExistsError('Reviewed baselines must not be overwritten')
    if a.record:BASE.mkdir(parents=True)
    reference=None if a.record else json.loads((BASE/'manifest.json').read_text('utf8'))
    runtime=Path(azl.__file__).resolve().parent;assert runtime.is_relative_to(Path(sys.prefix).resolve()),'Install the wheel before checking gates'
    rows=[]
    from azimlib.geodesy import Geodesic,WGS84
    result=Geodesic().inverse(0,0,1,0);expected=WGS84.semi_major_axis*math.pi/180
    error=abs(result.distance-expected);assert error<.00001
    for name in ('styles','cells','depth'):
        fig=create(name);scene=fig.to_scene();key=primitive_key(scene);samples=[];image=None
        for _ in range(4):
            if image is not None:image.close()
            start=time.perf_counter();image=render_image(fig.to_scene());samples.append(time.perf_counter()-start)
        assert len(scene.items)<500 and max(samples)<30,('Work/performance budget',name,len(scene.items),samples)
        path=a.output/(name+'.png');image.save(path)
        if a.record:
            image.save(BASE/(name+'.png'));comparison=dict(recorded=True)
        else:
            assert key==reference['cases'][name]['scene_sha256'],('Numeric/layout regression',name,key)
            with Image.open(BASE/(name+'.png')) as expected_image:comparison=pixels(image,expected_image,text_mask(scene,image.size))
        rows.append(dict(name=name,pixels=list(image.size),scene_sha256=key,primitives=len(scene.items),warm_seconds=samples[1:],median_seconds=statistics.median(samples[1:]),max_frame_seconds=30,visual=comparison,png_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        image.close();azl.close(fig)
    tool_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if a.record:
        manifest=dict(composition='Original synthetic Azimlib regression cases',license='BSD-3-Clause; DejaVu text retains bundled font terms; Viridis CC0',tool_sha256=tool_sha,cases={row['name']:{k:row[k] for k in ('pixels','scene_sha256','png_sha256')} for row in rows})
        (BASE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8',newline='\n')
    else:assert reference['tool_sha256']==tool_sha,'Review baseline changes explicitly'
    report=dict(passed=True,version=azl.__version__,tool_sha256=tool_sha,runtime_sha256={p.relative_to(runtime).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(runtime.rglob('*.py'))},numeric=dict(equatorial_one_degree_error_metres=error,tolerance_metres=.00001),cases=rows,scope='Bounded 320x280 synthetic static frames; 3 warm samples; 30s safety ceiling is not an interactive FPS/latency claim')
    (a.output/'result.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps({k:report[k] for k in ('passed','numeric','cases')},indent=2))
if __name__=='__main__':main()

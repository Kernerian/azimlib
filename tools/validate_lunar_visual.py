"""Original lunar visual packet: static/temporal, CPU/GPU, verified own windows."""
import argparse,hashlib,importlib.util,json,platform,shutil,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def body_occlusion(renderer):
    """Analytic aligned-body case, both camera sides and input face orders."""
    import math
    import azimlib as azl
    from azimlib.lunar_artists import EarthMoonArtist
    from azimlib.terrain3d import Camera,rasterize
    from azimlib.scene import Scene,Raster3D
    body=EarthMoonArtist(azl.MoonDirection(90,0,384e6,azl.SolarObserver(0,0)),distance_scale=.1,moon_radius_scale=2,shade=False,earth_color='blue',moon_color='red')
    c=body.display_centers['moon'];bounds=tuple(x for v in c for x in (v/2-30e6,v/2+30e6))
    az=math.degrees(math.atan2(c[1],c[0]));el=math.degrees(math.atan2(c[2],math.hypot(c[0],c[1])));checks=[]
    for moon_side in (True,False):
        camera=Camera(azim=az if moon_side else az+180,elev=el if moon_side else -el,projection='ortho')
        faces=body.faces(camera,bounds,1,1);expected=(255,0,0,255) if moon_side else (0,0,255,255)
        for reverse in (False,True):
            triangles=tuple(reversed(faces)) if reverse else tuple(faces)
            image=rasterize(triangles,256,256);index=(128*256+128)*4
            if tuple(image.rgba[index:index+4])!=expected:raise AssertionError('CPU body occlusion failed')
            if renderer:
                scene=Scene(256,256);scene.items.append(Raster3D(0,0,256,256,triangles))
                image=renderer.render(scene)
                try:
                    if image.getpixel((128,128))!=expected:raise AssertionError('GPU body occlusion failed')
                finally:image.close()
            checks.append(dict(camera_side='Moon' if moon_side else 'Earth',reversed_triangles=reverse,cpu=True,gpu=renderer is not None))
    return checks

def validate(output,*,gpu=False,native=False):
    output=output.resolve()
    if output.exists():raise FileExistsError('Use a new lunar visual directory')
    output.parent.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(output.parent).free<15_100_000_000:raise RuntimeError('System free-space reserve is insufficient')
    output.mkdir();sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
    import azimlib as azl
    from azimlib.renderers import render_image
    from publication_privacy import findings
    from datetime import timedelta
    spec=importlib.util.spec_from_file_location('lunar_example',ROOT/'examples/lunar_maps.py')
    example=importlib.util.module_from_spec(spec);spec.loader.exec_module(example)
    figures=[('world',example.make_map()),('physical',example.make_system(physical=True)),('system',example.make_system()),('phases',example.make_phases())]
    renderer=None;hardware=None;files=[];captures=[];timings=[]
    try:
        if gpu:
            from azimlib.renderers.gpu import GpuRenderer
            renderer=GpuRenderer();hardware=renderer.info
        occlusion=body_occlusion(renderer)
        for name,(fig,ax,artists) in figures:
            start=time.perf_counter();scene=fig.to_scene(simplify=False);compose=time.perf_counter()-start
            start=time.perf_counter();image=render_image(scene);image.save(output/(name+'-cpu.png'));image.close()
            timings.append(dict(scene=name,compose_seconds=compose,cpu_paint_seconds=time.perf_counter()-start))
            files.append(name+'-cpu.png')
            for extension in ('svg','pdf'):
                filename=name+'.'+extension;fig.savefig(output/filename);files.append(filename)
            if renderer:
                image=renderer.render(scene);image.save(output/(name+'-gpu.png'));image.close();files.append(name+'-gpu.png')
        fig,ax,artists=figures[0][1]
        times=[example.INSTANT+timedelta(hours=i*6) for i in range(3)]
        series=azl.TemporalSeries(times,[example.MODEL.position(t) for t in times])
        bindings=[series.bind(artist) for artist in artists]
        extent=ax.get_extent()
        def update(i):
            for binding in bindings:binding.apply(i)
        from azimlib.animation import FuncAnimation
        animation=FuncAnimation(fig,update,frames=3,autoplay=False)
        try:animation.save(output/'lunar-time.gif',fps=2)
        finally:animation.close()
        files.append('lunar-time.gif');assert ax.get_extent()==extent;update(0)
        skyfig,skyax,sky=figures[2][1];camera=skyax.camera
        skyseries=azl.TemporalSeries(times,[example.MODEL.position(t) for t in times]);binding=skyseries.bind(sky)
        binding.apply(1);assert skyax.camera is camera
        skyfig.savefig(output/'sky-time-1.png');files.append('sky-time-1.png');binding.apply(0)
        if native:
            from validate_text_engine import capture_tk
            for backend in ('tk','qt'):
                viewer=fig.show(backend=backend,block=False)
                try:
                    for _ in range(8):viewer.flush_events();time.sleep(.04)
                    viewer.draw();viewer.flush_events();filename=f'{backend}-lunar-native.png';path=output/filename
                    if backend=='tk':mode=capture_tk(viewer,path)
                    else:
                        expected={'Windows':'windows','Linux':'xcb','Darwin':'cocoa'}[platform.system()]
                        if viewer.application.platformName()!=expected:raise RuntimeError('Expected native Qt plugin')
                        if not viewer.window.grab().save(str(path)):raise RuntimeError('Own Qt capture failed')
                        mode='own-native-qt-window-grab'
                    captures.append(dict(backend=backend,mode=mode,file=filename));files.append(filename)
                finally:viewer.close()
        report=dict(passed=True,scope='Local source exports and own native windows; not hosted CI or human acceptance',
            system=platform.system(),python=platform.python_version(),hardware=hardware,native=captures,
            timings=timings,temporal_frames=3,static_scene_count=4,body_occlusion=occlusion,
            source_sha256={p.relative_to(ROOT).as_posix():digest(p) for p in sorted((ROOT/'src/azimlib').rglob('*.py'))},
            files={name:digest(output/name) for name in files},validation_tool_sha256=digest(__file__),
            example_sha256=digest(ROOT/'examples/lunar_maps.py'))
        (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
        (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Azimlib lunar review</title>'
            '<h1>Terrestrial Moon — original rendering</h1><p>Compare night cells and continuous terminator, dateline, '
            'polar clipping, round markers, text, CPU/GPU, static PNG/SVG/PDF and three temporal frames. '
            'Sky metre sizes are illustrative; native screenshots are not human approval.</p>'
            +''.join(f'<p><img src="{name}-cpu.png" width="650" alt="{name}"></p>' for name in ('world','physical','system','phases'))
            +'<ul>'+''.join(f'<li><a href="{name}">{name}</a></li>' for name in files)+'</ul>',encoding='utf8')
        for path in output.iterdir():
            if findings(path.read_bytes()):raise RuntimeError('Lunar visual evidence privacy scan failed')
        return report
    finally:
        if renderer:renderer.close()
        azl.close('all')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--gpu',action='store_true');p.add_argument('--native',action='store_true');args=p.parse_args()
    report=validate(args.output,gpu=args.gpu,native=args.native)
    print(json.dumps({k:v for k,v in report.items() if k not in ('source_sha256','files')},indent=2))

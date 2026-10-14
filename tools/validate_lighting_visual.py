"""Original lighting visual packet: static/temporal, CPU/GPU, verified own windows."""
import argparse,hashlib,importlib.util,json,platform,shutil,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def validate(output,*,gpu=False,native=False):
    output=output.resolve()
    if output.exists():raise FileExistsError('Use a new lighting visual directory')
    output.parent.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(output.parent).free<15_100_000_000:raise RuntimeError('System free-space reserve is insufficient')
    output.mkdir();sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
    import azimlib as azl
    from azimlib.renderers import render_image
    from publication_privacy import findings
    from datetime import timedelta
    spec=importlib.util.spec_from_file_location('lighting_example',ROOT/'examples/lighting_maps.py')
    example=importlib.util.module_from_spec(spec);spec.loader.exec_module(example)
    figures=[('urban',example.make_urban()),('eclipse',example.make_eclipse_map()),('lunar',example.make_lunar()),('volume',example.make_volume())]
    renderer=None;hardware=None;files=[];captures=[];timings=[]
    try:
        if gpu:
            from azimlib.renderers.gpu import GpuRenderer
            renderer=GpuRenderer();hardware=renderer.info
        for name,(fig,ax,artists) in figures:
            start=time.perf_counter();scene=fig.to_scene(simplify=False);compose=time.perf_counter()-start
            start=time.perf_counter();image=render_image(scene);image.save(output/(name+'-cpu.png'));image.close()
            timings.append(dict(scene=name,compose_seconds=compose,cpu_paint_seconds=time.perf_counter()-start))
            files.append(name+'-cpu.png')
            for extension in ('svg','pdf'):
                filename=name+'.'+extension;fig.savefig(output/filename);files.append(filename)
            if renderer:
                image=renderer.render(scene);image.save(output/(name+'-gpu.png'));image.close();files.append(name+'-gpu.png')
        fig,ax,light=figures[0][1]
        times=[example.INSTANT+timedelta(hours=i*3) for i in range(3)]
        series=azl.TemporalSeries(times,[example.MODEL.position(t,example.OBSERVER) for t in times])
        binding=series.bind(light);camera=ax.camera;geometry_builds=light.geometry_builds
        def update(i):binding.apply(i)
        from azimlib.animation import FuncAnimation
        animation=FuncAnimation(fig,update,frames=3,autoplay=False)
        try:animation.save(output/'lighting-time.gif',fps=2)
        finally:animation.close()
        files.append('lighting-time.gif');assert ax.camera is camera;update(0);fig.to_scene()
        assert light.geometry_builds==geometry_builds
        cache=dict(geometry_builds=geometry_builds,lighting_builds=light.lighting_builds,
            rays=light._index.rays,triangle_tests=light._index.tests,physical_bias_m=light.bias_m,max_edge_m=light.max_edge_m,
            camera_preserved=True,geometry_reused_across_time=True)
        if native:
            from validate_text_engine import capture_tk
            for backend in ('tk','qt'):
                viewer=fig.show(backend=backend,block=False)
                try:
                    for _ in range(8):viewer.flush_events();time.sleep(.04)
                    viewer.draw();viewer.flush_events();filename=f'{backend}-lighting-native.png';path=output/filename
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
            timings=timings,temporal_frames=3,static_scene_count=4,physical_cache=cache,
            source_sha256={p.relative_to(ROOT).as_posix():digest(p) for p in sorted((ROOT/'src/azimlib').rglob('*.py'))},
            files={name:digest(output/name) for name in files},validation_tool_sha256=digest(__file__),
            example_sha256=digest(ROOT/'examples/lighting_maps.py'))
        (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
        (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Azimlib lighting review</title>'
            '<h1>Physical local shadows and synthetic occultation</h1><p>Compare urban shadow placement and text, '
            'CPU/GPU widths, PNG/SVG/PDF and three daily frames. Eclipse inputs are synthetic; '
            'this is not real-event acceptance. 3D SVG/PDF embed raster layers; SVG volumes require Pillow.</p>'
            +''.join(f'<p><img src="{name}-cpu.png" width="650" alt="{name}"></p>' for name in ('urban','eclipse','lunar','volume'))
            +'<ul>'+''.join(f'<li><a href="{name}">{name}</a></li>' for name in files)+'</ul>',encoding='utf8')
        for path in output.iterdir():
            if findings(path.read_bytes()):raise RuntimeError('Lighting visual evidence privacy scan failed')
        return report
    finally:
        if renderer:renderer.close()
        azl.close('all')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--gpu',action='store_true');p.add_argument('--native',action='store_true');args=p.parse_args()
    report=validate(args.output,gpu=args.gpu,native=args.native)
    print(json.dumps({k:v for k,v in report.items() if k not in ('source_sha256','files')},indent=2))

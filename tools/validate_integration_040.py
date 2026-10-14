"""Offline cumulative source/wheel validation; no upload or release acceptance.

Native captures are restricted to the viewer's own verified windows. Raw data,
fonts, reference ephemerides and unrelated desktop contents are not captured.
"""
import argparse,hashlib,importlib.util,json,platform,shutil,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'examples'/f'{name}.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def validate(output,*,installed=False,core=False,gpu=False,native=False,gpu_context=None):
    output=output.resolve()
    if output.exists():raise FileExistsError('Use a new integration output directory')
    output.parent.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(output.parent).free<15_100_000_000:raise RuntimeError('15 GB system reserve required')
    if gpu_context is not None and not gpu:raise ValueError('GPU context requires explicit --gpu selection')
    if core and (gpu or native):raise ValueError('Core-only trial cannot request optional graphics')
    if not installed:sys.path.insert(0,str(ROOT/'src'))
    sys.path.insert(0,str(ROOT/'tools'))
    import azimlib as azl
    import azimlib.pyplot as plt
    from publication_privacy import findings
    from azimlib.renderers import render_image
    runtime=Path(azl.__file__).resolve().parent
    if installed and not runtime.is_relative_to(Path(sys.prefix).resolve()):raise ValueError('Installed trial imported source instead of the isolated package')
    if not installed and runtime!=ROOT/'src/azimlib':raise ValueError('Source trial imported an unrelated package')
    modules={name:load(name) for name in ('integration_040','lighting_maps','lunar_maps','solar_maps')}
    city,axes,state=modules['integration_040'].make_city();assert plt.gcf() is city
    figures=[('city',city),('urban-light',modules['lighting_maps'].make_urban()[0]),
        ('earth-moon',modules['lunar_maps'].make_system()[0]),('solar-globe',modules['solar_maps'].make_map('orthographic')[0]),
        ('volume-light',modules['lighting_maps'].make_volume()[0])]
    renderer=None;files=[];captures=[];timings=[];hardware=None
    try:
        if gpu:
            from azimlib.renderers.gpu import GpuRenderer,GpuConfig
            renderer=GpuRenderer(GpuConfig(context_backend=gpu_context));hardware=renderer.info
        for name,fig in figures:
            if core:fig.set_size_inches(2,1.5)
            start=time.perf_counter();scene=fig.to_scene(simplify=False);compose=time.perf_counter()-start
            formats=('pdf',) if core and name!='city' else ('svg','pdf')
            for kind in formats:
                filename=name+'.'+kind;fig.savefig(output/filename);files.append(filename)
            if not core:
                image=render_image(scene);filename=name+'-cpu.png';image.save(output/filename);image.close();files.append(filename)
            if renderer:
                image=renderer.render(scene);filename=name+'-gpu.png';image.save(output/filename);image.close();files.append(filename)
            timings.append(dict(scene=name,compose_seconds=compose,total_seconds=time.perf_counter()-start))
        route=state['route'];animation=route.playback(axes[0],frames=3,autoplay=False)
        try:
            animation.seek(0,draw=False);first=city.to_svg();animation.seek(2,draw=False);last=city.to_svg()
            if first==last:raise AssertionError('Route playback did not change map')
        finally:animation.close()
        if native:
            from validate_text_engine import capture_tk
            for backend in ('tk','qt'):
                viewer=city.show(backend=backend,block=False)
                try:
                    for _ in range(8):viewer.flush_events();time.sleep(.04)
                    viewer.draw();viewer.flush_events();filename=f'native-{backend}-city.png';path=output/filename
                    if backend=='tk':mode=capture_tk(viewer,path)
                    else:
                        expected={'Windows':'windows','Linux':'xcb','Darwin':'cocoa'}[platform.system()]
                        if viewer.application.platformName()!=expected:raise RuntimeError('Expected native Qt platform plugin')
                        if not viewer.window.grab().save(str(path)):raise RuntimeError('Own-window capture failed')
                        mode='own-native-qt-window-grab'
                    captures.append(dict(backend=backend,file=filename,mode=mode));files.append(filename)
                finally:viewer.close()
        if any(name.split('.')[0] in ('matplotlib','cartopy','shapely','pyproj','geopandas','folium') for name in sys.modules):raise AssertionError('External cartographic engine imported')
        if core and any(name.split('.')[0] in ('PIL','numpy','moderngl','uharfbuzz') for name in sys.modules):raise AssertionError('Core trial loaded optional provider')
        report=dict(passed=True,scope='Offline integration source/wheel trial; not hosted CI, human acceptance or publication',
            python=platform.python_version(),system=platform.system(),version=azl.__version__,installed=installed,core_only=core,
            hardware=hardware,native=captures,route_distance_m=route.distance_m,crs_max_degrees=state['crs_max_degrees'],
            route_playback_distinct=True,shared_pyplot_state=True,scene_count=len(figures),timings=timings,
            input_provenance=['Original synthetic city, terrain and volume: BSD-3-Clause','Bundled Natural Earth world layer: public domain; original notices retained','Bounded Azimlib solar/lunar models; no eclipse prediction'],
            source_sha256={p.relative_to(runtime).as_posix():sha(p) for p in sorted(runtime.rglob('*.py'))},
            example_sha256={name:sha(ROOT/'examples'/f'{name}.py') for name in modules},tool_sha256=sha(__file__),
            files={name:sha(output/name) for name in files})
        (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
        (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Azimlib 0.4 development integration</title>'
            '<h1>Offline integration review</h1><p>Compare text, margins, symbols, legend, scale, route clipping, '
            'solar terminator, opaque 3D bodies, local shadows and volume. CPU/GPU edge pixels may differ. '
            'Captures do not grant human platform acceptance; no real eclipse timing is claimed.</p>'
            +''.join(f'<p><img width="650" src="{name}-cpu.png" alt="{name}"></p>' for name,fig in figures if not core)
            +'<ul>'+''.join(f'<li><a href="{name}">{name}</a></li>' for name in files)+'</ul>',encoding='utf8')
        for path in output.iterdir():
            if findings(path.read_bytes()):raise RuntimeError('Generated integration evidence failed privacy scan')
        return report
    finally:
        if renderer:renderer.close()
        azl.close('all')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path)
    for option in ('installed','core','gpu','native'):p.add_argument('--'+option,action='store_true')
    p.add_argument('--gpu-context',choices=('egl',),help='Explicit headless context; no implicit environment selection')
    args=p.parse_args();r=validate(args.output,installed=args.installed,core=args.core,gpu=args.gpu,native=args.native,gpu_context=args.gpu_context)
    print(json.dumps({k:v for k,v in r.items() if k not in ('source_sha256','files','example_sha256')},indent=2))

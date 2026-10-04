"""Layout gate in real withdrawn Tk; programmatic toggles/resize/Home."""
import argparse,hashlib,importlib.util,io,json,platform,sys,tkinter
from pathlib import Path
from unittest.mock import patch
import azimlib as azl
from azimlib import renderers
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('layout_case',ROOT/'tools/layout_acceptance_case.py')
factory=importlib.util.module_from_spec(spec);spec.loader.exec_module(factory)


def run():
    original=tkinter.Tk;checks=[];frames=[]
    def hidden(*args,**kwargs):
        root=original(*args,**kwargs);root.withdraw();return root
    def frame(fig,viewer):
        report=factory.audit(viewer.scene)
        assert all(not report[key] for key in ('outside','collisions','text_collisions','crowded_ticks')),report
        with renderers.render_image(viewer.scene) as image:assert image.tobytes()==viewer._image.tobytes()
        output=io.BytesIO();svg=io.StringIO()
        with patch.object(tkinter,'Tk',side_effect=AssertionError('Static savefig creates no UI')):
            fig.savefig(output,format='png');fig.savefig(svg,format='svg')
        output.seek(0)
        with Image.open(output) as image:
            with image.convert('RGBA') as rgba:assert rgba.tobytes()==viewer._image.tobytes()
        assert '<script' not in svg.getvalue()
        frames.append(dict(size=viewer._image.size,rgba_sha256=hashlib.sha256(viewer._image.tobytes()).hexdigest()))
    for kind in factory.KINDS:
        for orientation in ('horizontal','vertical'):
            case=factory.build(kind,orientation,fontsize=14,dpi=100);fig=case['fig'];viewer=None
            name=kind+'-'+orientation
            try:
                with patch.object(tkinter,'Tk',hidden):viewer=fig.show(block=False)
                viewer.flush_events();home=[ax.get_extent() for ax in case['axes']]
                frame(fig,viewer);first=viewer._image.tobytes()
                checks.append(name+': initial layout/direct RGBA/static PNG/Tk agree; static SVG/PNG create no UI')
                artists=[*case['legends'],case['bar'],case['scale'],case['north'],case['compass'],case['heading'],case['globalx'],case['globaly']]
                if case['overview'] is not None:artists.append(case['overview'])
                with azl.ion():
                    for artist in artists:artist.set_visible(False)
                viewer.flush_events();assert viewer._image.tobytes()!=first
                with azl.ion():
                    for artist in artists:artist.set_visible(True)
                viewer.flush_events();assert viewer._image.tobytes()==first
                checks.append(name+': all opt-in decorations hide/restore with exact original pixels')
                before=[ax.get_extent() for ax in case['axes']]
                width,height=fig.get_size_inches()
                fig.set_size_inches(width+.6,height+.4);fig.set_dpi(200);viewer.flush_events()
                assert viewer._image.size==tuple(round(v*200) for v in fig.get_size_inches())
                assert [ax.get_extent() for ax in case['axes']]==before
                frame(fig,viewer);resized=viewer._image.tobytes()
                checks.append(name+': physical resize at 200 DPI reflows components and preserves extents')
                for ax in case['axes']:ax.set_extent((-52,-44,-26,-18))
                viewer.navigation.push();viewer.draw()
                viewer.home();viewer.flush_events()
                assert [ax.get_extent() for ax in case['axes']]==home
                assert viewer._image.tobytes()==resized
                frame(fig,viewer)
                if case['overview'] is not None:
                    mini=viewer.scene.maps[-1]['overview_map']
                    assert viewer.scene.items[mini['focus_index']].style['stroke']=='black'
                checks.append(name+': focus/Home restore exact resized scene; overview focus remains black')
            finally:
                if viewer is not None:
                    viewer.close();assert viewer._raster_cache.bytes==0
                azl.close(fig);azl.ioff()
            checks.append(name+': close releases raster cache')
    assert not any(name.split('.')[0] in ('matplotlib','cartopy','geopandas','shapely','pyproj') for name in sys.modules)
    modules=('layout_engine','nested_layout','colorbar_render','render_map','overview','scene','figure','backends.tk')
    hashes={'src/azimlib/'+m.replace('.','/')+'.py':hashlib.sha256(Path(__import__('azimlib.'+m,fromlist=['__file__']).__file__).read_bytes()).hexdigest() for m in modules}
    hashes.update({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'tools/layout_acceptance_case.py',Path(__file__))})
    return dict(python=platform.python_version(),platform=platform.platform(),checks=checks,frames=frames,sha256=hashes,
                runtime_origin=str(Path(azl.__file__).resolve().parent),independent_runtime=True,
                scope='Six real withdrawn Tk scenarios, 30 checks and 18 frame comparisons. Programmatic edits/navigation; no physical input or visible-paint latency.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();report=run()
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{len(report["checks"])} Tk checks passed')

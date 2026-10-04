"""Generate the regional/atlas/nested large-font component matrix."""
import hashlib,importlib.util,json,warnings
from pathlib import Path
import azimlib as azl

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('layout_case',ROOT/'tools/layout_acceptance_case.py')
factory=importlib.util.module_from_spec(spec);spec.loader.exec_module(factory)


def main():
    rows=[]
    for kind in factory.KINDS:
        for orientation in ('horizontal','vertical'):
            for fontsize in (14,18):
                for dpi in (100,200):
                    case=factory.build(kind,orientation,fontsize=fontsize,dpi=dpi);fig=case['fig']
                    try:
                        with warnings.catch_warnings(record=True) as caught:
                            warnings.simplefilter('always');scene=fig.to_scene(cull=True)
                        audit=factory.audit(scene)
                        assert not caught and all(not audit[key] for key in ('outside','collisions','text_collisions','crowded_ticks')),(kind,orientation,fontsize,dpi,audit,caught)
                        row=dict(kind=kind,orientation=orientation,fontsize=fontsize,dpi=dpi,figsize=fig.figsize,**audit)
                        # Six representative exports; all 24 scenes measured.
                        if fontsize==18 and dpi==200:
                            row['exports']={};stem='layout-acceptance-'+kind+'-'+orientation
                            for ext in ('png','svg','html'):
                                path=ROOT/'gallery'/f'{stem}.{ext}'
                                if ext=='html':path.write_text(fig.to_html(),encoding='utf-8')
                                else:fig.savefig(path)
                                row['exports'][str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
                        rows.append(row)
                    finally:azl.close(fig)
    modules=('layout_engine','nested_layout','colorbar_render','render_map','overview','scene','figure','typography')
    hashes={'src/azimlib/'+m+'.py':hashlib.sha256(Path(__import__('azimlib.'+m,fromlist=['__file__']).__file__).read_bytes()).hexdigest() for m in modules}
    hashes.update({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'tools/layout_acceptance_case.py',Path(__file__))})
    report=dict(cases=rows,sha256=hashes,scope='24 scene audits; six PNG/SVG/HTML sets. Bundled generalized boundaries; synthetic route. No pixel equality with Matplotlib or physical GUI validation.')
    (ROOT/'docs/layout-acceptance-matrix.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('24 scene audits; six 200-DPI PNG/SVG/HTML sets generated')


if __name__=='__main__':main()

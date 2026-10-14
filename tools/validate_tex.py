"""Explicit offline real-TeX review packet; no acquisition or publication."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]


def validation_config(engine, converter, cache, **kwargs):
    """Only for the documented default Latin Modern + AMS Type 1 specimen."""
    from azimlib import TexConfig, Provenance
    notices = (
        Provenance('https://ctan.org/pkg/lm','LicenseRef-GUST-Font',
            'Latin Modern Project authors; see upstream font distribution',
            license_text=(ROOT/'licenses/Latin-Modern.txt').read_text('utf8')+'\n'+
                         (ROOT/'licenses/LPPL-1.3c.txt').read_text('utf8')),
        Provenance('https://ctan.org/pkg/amsfonts','OFL-1.1',
            'Copyright (c) 1997, 2009, American Mathematical Society',
            license_text=(ROOT/'licenses/AMSFonts.txt').read_text('utf8')))
    return TexConfig(executable=engine,converter=converter,cache_dir=cache,
                     trusted=True,allow_outlines=True,font_notices=notices,**kwargs)


def make_packet(output, config):
    import azimlib as azl
    from azimlib.scene import Scene, Text
    from azimlib.renderers import render_png, render_pdf, render_svg
    from azimlib.tex import tex_layout
    from publication_privacy import findings
    output=Path(output)
    if output.exists(): raise FileExistsError('Use a new TeX review destination')
    output.mkdir(parents=True)
    spec=importlib.util.spec_from_file_location('tex_example',ROOT/'examples/tex_cartography.py')
    example=importlib.util.module_from_spec(spec);spec.loader.exec_module(example)
    fig=example.make(config);files=[]
    try:
        for dpi in (100,200):
            for extension in ('png','svg','pdf'):
                name=f'tex-map-{dpi}dpi.{extension}';fig.savefig(output/name,dpi=dpi);files.append(name)
        name='tex-map.html';(output/name).write_text(fig.to_html(),encoding='utf8',newline='\n');files.append(name)
        sample=Scene(800,320)
        cases=[r'Text and $\alpha+\beta=\gamma$',r'$\displaystyle\frac{1}{2}\int_0^{\infty}e^{-x^2}\,dx$',
               r'$\displaystyle\sum_{k=1}^{n} k^2=\frac{n(n+1)(2n+1)}{6}$',
               r'$\displaystyle\sqrt{a^2+b^2}\quad\begin{pmatrix}a&b\\c&d\end{pmatrix}$']
        metrics=[]
        for row,text in enumerate(cases):
            style=dict(textengine='tex',texconfig=config,font_size=22,fill='#147d92')
            item=Text(30,45+row*75,text,style);sample.add(item)
            layout=tex_layout(item.text,style)
            metrics.append(dict(text=text,width_em=layout.width,ascent_em=layout.ascent,
                descent_em=layout.descent,identity=layout.identity,commands=len(layout.commands),
                resources=[dict(p) for p in layout.notices],jobs=[dict(p) for p in layout.metrics]))
        render_png(sample,output/'tex-specimens.png');render_pdf(sample,output/'tex-specimens.pdf')
        (output/'tex-specimens.svg').write_text(render_svg(sample),encoding='utf8',newline='\n')
        files.extend(['tex-specimens.png','tex-specimens.pdf','tex-specimens.svg'])
        manifest=dict(schema_version=1,stage='8.08',status='local-evidence-not-multiplatform-human-acceptance',
            system=platform.system(),python=platform.python_version(),specimens=metrics,
            source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in sorted((ROOT/'src/azimlib').rglob('*.py'))},
            files={name:hashlib.sha256((output/name).read_bytes()).hexdigest() for name in files})
        (output/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=True)+'\n',encoding='utf8',newline='\n')
        links=''.join(f'<li><a href="{name}">{name}</a></li>' for name in files)
        (output/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Azimlib real TeX review</title><h1>Real TeX — review pending</h1><p>Offline Tectonic and pdftocairo; common vector contours in PNG/SVG/PDF. Compare baselines, fractions, roots, matrices, rotations, DPI and font notices.</p><img src="tex-specimens.png" width="800" alt="TeX specimens"><ul>'+links+'</ul>',encoding='utf8',newline='\n')
        for path in output.iterdir():
            if findings(path.read_bytes()): raise RuntimeError('TeX review privacy audit failed')
        return manifest
    finally: azl.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine',required=True);parser.add_argument('--converter',required=True)
    parser.add_argument('--cache',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
    result=make_packet(args.output,validation_config(args.engine,args.converter,args.cache))
    print(json.dumps(dict(system=result['system'],files=len(result['files']),status=result['status'])))

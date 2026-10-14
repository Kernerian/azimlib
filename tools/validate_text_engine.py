"""Generate an offline, privacy-audited 0.4 multilingual visual review packet.

Static generation and native captures are evidence, never human acceptance.
Run on the source tree explicitly; optional font acquisition is a separate step.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys
import time

ROOT=Path(__file__).resolve().parents[1]


def capture_tk(viewer,target):
    """Capture only the application, and reject an occluded/unrelated canvas."""
    from PIL import ImageGrab,ImageChops,ImageStat
    window=viewer.window;window.deiconify();window.lift();window.update()
    if platform.system()=='Windows':
        import ctypes
        from ctypes import wintypes
        user32=ctypes.windll.user32
        user32.GetAncestor.argtypes=[wintypes.HWND,wintypes.UINT]
        user32.GetAncestor.restype=wintypes.HWND
        hwnd=user32.GetAncestor(window.winfo_id(),2)
        origin=wintypes.POINT(0,0)
        if not hwnd or not user32.ClientToScreen(wintypes.HWND(hwnd),ctypes.byref(origin)):
            raise RuntimeError('Native Tk window bounds unavailable')
        image=ImageGrab.grab(window=int(hwnd));origin=(origin.x,origin.y)
        mode='verified-native-window-handle-grab'
    else:
        # Rectangle grabs are allowed only on a controlled hosted runner,
        # never on an ordinary developer desktop containing other apps.
        if os.environ.get('GITHUB_ACTIONS')!='true':
            raise RuntimeError('Tk rectangle capture requires the isolated GitHub Actions desktop')
        x,y=window.winfo_rootx(),window.winfo_rooty();w,h=window.winfo_width(),window.winfo_height()
        kwargs={'bbox':(x,y,x+w,y+h)}
        if platform.system()=='Linux':kwargs['xdisplay']=''
        if platform.system()=='Darwin':kwargs['scale_down']=True
        image=ImageGrab.grab(**kwargs);origin=(x,y)
        mode='verified-controlled-runner-window-crop'
    try:
        cx=viewer.widget.winfo_rootx()-origin[0];cy=viewer.widget.winfo_rooty()-origin[1]
        expected=viewer._image.convert('RGB')
        actual=image.crop((cx,cy,cx+expected.width,cy+expected.height)).convert('RGB')
        try:
            if max(ImageStat.Stat(ImageChops.difference(actual,expected)).mean)>5:
                raise RuntimeError('Tk capture does not show the Azimlib canvas; nothing saved')
        finally:expected.close();actual.close()
        image.save(target)
    finally:image.close()
    return mode


def make_packet(output,fonts,*,native=False):
    sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tools'))
    import azimlib as azl
    from azimlib.scene import Scene,Text
    from azimlib.renderers import render_png,render_svg,render_pdf
    from azimlib.text_engine import shape_text
    from acquire_text_fonts import register_acquired
    from publication_privacy import findings
    records=register_acquired(fonts)
    spec=importlib.util.spec_from_file_location('multilingual_example',ROOT/'examples/multilingual_text.py')
    example=importlib.util.module_from_spec(spec);spec.loader.exec_module(example)
    output=Path(output)
    if output.exists():raise FileExistsError('Visual packet requires a new destination')
    output.mkdir(parents=True)
    fig=example.make();files=[]
    try:
        for dpi in (100,200):
            for extension in ('png','svg','pdf'):
                file=output/f'multilingual-map-{dpi}dpi.{extension}'
                fig.savefig(file,dpi=dpi);files.append(file.name)
        (output/'multilingual-map.html').write_text(fig.to_html(),encoding='utf8',newline='\n');files.append('multilingual-map.html')
        sample=Scene(900,460)
        style=dict(textengine='harfbuzz',font_size=26,fontfallback=tuple(r.family for r in records))
        cases=['São Paulo · Á · office / fi / ffi','العربية: القاهرة 123 — abc','abc אבג 123 (LTR/RTL)','नमस्ते भारत · प्रिया','中文地图 · 日本語 · 東京']
        shapes=[]
        for row,text in enumerate(cases):
            sample.add(Text(25,50+row*70,text,style))
            line=shape_text(text,style);shapes.append(dict(text=text,glyphs=len(line.glyphs),width_em=line.width,
                runs=[dict(start=r.start,end=r.end,direction=r.direction,script=r.script,font_id=r.font) for r in line.runs]))
        sample.add(Text(730,260,'東京 / العربية',dict(style,rotation=90,anchor='middle')))
        render_png(sample,output/'specimens.png');(output/'specimens.svg').write_text(render_svg(sample),encoding='utf8',newline='\n')
        render_pdf(sample,output/'specimens.pdf');files.extend(['specimens.png','specimens.svg','specimens.pdf'])
        captures=[]
        if native:
            for backend in ('tk','qt'):
                viewer=fig.show(backend=backend,block=False)
                try:
                    for _ in range(10):viewer.flush_events();time.sleep(.04)
                    viewer.draw();viewer.flush_events()
                    target=output/f'{backend}-multilingual-native.png'
                    if backend=='qt':
                        expected={'Linux':'xcb','Darwin':'cocoa','Windows':'windows'}[platform.system()]
                        if viewer.application.platformName()!=expected:raise RuntimeError('Expected a native Qt platform plugin')
                        if not viewer.window.grab().save(str(target)):raise RuntimeError('Qt capture failed')
                        mode='native-qt-window-grab'
                    else:
                        mode=capture_tk(viewer,target)
                    captures.append(dict(backend=backend,file=target.name,mode=mode))
                    files.append(target.name)
                finally:viewer.close()
        manifest=dict(schema_version=1,stage='7.08',status='awaiting-three-platform-human-approval',
            python=platform.python_version(),system=platform.system(),engines=dict(shape_text('office',style).engines),
            fonts=[r.notice() for r in records],shapes=shapes,native=captures,
            source_sha256={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted((ROOT/'src/azimlib').rglob('*.py'))},
            files={name:hashlib.sha256((output/name).read_bytes()).hexdigest() for name in files})
        (output/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=True)+'\n',encoding='utf8',newline='\n')
        links=''.join(f'<li><a href="{name}">{name}</a></li>' for name in files)
        (output/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Azimlib complex text review</title><h1>Stage 7.08 — human approval pending</h1><p>Compare each platform at full size. Same pinned fonts and source are required; ICU/HarfBuzz versions are recorded. These are Azimlib exports, not Matplotlib references.</p><img src="specimens.png" width="900" alt="Multilingual type specimens"><ul>'+links+'</ul></html>',encoding='utf8',newline='\n')
        shutil_source=ROOT/'docs/text-review-0.4.md'
        (output/'review-guide.md').write_bytes(shutil_source.read_bytes())
        (output/'README.md').write_text('# Stage 7.08 — human review pending\n\nCompare PNG/SVG/PDF at 100/200 dpi, accents, Arabic joining and marks, mixed Hebrew/numbers/punctuation, Devanagari pre-base vowels/conjuncts, CJK glyph coverage, rotations, labels on curves, legend and colorbar. Verify native Tk/Qt captures, then mouse pan/zoom/Home in each OS. Logical text is in SVG descriptions and PDF ActualText; copy/search support depends on the reader. Preserve font license notices. Approval is required separately for Windows, Linux and macOS; screenshots are not a latency test.\n',encoding='utf8',newline='\n')
        bad={p.name:findings(p.read_bytes()) for p in output.iterdir() if p.is_file()}
        if any(bad.values()):raise RuntimeError('Visual packet privacy audit failed: '+repr(bad))
        return manifest
    finally:azl.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path);parser.add_argument('--fonts',required=True,type=Path)
    parser.add_argument('--native',action='store_true');args=parser.parse_args()
    result=make_packet(args.output,args.fonts,native=args.native)
    print(json.dumps(dict(system=result['system'],engines=result['engines'],files=len(result['files']),status=result['status'])))

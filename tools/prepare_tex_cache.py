"""Explicitly acquire only TeX resources for the documented validation scenes.

This developer tool may access the network only with --acquire. The library
always compiles with --only-cached and has no downloader/installer fallback.
Executable installation is a separate explicit administrator/user operation.
"""
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def prepare(engine,converter,cache,report,*,acquire=False):
    if not acquire: raise ValueError('Resource acquisition requires explicit --acquire')
    from validate_tex import validation_config
    from azimlib.tex import _document,_resources,_tool
    from azimlib._tex_process import run_tool,tree_bytes
    cache=Path(cache).resolve();report=Path(report)
    if report.exists(): raise FileExistsError('Use a new acquisition report')
    if shutil.disk_usage(cache.parent).free<16*1024**3:
        raise ValueError('Preserve at least 15 GiB free plus the bounded acquisition budget')
    cache.mkdir(exist_ok=True)
    config=validation_config(engine,converter,cache,timeout=120,max_temp_bytes=128*1024**2)
    executable,tool_hash=_tool(config.executable);_tool(config.converter)
    # One-page warmup, all optical sizes/styles used by the public specimen.
    # This is intentionally fixed, never a command supplied by a remote user.
    fragments=[]
    for size in (7,8,9,10,12,14,15,15.84,20,24):
        for font in ('',r'\bfseries ',r'\itshape '):
            fragments.append(r'\fontsize{'+str(size)+r'bp}{30bp}\selectfont '+font+
                r'Text 0123456789 $\displaystyle\frac{1}{2}\int_0^{\infty}e^{-x^2}\,dx'
                r'+\sum_{k=1}^n k^2+\sqrt{a^2+b^2}+\partial f+\rho+\lambda+\varphi'
                r'+\begin{pmatrix}a&b\\c&d\end{pmatrix}$\par')
    document=r'\documentclass{article}\usepackage{amsmath}\begin{document}'+''.join(fragments)+r'\end{document}'
    with tempfile.TemporaryDirectory(prefix='azimlib-tex-acquire-') as temporary:
        job=Path(temporary);(job/'warmup.tex').write_text(document,encoding='utf8')
        metrics=run_tool([executable,'-X','compile','--untrusted','--keep-logs','--reruns','0','warmup.tex'],
                         job,config,'acquisition.log',acquire=True)
    result=dict(schema_version=1,engine='Tectonic',executable_sha256=tool_hash,
                cache_sha256=_resources(config),cache_bytes=tree_bytes(cache,config.max_cache_bytes),
                explicit_acquisition=True,metrics=metrics)
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine',required=True);parser.add_argument('--converter',required=True)
    parser.add_argument('--cache',required=True,type=Path);parser.add_argument('--report',required=True,type=Path)
    parser.add_argument('--acquire',action='store_true');args=parser.parse_args()
    sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
    print(json.dumps(prepare(args.engine,args.converter,args.cache,args.report,acquire=args.acquire)))

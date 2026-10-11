"""Run offline contracts in the explicitly activated native TeX environment."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


def run(cache):
    root=Path(__file__).resolve().parents[1]
    tools={name:shutil.which(name) for name in ('tectonic','pdftocairo')}
    if not all(tools.values()):raise RuntimeError('Activated validation environment must provide Tectonic and pdftocairo')
    env=os.environ.copy()
    env.update(AZIMLIB_TEX_ENGINE=tools['tectonic'],AZIMLIB_TEX_CONVERTER=tools['pdftocairo'],
               AZIMLIB_TEX_CACHE=str(Path(cache).resolve()))
    subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_tex_040.py','-v'],
                   cwd=root,env=env,check=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cache',required=True,type=Path)
    run(p.parse_args().cache)

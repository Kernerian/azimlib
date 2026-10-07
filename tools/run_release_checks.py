"""Run installed-package unit/desktop checks and retain machine-readable evidence.

Used by GitHub Actions and local validation. A local execution never becomes a
remote CI result. Desktop smokes use withdrawn Tk/synthetic handlers, not human
input or visible-appearance approval.
"""

import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from publication_privacy import public_path,sanitize_text
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
DESKTOP=(
    'smoke_artist_tk.py','smoke_viewer_tk.py','smoke_component_lifecycle_tk.py',
    'smoke_composition_tk.py','smoke_series_tk.py','smoke_numeric_tk.py',
    'smoke_artist_validation_tk.py','smoke_raster_cache_tk.py',
    'smoke_stroke_kernels_tk.py','smoke_artist_acceptance_tk.py',
    'smoke_layout_acceptance_tk.py','smoke_toolbar_tk.py','smoke_pan_interaction_tk.py',
    'smoke_transform_composition_tk.py',
)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


class Results(unittest.TextTestResult):
    subtests=0
    def addSubTest(self,test,subtest,error):
        self.subtests+=1
        super().addSubTest(test,subtest,error)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind',choices=('unit','accelerator','desktop'),required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--scripts',nargs='+',choices=DESKTOP,help='Rerun selected failed desktop scripts; report retains the selected set')
    parser.add_argument('--desktop-timeout',type=int,default=900,help='Seconds per desktop script; large exact 200-DPI layouts can exceed five minutes')
    args=parser.parse_args();args.output=args.output.resolve();args.output.mkdir(parents=True,exist_ok=True)
    if args.desktop_timeout<=0 or (args.scripts and args.kind!='desktop'):parser.error('Positive timeout; script selection applies only to desktop checks')
    import azimlib as azl
    runtime=Path(azl.__file__).resolve().parent
    if not runtime.is_relative_to(Path(sys.prefix).resolve()):
        raise SystemExit('Install the wheel/package in this environment; source imports are not release installation evidence.')
    packages={}
    for name in ('Pillow','aggdraw','numpy','numba','llvmlite'):
        try:packages[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:packages[name]=None
    remote=os.environ.get('GITHUB_ACTIONS')=='true' and bool(os.environ.get('GITHUB_RUN_ID'))
    report=dict(schema_version=1,started_utc=datetime.now(timezone.utc).isoformat(),kind=args.kind,
        execution_context='github-actions' if remote else 'local',
        python=platform.python_version(),platform=platform.platform(),machine=platform.machine(),
        version=azl.__version__,runtime_origin=public_path(runtime),optional_packages=packages,
        tool_sha256=sha(Path(__file__)),runtime_sha256={p.relative_to(runtime).as_posix():sha(p) for p in sorted(runtime.rglob('*.py'))},
        github={key:os.environ.get(key) for key in ('GITHUB_REPOSITORY','GITHUB_SHA','GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT','GITHUB_JOB','RUNNER_OS','RUNNER_ARCH')} if remote else None,
        scope='Installed runtime; unit checks or real withdrawn Tk/synthetic handlers. Local results are not remote CI; desktop results are not native human appearance/input approval.')
    start=time.perf_counter();passed=True
    if args.kind=='desktop':
        scripts=[]
        report['desktop_timeout_seconds']=args.desktop_timeout
        for name in args.scripts or DESKTOP:
            command=[sys.executable,'-I',str(ROOT/'tools'/name)]
            output=args.output/(Path(name).stem+'.json')
            if name!='smoke_artist_tk.py':command+=['--output',str(output)]
            began=time.perf_counter();environment=os.environ.copy();environment.pop('PYTHONPATH',None);environment.pop('PYTHONHOME',None)
            child=subprocess.Popen(command,cwd=ROOT,env=environment,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                text=True,encoding='utf-8',errors='replace',start_new_session=os.name!='nt')
            try:
                stdout,stderr=child.communicate(timeout=args.desktop_timeout)
                code=child.returncode;log=stdout+'\n'+stderr
            except subprocess.TimeoutExpired:
                # Terminate our process tree before the Windows venv redirector
                # disappears; killing just that launcher can leave a pixel worker.
                if child.poll() is None:
                    if os.name=='nt':subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True,timeout=30)
                    else:os.killpg(child.pid,signal.SIGKILL)
                stdout,stderr=child.communicate(timeout=30)
                code=124;log=f'Timeout after {args.desktop_timeout} seconds\n'+stdout+'\n'+stderr
            log_path=args.output/(Path(name).stem+'.log');log_path.write_text(sanitize_text(log),encoding='utf-8')
            row=dict(tool=name,sha256=sha(ROOT/'tools'/name),returncode=code,seconds=time.perf_counter()-began,log_sha256=sha(log_path))
            if output.exists():row.update(report_file=output.name,report_sha256=sha(output))
            scripts.append(row);passed=passed and code==0
            print(f'{name}: {"PASS" if code==0 else "FAIL"}',flush=True)
        report['scripts']=scripts
    else:
        loader=unittest.TestLoader()
        if args.kind=='unit':suite=loader.discover(str(ROOT/'tests'))
        else:
            if not packages['numba']:raise SystemExit('Accelerator job requires the optional compiler; skipped compilation is not accelerator evidence.')
            suite=unittest.TestSuite(loader.discover(str(ROOT/'tests'),pattern=name) for name in ('test_native_coverage.py','test_pan_raster.py'))
        log_path=args.output/'unittest.log'
        with log_path.open('w',encoding='utf-8') as stream:
            result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=Results).run(suite)
        log_path.write_text(sanitize_text(log_path.read_text(encoding='utf-8')),encoding='utf-8')
        passed=result.wasSuccessful()
        report['unittest']=dict(tests=result.testsRun,subtests=result.subtests,failures=len(result.failures),errors=len(result.errors),
            skipped=[dict(test=str(test),reason=reason) for test,reason in result.skipped],log_sha256=sha(log_path))
        print(f'{result.testsRun} tests / {result.subtests} subtests; {"PASS" if passed else "FAIL"}',flush=True)
    forbidden={'matplotlib','cartopy','geopandas','shapely','pyproj','folium','rasterio','fiona','geographiclib'}
    imports=sorted(name for name in sys.modules if name.split('.')[0] in forbidden)
    report.update(seconds=time.perf_counter()-start,passed=passed and not imports,forbidden_imports=imports)
    (args.output/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if report['passed'] else 1)


if __name__=='__main__':main()

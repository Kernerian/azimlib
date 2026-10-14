"""Separate unpublished preparation from explicitly accepted scoped publication."""
import argparse,importlib.util,re
from pathlib import Path
from packaging.version import Version
import azimlib
ROOT=Path(__file__).resolve().parents[1]
def scope_check(text):
    spec=importlib.util.spec_from_file_location('progress040',ROOT/'tools/check_release_progress_040.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.check(text)
def check(version,progress,*,purpose='publish'):
    v=Version(version)
    if purpose not in ('publish','prepare'):raise AssertionError('Explicit known purpose required')
    if v.is_devrelease or v.is_prerelease:raise AssertionError('Stable candidate rejects prerelease metadata')
    if v.release[:2]==(0,4):
        try:state=scope_check(progress)
        except ValueError as exc:raise AssertionError(str(exc)) from exc
        if set(state['deferred'])!={'2.08','9.08','13.06','13.07'} or state['active_total']!=108:
            raise AssertionError('0.4 requires exactly four explicit preserved deferments and 108 active IDs')
        pending=set(state['pending'])
        if purpose=='publish' and (pending or state['completed']!=108):
            raise AssertionError('Publication requires all 108 active IDs, including human and final acceptance')
        if purpose=='prepare' and pending-{'14.04','14.05','14.07','14.08'}:
            raise AssertionError('Unpublished preparation still requires integrated regression, docs, benchmarks and audit')
        return str(v)
    if v.release[:2]!=(0,3) or purpose!='publish':raise AssertionError('No validated checklist contract for this version/purpose')
    entries=re.findall(r'^- \[([ x])\] \*\*(\d+\.\d{2})\*\*',progress,re.M)
    expected={f'{step}.{n:02}' for step in range(1,11) for n in range(1,9)}
    if len(entries)!=80 or {entry[1] for entry in entries}!=expected or any(state!='x' for state,item in entries):
        raise AssertionError('Every 0.3 release gate requires completion')
    return str(v)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--purpose',choices=('publish','prepare'),default='publish');a=p.parse_args()
    series='.'.join(str(n) for n in Version(azimlib.__version__).release[:2])
    print(a.purpose+':',check(azimlib.__version__,(ROOT/f'docs/release-progress-{series}.md').read_text('utf8'),purpose=a.purpose))

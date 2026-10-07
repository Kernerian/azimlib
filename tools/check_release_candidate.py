"""Reject stable publication before explicit final version/checklist acceptance."""
import re
from pathlib import Path
from packaging.version import Version
import azimlib
ROOT=Path(__file__).resolve().parents[1]
def check(version,progress):
    v=Version(version)
    assert not v.is_devrelease and not v.is_prerelease,'Stable publication rejects development/pre-release metadata'
    if v.release[:2]==(0,3):
        entries=re.findall(r'^- \[([ x])\] \*\*(\d+\.\d{2})\*\*',progress,re.M)
        expected={f'{step}.{n:02}' for step in range(1,11) for n in range(1,9)}
        assert len(entries)==80 and {entry[1] for entry in entries}==expected,'Complete release checklist required'
        pending=re.findall(r'^- \[ \] \*\*(\d+\.\d{2})\*\*',progress,re.M)
        assert not pending,'0.3.0 requires every release gate, including 7.08 and 10.08'
    return str(v)
if __name__=='__main__':
    print('Stable candidate:',check(azimlib.__version__,(ROOT/'docs/release-progress-0.3.md').read_text('utf8')))

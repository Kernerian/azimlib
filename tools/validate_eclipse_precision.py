"""Independent eclipse precision gate; reference input stays outside checkout.

This diagnostic may succeed while the scientific gate fails. Never interpret
execution success as permission to close the real-event validation checklist.
"""
import argparse,hashlib,json,re,shutil,sys
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import urlopen
ROOT=Path(__file__).resolve().parents[1]
SOURCE='https://eclipse.gsfc.nasa.gov/SEhistory/SEpath/SE2024Apr08Tpath.html'
# Fixed before acquisition; a screen-sized approximation is not a path gate.
MAX_CENTRAL_SEPARATION_DEGREES=.01
MAX_RESIDUAL_VISIBLE_FRACTION=.001
MAX_MODEL_BUDGET_DEGREES=.01

def validate(folder,fetch=False):
    folder=folder.resolve()
    if folder==ROOT or ROOT in folder.parents:raise ValueError('Raw reference must remain outside checkout')
    folder.mkdir(parents=True,exist_ok=True);path=folder/'nasa-2024-path.html'
    if fetch and not path.exists():
        if shutil.disk_usage(folder).free<15_002_000_000:raise RuntimeError('15 GB reserve required')
        with urlopen(SOURCE,timeout=60) as stream:raw=stream.read(2_000_001)
        if len(raw)>2_000_000:raise ValueError('Reference exceeds 2 MB')
        path.write_bytes(raw)
    raw=path.read_bytes()
    if len(raw)>2_000_000:raise ValueError('Reference exceeds 2 MB')
    text=raw.decode('utf8');sys.path.insert(0,str(ROOT/'src'));import azimlib as azl
    model=azl.LunarModel(time_policy='utc-approx');results=[]
    for line in text.splitlines():
        time=re.match(r'\s*(\d{2}):(\d{2})\s+',line)
        pairs=re.findall(r'(\d+)\s+(\d+\.\d+)([NS])\s+(\d+)\s+(\d+\.\d+)([EW])',line)
        if time is None or len(pairs)!=3:continue
        a,b,ns,c,d,ew=pairs[-1];lat=(int(a)+float(b)/60)*(-1 if ns=='S' else 1);lon=(int(c)+float(d)/60)*(-1 if ew=='W' else 1)
        instant=datetime(2024,4,8,*map(int,time.groups()),tzinfo=timezone.utc)
        geometry=azl.EclipseGeometry.from_moon(model.position(instant));result=geometry.solar(azl.SolarObserver(lon,lat))
        results.append((result.separation_degrees,result.visible_fraction,result.classification,geometry.angular_uncertainty_degrees))
    if len(results)<80:raise ValueError('Expected full two-minute central-line reference rows')
    separation=max(v[0] for v in results);residual=max(v[1] for v in results);budget=max(v[3] for v in results)
    gate=separation<=MAX_CENTRAL_SEPARATION_DEGREES and residual<=MAX_RESIDUAL_VISIBLE_FRACTION and budget<=MAX_MODEL_BUDGET_DEGREES
    return dict(passed=gate,diagnostic_execution_passed=True,real_event_gate_passed=gate,
        reference=dict(source=SOURCE,author='Fred Espenak, NASA GSFC',sha256=hashlib.sha256(raw).hexdigest(),rows=len(results),cadence_seconds=120,frame='WGS84',time='Universal Time interpreted as approximate UTC; no precision clock claim'),
        maximum_central_separation_degrees=separation,maximum_residual_visible_fraction=residual,
        central_line_totality_misses=sum(v[2]!='umbra' for v in results),maximum_model_budget_degrees=budget,
        required=dict(separation_degrees=MAX_CENTRAL_SEPARATION_DEGREES,residual_visible_fraction=MAX_RESIDUAL_VISIBLE_FRACTION,model_budget_degrees=MAX_MODEL_BUDGET_DEGREES),
        contact_timing_validated=False,lunar_event_timing_validated=False,
        pending=['13.06','13.07'],raw_reference_distributed=False,
        limitations=['One independent solar event is a counterexample, not a global precision survey',
            'Central angular separation is not a measured ground-track distance',
            'No contact solver or precise eclipse ephemeris is implemented',
            'Synthetic and opt-in approximate illustrations are not validated event predictions'])

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reference-dir',type=Path,required=True);p.add_argument('--fetch',action='store_true');p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    report=validate(args.reference_dir,args.fetch);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps(report,indent=2));sys.exit(0 if report['real_event_gate_passed'] else 3)

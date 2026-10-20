"""Evaluate the frozen Phase B corpus without importing the oracle libraries."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import azimlib as azl


def validate(output):
    path=Path(__file__).resolve().parents[1]/'tests/fixtures/surfaces-050.json'
    raw=path.read_bytes();fixture=json.loads(raw);t=fixture['tolerances'];rows=[]
    def surface(key):return azl.BodySurface(azl.PlanetaryContext.for_body(azl.BODIES.get(key),latitude_type='planetographic'))
    def angle(a,b):return abs((a-b+180)%360-180)
    for r in fixture['projections']:
        s=surface(r['body']);p=s.projection(r['method'],**r['parameters']);q=p.forward(*r['input'])
        valid=r['xy'] is not None and r['within_declared_domain']
        if not valid:
            assert q is None,r;rows.append(dict(body=r['body'],metric='projection domain',method=r['method'],pass_check=True));continue
        error=math.dist(q,r['xy']);budget=t['tm_xy_m'] if r['method']=='transverse_mercator' else t['sphere_xy_m'] if s.body.shape=='sphere' else t['oblate_xy_m']
        inv=p.inverse(*q);inverse=max(angle(inv[0],r['input'][0]),abs(inv[1]-r['input'][1]))
        rows.append(dict(body=r['body'],metric='projection_m',method=r['method'],input=r['input'],error=error,budget=budget,pass_check=error<=budget))
        rows.append(dict(body=r['body'],metric='inverse_deg',method=r['method'],error=inverse,budget=t['inverse_deg'],pass_check=inverse<=t['inverse_deg']))
    for r in fixture['geodesics']:
        q=surface(r['body']).inverse(r['start'],r['end']);error=abs(q.distance-r['distance_m']);budget=t['difficult_distance_m'] if r['difficult'] else t['distance_m']
        rows.append(dict(body=r['body'],metric='distance_m',error=error,budget=budget,pass_check=error<=budget))
        if not r['ambiguous']:
            error=max(angle(q.azimuth1,r['azimuth1']),angle(q.azimuth2,r['azimuth2']))
            rows.append(dict(body=r['body'],metric='azimuth_deg',error=error,budget=t['azimuth_deg'],pass_check=error<=t['azimuth_deg']))
    for r in fixture['areas']:
        error=abs(surface(r['body']).polygon_area(r['vertices'])-r['area_m2']);budget=max(t['area_abs_m2'],r['area_m2']*t['area_relative'])
        rows.append(dict(body=r['body'],metric='area_m2',error=error,relative_error=error/r['area_m2'],budget=budget,pass_check=error<=budget))
    for r in fixture['normals']:
        light=azl.GeometricLight(surface(r['body']).context,direction=(1,2,3));error=math.dist(light.normal(*r['input']),r['normal'])
        rows.append(dict(body=r['body'],metric='normal',error=error,budget=1e-10,pass_check=error<=1e-10))
    aggregates={}
    for metric in sorted({r['metric'] for r in rows if 'error' in r}):
        values=sorted(r['error'] for r in rows if r['metric']==metric)
        aggregates[metric]=dict(count=len(values),maximum=max(values),median=values[len(values)//2],p95=values[math.ceil(.95*len(values))-1])
    report=dict(version=azl.__version__,platform=platform.system(),python=platform.python_version(),fixture_sha256=hashlib.sha256(raw).hexdigest(),
                independent_tools=fixture['reference'],passed=all(r['pass_check'] for r in rows),checks=len(rows),aggregates=aggregates,results=rows,
                limitations='Frozen ideal-surface corpus; not global certification of datum, mission coordinates or arbitrary body shapes')
    Path(output).write_text(json.dumps(report,indent=2)+'\n','utf8');assert report['passed'],report
    print(json.dumps(dict(checks=len(rows),aggregates=aggregates)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);validate(p.parse_args().output)

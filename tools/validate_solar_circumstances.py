"""Independent frozen NASA local references; offline, external data only.

Published calculator output is supplied as immutable data, never imported or
executed here. No third-party implementation enters Azimlib. A successful
sample comparison is not a global ephemeris accuracy certificate.
"""
import functools,hashlib,json,math
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LOCAL_CONTRACT_SHA256='75c025189b77dda697bd31efc8f98d48ce29779859bb94cd31bbf9903408642d'


def read_references(path):
    path=Path(path).resolve()
    if path==ROOT or ROOT in path.parents:raise ValueError('External references must remain outside checkout')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=LOCAL_CONTRACT_SHA256:raise ValueError('Frozen local solar contract changed')
    contract=json.loads(raw);folder=path.parent/'references'
    manifest=(folder/'source-manifest-frozen.json').read_bytes()
    if hashlib.sha256(manifest).hexdigest()!=contract['source_manifest_sha256']:raise ValueError('Frozen source manifest changed')
    for name,reference in json.loads(manifest).items():
        if Path(name).name!=name or 'sha256' not in reference:raise ValueError('Incomplete reference provenance')
        data=(folder/name).read_bytes()
        if len(data)!=reference['bytes'] or hashlib.sha256(data).hexdigest()!=reference['sha256']:raise ValueError('External reference changed: '+name)
    oracle=(folder/'nasa-local-circumstances.json').read_bytes()
    if hashlib.sha256(oracle).hexdigest()!=contract['oracle_output_sha256']:raise ValueError('Independent oracle output changed')
    return contract


def minimum(function,start,end):
    if not start<end or not math.isfinite(start+end):raise ValueError('Invalid bounded minimum interval')
    ratio=(math.sqrt(5)-1)/2;a,b=start,end;c=b-ratio*(b-a);d=a+ratio*(b-a);fc,fd=function(c),function(d)
    for _ in range(64):
        if not math.isfinite(fc+fd):raise ValueError('Non-finite local separation')
        if b-a<.001:break
        if fc<fd:b,d,fd=d,c,fc;c=b-ratio*(b-a);fc=function(c)
        else:a,c,fc=c,d,fd;d=a+ratio*(b-a);fd=function(d)
    return (a+b)/2


def validate(path,model):
    from azimlib._eclipse_ephemeris import contact_roots
    from azimlib._timescales import Instant,JulianCoordinate
    from azimlib._frames import Observer
    contract=read_references(path);cases=[]
    def seconds(clock):return sum(float(v)*factor for v,factor in zip(clock.split(':'),(3600,60,1)))
    for case in contract['cases']:
        day=Instant(datetime.fromisoformat(case['date']).replace(tzinfo=timezone.utc)).coordinate();observer=Observer(case['longitude'],case['latitude'])
        @functools.lru_cache(maxsize=10000)
        def state(t):return model.at(JulianCoordinate(day.day,day.seconds+t+case['delta_t_s'],'TT'),JulianCoordinate(day.day,day.seconds+t,'UT1'))
        def disk(t,limb):return state(t).solar(observer,lunar_limb=limb)
        def outer(t):
            p=disk(t,'nasa-canon-external');return p.separation_degrees-p.source_radius_degrees-p.occulter_radius_degrees
        def inner(t):
            p=disk(t,'nasa-bulletin-internal');return p.separation_degrees-abs(p.source_radius_degrees-p.occulter_radius_degrees)
        reference=case['contacts_ut1'];start,end=seconds(reference['C1'])-120,seconds(reference['C4'])+120
        external=contact_roots(outer,start,end,step=30,tolerance=.001);internal=contact_roots(inner,start,end,step=30,tolerance=.001)
        if len(external)!=2 or len(internal)!=2:raise ValueError('Missing fixed-case absolute solar contacts')
        t=minimum(lambda t:disk(t,'nasa-bulletin-internal').separation_degrees,seconds(reference['MAX'])-120,seconds(reference['MAX'])+120)
        contacts=dict(zip(('C1','C2','MAX','C3','C4'),(external[0],internal[0],t,internal[1],external[1])))
        rows=[dict(contact=k,reference_ut1=reference[k],actual_ut1_seconds=value,error_s=value-seconds(reference[k]),passed=abs(value-seconds(reference[k]))<=30) for k,value in contacts.items()]
        p=disk(t,'nasa-bulletin-internal')
        # Local linear overlap magnitude differs from global central M/S ratio.
        magnitude=(p.source_radius_degrees+p.occulter_radius_degrees-p.separation_degrees)/(2*p.source_radius_degrees)
        obscuration=1-p.visible_fraction;errors=dict(magnitude=magnitude-case['magnitude'],obscuration=obscuration-case['obscuration'])
        passed=all(r['passed'] for r in rows) and all(abs(v)<=.001 for v in errors.values())
        cases.append(dict(date=case['date'],reference=case,contacts=rows,magnitude=magnitude,obscuration=obscuration,errors=errors,passed=passed))
    return dict(contract_sha256=LOCAL_CONTRACT_SHA256,cases=cases,passed=all(c['passed'] for c in cases),
        absolute_solar_contacts_complete=True,solar_limb='unchanged physical state radius, 695700000m',
        lunar_limbs=dict(external='published Canon k1=.272488',internal_and_photometry='published Canon k2=.272281'),
        solar_catalog_radius_confirmed=False,
        scope='Three frozen observers/native clocks. NASA local finite disks compared with explicit published lunar constants; no fitted radius, new tolerance, global uncertainty bound or grazing-contact completeness claim.')

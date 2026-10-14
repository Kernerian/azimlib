"""Reproduce frozen independent eclipse comparisons; fail closed on unmet gates.

Raw NASA/JPL references stay outside checkout and are never fetched implicitly.
Execution success is not a scientific accuracy claim or checklist acceptance.
"""
import argparse,functools,hashlib,json,math,re,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from azimlib._timescales import Instant,JulianCoordinate
from azimlib._spk import SpkKernel
from azimlib._eclipse_ephemeris import EclipseEphemeris,contact_roots
from azimlib._frames import Observer
from azimlib.eclipse import SUN_RADIUS_M
from azimlib.geodesy import Geodesic
CONTRACT_SHA256='31cddc2f9af5fbd5a93ca294985043f2e220643418cb9921b48a25d0359cc965'
CENTRAL_ORACLE_V2_SHA256='376238239d1e35e0a5caeb89f4e8940a9d667db7cadc4976443be181422f8ef3'

def read_central_oracle(path):
    path=Path(path).resolve()
    if path==ROOT or ROOT in path.parents:raise ValueError('Raw references must stay outside checkout')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=CENTRAL_ORACLE_V2_SHA256:raise ValueError('Frozen central oracle changed')
    record=json.loads(raw)
    if record['date']!='2023-10-14' or record['limit_m']!=2000 or record['original_contract_sha256']!=CONTRACT_SHA256:
        raise ValueError('Central oracle contract mismatch')
    for name,expected in ((record['justification_file'],record['justification_sha256']),(record['source_file'],record['source_sha256'])):
        source=(path.parent/name).resolve()
        if path.parent.parent not in source.parents or ROOT in source.parents:raise ValueError('Oracle source escapes evidence root')
        if hashlib.sha256(source.read_bytes()).hexdigest()!=expected:raise ValueError('Central oracle provenance mismatch')
    return record

def require_reference_hash(raw,reference,contract):
    if hashlib.sha256(raw).hexdigest()!=contract['references'][reference]['sha256']:
        raise ValueError('Reference integrity mismatch: '+reference)

def solar_rows(text,date):
    """All timed rows, including rejection of partial parses or duplicates."""
    expected={'2017-08-21':97,'2023-10-14':107,'2024-04-08':98}[date]
    rows=[];seen=set()
    for line in text.splitlines():
        clock=re.match(r'\s*(\d{2}):(\d{2})\s+',line)
        if clock is None:continue
        pairs=re.findall(r'(\d+)\s+(\d+\.\d+)([NS])\s+(\d+)\s+(\d+\.\d+)([EW])',line)
        # The catalog explicitly has no northern boundary at three limb rows;
        # their southern boundary and central point must still be compared.
        if len(pairs)==2 and re.match(r'\s*-\s+-\s+',line[clock.end():]):pairs=[None,*pairs]
        key=clock[0].strip()
        if len(pairs)!=3 or key in seen:raise ValueError('Incomplete/duplicate timed solar row')
        seen.add(key);rows.append((line,clock,pairs))
    if len(rows)!=expected:raise ValueError('Timed solar reference coverage changed')
    return rows

def verify_inputs(folder):
    folder=Path(folder).resolve()
    if folder==ROOT or ROOT in folder.parents:raise ValueError('Raw references must stay outside checkout')
    raw=(folder/'frozen-contract.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=CONTRACT_SHA256:raise ValueError('Frozen eclipse contract changed')
    contract=json.loads(raw)
    for name,reference in contract['references'].items():
        path=folder/name
        with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
        if path.stat().st_size!=reference['bytes'] or digest!=reference['sha256']:
            raise ValueError('Reference integrity mismatch: '+name)
    return contract

def validate_central(reference_dir,central_oracle=None):
    folder=Path(reference_dir);verify_inputs(folder);contract=json.loads((folder/'frozen-contract.json').read_text());kernel=SpkKernel(folder/'de440s.bsp',sha256=contract['references']['de440s.bsp']['sha256'],source='NASA/JPL DE440s supplied explicitly');model=EclipseEphemeris(kernel);cases=[]
    override=read_central_oracle(central_oracle) if central_oracle is not None else None
    for case in contract['solar_cases']:
        raw=(folder/case['reference']).read_bytes();require_reference_hash(raw,case['reference'],contract);text=raw.decode();delta=float(re.search(r'&Delta;T\s*=\s*([0-9.]+)',text).group(1));rows=[]
        source_rows=solar_rows(text,case['date']);changed=override is not None and case['date']==override['date']
        if changed:
            replacement={r['ut']:r for r in override['rows']}
            if len(replacement)!=len(source_rows) or set(replacement)!={c[0].strip() for _,c,_ in source_rows}:raise ValueError('Corrected oracle timed-row coverage changed')
            delta=override['delta_t_seconds']
        for line,clock,pairs in source_rows:
            def position(pair):
                a,b,ns,c,d,ew=pair;return (int(c)+float(d)/60)*(-1 if ew=='W' else 1),(int(a)+float(b)/60)*(-1 if ns=='S' else 1)
            lon,lat=position(pairs[-1])
            if changed:
                point=replacement[clock[0].strip()];lon,lat=point['longitude'],point['latitude']
            instant=datetime.fromisoformat(case['date']).replace(hour=int(clock[1]),minute=int(clock[2]),tzinfo=timezone.utc)
            nominal=Instant(instant).coordinate();ut1=JulianCoordinate(nominal.day,nominal.seconds,'UT1');tt=JulianCoordinate(nominal.day,nominal.seconds+delta,'TT');state=model.at(tt,ut1);occ=state.solar(Observer(lon,lat));point=state.central_point()
            error=None if point is None else Geodesic().inverse(lon,lat,*point).distance
            rows.append(dict(time=clock[0].strip(),longitude=lon,latitude=lat,central_point=point,track_error_m=error,separation_degrees=occ.separation_degrees,visible_fraction=occ.visible_fraction,classification=occ.classification))
        required=contract['required'];kind='umbra' if case['expected']=='total' else 'antumbra'
        passed=all(r['track_error_m'] is not None and r['track_error_m']<=required['ground_central_track_error_m'] and r['separation_degrees']<=required['central_separation_degrees'] and r['classification']==kind and (kind!='umbra' or r['visible_fraction']<=required['residual_totality_fraction']) for r in rows)
        cases.append(dict(date=case['date'],rows=len(rows),reference_delta_t_seconds=delta,maximum_track_error_m=max(r['track_error_m'] for r in rows if r['track_error_m'] is not None),axis_misses=sum(r['track_error_m'] is None for r in rows),maximum_separation_degrees=max(r['separation_degrees'] for r in rows),maximum_visible_fraction=max(r['visible_fraction'] for r in rows),results=rows,passed=passed))
    report=dict(contract_sha256=hashlib.sha256((folder/'frozen-contract.json').read_bytes()).hexdigest(),central_oracle_version=2 if override is not None else 1,central_oracle_sha256=CENTRAL_ORACLE_V2_SHA256 if override is not None else None,legacy_reference_preserved=True,cases=cases,passed=all(c['passed'] for c in cases),scientific_gate_passed=False,accuracy_bound_established=False)
    
    return report

def validate_lunar(reference_dir):
    folder=Path(reference_dir);verify_inputs(folder);raw=(folder/'frozen-contract.json').read_bytes();contract=json.loads(raw);model=EclipseEphemeris(SpkKernel(folder/'de440s.bsp',sha256=contract['references']['de440s.bsp']['sha256'],source='NASA/JPL DE440s'))
    # Manually transcribed after rendering every PDF page; original hashes fixed before implementation.
    cases=[dict(date='2022-11-08',reference='lunar-2022.pdf',delta_t=73.,contacts={'P1':'08:02:17','U1':'09:09:12','U2':'10:16:39','U3':'11:41:37','U4':'12:49:03','P4':'13:56:08'}),dict(date='2025-03-14',reference='lunar-2025.pdf',delta_t=75.,contacts={'P1':'03:57:24','U1':'05:09:33','U2':'06:25:59','U3':'07:31:23','U4':'08:47:48','P4':'10:00:01'})]
    results=[]
    for case in cases:
        require_reference_hash((folder/case['reference']).read_bytes(),case['reference'],contract)
        day=Instant(datetime.fromisoformat(case['date']).replace(tzinfo=timezone.utc)).coordinate()
        @functools.lru_cache(maxsize=6000)
        def state(seconds):return model.at(JulianCoordinate(day.day,day.seconds+seconds+case['delta_t'],'TT'),JulianCoordinate(day.day,day.seconds+seconds,'UT1'))
        found={}
        for i,names in enumerate((('P1','P4'),('U1','U4'),('U2','U3'))):
            roots=contact_roots(lambda t:state(t).lunar_margins(shadow_convention='danjon-mean')[i],0.,18*3600.)
            if len(roots)!=2:raise ValueError('Expected two crossings for fixed total-eclipse case')
            found.update(zip(names,roots))
        rows=[]
        for name,time in case['contacts'].items():
            h,m,s=map(int,time.split(':'));expected=h*3600+m*60+s
            rows.append(dict(contact=name,reference_ut=time,reference_seconds_since_ut1_midnight=expected,actual_seconds_since_ut1_midnight=found[name],error_seconds=found[name]-expected))
        results.append(dict(date=case['date'],clock='NASA UT1/TD with native deltaT; not UTC approximation',delta_t_seconds=case['delta_t'],shadow_convention='danjon-mean, published NASA 1.01 effective radius',maximum_absolute_error_seconds=max(abs(r['error_seconds']) for r in rows),rows=rows))
    report=dict(contract_sha256=hashlib.sha256(raw).hexdigest(),required_seconds=contract['required']['lunar_contact_error_seconds'],cases=results,passed=all(r['maximum_absolute_error_seconds']<=contract['required']['lunar_contact_error_seconds'] for r in results),scope='Contact comparisons with independently computed VSOP87/ELP2000-85 NASA cases; not a global model accuracy bound')
    
    return report

def validate_boundaries(reference_dir):
    folder=Path(reference_dir);verify_inputs(folder);rawcontract=(folder/'frozen-contract.json').read_bytes();contract=json.loads(rawcontract);kernel=SpkKernel(folder/'de440s.bsp',sha256=contract['references']['de440s.bsp']['sha256'],source='NASA/JPL DE440s');model=EclipseEphemeris(kernel);results=[];began=time.perf_counter()
    for case in contract['solar_cases']:
        raw=(folder/case['reference']).read_bytes();require_reference_hash(raw,case['reference'],contract);text=raw.decode();delta=float(re.search(r'&Delta;T\s*=\s*([0-9.]+)',text).group(1));rows=[];durations=[]
        day=Instant(datetime.fromisoformat(case['date']).replace(tzinfo=timezone.utc)).coordinate()
        @functools.lru_cache(maxsize=18000)
        def at(seconds):return model.at(JulianCoordinate(day.day,day.seconds+seconds+delta,'TT'),JulianCoordinate(day.day,day.seconds+seconds,'UT1'))
        def margin(seconds,observer):
            # These are internal-phase limits. The reference explicitly uses
            # k2=0.272281, not the physical mean lunar radius. Selecting its
            # published limb is a convention match, never an error-fitted radius.
            p=at(seconds).solar(observer,lunar_limb='nasa-bulletin-internal')
            return p.separation_degrees-abs(p.occulter_radius_degrees-p.source_radius_degrees)
        def minimum(nominal,observer):
            a=nominal-900;b=nominal+900;gold=(math.sqrt(5)-1)/2
            c=b-gold*(b-a);d=a+gold*(b-a);fc=margin(c,observer);fd=margin(d,observer)
            for _ in range(32):
                if fc<fd:b,d,fd=d,c,fc;c=b-gold*(b-a);fc=margin(c,observer)
                else:a,c,fc=c,d,fd;d=a+gold*(b-a);fd=margin(d,observer)
            return ((c,fc) if fc<fd else (d,fd))
        for line,clock,pairs in solar_rows(text,case['date']):
            def position(pair):
                a,b,ns,c,d,ew=pair;return (int(c)+float(d)/60)*(-1 if ew=='W' else 1),(int(a)+float(b)/60)*(-1 if ns=='S' else 1)
            nominal=int(clock[1])*3600+int(clock[2])*60
            for side,pair in zip(('north','south'),pairs[:2]):
                if pair is None:
                    rows.append(dict(ut=clock[0].strip(),side=side,reference_available=False,
                        passed=None,reason='Catalog explicitly supplies dashes, no coordinate'))
                    continue
                lon,lat=position(pair)
                # Both interval ends can be outside a narrow track even when
                # two roots lie inside it. Scan the same fixed search interval;
                # select the crossing nearest the published boundary, without
                # changing tolerances or excluding any timed catalog row.
                samples=[(max(-89.99,min(89.99,lat-1+i*.1)),None) for i in range(21)]
                samples=[(a,minimum(nominal,Observer(lon,a))[1]) for a,_ in samples]
                brackets=[(a,b,fa) for (a,fa),(b,fb) in zip(samples,samples[1:]) if fa*fb<=0]
                if not brackets:
                    rows.append(dict(ut=clock[0].strip(),side=side,longitude=lon,reference_latitude=lat,passed=False,reason='No boundary bracket in fixed +/-1 degree meridian interval'));continue
                lo,hi,flo=min(brackets,key=lambda bracket:abs((bracket[0]+bracket[1])/2-lat))
                for _ in range(18):
                    mid=(lo+hi)/2;t,fmid=minimum(nominal,Observer(lon,mid))
                    if flo*fmid<=0:hi=mid
                    else:lo=mid;flo=fmid
                actual=(lo+hi)/2;error=Geodesic().inverse(lon,lat,lon,actual).distance
                rows.append(dict(ut=clock[0].strip(),side=side,longitude=lon,reference_latitude=lat,actual_latitude=actual,meridian_error_m=error,maximum_internal_phase_ut1_seconds=t,passed=error<=contract['required']['ground_boundary_error_m']))
            match=re.search(r'(\d+)m(\d+\.\d+)s',line)
            if match:
                lon,lat=position(pairs[2]);observer=Observer(lon,lat)
                roots=contact_roots(lambda t:margin(t,observer),nominal-600,nominal+600,step=20)
                expected=int(match[1])*60+float(match[2]);actual=None if len(roots)!=2 else roots[1]-roots[0]
                durations.append(dict(ut=clock[0].strip(),reference_duration_seconds=expected,actual_duration_seconds=actual,error_seconds=None if actual is None else actual-expected,independent_absolute_contact_times_available=False))
        results.append(dict(date=case['date'],boundary_rows=len(rows),boundary_coordinates_available=sum(r['passed'] is not None for r in rows),boundary_failures=sum(r['passed'] is False for r in rows),maximum_meridian_error_m=max((r.get('meridian_error_m',0) for r in rows),default=None),results=rows,durations=durations,maximum_duration_error_seconds=max(abs(r['error_seconds']) for r in durations if r['error_seconds'] is not None)))
        print(case['date'],results[-1]['boundary_failures'],results[-1]['maximum_meridian_error_m'],flush=True)
    report=dict(contract_sha256=hashlib.sha256(rawcontract).hexdigest(),elapsed_seconds=time.perf_counter()-began,cases=results,required_meridian_error_m=contract['required']['ground_boundary_error_m'],lunar_limb='NASA published internal k2=0.272281',solar_radius_m=SUN_RADIUS_M,solar_catalog_radius_convention_confirmed=False,scope='Swept boundary: minimize internal-contact margin in fixed +/-15 minute window, then solve latitude at fixed published longitude. Meridian distance is a conservative point-to-boundary comparison, not an instantaneous cone radius or angular-to-metre conversion.',passed=all(c['boundary_failures']==0 for c in results),absolute_solar_contact_validation_complete=False)
    
    return report

def validate_clear(reference_dir):
    folder=Path(reference_dir);contract=verify_inputs(folder)
    kernel=SpkKernel(folder/'de440s.bsp',sha256=contract['references']['de440s.bsp']['sha256'],source='NASA/JPL DE440s')
    model=EclipseEphemeris(kernel);rows=[]
    for case in contract['clear_cases']:
        nominal=Instant(datetime.fromisoformat(case['utc'])).coordinate()
        # Explicit post-2017 TAI-UTC=37 s; UT1-UTC=0 with +/-1 s
        # uncertainty is adequate only for these widely separated clear cases.
        state=model.at(JulianCoordinate(nominal.day,nominal.seconds+69.184,'TT'),JulianCoordinate(nominal.day,nominal.seconds,'UT1'))
        actual=state.solar(Observer(*case['solar_observer'])).classification
        margins=state.lunar_margins(shadow_convention='danjon-mean')
        lunar='clear' if margins[0]>0 else 'eclipse'
        rows.append(dict(utc=case['utc'],solar=actual,lunar=lunar,expected=case,clock_uncertainty_seconds=1,
            passed=actual==case['solar'] and ('lunar' not in case or lunar==case['lunar'])))
    return dict(cases=rows,passed=all(r['passed'] for r in rows))

def validate(reference_dir,sections,solar_circumstances=None,central_oracle=None):
    contract=verify_inputs(reference_dir);reports={}
    for section in sections:reports[section]=validate_central(reference_dir,central_oracle) if section=='central' else globals()['validate_'+section](reference_dir)
    absolute=False
    if solar_circumstances is not None:
        # -I excludes the script directory; load only this owned adjacent tool.
        import importlib.util
        spec=importlib.util.spec_from_file_location('_azimlib_solar_validation',ROOT/'tools/validate_solar_circumstances.py')
        local=importlib.util.module_from_spec(spec);spec.loader.exec_module(local)
        validate_local=local.validate
        model=EclipseEphemeris(SpkKernel(Path(reference_dir)/'de440s.bsp',sha256=contract['references']['de440s.bsp']['sha256'],source='Explicit NASA/JPL DE440s'))
        reports['solar_local']=validate_local(solar_circumstances,model)
        absolute=reports['solar_local']['passed'] and reports['solar_local']['absolute_solar_contacts_complete']
    # An explicitly justified oracle correction does not establish the global
    # model bound or waive failures in any other comparison.
    return dict(schema=1,contract_sha256=CONTRACT_SHA256,diagnostic_execution_passed=True,
        input_verification_passed=True,reference_sha256={name:r['sha256'] for name,r in contract['references'].items()},
        implementation_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
            for name in ('src/azimlib/_spk.py','src/azimlib/_eclipse_ephemeris.py','tools/validate_eclipse_contract.py',
                         *(['tools/validate_solar_circumstances.py'] if solar_circumstances is not None else []))},
        reports=reports,real_event_gate_passed=False,accuracy_bound_established=False,
        pending=['13.06','13.07'],absolute_solar_contact_validation_complete=absolute,
        limitations=['Central trajectory must satisfy frozen 2 km for every timed row',
            'A short Earth-orientation reduction has no certified global error bound',
            'Lunar Danjon-mean is an empirical catalog convention, not an atmospheric model',
            *([] if absolute else ['Absolute solar contacts need independent reference acquisition and comparison']),
            'Grazing contacts are not covered by sign-change root searches'])

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--sections',nargs='+',choices=('central','lunar','boundaries','clear'),default=['central','lunar','boundaries','clear'])
    p.add_argument('--solar-circumstances',type=Path,help='Explicit frozen independent local-circumstance reference file outside checkout')
    p.add_argument('--central-oracle',type=Path,help='Explicit hash-frozen version-2 central oracle; omission preserves legacy version-1 audit')
    args=p.parse_args();report=validate(args.reference_dir,args.sections,args.solar_circumstances,args.central_oracle)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(dict(real_event_gate_passed=report['real_event_gate_passed'],pending=report['pending']),indent=2))
    sys.exit(0 if report['real_event_gate_passed'] else 3)

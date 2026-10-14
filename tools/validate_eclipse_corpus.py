"""Offline, explicitly frozen stratified eclipse validation; never certifies a global bound.

Raw external references and derived oracle values must remain outside checkout.
No downloading, tolerance fitting, reference replacement or publication occurs.
"""
import argparse,functools,hashlib,html,json,math,re,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'tools'))
from azimlib._eclipse_ephemeris import EclipseEphemeris,EclipseDomainError,contact_roots
from azimlib._timescales import Instant,JulianCoordinate
from azimlib._spk import SpkKernel
from azimlib._frames import Observer
from azimlib.geodesy import Geodesic
from eclipse_spatial_metric import boundary_distance
from eclipse_global_metric import GlobalGeodesicCurve
LIMITS=dict(center_m=2000,boundary_m=3000,solar_contact_s=30,lunar_contact_s=60,magnitude=.001,obscuration=.001)

def frozen(path,expected):
    path=Path(path).resolve()
    if path==ROOT or ROOT in path.parents:raise ValueError('References must stay outside checkout')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Frozen corpus integrity mismatch')
    record=json.loads(raw)
    if record['limits']!=LIMITS:raise ValueError('Frozen scientific limits changed')
    if len(record['solar'])!=52 or len(record['lunar'])!=30:raise ValueError('Frozen stratified coverage changed')
    for name in ('corpus-protocol-frozen.json','corpus-selection-frozen.json','solar-local-oracles-v5-frozen.json','lunar-oracles-v2-frozen.json','central-oracle-v2-frozen.json'):
        if hashlib.sha256((path.parent/name).read_bytes()).hexdigest()!=record['input_sha256'][name]:raise ValueError('Frozen input changed: '+name)
    selection=json.loads((path.parent/'corpus-selection-frozen.json').read_bytes())
    protocol=json.loads((path.parent/'corpus-protocol-frozen.json').read_bytes())
    if protocol['limits']!=LIMITS:raise ValueError('Protocol limits changed')
    import importlib.util
    spec=importlib.util.spec_from_file_location('_owned_central_oracle',ROOT/'tools/validate_eclipse_contract.py')
    verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
    corrected=verifier.read_central_oracle(path.parent/'central-oracle-v2-frozen.json')
    case2023=next(c for c in record['solar'] if c['date']=='2023-10-14')
    if case2023.get('central_oracle')!=corrected:raise ValueError('Explicit corrected central oracle differs')
    for body in ('solar','lunar'):
        dates=[c['date'] for c in record[body]]
        if dates!=[c['date'] for c in selection[body]['selected']] or len(set(dates))!=len(dates):raise ValueError('Selected event matrix changed')
    for source in record['sources']:
        p=(path.parent/'references'/source['file']).resolve()
        if path.parent not in p.parents:raise ValueError('Reference escapes evidence directory')
        if hashlib.sha256(p.read_bytes()).hexdigest()!=source['sha256']:raise ValueError('External source hash changed: '+source['file'])
    return record

def statistics(values):
    values=sorted(values)
    return dict(n=len(values),maximum=max(values),p50=values[len(values)//2],p95=values[math.ceil(.95*len(values))-1]) if values else dict(n=0,maximum=None,p50=None,p95=None)

def corrected_centers(corpus, path, expected, original_sha):
    """Explicit audited whole-event correction; the historical corpus stays intact.

    Acceptance uses external-to-external geometry, never implementation errors.
    This cannot override the separately resolved 2023 oracle or scientific limits.
    """
    import copy
    path=Path(path).resolve()
    if ROOT==path or ROOT in path.parents:raise ValueError('Corrections must stay outside checkout')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Correction hash mismatch')
    record=json.loads(raw)
    if record['schema']!=3 or record['limit_m']!=2000 or record['original_corpus_sha256']!=original_sha:
        raise ValueError('Correction contract mismatch')
    if record['previous_2023_oracle_sha256']!=corpus['input_sha256']['central-oracle-v2-frozen.json']:
        raise ValueError('Resolved 2023 provenance changed')
    audit_path=path.parent/'center-reference-audit.json'
    audit_raw=audit_path.read_bytes()
    if hashlib.sha256(audit_raw).hexdigest()!=record['audit_sha256']:raise ValueError('Independent audit hash mismatch')
    audit=json.loads(audit_raw);dates=[c['date'] for c in record['cases']]
    if not dates or len(dates)!=len(set(dates)) or dates!=audit['accepted_dates'] or '2023-10-14' in dates:
        raise ValueError('Correction event coverage mismatch')
    result=copy.deepcopy(corpus);events={c['date']:c for c in result['solar']}
    for change in record['cases']:
        event=events[change['date']];proof=next(c for c in audit['events'] if c['date']==change['date'])
        comparisons=proof['comparisons']
        if not proof['acceptance_independent_of_Azimlib'] or proof['decision']!='Correct whole-event central oracle':
            raise ValueError('No independent whole-event acceptance')
        if change['source_sha256']!=event['source_sha256'] or proof['current_source_sha256']!=event['source_sha256']:
            raise ValueError('Published source provenance mismatch')
        if change['delta_t_seconds']!=proof['normalized_delta_t_s'] or len(comparisons)!=proof['rows']:
            raise ValueError('Clock/coverage mismatch')
        if [r['ut'] for r in change['rows']]!=[r['ut'] for r in comparisons]:raise ValueError('Timed rows differ')
        for row, external in zip(change['rows'],comparisons):
            if not external['presence_agrees']:raise ValueError('Independent axis presence disagrees')
            value=external['nasa_to_DE440_m']
            if external['nasa_point'] is not None and (value is None or not math.isfinite(value) or value>2000):
                raise ValueError('Independent center budget failed')
            for name in ('nasa_to_DE421_m','nasa_to_Horizons_m'):
                value=external.get(name)
                if value is not None and (not math.isfinite(value) or value>2000):raise ValueError('Secondary reference budget failed')
            point=None if row['longitude'] is None and row['latitude'] is None else [row['longitude'],row['latitude']]
            if point!=external['nasa_point']:raise ValueError('Correction differs from independent audit')
        event['central_oracle']=dict(change,version=3)
    return result

def minimum(fn,a,b):
    g=(math.sqrt(5)-1)/2;c=b-g*(b-a);d=a+g*(b-a);fc=fn(c);fd=fn(d)
    for _ in range(34):
        if fc<fd:b,d,fd=d,c,fc;c=b-g*(b-a);fc=fn(c)
        else:a,c,fc=c,d,fd;d=a+g*(b-a);fd=fn(d)
    return (a+b)/2

def state_function(case,model):
    day=Instant(datetime.fromisoformat(case['date']).replace(tzinfo=timezone.utc)).coordinate()
    @functools.lru_cache(maxsize=24000)
    def at(t):return model.at(JulianCoordinate(day.day,day.seconds+t+case['delta_t_s'],'TT'),JulianCoordinate(day.day,day.seconds+t,'UT1'))
    return at

def clock(value):return sum(float(v)*f for v,f in zip(value.split(':'),(3600,60,1)))

def unwrap_rows(rows,anchor_ut_seconds):
    """Calendar-day normalization about the external greatest-eclipse epoch."""
    result=[];previous=None
    for row in rows:
        value=row['seconds']
        if previous is None:
            while value-anchor_ut_seconds>43200:value-=86400
            while value-anchor_ut_seconds<-43200:value+=86400
        else:
            while value>previous+43200:value-=86400
            while value<previous-43200:value+=86400
        result.append(dict(row,seconds=value));previous=value
    return result

def timed_rows(raw):
    text=html.unescape(re.sub('<[^>]+>','',raw));rows=[];seen=set()
    for line in text.splitlines():
        match=re.match(r'\s*(\d\d:\d\d)\s+',line)
        if not match:continue
        pattern=r'\s*(?:(\d+)\s*[° ]\s*(\d+\.\d+)[\x27’]?([NS])|(-))\s+(?:(\d+)\s*[° ]\s*(\d+\.\d+)[\x27’]?([EW])|(-))'
        points=[];offset=match.end()
        for _ in range(3):
            pair=re.compile(pattern).match(line,offset)
            if pair is None:raise ValueError('Incomplete/duplicate timed path row')
            offset=pair.end();a,b,ns,missing_lat,c,d,ew,missing_lon=pair.groups()
            if missing_lat or missing_lon:points.append(None);continue
            points.append(((int(c)+float(d)/60)*(-1 if ew=='W' else 1),(int(a)+float(b)/60)*(-1 if ns=='S' else 1)))
        if match[1] in seen:raise ValueError('Incomplete/duplicate timed path row')
        seen.add(match[1])
        rows.append(dict(ut=match[1],seconds=clock(match[1]+':00'),points=points))
    if not rows:raise ValueError('No timed path rows')
    delta=float(re.search(r'ΔT\s*=\s*([\d.]+)',text)[1])
    return delta,rows

def altitude(state,observer):
    lon,lat=map(math.radians,(observer.longitude,observer.latitude))
    p=observer.fixed_position.xyz;v=[a-b for a,b in zip(state.sun.center.xyz,p)];n=math.sqrt(sum(x*x for x in v))
    up=(math.cos(lat)*math.cos(lon),math.cos(lat)*math.sin(lon),math.sin(lat))
    return math.degrees(math.asin(max(-1,min(1,sum(a*b for a,b in zip(v,up))/n))))

def same_boundary_branch(at,t,reference,candidate):
    """Cross-track side correspondence; ambiguity is never implicit approval."""
    before,center,after=(at(t+d).central_point() for d in (-.5,0,.5))
    if before is None or center is None or after is None:
        return dict(verified=False,reason='No central-axis segment for independent north/south association')
    geo=Geodesic();heading=geo.inverse(*before,*after).azimuth1
    def cross(point):
        v=geo.inverse(*center,*point)
        return v.distance*math.sin(math.radians(v.azimuth1-heading))
    a,b=cross(reference),cross(candidate)
    return dict(verified=abs(a)>.1 and abs(b)>.1 and a*b>0,
                reference_cross_track_m=a,candidate_cross_track_m=b,
                reason=None if a*b>0 else 'Candidate is not on the reference cross-track branch')

def finalize_boundaries(rows):
    """Replace seed-local acceptance with a global represented-curve search.

    Local roots are discovery diagnostics only. Their sampled geodesic graph
    has no proof of physical completeness/interpolation error. Consequently a
    small global distance to that graph cannot approve a scientific boundary.
    No guessed north/south association or absent root counts as approval.
    """
    boundaries=[r for r in rows if r['quantity']=='boundary_m']
    if not boundaries:return
    components=[];geo=Geodesic()
    for side in ('north','south'):
        current=[];last_time=None
        for row in (r for r in boundaries if r['side']==side):
            certificate=row.get('certificate')
            feasible=certificate is not None and row.get('temporal_minimum_is_interior') and abs(certificate['residual'])<=1e-9
            if not feasible:
                if current:components.append(current);current=[]
                last_time=None;continue
            point=certificate['point'];epoch=row['closest_ut1_seconds']
            if current and (abs(epoch-last_time)>300 or geo.inverse(*current[-1],*point).distance>300000):
                components.append(current);current=[]
            current.append(point);last_time=epoch
        if current:components.append(current)
    curve=GlobalGeodesicCurve(components)
    for row in boundaries:
        row['local_discovery']=dict(error_m=row['error'],accepted_by_previous_local_rule=row['passed'],reason=row.get('reason'))
        try:certificate=curve.distance(row['reference'],tolerance_m=1.)
        except ArithmeticError as exc:
            certificate=dict(status='geodesic_convergence_failure',global_represented_curve_certified=False,distance_m=None,reason=str(exc))
        row['global_certificate']=certificate
        row['represented_curve_numeric_pass']=certificate.get('global_represented_curve_certified',False) and certificate['upper_m']<=3000
        row['error']=certificate.get('distance_m')
        row['error_scope']='Global minimum to represented geodesic graph; not a certified distance to the complete physical boundary'
        row['passed']=False
        row['reason']='Physical branch completeness and interpolation error are not certified; represented-curve proximity alone cannot approve the 3 km scientific gate'

def lunar(case,model):
    at=state_function(case,model);nominal=case['greatest_ut1_seconds'];rows=[]
    for i,names in enumerate((('P1','P4'),('U1','U4'),('U2','U3'))):
        required=[k for k in names if k in case['contacts_ut1_seconds']]
        roots=contact_roots(lambda t:at(t).lunar_margins(shadow_convention='danjon-mean')[i],nominal-5*3600,nominal+5*3600,step=60,tolerance=.001)
        if len(roots)!=len(required):rows.append(dict(quantity='contact_count',names=names,expected=len(required),actual=len(roots),passed=False));continue
        for name,t in zip(required,roots):
            error=t-case['contacts_ut1_seconds'][name];rows.append(dict(quantity='contact_s',name=name,error=error,passed=abs(error)<=60))
    # NASA lunar magnitude is linear immersion in the shadow, not obscuration.
    def magnitudes(t):
        s=at(t);m=s.lunar_margins(shadow_convention='danjon-mean');r=s.moon.radius_m
        return -m[1]/(2*r),-m[0]/(2*r)
    greatest=minimum(lambda t:-magnitudes(t)[0],nominal-120,nominal+120);mag,pen=magnitudes(greatest)
    rows.extend([dict(quantity='magnitude',name='umbral',error=mag-case['umbral_magnitude'],passed=abs(mag-case['umbral_magnitude'])<=.001),dict(quantity='magnitude',name='penumbral',error=pen-case['penumbral_magnitude'],passed=abs(pen-case['penumbral_magnitude'])<=.001)])
    clear=at(nominal+7*86400).lunar_margins(shadow_convention='danjon-mean')[0]>0
    rows.append(dict(quantity='no_event',passed=clear))
    return dict(date=case['date'],body='lunar',kind=case['kind'],rows=rows,greatest_error_s=greatest-nominal,passed=all(r['passed'] for r in rows),obscuration='Not supplied by lunar reference; umbral magnitude is a different quantity')

def solar(case,model,folder):
    rows=[];at=state_function(case,model)
    for observer_case in case['observers']:
        if 'error' in observer_case:
            rows.append(dict(quantity='unavailable',reason=observer_case['error'],passed=False));continue
        observer=Observer(observer_case['longitude'],observer_case['latitude']);refs=observer_case['contacts'];nominal=refs['MAX']['ut1_seconds']
        disk=lambda t,limb:at(t).solar(observer,lunar_limb=limb)
        t=minimum(lambda t:disk(t,'nasa-bulletin-internal').separation_degrees,nominal-120,nominal+120)
        p=disk(t,'nasa-bulletin-internal');mag=(p.source_radius_degrees+p.occulter_radius_degrees-p.separation_degrees)/(2*p.source_radius_degrees);obsc=1-p.visible_fraction
        geometry=dict(observer=[observer.longitude,observer.latitude],sun_altitude_degrees=altitude(at(t),observer),local_kind=observer_case['kind'])
        if observer_case['kind']==0:
            rows.append(dict(quantity='no_event',passed=p.classification=='clear',**geometry));continue
        rows.extend([dict(quantity='magnitude',error=mag-observer_case['magnitude'],passed=abs(mag-observer_case['magnitude'])<=.001,**geometry),dict(quantity='obscuration',error=obsc-observer_case['obscuration'],passed=abs(obsc-observer_case['obscuration'])<=.001,**geometry),dict(quantity='solar_contact_s',name='MAX',error=t-nominal,passed=abs(t-nominal)<=30,**geometry)])
        start=refs['C1']['ut1_seconds']-120;end=refs['C4']['ut1_seconds']+120
        for limb,names in [('nasa-canon-external',('C1','C4')),('nasa-bulletin-internal',('C2','C3'))]:
            required=[n for n in names if n in refs]
            def margin(x):
                p=disk(x,limb);return p.separation_degrees-(p.source_radius_degrees+p.occulter_radius_degrees if limb=='nasa-canon-external' else abs(p.source_radius_degrees-p.occulter_radius_degrees))
            critical=minimum(margin,max(start,t-120),min(end,t+120))
            roots=contact_roots(margin,start,end,step=30,tolerance=.001,critical_points=(critical,))
            if case['date'] in ('1986-10-03','1987-03-29') and limb=='nasa-bulletin-internal' and required:
                rows.append(dict(quantity='contact_detection_diagnostic',passed=True,
                    legacy_roots=contact_roots(margin,start,end,step=30,tolerance=.001),
                    refined_roots=roots,critical_time=critical,minimum_margin_degrees=margin(critical),
                    external_roots=[refs[n]['ut1_seconds'] for n in required],**geometry))
            if len(roots)!=len(required):rows.append(dict(quantity='contact_count',names=names,expected=len(required),actual=len(roots),passed=False,**geometry));continue
            for name,value in zip(required,roots):rows.append(dict(quantity='solar_contact_s',name=name,error=value-refs[name]['ut1_seconds'],passed=abs(value-refs[name]['ut1_seconds'])<=30,**geometry))
        rows.append(dict(quantity='no_event',passed=at(nominal+7*86400).solar(observer).classification=='clear',**geometry))
    if case.get('path'):
        path=(folder/case['path']).resolve()
        if folder.resolve() not in path.parents:raise ValueError('Path reference escapes evidence directory')
        delta,reference=timed_rows(path.read_text('utf8'))
        reference=unwrap_rows(reference,clock(case['td_greatest'])-delta)
        path_at=state_function(dict(case,delta_t_s=delta),model)
        override=case.get('central_oracle')
        if override is not None:
            corrected={r['ut']:r for r in override['rows']}
            if len(corrected)!=len(reference) or set(corrected)!={r['ut'] for r in reference}:raise ValueError('Corrected center coverage differs from full source table')
            center_at=state_function(dict(case,delta_t_s=override['delta_t_seconds']),model)
        else:center_at=path_at
        for r in reference:
            nominal=r['seconds'];center=r['points'][2]
            if override is not None:
                c=corrected[r['ut']];center=None if c['longitude'] is None and c['latitude'] is None else (c['longitude'],c['latitude'])
            actual=center_at(nominal).central_point()
            if center is None:
                rows.append(dict(quantity='axis_presence',ut=r['ut'],expected=False,actual=actual is not None,passed=actual is None))
            else:
                error=None if actual is None else Geodesic().inverse(*center,*actual).distance
                rows.append(dict(quantity='center_m',ut=r['ut'],ut1_seconds_since_event_date=nominal,error=error,reference=center,actual=actual,oracle_version=override.get('version',2) if override is not None else 1,sun_altitude_degrees=altitude(center_at(nominal),Observer(*center)),passed=error is not None and error<=2000))
            for side,point in zip(('north','south'),r['points'][:2]):
                if point is None:continue
                def minimized(lon,lat):
                    observer=Observer(lon,lat)
                    def margin(t):
                        p=path_at(t).solar(observer,lunar_limb='nasa-bulletin-internal');return p.separation_degrees-abs(p.source_radius_degrees-p.occulter_radius_degrees)
                    t=minimum(margin,nominal-900,nominal+900)
                    return margin(t),t
                try:
                    certificate=boundary_distance(point,lambda lon,lat:minimized(lon,lat)[0])
                    value,closest_time=minimized(*certificate['point'])
                    interior=nominal-899<closest_time<nominal+899
                    branch=same_boundary_branch(path_at,closest_time,point,certificate['point'])
                    error=certificate['distance_m']
                    rows.append(dict(quantity='boundary_m',ut=r['ut'],side=side,error=error,reference=point,
                        certificate=certificate,closest_ut1_seconds=closest_time,temporal_minimum_is_interior=interior,
                        branch=branch,passed=error<=3000 and interior and branch['verified'],
                        reason=('Temporal minimum is a search-window endpoint; envelope unverified' if not interior else branch['reason'] if not branch['verified'] else None)))
                except ArithmeticError as exc:
                    rows.append(dict(quantity='boundary_m',ut=r['ut'],side=side,error=None,reference=point,passed=False,reason=str(exc)))
    finalize_boundaries(rows)
    return dict(date=case['date'],body='solar',kind=case['kind'],rows=rows,passed=all(r['passed'] for r in rows))

def evaluate(task):
    body,case,kernel,kernel_sha,folder=task;start=time.perf_counter()
    try:
        model=EclipseEphemeris(SpkKernel(kernel,sha256=kernel_sha,source='Explicit JPL DE440s validation kernel'))
        result=lunar(case,model) if body=='lunar' else solar(case,model,Path(folder))
    except EclipseDomainError as exc:
        result=dict(date=case['date'],body=body,kind=case['kind'],rows=[],passed=False,
            status='outside_experimental_domain',scientific_prediction_valid=False,
            domain_quantity=exc.quantity,domain_value=exc.value,error=type(exc).__name__+': '+str(exc))
    except Exception as exc:result=dict(date=case['date'],body=body,kind=case['kind'],rows=[],passed=False,error=type(exc).__name__+': '+str(exc))
    result['elapsed_s']=time.perf_counter()-start;return result

def run(args):
    corpus=frozen(args.corpus,args.expected_sha256)
    corrections=getattr(args,'central_corrections',None);correction_sha=getattr(args,'central_corrections_sha256',None)
    if bool(corrections)!=bool(correction_sha):raise ValueError('Both explicit correction path and hash required')
    if corrections:corpus=corrected_centers(corpus,corrections,correction_sha,args.expected_sha256)
    tasks=[(body,case,str(args.kernel),args.kernel_sha256,str(args.corpus.parent/'references')) for body in ('solar','lunar') for case in corpus[body]]
    from concurrent.futures import ProcessPoolExecutor
    results=[]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for result in pool.map(evaluate,tasks):
            results.append(result);print(result['body'],result['date'],result['passed'],result.get('error',''),flush=True)
            args.output.with_suffix('.progress.json').write_text(json.dumps(results,indent=2,allow_nan=False)+'\n')
    aggregate={}
    for quantity in ('center_m','boundary_m','solar_contact_s','contact_s','magnitude','obscuration'):
        pairs=[(abs(r['error']),c,r) for c in results for r in c['rows'] if r['quantity']==quantity and r.get('error') is not None]
        aggregate[quantity]=statistics([v for v,c,r in pairs])
        if pairs:
            value,c,r=max(pairs,key=lambda x:x[0]);aggregate[quantity]['worst']=dict(date=c['date'],body=c['body'],row=r)
    report=dict(schema=2,corpus_sha256=args.expected_sha256,kernel_sha256=args.kernel_sha256,limits=LIMITS,cases=results,aggregate=aggregate,all_cases_passed=all(c['passed'] for c in results),accuracy_bound_established=False,central_2023_oracle_version=2,legacy_reference_preserved=True,domain=EclipseEphemeris.domain_contract(),outside_domain_cases=[dict(date=c['date'],body=c['body'],quantity=c['domain_quantity'],value=c['domain_value']) for c in results if c.get('status')=='outside_experimental_domain'],limitations=['A stratified corpus is not a continuous uncertainty proof across 1972-2100','Surface roots certify local distance, not global nearest branch or a Hausdorff bound','Critical-point splitting detects narrow pairs; double tangencies still need explicit scientific classification','Earth orientation reduction and catalog-specific radii require an independent global uncertainty budget','Lunar obscuration has no independent numeric reference in these plates'],implementation_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('src/azimlib/_spk.py','src/azimlib/_eclipse_ephemeris.py','tools/validate_eclipse_corpus.py','tools/validate_eclipse_contract.py','tools/eclipse_spatial_metric.py')})
    report['explicit_center_corrections_sha256']=correction_sha
    report['implementation_sha256']['tools/eclipse_global_metric.py']=hashlib.sha256((ROOT/'tools/eclipse_global_metric.py').read_bytes()).hexdigest()
    report['boundary_validation']=dict(metric='Global WGS84 distance over all represented components, no seed-local branch acceptance',distance_interval_m=1,physical_representation_complete=False,numeric_checks_pass=sum(r.get('represented_curve_numeric_pass',False) for c in results for r in c['rows']),scientific_boundary_gate_passed=False)
    report['limitations'][1]='Global distance bounds certify the represented geodesic graph only; physical completeness and interpolation bounds are missing'
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return 0 if report['all_cases_passed'] else 3

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--corpus',type=Path,required=True);p.add_argument('--expected-sha256',required=True);p.add_argument('--kernel',type=Path,required=True);p.add_argument('--kernel-sha256',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--central-corrections',type=Path);p.add_argument('--central-corrections-sha256');p.add_argument('--workers',type=int,choices=range(1,5),default=2);args=p.parse_args();raise SystemExit(run(args))

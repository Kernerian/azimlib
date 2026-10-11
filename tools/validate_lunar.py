"""Explicit independent reference comparison; raw ephemerides stay external.

Only original error statistics and query hashes are distributable outputs.
No raw Horizons response, kernel, table or reference implementation is bundled.
"""
import argparse,hashlib,json,math,shutil,sys,time
from datetime import datetime,timedelta,timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
sys.path.insert(0,str(Path(__file__).resolve().parent))
from validate_solar import rows,direction,separation,ENDPOINT
ROOT=Path(__file__).resolve().parents[1]
# Declared before acquiring the independent reference.
LIMITS={'angle_degrees':.5,'range_m':5000000.,'phase_fraction':.01,'limb_degrees':2.,'parallax_degrees':.03}

def dates():
    extremes=[datetime(y,m,2,12,tzinfo=timezone.utc) for y in (1972,2000,2099,2100) for m in (1,6,12)]
    return extremes+[datetime(2025,1,1,12,tzinfo=timezone.utc)+timedelta(days=i) for i in range(60)]

def plan():
    base=dict(format='json',COMMAND="'301'",EPHEM_TYPE="'OBSERVER'",ANG_FORMAT="'DEG'",CSV_FORMAT="'YES'",EXTRA_PREC="'YES'",OBJ_DATA="'NO'",APPARENT="'AIRLESS'")
    jds=[t.toordinal()+1721424.5+(t.hour*3600+t.minute*60+t.second)/86400 for t in dates()]
    base['TLIST']="'"+' '.join(map(str,jds))+"'"
    requests=[dict(name='geocentric',observer=None,params={**base,'CENTER':"'500@399'",'QUANTITIES':"'2,10,16,20,24'"})]
    for i,site in enumerate(((-46.63,-23.55,0),(0,0,0),(179.9,20,2500),(0,90,0),(0,-90,0))):
        lon,lat,h=site
        requests.append(dict(name=f'topocentric-{i}',observer=site,params={**base,'CENTER':"'coord@399'",'COORD_TYPE':"'GEODETIC'",'SITE_COORD':f"'{lon},{lat},{h/1000}'",'QUANTITIES':"'2,4,10,16,20,24'"}))
    return requests

def fetch(folder):
    folder=folder.resolve()
    if folder==ROOT or ROOT in folder.parents:raise ValueError('Raw references must remain outside the repository')
    folder.mkdir(parents=True,exist_ok=True)
    for request in plan():
        p=folder/(request['name']+'.json')
        if p.exists():continue
        if shutil.disk_usage(folder).free<15_002_000_000:raise RuntimeError('15 GB free-space reserve required')
        with urlopen(ENDPOINT+'?'+urlencode(request['params']),timeout=60) as response:raw=response.read(2_000_001)
        data=json.loads(raw)
        if len(raw)>2_000_000 or 'error' in data or '$$SOE' not in data.get('result',''):raise ValueError('Invalid bounded reference response: '+request['name'])
        with p.open('xb') as stream:stream.write(raw)
        print('Fetched '+request['name'],flush=True);time.sleep(.25)

def validate(folder):
    folder=folder.resolve()
    if folder==ROOT or ROOT in folder.parents:raise ValueError('Raw references must remain outside the repository')
    sys.path.insert(0,str(ROOT/'src'))
    import azimlib as azl
    from azimlib.solar import AU_METRES
    model=azl.LunarModel(time_policy='utc-approx');errors={k:[] for k in LIMITS};provenance=[]
    geocentric={}
    for request in plan():
        file=folder/(request['name']+'.json')
        if file.stat().st_size>2_000_000:raise ValueError('Reference input exceeds 2 MB')
        raw=file.read_bytes();values=rows(raw)
        if [v[0] for v in values]!=sorted(dates()):raise ValueError('Reference dates differ from requested grid')
        provenance.append(dict(case=request['name'],sha256=hashlib.sha256(raw).hexdigest(),rows=len(values),request_url=ENDPOINT+'?'+urlencode(request['params']),signature=json.loads(raw).get('signature')))
        observer=None if request['observer'] is None else azl.SolarObserver(*request['observer'])
        for dt,fields in values:
            p=model.position(dt,observer);ra,dec=fields[:2];offset=2
            if observer is not None:
                az,el=fields[2:4];offset=4
                # Exact poles have no unique geographic meridian/azimuth.
                # Elevation and full equatorial direction remain testable there.
                errors['angle_degrees'].append(abs(p.geometric_elevation-el) if abs(observer.latitude)==90 else separation(direction(p.azimuth or 0,p.geometric_elevation),direction(az,el)))
                pra,pdec=p.topocentric_right_ascension,p.topocentric_declination;distance=p.topocentric_distance_m
                expected=separation(direction(ra,dec),direction(*geocentric[dt][:2]))
                actual=separation(direction(pra,pdec),direction(p.right_ascension,p.declination))
                errors['parallax_degrees'].append(abs(actual-expected))
            else:
                pra,pdec=p.right_ascension,p.declination;distance=p.distance_m;geocentric[dt]=fields
            errors['angle_degrees'].append(separation(direction(pra,pdec),direction(ra,dec)))
            illumination,limb,limb_distance,range_au,range_rate,phase=fields[offset:offset+6]
            errors['range_m'].append(abs(distance-range_au*AU_METRES))
            errors['phase_fraction'].append(abs(p.illuminated_fraction-illumination/100))
            if 20<p.elongation<160 and p.bright_limb_position_angle is not None:
                errors['limb_degrees'].append(abs((p.bright_limb_position_angle-limb+180)%360-180))
    statistics={key:dict(count=len(data),maximum=max(data),rms=math.sqrt(sum(x*x for x in data)/len(data)),limit=LIMITS[key],passed=max(data)<=LIMITS[key]) for key,data in errors.items()}
    return dict(passed=all(v['passed'] for v in statistics.values()),model='azim-almanac-short-v1',time_policy='utc-approx',statistics=statistics,references=provenance,
        caveats=['Sampled validation, not a global maximum guarantee','At exact geographic poles compare elevation and equatorial direction, not arbitrary azimuth','Mean-of-date geometric short series; no full IAU reduction, light time or lunar aberration','Limb orientation gate excludes elongations <=20 or >=160 degrees','No eclipse timing or full astrodynamics claim'])

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--reference-dir',required=True,type=Path);parser.add_argument('--fetch',action='store_true');parser.add_argument('--output',required=True,type=Path);args=parser.parse_args()
    if args.fetch:fetch(args.reference_dir)
    report=validate(args.reference_dir);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k!='references'},indent=2));sys.exit(0 if report['passed'] else 1)

"""Explicit reference-only solar comparison; no ephemeris data is distributed.

Fetch only on request, outside the repository, with bounded sequential requests.
JPL responses remain private inputs; reports contain original error statistics,
request identities and hashes, never raw response text or reference tables.
"""
import argparse,csv,hashlib,io,json,math,shutil,sys,time
from datetime import datetime,date,timedelta,timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[1]
ENDPOINT='https://ssd.jpl.nasa.gov/api/horizons.api'
POSITION_LIMIT_DEGREES=.06
DISTANCE_RELATIVE_LIMIT=.0003
EVENT_LIMIT_SECONDS=120.

def dates():
    return [datetime(y,m,d,12,tzinfo=timezone.utc) for y,m,d in
        ((1972,1,2),(1972,6,21),(1980,3,20),(2000,1,2),(2000,6,21),
         (2025,3,20),(2025,6,21),(2025,9,22),(2025,12,21),(2099,6,21),
         (2099,12,21),(2100,1,2),(2100,6,21),(2100,12,21))]

def plan():
    base=dict(format='json',COMMAND="'10'",EPHEM_TYPE="'OBSERVER'",ANG_FORMAT="'DEG'",
        CSV_FORMAT="'YES'",EXTRA_PREC="'YES'",OBJ_DATA="'NO'",APPARENT="'AIRLESS'")
    instants=dates();jds=[t.toordinal()+1721424.5+.5 for t in instants]
    requests=[dict(name='geocentric',observer=None,kind='positions',params={**base,
        'CENTER':"'500@399'",'TLIST':"'"+' '.join(map(str,jds))+"'",'QUANTITIES':"'2,20'"})]
    sites=[(-46.63,-23.55,0),(0,0,0),(-77.04,38.9,0),(179.9,20,2500),(0,90,0),(0,-90,0)]
    for i,(lon,lat,height) in enumerate(sites):
        params={**base,'CENTER':"'coord@399'",'COORD_TYPE':"'GEODETIC'",
            'SITE_COORD':f"'{lon},{lat},{height/1000}'"}
        requests.append(dict(name=f'topocentric-{i}',observer=[lon,lat,height],kind='positions',
            params={**params,'TLIST':"'"+' '.join(map(str,jds))+"'",'QUANTITIES':"'2,4,20'"}))
        # Airless center elevations at a fixed -5/6-degree event convention.
        requests.append(dict(name=f'events-{i}',observer=[lon,lat,height],kind='events',params={**params,
            'START_TIME':"'2025-06-21 00:00'",'STOP_TIME':"'2025-06-22 00:00'",
            'STEP_SIZE':"'5 min'",'QUANTITIES':"'4,42'"}))
    return requests

def fetch(folder):
    folder=folder.resolve()
    if folder==ROOT or ROOT in folder.parents:raise ValueError('Reference inputs must remain outside the repository/distribution')
    folder.mkdir(parents=True,exist_ok=True)
    for request in plan():
        path=folder/(request['name']+'.json')
        if path.exists():continue
        if sum(p.stat().st_size for p in folder.glob('*.json'))+2_000_000>20_000_000_000 or shutil.disk_usage(folder).free<15_002_000_000:
            raise RuntimeError('Reference storage budget or free-space reserve exceeded')
        url=ENDPOINT+'?'+urlencode(request['params'])
        with urlopen(url,timeout=60) as response:raw=response.read(2_000_001)
        if len(raw)>2_000_000:raise ValueError('Reference response exceeds 2 MB')
        content=json.loads(raw)
        if 'error' in content or '$$SOE' not in content.get('result',''):raise ValueError('Horizons rejected reference request '+request['name'])
        with path.open('xb') as output:output.write(raw)
        print('Fetched '+request['name'],flush=True);time.sleep(.25)

def rows(raw):
    result=json.loads(raw)['result']
    text=result.split('$$SOE',1)[1].split('$$EOE',1)[0]
    data=[]
    for row in csv.reader(io.StringIO(text)):
        if not row or not row[0].strip():continue
        stamp=row[0].strip().removeprefix('A.D. ')
        calendar,clock=stamp.split();year,month,day=calendar.split('-')
        month_number=('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec').index(month)+1
        dt=datetime.fromisoformat(f'{year}-{month_number:02d}-{day}T{clock}').replace(tzinfo=timezone.utc)
        data.append((dt,tuple(float(v.strip()) for v in row[3:] if v.strip())))
    if not data:raise ValueError('Empty reference series')
    return data

def direction(az,el):
    a,e=math.radians(az),math.radians(el)
    return (math.cos(e)*math.sin(a),math.cos(e)*math.cos(a),math.sin(e))

def separation(a,b):
    # atan2 remains stable for small angular errors and near poles.
    cross=(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
    return math.degrees(math.atan2(math.sqrt(sum(v*v for v in cross)),sum(x*y for x,y in zip(a,b))))

def crossings(values,column,threshold,*,transit=False):
    found=[]
    for (a,x),(b,y) in zip(values,values[1:]):
        left,right=x[column]-threshold,y[column]-threshold
        if transit and not (left<=0<right and right-left<12):continue
        if not transit and not (left*right<0 or left==0):continue
        found.append((a+(b-a)*(-left/(right-left)),right>left))
    return found

def validate(folder):
    sys.path.insert(0,str(ROOT/'src'))
    import azimlib as azl
    from azimlib.solar import AU_METRES
    model=azl.SolarModel(time_policy='utc-approx');angular=[];distance=[];events=[];provenance=[];statuses=[]
    for request in plan():
        raw=(folder/(request['name']+'.json')).read_bytes();values=rows(raw)
        provenance.append(dict(case=request['name'],sha256=hashlib.sha256(raw).hexdigest(),rows=len(values),
            request_url=ENDPOINT+'?'+urlencode(request['params']),signature=json.loads(raw).get('signature')))
        observer=azl.SolarObserver(*request['observer']) if request['observer'] is not None else None
        if request['kind']=='positions':
            if len(values)!=len(dates()):raise ValueError('Incomplete reference position sample')
            for instant,fields in values:
                position=model.position(instant,observer)
                angular.append(separation(direction(fields[0],fields[1]),direction(position.right_ascension,position.declination)))
                if observer is None:distance.append(abs(position.distance_m/AU_METRES-fields[2])/fields[2])
                else:
                    if abs(observer.latitude)==90:
                        # At an exact pole, azimuth/meridian depend on arbitrary
                        # longitude and polar-motion conventions. Compare elevation.
                        angular.append(abs(fields[3]-position.geometric_elevation))
                    else:angular.append(separation(direction(fields[2],fields[3]),direction(position.azimuth or 0,position.geometric_elevation)))
        else:
            if len(values)!=289 or values[-1][0]-values[0][0]!=timedelta(days=1):raise ValueError('Incomplete event reference day')
            actual=model.events(date(2025,6,21),observer);ref=crossings(values,1,-5/6)
            for rising,own in ((True,actual.rises),(False,actual.sets)):
                expected=[t for t,r in ref if r==rising]
                if len(expected)!=len(own):raise AssertionError('Reference event count differs: '+request['name'])
                events.extend(abs((a-b).total_seconds()) for a,b in zip(expected,own))
            expected=[] if abs(observer.latitude)==90 else [t for t,r in crossings(values,2,0,transit=True)]
            if len(expected)!=len(actual.transits):raise AssertionError('Reference transit count differs')
            events.extend(abs((a-b).total_seconds()) for a,b in zip(expected,actual.transits))
            statuses.append(dict(case=request['name'],status=actual.status,rises=len(actual.rises),sets=len(actual.sets),transits=len(actual.transits)))
    result=dict(model=model.position(dates()[0]).model,reference='JPL Horizons observer ephemerides; airless apparent; not distributed',
        reference_terms='https://ssd.jpl.nasa.gov/faq.html',reference_inputs_distributed=False,
        time_policy='explicit utc-approx; not exact EOP/TT or a full IAU apparent frame',
        limits_fixed_before_comparison=dict(position_degrees=POSITION_LIMIT_DEGREES,distance_relative=DISTANCE_RELATIVE_LIMIT,event_seconds=EVENT_LIMIT_SECONDS),
        comparison_count=len(angular),maximum_position_error_degrees=max(angular),maximum_relative_distance_error=max(distance),
        event_comparison_count=len(events),maximum_event_error_seconds=max(events),polar_and_other_statuses=statuses,provenance=provenance)
    result['passed']=max(angular)<=POSITION_LIMIT_DEGREES and max(distance)<=DISTANCE_RELATIVE_LIMIT and max(events)<=EVENT_LIMIT_SECONDS
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--references',type=Path,required=True)
    parser.add_argument('--fetch',action='store_true');parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    if args.fetch:fetch(args.references)
    report=validate(args.references);args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='provenance'},indent=2));sys.exit(0 if report['passed'] else 1)

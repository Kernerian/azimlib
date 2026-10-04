"""Audit recorded performance evidence without downloading or timing anything.

Historical hashes must resolve to preserved modules, never be relabelled as the
current runtime. Timings are observations, not portable performance thresholds.
"""
import hashlib
import json
from pathlib import Path
import statistics


ROOT=Path(__file__).resolve().parents[1]


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(name):return json.loads((ROOT/'docs'/name).read_text(encoding='utf-8'))


def verify(report,tool,current=False):
    candidates=[ROOT/'tools'/tool,* (ROOT/'tools/baselines').rglob(tool)]
    assert report['tool_sha256'] in {digest(p) for p in candidates if p.is_file()},tool
    for name,sha in report['runtime_sha256'].items():
        path=ROOT/'src/azimlib'/name
        candidates=[path] if current else [path,*(ROOT/'tools/baselines').rglob(path.name)]
        assert sha in {digest(p) for p in candidates if p.is_file()},name


def main():
    provenance=read('original-geojson-provenance.json')
    assert provenance['features']==645 and provenance['vertices']==892336
    assert provenance['decoder_sha256']==digest(ROOT/'tools/prepare_original_benchmark.py')
    rows=[]
    for view,dpi in [('whole',100),('pan',100),('focus',100),('whole',200)]:
        before=[];after=[]
        for repeat in (1,2):
            b=read(f'detailed-before-{view}-{dpi}-r{repeat}.json')
            a=read(f'detailed-final-{view}-{dpi}-r{repeat}.json')
            intermediate=read(f'detailed-after-{view}-{dpi}-r{repeat}.json')
            verify(intermediate,'benchmark_detailed_map.py')
            verify(b,'benchmark_detailed_map.py');verify(a,'benchmark_detailed_map.py',True)
            assert not b['profiled'] and not a['profiled']
            assert a['input_sha256']==provenance['geojson_sha256']
            for key in ('input_sha256','rgba_sha256','png_sha256','pixels','items','layers','view','dpi'):
                assert a[key]==b[key],(view,dpi,repeat,key)
                assert intermediate[key]==b[key],(view,dpi,repeat,key,'intermediate')
            before.append(b);after.append(a)
        bm=statistics.median(r['precise_raster_seconds'] for r in before)
        am=statistics.median(r['precise_raster_seconds'] for r in after)
        rows.append(dict(view=view,dpi=dpi,before_seconds=bm,after_seconds=am,
                         reduction_percent=100*(1-am/bm),
                         before_peak_mib=max(r['memory_after']['peak_working_set_bytes'] for r in before)/2**20,
                         after_peak_mib=max(r['memory_after']['peak_working_set_bytes'] for r in after)/2**20))
    b=read('detailed-new-views-before.json');a=read('detailed-new-views-after.json')
    verify(b,'benchmark_new_views.py');verify(a,'benchmark_new_views.py',True)
    assert b['input_sha256']==a['input_sha256']
    for old,new in zip(b['views'],a['views'],strict=True):
        for key in ('name','extent','items','exact_scene_sha256'):assert old[key]==new[key],key
        assert new['cache']['payload_bytes']<=new['cache']['max_bytes']
    human=read('visible-navigation-brazil.json');stress=read('visible-navigation-detailed.json')
    verify(human,'measure_visible_navigation.py',True)
    verify(stress,'measure_visible_navigation.py',True)
    assert human['final'] and not human.get('scripted_model_edits',False)
    assert stress['final'] and stress['scripted_model_edits']
    for action in ('press','motion','release','wheel','home','back','forward'):
        assert human['summary']['actions'][action]>0,action
    assert human['summary']['paint_idle_records']>0
    settled=[r for r in stress['records'] if r['kind']=='model_settled']
    assert [r['stage'] for r in settled]==['new_pan','returned_home']
    assert all(r['canvas_viewable'] for r in settled)
    # Input uses (west,east,south,north); Scene uses (west,south,east,north).
    # Match only until another input changes the view: a later revisit is not
    # latency for a coalesced/discarded intermediate view.
    inputs=[r for r in human['records'] if r['kind']=='input']
    frames=[r for r in human['records'] if r['kind']=='tk_paint_idle'];latencies=[]
    for i,event in enumerate(inputs):
        action=event['action']
        if not (action in ('wheel','release','home','back','forward') or
                (action=='motion' and event['mode']=='pan' and (event['button_state'] or 0)&256)):continue
        end=next((r['t'] for r in inputs[i+1:] if r['extents']!=event['extents']),float('inf'))
        target=[[w,s,e,n] for w,e,s,n in event['extents']]
        frame=next((r for r in frames if event['t']<=r['t']<end and r['extents']==target),None)
        if frame:latencies.append(1000*(frame['t']-event['t']))
    latencies.sort()
    assert latencies
    checks=read('performance-acceptance-checks.json')
    assert checks['source_suite']['passed'] and checks['source_suite']['tests']==675
    assert checks['source_suite']['subtests']==22192
    for kind in ('scalar','native'):assert checks['installed_tests'][kind]['passed']
    for kind in ('source','wheel'):
        assert len(checks['pan_checks'][kind]['checks'])==11
        assert len(checks['toolbar_checks'][kind]['checks'])==28
    progress=(ROOT/'docs/release-progress.md').read_text(encoding='utf-8')
    assert all(f'- [x] **4.{i:02}**' in progress for i in range(1,11))
    result=dict(schema_version=1,raster=rows,scene_pixels_exact=True,
                human_summary=human['summary'],
                matched_latest_extent=dict(count=len(latencies),median_ms=statistics.median(latencies),
                    p95_ms=latencies[int(.95*(len(latencies)-1))],max_ms=max(latencies)),
                scope='Local Windows observations. No timing pass rerun here. Matched latest extents exclude coalesced views; Tk idle is not monitor latency. Stress model edits are not physical input.')
    (ROOT/'docs/performance-acceptance-audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()

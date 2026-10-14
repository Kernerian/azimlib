"""Offline reproducible own-geocoder trial: synthetic corpus and licensed OSM.

No download, address enrichment or release action. Temporary indexes are removed.
The storage cap covers this output directory and new indexes, not other files or
processes. RAM metric is traced Python allocations, not total/native process RSS.
"""
import argparse,hashlib,json,platform,shutil,statistics,sys,tempfile,time,tracemalloc
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import azimlib as az


def synthetic(count):
    for i in range(count):
        yield az.GeocodingRecord(str(i),'poi',(f'Station {i:05d}',),
            az.Geometry('Point',(-.5+(i%100)/100,-.5+(i//100)/100)),'synthetic-geocoding')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--records',type=int,default=5000)
    parser.add_argument('--storage-limit',type=int,default=20_000_000_000)
    parser.add_argument('--reserve-free',type=int,default=15_000_000_000)
    args=parser.parse_args()
    if not 100<=args.records<=10000: parser.error('Trial supports 100..10000 synthetic records')
    if not 1024*1024<=args.storage_limit<=20_000_000_000 or args.reserve_free<15_000_000_000:
        parser.error('Trial requires storage <=20 GB and free reserve >=15 GB')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    existing=sum(p.stat().st_size for p in args.output.parent.rglob('*') if p.is_file())
    available=min(256*1024*1024,args.storage_limit-existing)
    if available<1024*1024 or shutil.disk_usage(args.output.parent).free<args.reserve_free+available:
        raise az.GeocodingLimitError('Insufficient storage budget/free reserve before trial')
    digest=hashlib.sha256()
    for record in synthetic(args.records): digest.update((json.dumps(record.as_dict(),sort_keys=True,separators=(',',':'))+'\n').encode())
    source=az.GeocodingSource('synthetic-geocoding','1','BSD-3-Clause','Kernerian','Own synthetic trial corpus',
                              'urn:azimlib:synthetic:geocoding-grid-1',digest.hexdigest())
    tracemalloc.start(); start=time.perf_counter()
    with tempfile.TemporaryDirectory(prefix='geocoding-trial-',dir=args.output.parent) as folder:
        with az.LocalGeocoder.build(Path(folder)/'synthetic',synthetic(args.records),sources=(source,),
                max_records=args.records,max_bytes=available//2,min_free_bytes=args.reserve_free) as index:
            build_seconds=time.perf_counter()-start; latencies=[]
            for i in range(0,args.records,max(1,args.records//40)):
                start=time.perf_counter(); results=index.search(f'Station {i:05d}')
                latencies.append(time.perf_counter()-start)
                assert results.total==1 and results[0].record.id==str(i)
                point=next(synthetic(1)).geometry.coordinates if i==0 else (-.5+(i%100)/100,-.5+(i//100)/100)
                reverse=index.reverse(*point,radius_m=1)
                assert reverse.total==1 and reverse[0].record.id==str(i)
            synthetic_bytes=sum(p.stat().st_size for p in index.directory.iterdir())
        catalog=az.DatasetCatalog(ROOT/'optional-data/urban-sao-paulo-1.0/catalog.json')
        with az.LocalGeocoder.from_catalog(catalog,'urban-sao-paulo',Path(folder)/'real',
                max_bytes=available//2,min_free_bytes=args.reserve_free) as index:
            rows=list(index._db.execute('SELECT rid FROM records'))
            records=[index._record(row[0]) for row in rows]
            streets=[r for r in records if r.kind=='street']; queries=0
            for street in streets:
                found=index.search(street.name,kinds=('street',),limit=1000)
                assert street.id in {r.record.id for r in found}
                queries+=1
            actual=index.reverse(-46.639,-23.545,radius_m=1000,limit=1000)
            assert actual.total>0
            real=dict(source=index.sources['urban-sao-paulo'].as_dict(),records=len(records),
                      kind_counts={kind:sum(r.kind==kind for r in records) for kind in ('street','poi','locality','address')},
                      street_queries=queries,reverse_matches=actual.total,
                      address_import=False,contact_editor_metadata_import=False,
                      index_bytes=sum(p.stat().st_size for p in index.directory.iterdir()))
            # Notices are maintained in the disposable DB, not duplicated in reports.
            real['source'].pop('notices')
        peak_disk=existing+synthetic_bytes+real['index_bytes']
        assert peak_disk<args.storage_limit
    peak=tracemalloc.get_traced_memory()[1];tracemalloc.stop()
    assert peak<128*1024*1024
    report=dict(passed=True,scope='Local regional/synthetic trial; not planet-scale, postal coverage or native RSS',
        python=platform.python_version(),system=platform.system(),
        synthetic=dict(records=args.records,source_sha256=source.sha256,build_seconds=build_seconds,
                       queries=len(latencies),median_seconds=statistics.median(latencies),
                       p95_seconds=sorted(latencies)[int(.95*(len(latencies)-1))],index_bytes=synthetic_bytes),
        real=real,peak_python_bytes=peak,python_memory_budget_bytes=128*1024*1024,
        generated_storage_peak_upper_bound_bytes=peak_disk,storage_limit_bytes=args.storage_limit,
        reserve_free_bytes=args.reserve_free,free_bytes_after=shutil.disk_usage(args.output.parent).free,
        runtime_sha256={p.relative_to(ROOT/'src/azimlib').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'src/azimlib').rglob('*.py'))})
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='runtime_sha256'},indent=2))


if __name__=='__main__':main()

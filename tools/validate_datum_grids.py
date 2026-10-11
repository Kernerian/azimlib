"""Offline cross-format validation against pinned primary LINZ numeric data.

Expected values come from separately published ASCII/Sideris files, never from
Azimlib output or a GIS engine. Full reference inputs are hashed and consumed;
only bounded selected cells are retained. No download or publication occurs.
"""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
import tracemalloc

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from azimlib import DatasetCatalog

REFERENCES = {
    'ntv2_ascii': ('e422770159af0759bf4fc190c0dd1bd8a2e86cf8495e7801a4670dfdd71a7f78',
                  'https://www.linz.govt.nz/sites/default/files/software/nzgd2kgrid9911.zip'),
    'geoid_sideris': ('c642bfd1b9f1bfaa417840ae28a9c6a4ae057033bc54469c89bd81c820a8499d',
                      'https://www.linz.govt.nz/sites/default/files/nzgeoid2016_sid_0.zip'),
}


def _verified(path, key):
    expected,url = REFERENCES[key]; digest=hashlib.sha256();count=0
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):
            digest.update(chunk);count+=len(chunk)
    if digest.hexdigest() != expected: raise ValueError('Primary reference SHA256 mismatch')
    return dict(sha256=expected,source=url,bytes=count)


def _weighted(nodes):
    u,v=Decimal('.25'),Decimal('.75')
    weights=((1-u)*(1-v),u*(1-v),(1-u)*v,u*v)
    return tuple(float(sum(Decimal(node[k])*w for node,w in zip(nodes,weights))) for k in range(len(nodes[0])))


def validate(horizontal_catalog, vertical_catalog, ntv2_ascii, geoid_sideris, *, max_python_bytes=128*1024*1024):
    start=time.perf_counter();tracemalloc.start()
    references={key:_verified(path,key) for key,path in [('ntv2_ascii',ntv2_ascii),('geoid_sideris',geoid_sideris)]}
    horizontal=DatasetCatalog(horizontal_catalog).grid_operation('linz-nzgd1949-nzgd2000',version='20200110')
    vertical=DatasetCatalog(vertical_catalog).grid_operation('linz-nzgeoid2016',version='20200110')
    if horizontal.grid.sha256 != '116d54c9ad2f7082610d887439106bac23d2df364b48506acf6c82ca8b5aba1d' or vertical.grid.sha256 != '081040dd085bf4da6995c927ca69fd1c6043dc9ae708b8ccbf1b59f81525981f':
        raise ValueError('Official grid payload/version mismatch')
    cells=[(1+13*(k//10),1+13*(k%10)) for k in range(100)]
    slots={r*141+c for j,i in cells for r,c in [(j,i),(j,i+1),(j+1,i),(j+1,i+1)]}
    retained={}; maximum=0.; count=0
    with Path(ntv2_ascii).open(encoding='ascii') as stream:
        lines=(line.strip() for line in stream if line.strip())
        headers=[next(lines) for _ in range(22)]
        if not headers[0].startswith('NUM_OREC') or not headers[-1].endswith('19881'):
            raise ValueError('Unexpected primary NTv2 ASCII geometry')
        for line in lines:
            if line.startswith('END'): continue
            fields=line.split()
            if len(fields)!=4: raise ValueError('Malformed primary ASCII node')
            r,c=divmod(count,141)
            actual=horizontal.grid.sample(180-c/10,-48+r/10)
            maximum=max(maximum,abs(actual[0]+float(fields[1])),abs(actual[1]-float(fields[0])))
            if count in slots:retained[count]=fields[:2]
            count+=1
    if count != 19881 or maximum > 1e-6: raise ValueError('NTv2 primary node comparison failed')
    interpolated_error=0.
    for r,c in cells:
        expected=_weighted([retained[j*141+i] for j,i in [(r,c),(r,c+1),(r+1,c),(r+1,c+1)]])
        actual=horizontal.grid.sample(180-(c+.25)/10,-48+(r+.75)/10)
        interpolated_error=max(interpolated_error,abs(actual[0]+expected[1]),abs(actual[1]-expected[0]))
    if interpolated_error > 1e-6: raise ValueError('NTv2 primary interpolation comparison failed')
    geoid_cells=[(1+200*(k//10),1+115*(k%10)) for k in range(100)]
    slots={r*1801+c for j,i in geoid_cells for r,c in [(j,i),(j,i+1),(j+1,i),(j+1,i+1)]}
    retained={};geoid_max=0.;geoid_count=0;checked=0
    with Path(geoid_sideris).open(encoding='ascii') as stream:
        header=next(stream).split()
        if header != ['2101','1801','-25.0000','160.0000','1.00','1.00']:
            raise ValueError('Unexpected primary Sideris geometry')
        for line in stream:
            for token in line.split():
                r,c=divmod(geoid_count,1801)
                if r%70 == 0 and c%60 == 0 and c<=1200:
                    actual=vertical.grid.sample(160+c/60,-25-r/60)[0]
                    geoid_max=max(geoid_max,abs(actual-float(token)));checked+=1
                if geoid_count in slots:retained[geoid_count]=(token,)
                geoid_count+=1
    if geoid_count != 2101*1801 or geoid_max > .00011: raise ValueError('GTX primary node comparison failed')
    geoid_interpolated_error=0.
    for r,c in geoid_cells:
        expected=_weighted([retained[j*1801+i] for j,i in [(r,c),(r,c+1),(r+1,c),(r+1,c+1)]])[0]
        actual=vertical.grid.sample(160+(c+.25)/60,-25-(r+.75)/60)[0]
        geoid_interpolated_error=max(geoid_interpolated_error,abs(actual-expected))
    if geoid_interpolated_error > .00011: raise ValueError('GTX primary interpolation comparison failed')
    roundtrip_error=0.
    for i in range(100):
        p=(166.01+i*.13,-47.99+i*.13,100.)
        q=horizontal.inverse().transform(*horizontal.transform(*p))
        roundtrip_error=max(roundtrip_error,max(abs(a-b) for a,b in zip(p,q)))
        q=vertical.inverse().transform(*vertical.transform(*p))
        if abs(q[2]-p[2]) > 1e-10:raise ValueError('Vertical real-grid inverse failed')
    if roundtrip_error > 1e-10:raise ValueError('Horizontal real-grid inverse failed')
    peak=tracemalloc.get_traced_memory()[1];tracemalloc.stop()
    if peak > max_python_bytes:raise ValueError('Grid validation exceeded Python memory budget')
    return dict(passed=True,scope='Independent primary cross-format numeric fixtures; no external GIS implementation',
                references=references,models=[dict(id=m,version='20200110',sha256=op.grid.sha256,license='CC-BY-4.0') for m,op in [('linz-nzgd1949-nzgd2000',horizontal),('linz-nzgeoid2016',vertical)]],
                ntv2=dict(nodes_compared=count,cells_compared=len(cells),max_node_error_arcsec=maximum,max_interpolation_error_arcsec=interpolated_error,tolerance_arcsec=1e-6),
                gtx=dict(reference_nodes_consumed=geoid_count,nodes_compared=checked,cells_compared=len(geoid_cells),max_node_error_metres=geoid_max,max_interpolation_error_metres=geoid_interpolated_error,tolerance_metres=.00011),
                roundtrips=100,max_horizontal_roundtrip_degrees=roundtrip_error,
                python_peak_bytes=peak,memory_scope='tracemalloc including grid reads, excluding interpreter/imports and OS page cache',
                max_python_bytes=max_python_bytes,seconds=time.perf_counter()-start,python=platform.python_version(),system=platform.system(),
                caveat='Validates parsing/interpolation/signs against published numeric data, not field survey accuracy or full EPSG coverage. No live converter comparison claimed.')


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('horizontal-catalog','vertical-catalog','ntv2-ascii','geoid-sideris','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--max-python-bytes',type=int,default=128*1024*1024)
    args=parser.parse_args(argv)
    report=validate(args.horizontal_catalog,args.vertical_catalog,args.ntv2_ascii,args.geoid_sideris,max_python_bytes=args.max_python_bytes)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__': main()

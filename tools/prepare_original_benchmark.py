"""Dev-only Polygon SHP/DBF -> benchmark GeoJSON, using only the stdlib.

This narrow decoder is NOT a public shapefile reader. Coordinates are retained
without simplification/quantization or datum conversion. SIRGAS 2000 is recorded
explicitly; Azimlib's spherical view is not a cadastral/ellipsoidal calculation.
Input remains outside the package. Specification: esri.com/library/whitepapers/pdfs/shapefile.pdf
"""
import argparse
from datetime import datetime,timezone
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import urllib.request
import zipfile

URL='https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2024/UFs/SP/SP_Municipios_2024.zip'

def area(ring):
    x,y=ring[0]
    return sum((a[0]-x)*(b[1]-y)-(b[0]-x)*(a[1]-y) for a,b in zip(ring,ring[1:]))/2

def inside(point,ring):
    x,y=point;result=False
    for a,b in zip(ring,ring[1:]):
        if (a[1]>y)!=(b[1]>y) and x<a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1]):result=not result
    return result

def polygons(blob):
    assert struct.unpack_from('>i',blob)[0]==9994
    assert struct.unpack_from('<ii',blob,28)==(1000,5),'Only Polygon type 5 is supported here'
    assert struct.unpack_from('>i',blob,24)[0]*2==len(blob)
    offset=100;result=[];vertices=0
    while offset<len(blob):
        number,words=struct.unpack_from('>ii',blob,offset);offset+=8
        body=memoryview(blob)[offset:offset+words*2];offset+=words*2
        shape=struct.unpack_from('<i',body)[0]
        if shape==0:result.append(None);continue
        assert shape==5 and number==len(result)+1
        count,size=struct.unpack_from('<ii',body,36)
        indices=struct.unpack_from('<'+'i'*count,body,44)+(size,)
        assert indices[0]==0 and all(a<b for a,b in zip(indices,indices[1:]))
        points=list(struct.iter_unpack('<dd',body[44+4*count:]))
        assert len(points)==size and all(math.isfinite(v) for p in points for v in p)
        vertices+=size;rings=[points[a:b] for a,b in zip(indices,indices[1:])]
        assert all(len(r)>=4 and r[0]==r[-1] for r in rings)
        outers=[r for r in rings if area(r)<0];holes=[r for r in rings if area(r)>0]
        assert len(outers)+len(holes)==len(rings) and outers
        assembled=[[list(reversed(r))] for r in outers]
        for hole in holes:
            candidates=[i for i,r in enumerate(outers) if inside(hole[0],r)]
            assert candidates,'Hole without an enclosing outer ring'
            index=min(candidates,key=lambda i:abs(area(outers[i])))
            assembled[index].append(list(reversed(hole)))
        result.append(dict(type='MultiPolygon',coordinates=assembled))
    assert offset==len(blob)
    return result,vertices

def attributes(blob,encoding):
    count=struct.unpack_from('<I',blob,4)[0];header,length=struct.unpack_from('<HH',blob,8)
    fields=[];offset=32
    while blob[offset]!=13:
        raw=blob[offset:offset+32]
        fields.append((raw[:11].split(b'\0')[0].decode('ascii'),chr(raw[11]),raw[16],raw[17]));offset+=32
    rows=[]
    for index in range(count):
        raw=blob[header+index*length:header+(index+1)*length]
        assert len(raw)==length
        if raw[0]==42:rows.append(None);continue
        assert raw[0]==32;values={};position=1
        for name,kind,size,decimals in fields:
            value=raw[position:position+size].decode(encoding).strip();position+=size
            values[name]=(float(value) if decimals else int(value)) if kind in ('N','F') and value else value
        rows.append(values)
    return rows

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path,required=True)
    parser.add_argument('--provenance',type=Path,required=True)
    args=parser.parse_args();args.directory.mkdir(parents=True,exist_ok=True)
    archive_path=args.directory/'SP_Municipios_2024.zip'
    if not archive_path.exists():
        with urllib.request.urlopen(URL,timeout=120) as response:archive_path.write_bytes(response.read())
    raw=archive_path.read_bytes()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names={Path(n).suffix.lower():n for n in archive.namelist() if not n.endswith('/')}
        encoding=archive.read(names['.cpg']).decode().strip().strip('\ufeff') if '.cpg' in names else 'utf-8'
        geometry,vertices=polygons(archive.read(names['.shp']))
        rows=attributes(archive.read(names['.dbf']),encoding)
        assert len(rows)==len(geometry)
        prj=archive.read(names['.prj']).decode('utf-8').strip()
        assert 'SIRGAS' in prj
        files={n:hashlib.sha256(archive.read(n)).hexdigest() for n in archive.namelist() if not n.endswith('/')}
    features=[dict(type='Feature',id=p.get('CD_MUN'),properties=p,geometry=g) for p,g in zip(rows,geometry) if p is not None and g is not None]
    output=args.directory/'ibge-sp-original-2024.geojson'
    output.write_text(json.dumps(dict(type='FeatureCollection',benchmark_source_crs=prj,
        features=features),ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    report=dict(source_url=URL,documentation='https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/15774-malhas.html',
        inspected_utc=datetime.now(timezone.utc).isoformat(),archive_sha256=hashlib.sha256(raw).hexdigest(),
        archive_bytes=len(raw),members_sha256=files,features=len(features),vertices=vertices,source_crs=prj,
        geojson_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),geojson_bytes=output.stat().st_size,
        decoder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='Original IBGE download, every supplied XY retained; winding/order adapted only. No simplification, datum transformation or GIS wrapper. Spherical geographic visualization only.',
        distribution='Input ZIP/GeoJSON remains outside wheel/sdist/source ZIP; no redistribution or licence assertion.')
    args.provenance.parent.mkdir(parents=True,exist_ok=True);args.provenance.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('features','vertices','archive_bytes','geojson_bytes','geojson_sha256')}))

if __name__=='__main__':main()

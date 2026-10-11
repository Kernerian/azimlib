"""Explicit, hash-pinned Unicode 15.1 conformance; no bundled test datasets.

Checks levels AND visual order, without excluding failing cases. The only
omitted positions are X9 controls marked x by the official test format.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
FIXTURES={
    'BidiCharacterTest.txt':('BidiCharacterTest.txt',6880530,'18507f7ec57ec8155b7771dbc88f3e3201ad08eba4dba70e4e095ef628020fa8'),
    'BidiTest.txt':('BidiTest.txt',7959974,'23413900dddcd2a246440f1f0cf27a3e1e62b3d0aebfa8f44ce241f5950fe956'),
    'GraphemeBreakTest.txt':('auxiliary/GraphemeBreakTest.txt',188211,'ed9c5e92fd0911ccbeeb63c97cb19c519ea272ff1112ce843abd991582dd848f'),
}


def acquire(directory):
    directory=Path(directory)
    if directory.exists():raise FileExistsError('Unicode acquisition requires a new destination')
    directory.parent.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(directory.parent).free-sum(v[1] for v in FIXTURES.values())<15*1024**3:
        raise OSError('Unicode fixtures would violate the 15 GiB reserve')
    with tempfile.TemporaryDirectory(prefix='azimlib-unicode-',dir=directory.parent) as folder:
        temporary=Path(folder)
        for name,(relative,size,sha) in FIXTURES.items():
            with urllib.request.urlopen('https://www.unicode.org/Public/15.1.0/ucd/'+relative,timeout=60) as response:
                raw=response.read(size+1)
            if len(raw)!=size or hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('Unicode fixture size/hash mismatch')
            (temporary/name).write_bytes(raw)
        (temporary/'LICENSE.txt').write_bytes((ROOT/'licenses/Unicode-Data.txt').read_bytes())
        temporary.rename(directory)


def validate(directory):
    sys.path.insert(0,str(ROOT/'src'))
    from azimlib._bidi import resolved_levels,visual_runs,properties
    from azimlib._unicode_icu import graphemes,unicode_version,unicode_data_version
    results=[]
    def lines(name):
        relative,size,sha=FIXTURES[name];raw=(Path(directory)/name).read_bytes()
        if len(raw)!=size or hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('Unicode fixture differs from pinned data')
        for line in raw.decode('utf8').splitlines():
            line=line.split('#',1)[0].strip()
            if line:yield line
    def check(text,direction,expected_levels,expected_order):
        levels,base=resolved_levels(text,direction)
        actual=[i for a,b,d in visual_runs(text,direction)
                for i in (range(b-1,a-1,-1) if d=='rtl' else range(a,b)) if expected_levels[i]!='x']
        passed=(len(levels)==len(expected_levels) and actual==expected_order
                and all(v=='x' or int(v)==a for v,a in zip(expected_levels,levels)))
        return passed,base
    def record(name,count,errors):
        relative,size,sha=FIXTURES[name]
        results.append(dict(file=name,cases=count,failures=len(errors),examples=errors[:10],
                            source='https://www.unicode.org/Public/15.1.0/ucd/'+relative,bytes=size,sha256=sha))
    errors=[];count=0
    for line in lines('BidiCharacterTest.txt'):
        chars,paragraph,base,levels,order=line.split(';')[:5]
        text=''.join(chr(int(v,16)) for v in chars.split())
        passed,actual_base=check(text,{'0':'ltr','1':'rtl','2':'auto'}[paragraph.strip()],levels.split(),list(map(int,order.split())))
        if not passed or actual_base!=int(base):errors.append(dict(case=count,codepoints=chars))
        count+=1
    record('BidiCharacterTest.txt',count,errors)
    chars=dict(L='a',R='א',AL='ا',EN='1',AN='١',ES='+',ET='$',CS=',',NSM='\u0300',BN='\u00ad',B='\u2029',S='\t',WS=' ',ON='!',LRE='\u202a',RLE='\u202b',LRO='\u202d',RLO='\u202e',PDF='\u202c',LRI='\u2066',RLI='\u2067',FSI='\u2068',PDI='\u2069')
    if not all(properties(c)[0]==t for t,c in chars.items()):raise ValueError('Unicode class representatives mismatch')
    errors=[];count=0
    for line in lines('BidiTest.txt'):
        if line.startswith('@Levels:'):levels=line.split(':',1)[1].split();continue
        if line.startswith('@Reorder:'):order=list(map(int,line.split(':',1)[1].split()));continue
        if line.startswith('@'):continue
        types,bits=line.split(';');text=''.join(chars[t] for t in types.split())
        for flag,direction in ((1,'auto'),(2,'ltr'),(4,'rtl')):
            if not int(bits.strip(),16)&flag:continue
            if not check(text,direction,levels,order)[0]:errors.append(dict(case=count,types=types,direction=direction))
            count+=1
    record('BidiTest.txt',count,errors)
    errors=[];count=0
    for line in lines('GraphemeBreakTest.txt'):
        text='';boundaries=[]
        for token in line.split():
            if token=='÷':boundaries.append(len(text))
            elif token!='×':text+=chr(int(token,16))
        if tuple(zip(boundaries,boundaries[1:]))!=graphemes(text):errors.append(dict(case=count))
        count+=1
    record('GraphemeBreakTest.txt',count,errors)
    return dict(passed=not any(r['failures'] for r in results),resolver='Azimlib UAX #9 r51',
                fixture_unicode_version='15.1.0',ICU=unicode_version(),property_unicode_version=unicode_data_version(),results=results,
                scope='Pinned official levels, order and grapheme tests; not a proof for every future Unicode property version or visual acceptance')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--acquire',action='store_true');args=parser.parse_args()
    if args.acquire:acquire(args.data)
    result=validate(args.data);args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(result,indent=2));sys.exit(0 if result['passed'] else 1)

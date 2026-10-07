"""Check generated site file/fragment targets and exact assets, without HTTP."""
import argparse,hashlib,json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote,urlsplit
ROOT=Path(__file__).resolve().parents[1]
class Page(HTMLParser):
    def __init__(self,text):
        super().__init__();self.links=[];self.ids=set();self.feed(text)
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'id' in attrs:self.ids.add(attrs['id'])
        for name in ('href','src'):
            if name in attrs:self.links.append(attrs[name])
def check(site):
    site=Path(site).resolve();parsed={p:Page(p.read_text('utf8')) for p in site.rglob('*.html')}
    broken=[];local=0;fragments=0
    for path,page in parsed.items():
        for value in page.links:
            link=urlsplit(value)
            if link.scheme or value.startswith('//'):continue
            target=(path.parent/unquote(link.path)).resolve() if link.path else path
            local+=1
            if not target.is_relative_to(site) or not target.exists():broken.append((path.relative_to(site).as_posix(),value));continue
            if link.fragment and target in parsed:
                fragments+=1
                if unquote(link.fragment) not in parsed[target].ids:broken.append((path.relative_to(site).as_posix(),value))
    manifest=json.loads((site/'site-manifest.json').read_text('utf8'))
    for name,digest in manifest['source_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    copies=0
    for path in (site/'docs').rglob('*'):
        source=ROOT/path.relative_to(site)
        if path.is_file() and path.suffix!='.html' and source.is_file():assert path.read_bytes()==source.read_bytes(),path;copies+=1
    result=dict(passed=not broken,version=manifest['version'],pages=len(parsed),local_targets=local,fragment_targets=fragments,copied_assets_exact=copies,broken=broken,hosted=False)
    assert not broken,result
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--site',type=Path,required=True);p.add_argument('--output',type=Path);a=p.parse_args();result=check(a.site)
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,indent=2))

"""Build version-labelled static docs atomically; parser is development tooling."""
import argparse,hashlib,html,json,os,re,shutil,tempfile,unicodedata
from pathlib import Path
from urllib.parse import quote,urlsplit,urlunsplit,unquote
try:import tomllib
except ImportError:import tomli as tomllib
ROOT=Path(__file__).resolve().parents[1]
POLICIES=('README.md','CHANGELOG.md','THIRD_PARTY_LICENSES.md','CONTRIBUTING.md','CODE_OF_CONDUCT.md','SECURITY.md')
CSS="""*{box-sizing:border-box}body{margin:0;background:#fff;color:#23323e;font:16px/1.65 system-ui,sans-serif}header{padding:14px 24px;border-bottom:1px solid #dce3e8;background:#f7f9fa;display:flex;gap:18px;align-items:center;position:sticky;top:0}header a{font-weight:750}header span{font-size:13px;color:#526570}input{padding:8px;border:1px solid #ccd5dd;border-radius:6px;max-width:280px}a{color:#167c9e;text-decoration:none}a:hover{text-decoration:underline}aside{position:fixed;top:77px;bottom:0;width:230px;padding:24px;border-right:1px solid #e1e7ec;overflow:auto}aside a{display:block;padding:7px 0}main{margin-left:230px;max-width:1160px;padding:32px 48px 80px}h1,h2,h3{line-height:1.25;color:#1c303c;scroll-margin-top:100px}h1{font-size:34px}h2{margin-top:40px;font-size:25px}img{max-width:100%;height:auto}pre{overflow:auto;background:#f4f7f9;border:1px solid #dfe7eb;border-radius:8px;padding:18px;font-size:13px;line-height:1.5}code{font-family:ui-monospace,Consolas,monospace}table{border-collapse:collapse;width:100%;display:block;overflow:auto}td,th{border:1px solid #dce3e8;padding:9px 12px}th{background:#f3f6f8;text-align:left}blockquote{border-left:3px solid #2d99aa;padding-left:16px;color:#566b77}footer{border-top:1px solid #dce3e8;margin-top:45px;padding-top:16px;font-size:13px;color:#627480}#results{background:#fff;position:absolute;right:20px;top:62px;box-shadow:0 4px 12px #0002;max-width:400px;max-height:400px;overflow:auto}#results a{display:block;padding:10px 16px}@media(max-width:800px){aside{position:static;width:auto;border-bottom:1px solid #ddd}aside a{display:inline-block;margin-right:14px}main{margin:0;padding:24px}header{flex-wrap:wrap;position:static}h1{font-size:28px}}"""
JS="""const input=document.getElementById('search'),results=document.getElementById('results');let index=[];fetch(document.body.dataset.root+'search.json').then(r=>r.json()).then(data=>index=data);input.addEventListener('input',()=>{results.replaceChildren();const q=input.value.toLowerCase().trim();if(q.length<2)return;for(const item of index.filter(x=>x.title.toLowerCase().includes(q)).slice(0,12)){const a=document.createElement('a');a.textContent=item.title;a.href=document.body.dataset.root+item.path;results.appendChild(a)}});"""
def slug(text):
    return re.sub(r'\s+','-',re.sub(r'[^\w\s-]','',unicodedata.normalize('NFKC',text).lower())).strip('-') or 'section'
def link_target(current,target,ref):
    parts=urlsplit(target)
    if parts.scheme or target.startswith('//') or not parts.path:return target
    source=(current.parent/unquote(parts.path)).resolve()
    if not source.is_relative_to(ROOT):raise ValueError('Documentation link escapes repository')
    relative=source.relative_to(ROOT).as_posix()
    if not source.exists():raise ValueError(f'Missing documentation link: {current.relative_to(ROOT)} -> {target}')
    if source.suffix=='.md' and (relative.startswith('docs/') or relative in POLICIES):parts=parts._replace(path=parts.path[:-3]+'.html')
    elif relative.startswith('docs/') or relative.startswith('licenses/') or relative in ('LICENSE','NOTICE_COLORMAPS'):pass
    else:return 'https://github.com/Kernerian/azimlib/'+('tree/' if source.is_dir() else 'blob/')+quote(ref,safe='/')+'/'+quote(relative,safe='/')+(('#'+parts.fragment) if parts.fragment else '')
    return urlunsplit(parts)
def build(output,ref):
    from markdown_it import MarkdownIt
    output=Path(output).resolve()
    if output.exists():raise FileExistsError('Documentation output must be a new directory')
    if output==ROOT or ROOT.is_relative_to(output):raise ValueError('Output cannot contain the source repository')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9/._-]*',ref) or '..' in ref.split('/'):raise ValueError('Invalid source ref')
    version=tomllib.loads((ROOT/'pyproject.toml').read_text('utf8'))['project']['version']
    output.parent.mkdir(parents=True,exist_ok=True)
    sources=sorted([ROOT/n for n in POLICIES]+list((ROOT/'docs').rglob('*.md')))
    with tempfile.TemporaryDirectory(prefix='azimlib-docs-',dir=output.parent) as folder:
        staging=Path(folder)/'site';staging.mkdir();files={};search=[]
        for source in (ROOT/'docs').rglob('*'):
            if source.is_symlink():raise ValueError('Documentation symlinks are not allowed')
            if not source.is_file() or source.suffix not in ('.json','.png','.svg','.pdf','.gif','.html','.txt'):continue
            if any(part.startswith('.') or part=='__pycache__' for part in source.relative_to(ROOT/'docs').parts):continue
            target=staging/source.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
        for source in [ROOT/'LICENSE',ROOT/'NOTICE_COLORMAPS',*sorted((ROOT/'licenses').glob('*.txt'))]:
            target=staging/source.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
        for source in sources:
            md=MarkdownIt('commonmark',{'html':False,'linkify':False}).enable('table').enable('strikethrough')
            tokens=md.parse(source.read_text('utf8'));seen={};headings=[]
            for i,token in enumerate(tokens):
                if token.type=='heading_open':
                    text=tokens[i+1].content;base=slug(text);n=seen.get(base,0);seen[base]=n+1
                    token.attrSet('id',base+(f'-{n}' if n else ''));headings.append(text)
                for child in token.children or []:
                    for attr in ('href','src'):
                        value=child.attrGet(attr)
                        if value is not None:child.attrSet(attr,link_target(source,value,ref))
            relative=source.relative_to(ROOT).with_suffix('.html');target=staging/relative
            prefix=os.path.relpath(staging,target.parent).replace('\\','/')+'/'
            if prefix=='./':prefix=''
            title=headings[0] if headings else source.stem
            nav=''.join(f'<a href="{prefix}docs/{name}.html">{label}</a>' for name,label in (('index','Overview'),('getting-started','Getting started'),('migration-0.3','Migration'),('gallery-0.3','Gallery'),('api','API reference'),('api-stability','Compatibility policy'),('release-progress-0.3','Release progress'),('roadmap','Roadmap')))
            body=md.renderer.render(tokens,md.options,{})
            source_url='https://github.com/Kernerian/azimlib/blob/'+quote(ref,safe='/')+'/'+source.relative_to(ROOT).as_posix()
            page=f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} · Azimlib {version}</title><link rel="stylesheet" href="{prefix}site.css"><body data-root="{prefix}"><header><a href="{prefix}docs/index.html">Azimlib</a><span>{version} · development documentation</span><input id="search" type="search" aria-label="Search documentation titles" placeholder="Find a guide"><div id="results"></div></header><aside>{nav}</aside><main>{body}<footer>Original code/compositions: BSD 3-Clause · Kernerian. <a href="{prefix}THIRD_PARTY_LICENSES.html">Third-party notices</a>. <a href="{source_url}">Source</a>.</footer></main><script src="{prefix}site.js"></script></body></html>'
            target.parent.mkdir(parents=True,exist_ok=True);target.write_text(page,encoding='utf8',newline='\n')
            search.append(dict(title=title,path=relative.as_posix()));files[source.relative_to(ROOT).as_posix()]=hashlib.sha256(source.read_bytes()).hexdigest()
        (staging/'index.html').write_text('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=docs/index.html"><a href="docs/index.html">Azimlib documentation</a>\n',encoding='utf8')
        (staging/'site.css').write_text(CSS,encoding='utf8');(staging/'site.js').write_text(JS,encoding='utf8')
        (staging/'search.json').write_text(json.dumps(search,ensure_ascii=False),encoding='utf8')
        report=dict(version=version,ref=ref,pages=len(search),source_sha256=files,parser='markdown-it-py (external MIT tooling)',hosted=False)
        (staging/'site-manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
        if output.exists():raise FileExistsError(output)
        staging.rename(output)
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--ref',default='dev/0.3.0');a=p.parse_args()
    result=build(a.output,a.ref);print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))

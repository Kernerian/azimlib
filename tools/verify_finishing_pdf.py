"""Validate finishing exports with independent optional pypdf/Pillow/Poppler.

Run audit_finishing.py and examples/finishing_atlas.py into installed-export
and gallery-installed subdirectories of --output first. No network/download.
Dependencies are validation tools only; report includes input file hashes.
"""
from pathlib import Path
import hashlib,json,subprocess
from pypdf import PdfReader
from PIL import Image
import argparse
parser=argparse.ArgumentParser(description='Independent pypdf/Poppler check; optional validation tools, not Azimlib runtime dependencies')
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--pdftoppm',type=Path,required=True)
args=parser.parse_args();ROOT=args.output;POP=args.pdftoppm
notice=(Path(__file__).resolve().parents[1]/'src/azimlib/fonts/LICENSE_DEJAVU').read_bytes()
rows=[]
for dpi in (100,150,200):
 file=ROOT/f'installed-export/backend-{dpi}.pdf';reader=PdfReader(file,strict=True)
 assert len(reader.pages)==1
 assert tuple(float(v) for v in reader.pages[0].mediabox)==(0.,0.,288.,144.)
 assert reader.attachments['DejaVu-license.txt']==[notice]
 assert '/JavaScript' not in reader.trailer['/Root'] and '/OpenAction' not in reader.trailer['/Root']
 prefix=file.with_name(f'pdf-{dpi}-preview')
 subprocess.run([str(POP),'-r',str(dpi),'-png','-singlefile',str(file),str(prefix)],check=True,capture_output=True)
 with Image.open(file.with_suffix('.png')).convert('RGBA') as original,Image.open(prefix.with_suffix('.png')).convert('RGB') as rendered:
  white=Image.new('RGBA',original.size,'white');white.alpha_composite(original);rgb=white.convert('RGB');white.close()
  assert rgb.size==rendered.size==(4*dpi,2*dpi)
  errors=[]
  for x,y in ((50,50),(100,60),(180,75)):
   px,py=round(x*dpi/100),round(y*dpi/100)
   a,b=rgb.getpixel((px,py)),rendered.getpixel((px,py));errors.append(max(abs(a[i]-b[i]) for i in range(3)))
  assert max(errors)<=2,errors;rgb.close()
 rows.append(dict(file=file.name,dpi=dpi,page_inches=[4,2],alpha_probe_max_channel_error=max(errors),sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
atlas=ROOT/'gallery-installed/finishing-atlas.pdf';reader=PdfReader(atlas,strict=True)
assert tuple(float(v) for v in reader.pages[0].mediabox)==(0.,0.,864.,432.)
assert reader.attachments['DejaVu-license.txt']==[notice]
provenance=json.loads(reader.attachments['Material-provenance.json'][0]);assert any(p['source']=='examples/finishing_atlas.py' for p in provenance)
subprocess.run([str(POP),'-png','-scale-to','1440','-singlefile',str(atlas),str(atlas.with_name('pdf-preview'))],check=True,capture_output=True)
report=dict(passed=True,scope='Strict independent pypdf parsing, embedded notices and Poppler rasterization; three interior color probes per DPI, not whole-image pixel equality',
            backends=rows,atlas=dict(file=atlas.name,page_inches=[12,6],font_notice_exact=True,material_notice_present=True,sha256=hashlib.sha256(atlas.read_bytes()).hexdigest()))
(ROOT/'pdf-independent-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps(report,indent=2))

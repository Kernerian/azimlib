"""Optional independent-reader verification; pypdf is a dev tool, not a backend."""
import argparse,hashlib,importlib.metadata,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--pdf',type=Path,required=True);p.add_argument('--pages',type=int,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    try:from pypdf import PdfReader
    except ImportError as exc:raise ImportError('This optional independent check needs separately installed pypdf') from exc
    reader=PdfReader(args.pdf,strict=True);assert len(reader.pages)==args.pages
    notice=(ROOT/'src/azimlib/fonts/LICENSE_DEJAVU').read_bytes();attachments=reader.attachments
    for i in range(args.pages):
        values=attachments[f'page-{i+1}-DejaVu-license.txt'];assert values and all(v==notice for v in values)
    root=reader.trailer['/Root'];assert '/OpenAction' not in root
    assert all(len(page.get_contents().get_data())>0 for page in reader.pages)
    report=dict(passed=True,file=args.pdf.name,pdf_sha256=hashlib.sha256(args.pdf.read_bytes()).hexdigest(),pages=len(reader.pages),
        page_sizes_points=[[float(v) for v in page.mediabox] for page in reader.pages],font_notices_exact=True,
        reader='pypdf',reader_version=importlib.metadata.version('pypdf'),tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='Independent strict page/content/attachment reader check; does not render pixels or validate third-party source ownership')
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()

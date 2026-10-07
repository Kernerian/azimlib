"""Own multipage PDF facade; no third-party PDF merger or plotting backend."""
from pathlib import Path
import os
import tempfile
from ..figure import Figure
from ..renderers.pdf import render_pdf_pages

class PdfPages:
    def __init__(self,filename):self.filename=filename;self._pages=[];self.closed=False
    def savefig(self,figure=None):
        if self.closed:raise RuntimeError('PdfPages is closed')
        if figure is None:
            from .. import gcf
            figure=gcf()
        if not isinstance(figure,Figure):raise TypeError('Require an Azimlib Figure')
        if len(self._pages)>=256:raise ValueError('PDF budget is 256 pages')
        # Snapshot the complete own object graph now; later edits do not alter it.
        from ..renderers.pdf import render_pdf
        objects=render_pdf(figure.to_scene(cull=False,simplify=False),dpi=figure.dpi,_objects=True)
        if sum(sum(map(len,p)) for p in self._pages)+sum(map(len,objects))>64000000:raise ValueError('PDF object budget is 64 MB')
        self._pages.append(objects)
    def get_pagecount(self):return len(self._pages)
    def close(self):
        if self.closed:return
        if not self._pages:self.closed=True;return
        value=render_pdf_pages(self._pages)
        if hasattr(self.filename,'write'):self.filename.write(value)
        else:
            path=Path(self.filename)
            if path.suffix.lower()!='.pdf':raise ValueError('PdfPages requires a .pdf path')
            path.parent.mkdir(parents=True,exist_ok=True);fd,temp=tempfile.mkstemp(prefix='.azimlib-',suffix='.pdf',dir=path.parent);os.close(fd)
            try:Path(temp).write_bytes(value);os.replace(temp,path)
            finally:
                if Path(temp).exists():Path(temp).unlink()
        self._pages.clear();self.closed=True
    def __enter__(self):return self
    def __exit__(self,kind,value,tb):
        if kind is None:self.close()
        else:self._pages.clear();self.closed=True

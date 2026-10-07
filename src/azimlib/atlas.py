"""Owned region/page composition and static exports with no implicit basemap."""
from dataclasses import dataclass
from pathlib import Path
import os
import tempfile
from .figure import Figure

@dataclass(frozen=True)
class Region:
    name:str
    extent:tuple
    def __post_init__(self):
        import math
        extent=tuple(float(v) for v in self.extent)
        if len(extent)!=4 or not all(math.isfinite(v) for v in extent):raise ValueError('Region extent requires four finite values')
        w,e,s,n=extent
        if not -180<=w<=180 or not -180<=e<=180 or w==e or (e<w and e+360<=w) or not -90<=s<n<=90:raise ValueError('Region extent is west,east,south,north; longitude may cross the antimeridian')
        object.__setattr__(self,'name',str(self.name));object.__setattr__(self,'extent',extent)

def export_directory(directory,export):
    target=Path(directory)
    if target.exists():raise FileExistsError('Choose a new output directory to preserve existing files')
    target.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.azimlib-',dir=target.parent) as temp:
        folder=Path(temp)/'pages';folder.mkdir();export(folder)
        if target.exists():raise FileExistsError('Output directory appeared during export')
        os.rename(folder,target)
    return target

class Atlas:
    def __init__(self,pages,*,labels=None):
        pages=tuple(pages)
        if not 1<=len(pages)<=256 or any(not isinstance(p,Figure) for p in pages):raise ValueError('Atlas requires 1..256 Figures')
        labels=tuple(str(v) for v in labels) if labels is not None else tuple(f'Page {i+1}' for i in range(len(pages)))
        if len(labels)!=len(pages):raise ValueError('One label per page is required')
        self.pages,self.labels=pages,labels
    def __len__(self):return len(self.pages)
    def __getitem__(self,index):return self.pages[index]
    @classmethod
    def from_regions(cls,regions,draw,*,projection='equirectangular',figsize=(6.4,4.8),style='default'):
        from . import style as styles
        regions=tuple(regions)
        if not regions or len(regions)>256 or any(not isinstance(v,Region) for v in regions):raise ValueError('Require 1..256 Region objects')
        if not callable(draw):raise TypeError('draw must be callable (axes, region)')
        pages=[]
        with styles.context(style):
            for region in regions:
                fig=Figure(figsize=figsize);ax=fig.add_subplot(111,projection=projection)
                ax.set_extent(region.extent);draw(ax,region);ax.set_extent(region.extent);pages.append(fig)
        return cls(pages,labels=[r.name for r in regions])
    def save_pages(self,directory,*,format='png',dpi=None):
        if format not in ('png','svg','pdf'):raise ValueError('Page format must be png, svg or pdf')
        def export(folder):
            for i,page in enumerate(self.pages):page.savefig(folder/f'page-{i:03}.{format}',dpi=dpi)
        return export_directory(directory,export)
    def savefig(self,path):
        from .backends.backend_pdf import PdfPages
        with PdfPages(path) as pdf:
            for page in self.pages:pdf.savefig(page)
        return Path(path) if not hasattr(path,'write') else path
    save=savefig

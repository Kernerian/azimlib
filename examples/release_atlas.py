"""Integrated original 0.3 development gallery; no implicit dataset download."""
import argparse,hashlib,json,math,sys
from pathlib import Path
import azimlib as azl
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))

def create(name):
    if name=='urban':
        from urban import create as factory
        return factory()
    if name=='terrain3d':
        from terrain3d import make_figure
        return make_figure()
    if name=='temporal':
        from temporal_atlas import create as factory
        fig,movie=factory();movie.seek(2,draw=False);movie.close();return fig
    fig,ax=azl.subplots(figsize=(4.8,4),projection='mercator');ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
    if name=='political':
        ax.map('brazil',facecolor='#f2f4f5',edgecolor='#445560',linewidth=.7)
        ax.states(facecolor='none',edgecolor='#82919a',linewidth=.35);ax.set_extent((-76,-32,-36,8));ax.set_title('Political geography');ax.north_arrow(size=18)
    elif name=='physical':
        ax.map('brazil',facecolor='#ecefdf',edgecolor='#68746a',linewidth=.5)
        ax.rivers(color='#248cb0',linewidth=.6,label='Natural Earth rivers');ax.lakes(facecolor='#bbd8e1',edgecolor='#248cb0',linewidth=.3)
        ax.set_extent((-76,-32,-36,8));ax.set_title('Physical geography');ax.scale_bar();ax.legend(loc='lower right',fontsize=7)
    elif name=='scientific':
        n=18;z=[[math.exp(-((i-7)**2+(j-10)**2)/24)+.4*math.exp(-((i-14)**2+(j-3)**2)/12) for i in range(n)] for j in range(n)]
        im=ax.imshow(z,extent=(-55,-40,-30,-15),origin='lower',cmap='viridis');ax.set_extent((-55,-40,-30,-15))
        ax.set_title('Synthetic scientific field');cax=fig.add_axes([.28,.11,.54,.035]);fig.colorbar(im,cax=cax,orientation='horizontal',label='Synthetic intensity')
    else:raise ValueError(name)
    fig.subplots_adjust(left=.18,right=.91,bottom=.32 if name=='scientific' else .16,top=.86)
    return fig

def main(output):
    from PIL import Image
    folder=Path(output);folder.mkdir(parents=True,exist_ok=True);runtime=Path(azl.__file__).resolve().parent;records=[];panels=[]
    for name in ('political','physical','urban','scientific','terrain3d','temporal'):
        fig=create(name);files={}
        for extension in ('png','svg','pdf'):
            path=folder/f'{name}.{extension}';fig.savefig(path,dpi=100)
            if extension=='svg':
                from temporal_atlas import portable_svg
                portable_svg(path)
            files[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
        with Image.open(folder/f'{name}.png') as original:
            im=original.convert('RGB');im.thumbnail((540,380));panel=Image.new('RGB',(560,400),'white');panel.paste(im,((560-im.width)//2,(400-im.height)//2));panels.append(panel)
            dimensions=list(original.size)
        records.append(dict(name=name,files=files,pixels=dimensions,data='Natural Earth public domain boundaries/rivers/lakes' if name in ('political','physical') else 'Original synthetic features/fields/terrain; temporal basemap Natural Earth',composition_license='BSD-3-Clause',font='Bundled DejaVu with its own terms',palettes='Original AZIM10/terrain or CC0 Viridis/Magma',static_without_controls=True));azl.close(fig)
    overview=Image.new('RGB',(1120,1200),'white')
    for i,panel in enumerate(panels):overview.paste(panel,(560*(i%2),400*(i//2)))
    overview.save(folder/'overview.png');overview.close()
    names=('release_atlas.py','urban.py','terrain3d.py','temporal_atlas.py')
    report=dict(version=azl.__version__,generator='examples/release_atlas.py',example_sha256={n:hashlib.sha256((ROOT/'examples'/n).read_bytes()).hexdigest() for n in names},runtime_sha256={p.relative_to(runtime).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(runtime.rglob('*.py'))},cases=records,overview_sha256=hashlib.sha256((folder/'overview.png').read_bytes()).hexdigest(),scope='Own installed rendering; no reference/GIS import or implicit downloads; synthetic gallery, not platform acceptance')
    (folder/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('Six current gallery cases exported.')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.output)

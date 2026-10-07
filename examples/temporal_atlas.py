"""Original repeatable climate/population fields and regional multi-page atlas."""
import argparse,hashlib,json,math,re
from pathlib import Path
import azimlib as azl
from azimlib.animation import FuncAnimation
EXTENT=(-54,-42,-28,-16)

def climate(frame,n=12):
    return [[12+frame*2+15*math.exp(-((i-n*.3-frame*.7)**2+(j-n*.55)**2)/12) for i in range(n)] for j in range(n)]

def create():
    with azl.style.context('default'):
        fig,axes=azl.subplots(1,3,figsize=(10.5,3.9),dpi=100)
        times=[2000,2005,2010,2015];series=azl.TemporalSeries(times,[climate(i) for i in range(4)],unit='year',name='Synthetic temperature')
        bindings=[];bars=[]
        for ax,policy in zip(axes.flat[:2],('global','frame')):
            ax.map('brazil',facecolor='#f7f8f9',edgecolor='#77838b',linewidth=.35)
            image=ax.imshow(series[0].data,extent=EXTENT,origin='lower',cmap='magma',alpha=.85)
            ax.set_extent(EXTENT);ax.set_title('Temperature · '+policy+' limits',fontsize=10);ax.tick_params(labelsize=8)
            cb=fig.colorbar(image,ax=ax,orientation='horizontal',label='Synthetic temperature (°C)',shrink=.85)
            bars.append(cb)
            bindings.append(series.bind(image,scale=policy))
        ax=axes[2];ax.map('brazil',facecolor='#f7f8f9',edgecolor='#77838b',linewidth=.35);ax.set_extent(EXTENT)
        ax.set_title('Population · proportional points',fontsize=10);ax.tick_params(labelsize=8)
        lon=[-52,-49,-45,-44];lat=[-19,-23,-21,-26];values=[[20+10*i+15*t for i in range(4)] for t in range(4)]
        points=ax.scatter(lon,lat,s=values[0],c=values[0],cmap='viridis',edgecolor='white',linewidth=.5)
        population=azl.TemporalSeries(times,values,unit='year',name='Synthetic population');pop=population.bind(points)
        cb=fig.colorbar(points,ax=ax,orientation='horizontal',label='Synthetic population (index)',shrink=.85)
        bars.append(cb)
        title=fig.suptitle('Temporal geography · year 2000',fontsize=14)
        def update(index):
            for binding in bindings:binding.apply(index)
            pop.apply(index)
            for bar in bars:bar.locator=azl.ticker.MaxNLocator(4)
            points.set_sizes(values[index]);title.set_text(f'Temporal geography · year {times[index]}')
        ani=FuncAnimation(fig,update,4,interval=350,autoplay=False)
    return fig,ani

def create_atlas():
    regions=[azl.Region('South / Southeast',(-55,-40,-34,-16)),azl.Region('North',(-74,-45,-13,6)),azl.Region('Northeast',(-48,-34,-18,0))]
    def draw(ax,region):
        ax.map('brazil',facecolor='#f0f2f3',edgecolor='#5d6c75',linewidth=.45);ax.states(facecolor='none',edgecolor='#8b969b',linewidth=.3)
        ax.set_title(region.name);ax.set_xlabel('Longitude');ax.set_ylabel('Latitude');ax.tick_params(labelsize=8)
    return azl.Atlas.from_regions(regions,draw,figsize=(4.8,4.3))

def portable_svg(path):
    # Keep the font notice exact after XML decoding; normalize only storage.
    def notice(match):
        body='\n'.join(line.rstrip(' ')+('&#32;'*(len(line)-len(line.rstrip(' ')))) for line in match[2].split('\n'))
        return match[1]+body+match[3]
    text=re.sub(r'(<metadata id="azimlib-font-license">)(.*?)(</metadata>)',notice,path.read_text('utf8'),flags=re.S)
    path.write_text(text,encoding='utf8',newline='\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('outputs/temporal'));p.add_argument('--show',action='store_true');args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    fig,ani=create();ani.seek(2,draw=False)
    for suffix in ('png','svg','pdf'):fig.savefig(args.output/f'temporal-atlas.{suffix}')
    small,ax=azl.subplots(figsize=(3,3),dpi=80);image=ax.imshow(climate(0,8),extent=EXTENT,origin='lower',cmap='magma');ax.set_extent(EXTENT);ax.set_title('Synthetic climate')
    series=azl.TemporalSeries(range(4),[climate(i,8) for i in range(4)],unit='step');binding=series.bind(image)
    movie=FuncAnimation(small,lambda i:binding.apply(i),4,autoplay=False);movie.save(args.output/'climate.gif',fps=2);movie.save_frames(args.output/'frames')
    atlas=create_atlas();atlas.savefig(args.output/'regions.pdf');atlas.save_pages(args.output/'pages',format='svg')
    for path in [args.output/'temporal-atlas.svg',*sorted((args.output/'pages').glob('*.svg'))]:portable_svg(path)
    runtime=Path(azl.__file__).parent
    outputs=['temporal-atlas.png','temporal-atlas.svg','temporal-atlas.pdf','climate.gif','regions.pdf']+[p.relative_to(args.output).as_posix() for folder in ('frames','pages') for p in sorted((args.output/folder).iterdir())]
    manifest=dict(version=azl.__version__,source='Original deterministic synthetic fields/population; regional basemaps Natural Earth; bundled DejaVu text',generator='examples/temporal_atlas.py',generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),runtime_sha256={p.relative_to(runtime).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(runtime.rglob('*.py'))},files={name:hashlib.sha256((args.output/name).read_bytes()).hexdigest() for name in outputs})
    (args.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8',newline='\n')
    if args.show:
        movie.close();azl.close(small);ani.autoplay=True;ani._started=False;fig.show(block=True)
    else:movie.close();ani.close();azl.close('all')
if __name__=='__main__':main()

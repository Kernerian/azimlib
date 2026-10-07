"""Original synthetic scientific 2D maps; no external scientific dataset."""
import argparse
import math
import random
from pathlib import Path
import azimlib as azl

EXTENT=(-54,-42,-28,-16)

def terrain_grid(n=25):
    x=[EXTENT[0]+(EXTENT[1]-EXTENT[0])*(i+.5)/n for i in range(n)]
    y=[EXTENT[2]+(EXTENT[3]-EXTENT[2])*(j+.5)/n for j in range(n)]
    z=[[150+2400*math.exp(-((a+49)**2+(b+22)**2)/10)+750*math.exp(-((a+44)**2+(b+26)**2)/3) for a in x] for b in y]
    return x,y,z

def decorate(ax,title):
    ax.set_extent(EXTENT);ax.set_title(title,fontsize=11)
    ax.set_xlabel('Longitude',fontsize=9);ax.set_ylabel('Latitude',fontsize=9)
    ax.tick_params(labelsize=8)

def create():
    with azl.style.context('default'):
        fig,axes=azl.subplots(1,3,figsize=(13,4.8),dpi=120,layout='constrained')
        x,y,z=terrain_grid()
        image,elevation=axes[0].terrain(z,extent=EXTENT,dx=12000,dy=12000,vmin=0,vmax=3000,shade=.55)
        contours=axes[0].contour(x,y,z,levels=[500,1000,1500,2000],colors='#4c5952',linewidths=.4)
        axes[0].clabel(contours,fmt='%g',fontsize=6,inline=True)
        axes[0].line([(-52,-18),(-50.5,-20),(-49,-23),(-46,-26)],color='#288eaf',linewidth=1.3)
        axes[0].scale_bar(length=200,fontsize=6)
        fig.colorbar(elevation,ax=axes[0],orientation='horizontal',label='Synthetic elevation (m)',shrink=.85)
        decorate(axes[0],'Hypsometry + hillshade + contours')
        masked=[row[:] for row in z]
        for j in range(10,14):
            for i in range(10,14):masked[j][i]=None
        bands=axes[1].contourf(x,y,masked,levels=[0,500,1000,1500,2000,3000],cmap='terrain')
        axes[1].contour(x,y,masked,levels=[500,1000,1500,2000],colors='#4b5558',linewidths=.4)
        fig.colorbar(bands,ax=axes[1],orientation='horizontal',spacing='proportional',label='Filled bands with a NoData hole',shrink=.85,drawedges=True)
        decorate(axes[1],'Own contourf / actual inner rings')
        rng=random.Random(503)
        lon=[rng.uniform(-53.5,-42.5) for _ in range(40)];lat=[rng.uniform(-27.5,-16.5) for _ in lon]
        values=[math.sin((a+48)/2)+math.cos((b+22)/2) for a,b in zip(lon,lat)]
        tri=azl.Triangulation(lon,lat);irregular=axes[2].tricontourf(tri,values,levels=[-2,-1,0,1,2],cmap='ocean')
        axes[2].scatter(lon,lat,s=6,color='#4a555d',edgecolor='none')
        fig.colorbar(irregular,ax=axes[2],orientation='horizontal',label='Synthetic irregular scalar field',shrink=.85)
        decorate(axes[2],'Own regional triangulation')
        fig.suptitle('Azimlib · scientific cartography 2D',fontsize=15)
    return fig

def create_rasters():
    fig,axes=azl.subplots(1,3,figsize=(12,4.6),dpi=120,layout='constrained')
    pixels=[[(.12,.5+.2*j/10,.75,.25+.7*i/10) if not (3<=i<=5 and 3<=j<=5) else (0.,0.,0.,0.) for i in range(11)] for j in range(11)]
    axes[0].imshow(pixels,extent=EXTENT,origin='lower')
    decorate(axes[0],'RGBA / alpha / missing pixels')
    source=azl.GeoRaster([[0,1,2],[1,None,3],[2,3,4]],(4,0,-54,0,-4,-16))
    for ax,policy in zip(axes[1:],('strict','renormalize')):
        output=source.resample((20,20),method='bilinear',missing=policy)
        mapped=ax.raster(output,cmap='viridis',vmin=0,vmax=4)
        fig.colorbar(mapped,ax=ax,orientation='horizontal',label='Synthetic scalar value',shrink=.8)
        decorate(ax,'Bilinear / '+policy+' NoData')
    fig.suptitle('Azimlib · color raster and own resampling',fontsize=14)
    return fig

def create_flows():
    fig,axes=azl.subplots(1,2,figsize=(10,5),dpi=120,layout='constrained')
    rng=random.Random(505);lon=[rng.gauss(-48,1.5) for _ in range(300)];lat=[rng.gauss(-22,1.5) for _ in lon]
    weights=[1+i%4 for i in range(len(lon))]
    density=axes[0].density(lon,lat,weights=weights,extent=EXTENT,bins=(24,24),smoothing=1.2,normalization='density',cmap='magma')
    fig.colorbar(density,ax=axes[0],orientation='horizontal',label='Probability / square degree')
    decorate(axes[0],'Weighted density / conserved mass')
    axes[1].map('brazil',facecolor='#f1f3f4',edgecolor='#7c8790',linewidth=.5)
    axes[1].states(edgecolor='#9ba5ad',linewidth=.25)
    flow=axes[1].flow([(-52,-26),(-52,-26),(-51,-18)],[(-43,-22),(-47,-18),(-44,-26)],[10,60,100],ellipsoid=azl.WGS84,cmap='sunset',arrowsize=7)
    axes[1].quiver([-51,-48,-45],[-21,-24,-20],[1,1,-1],[1,-1,1],scale=15,color='#526870',linewidth=.8)
    axes[1].legend(handles=[flow],title='Synthetic flow magnitude',fontsize=7,loc='lower left')
    axes[1].north_arrow(size=24)
    decorate(axes[1],'Ellipsoidal routes + east/north vectors')
    fig.suptitle('Azimlib · weighted points and geographic flows',fontsize=14)
    return fig

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('gallery/scientific-2d'))
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    for name,factory in (('scientific-atlas',create),('color-raster',create_rasters),('weighted-flows',create_flows)):
        fig=factory()
        for extension in ('png','svg'):fig.savefig(args.output/f'{name}.{extension}')
        (args.output/f'{name}.html').write_text(fig.to_html(),encoding='utf8',newline='\n')
        azl.close(fig)

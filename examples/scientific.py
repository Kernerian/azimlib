"""Editable colors, hatch vocabulary, terrain and a vector-field globe.

All geographic/math composition uses Azimlib. Fields/values are synthetic.
Run python examples/scientific.py [--show] to export gallery artifacts.
"""
from pathlib import Path
import argparse,math
import azimlib.pyplot as plt
from azimlib import datasets
from azimlib.colors import Normalize
from azimlib.fields import hillshade

def colorbar_example(orientation='vertical'):
    fig,ax=plt.subplots(figsize=(7.2,6.2),projection='mercator')
    data=datasets.load('states',country='brazil')
    values=[2.2*i/(len(data['features'])-1) for i in range(len(data['features']))]
    layer=ax.choropleth(data,values,cmap='viridis',bins=None,norm=Normalize(0,2.2),linewidth=.4,edgecolor='white')
    ax.set_title('Colorbar editável',fontsize=14)
    ax.subtitle('Valores sintéticos por estado · sem grade automática',fontsize=9)
    bar=fig.colorbar(layer,ax=ax,label='Intensidade (unidades arbitrárias)',orientation=orientation)
    bar.set_ticks([i*.25 for i in range(9)])
    bar.ax.tick_params(labelsize=9)
    # Edit after creation: layer.set_clim(0, 3), layer.set_cmap('blues'),
    # bar.set_label('Outro indicador'), bar.set_visible(False).
    return fig

def horizontal_example():
    return colorbar_example(orientation='horizontal')

def hatch_catalog():
    fig,axes=plt.subplots(3,5,figsize=(10,6))
    fig.subplots_adjust(left=.035,right=.97,bottom=.035,top=.90,wspace=.25,hspace=.45)
    patterns=('/', '\\', '|', '-', '+', 'x', '.', 'o', 'O', '*', '////', 'xxxx', '....', '/o', '+*')
    for ax,pattern in zip(axes.flat,patterns):
        ax.polygon([(0,0),(10,0),(10,7),(0,7)],holes=[[(4,2),(6,2),(6,4),(4,4)]],
                   facecolor='white',edgecolor='#333333',linewidth=.7,hatch=pattern,hatch_color='#346087')
        ax.set_extent((-1,11,-1,8));ax.set_axis_off();ax.set_title(pattern,fontsize=12)
    fig.suptitle('Dez padrões básicos · repetições e combinações',fontsize=14)
    return fig

def hatches_example():
    fig,axes=plt.subplots(2,3,figsize=(9,6))
    fig.subplots_adjust(left=.04,right=.97,bottom=.04,top=.90,wspace=.2,hspace=.35)
    patterns=('////','\\\\\\\\','xxxx','....','----','||||')
    for ax,pattern in zip(axes.flat,patterns):
        ax.polygon([(0,0),(8,0),(10,5),(7,9),(1,8)],holes=[[(3,3),(5,3),(5,5),(3,5)]],
                   facecolor='#f6f6f6',edgecolor='#333333',linewidth=.8,hatch=pattern,hatch_color='#346087',hatch_linewidth=.6,hatch_spacing=12)
        ax.set_extent((-1,11,-1,10));ax.set_axis_off()
        ax.set_title(pattern,fontsize=12)
    fig.suptitle('Hachuras · repetição aumenta a densidade',fontsize=15)
    return fig

def terrain_example():
    fig,ax=plt.subplots(figsize=(8,6.5),projection='mercator')
    x=[-70+30*i/40 for i in range(41)];y=[-35+40*j/36 for j in range(37)]
    z=[[1200+800*math.sin(i/6)*math.cos(j/8)+1100*math.exp(-((i-14)**2+(j-22)**2)/90) for i in range(41)] for j in range(37)]
    # pcolormesh needs edge arrays; use imshow for an extent-defined field.
    field=ax.imshow(z,extent=(-70,-40,-35,5),origin='lower',cmap='terrain',vmin=0,vmax=3000)
    illumination=hillshade(z,dx=15000,dy=15000,vert_exag=12)
    ax.imshow(illumination,extent=(-70,-40,-35,5),origin='lower',cmap='gray',vmin=0,vmax=1,alpha=.22,zorder=1.1)
    contours=ax.contour(x,y,z,levels=[800,1200,1600,2000,2400],colors='#333333',linewidth=.55,alpha=.65)
    ax.clabel(contours,fontsize=7,halo='white',padding=1)
    ax.coastlines(linewidth=.7,color='black')
    ax.set_title('Campo geográfico, isolinhas e hillshade',fontsize=14)
    ax.subtitle('Terreno sintético · não representa altitudes reais',fontsize=9)
    fig.colorbar(field,ax=ax,label='Elevação sintética (m)',shrink=.9)
    return fig

def globe_example():
    fig,ax=plt.subplots(figsize=(8,8),projection='orthographic',projection_kw={'central_longitude':-60,'central_latitude':10})
    ax.countries(facecolor='#f7f7f7',edgecolor='#777777',linewidth=.4)
    ax.set_extent((-180,180,-89,89));ax.set_axis_off()
    ax.grid(step=30,color='#a0a0a0',linewidth=.4,alpha=.55)
    lon=[];lat=[];u=[];v=[]
    for yy in range(-60,76,15):
        for xx in range(-135,31,15):
            lon.append(xx);lat.append(yy);u.append(math.cos(math.radians(yy))*1.2);v.append(math.sin(math.radians(xx+60))*.7)
    ax.quiver(lon,lat,u,v,scale=25,color='#222222',linewidth=.55)
    for route,color in (([(-46.63,-23.55),(-.12,51.5)],'#d85b40'),([(-74,40.7),(-70.7,-33.4)],'#427cb6'),([(-79.5,-.2),(-3.7,40.4)],'#489a5a')):
        ax.route(route,color=color,linewidth=.9,arrow=False,zorder=3)
    ax.set_title('Globo ortográfico · rotas e campo vetorial',fontsize=14)
    ax.subtitle('Vetores sintéticos · orientação calculada na projeção',fontsize=9)
    return fig

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--show',action='store_true');args=parser.parse_args()
    folder=Path(__file__).resolve().parents[1]/'gallery'
    for name,make in (('colorbar',colorbar_example),('colorbar-horizontal',horizontal_example),('hatches',hatches_example),('hatch-catalog',hatch_catalog),('terrain',terrain_example),('globe',globe_example)):
        fig=make();fig.savefig(folder/f'{name}.svg');fig.savefig(folder/f'{name}.png')
        fig.show(backend='browser',open_browser=False,path=folder/f'{name}.html')
        print(name,flush=True)
    if args.show:plt.show()

"""Original synthetic terrain; no downloaded DEM, building or third-party renderer."""
import math,re
from pathlib import Path
import azimlib as azl
from azimlib.raster import GeoRaster

def make_figure():
    fig=azl.figure(figsize=(9,4.5))
    left=fig.add_subplot(121,projection='3d');right=fig.add_subplot(122,projection='3d')
    n=25;coordinates=[i*50 for i in range(n)]
    Z=[[25+200*math.exp(-((x-450)**2+(y-600)**2)/85000)+95*math.exp(-((x-1000)**2+(y-250)**2)/40000) for x in coordinates] for y in coordinates]
    left.plot_surface(coordinates,coordinates,Z,cmap='terrain');left.set_vertical_exaggeration(1.5)
    left.set_title('Physical terrain · perspective');left.set_xlabel('East (m)');left.set_ylabel('North (m)');left.set_zlabel('Height (m)')
    raster=GeoRaster(tuple(tuple(row) for row in Z),(.0005,.00006,-46.006,0,-.0005,-22.994))
    surface=right.terrain(raster,origin=(-46,-23),elevation_reference='synthetic metres, no vertical datum')
    footprints={'type':'FeatureCollection','features':[]}
    for i,(lon,lat) in enumerate(((-46.003,-23.002),(-45.999,-23.004),(-45.996,-23.002))):
        ring=[(lon,lat),(lon+.0008,lat),(lon+.0008,lat+.0008),(lon,lat+.0008),(lon,lat)]
        footprints['features'].append({'type':'Feature','id':i,'properties':{'base':120,'height':130+i*30},'geometry':{'type':'Polygon','coordinates':[ring]}})
    right.buildings(footprints,height='height',base='base',coordinates='geographic',color='#8897ac')
    right.set_proj_type('ortho');right.view_init(elev=35,azim=-50)
    right.set_title('Local DEM + explicit buildings');right.set_xlabel('East (m)');right.set_ylabel('North (m)');right.set_zlabel('Height (m)')
    fig.colorbar(surface,ax=[right],label='Source elevation (m)',fraction=.04,pad=.06)
    fig.subplots_adjust(left=.06,right=.91,bottom=.16,top=.84,wspace=.3)
    return fig

def main(output=Path('outputs/terrain3d')):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);fig=make_figure()
    for ext in ('png','svg','pdf'):fig.savefig(output/('terrain3d.'+ext))
    def portable_markup(text):
        # Preserve the licensed notice verbatim after XML decoding, while
        # avoiding trailing whitespace and platform-dependent line endings.
        def notice(match):
            body='\n'.join(line.rstrip(' ')+('&#32;'*(len(line)-len(line.rstrip(' ')))) for line in match[2].split('\n'))
            return match[1]+body+match[3]
        return re.sub(r'(<metadata id="azimlib-font-license">)(.*?)(</metadata>)',notice,text,flags=re.S)
    svg=output/'terrain3d.svg';svg.write_text(portable_markup(svg.read_text('utf8')),encoding='utf8',newline='\n')
    (output/'terrain3d.html').write_text(portable_markup(fig.to_html()),encoding='utf8',newline='\n')
    return fig
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('outputs/terrain3d'));p.add_argument('--show',action='store_true');a=p.parse_args();fig=main(a.output)
    if a.show:fig.show()

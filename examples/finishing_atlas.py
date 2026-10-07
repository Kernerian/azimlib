"""Reproducible original cartographic composition; all thematic data synthetic.

Natural Earth context and bundled DejaVu keep their separately credited terms.
SVG icon geometry and custom hatch here are original BSD-3-Clause fixtures.
Run with --output DIRECTORY. No viewer or automatic download is opened.
"""
import argparse
import math
from pathlib import Path
import azimlib as azl

def make_atlas(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    f,axes=azl.subplots(1,2,figsize=(12,6),dpi=120)
    a,b=axes
    f.subplots_adjust(left=.075,right=.96,bottom=.15,top=.83,wspace=.28)
    f.suptitle('Cartographic finishing',fontsize=17)
    f.text(.5,.9,'Original paths, curved names, physical symbols and vector export',ha='center',fontsize=10,color='#5f7180')
    a.set_extent((-74,-34,-35,6));a.map('brazil',facecolor='#edf1f2',edgecolor='#66737c',linewidth=.55)
    a.states(facecolor='none',edgecolor='#a0aab0',linewidth=.3)
    a.set_title('Map and optional components',fontsize=11)
    a.set_xlabel('Longitude',labelpad=6);a.set_ylabel('Latitude',labelpad=6)
    a.grid(step=10,linewidth=.35,color='#ccd4d9',linestyle='--')
    a.plot([-67,-62,-56,-51,-44],[-7,-10,-11,-15,-20],color='#258bb0',linewidth=1.4,linestyle='--',marker='^',markersize=5,label='Synthetic route')
    a.labels({'type':'FeatureCollection','features':[{'type':'Feature','properties':{'name':'Amazonas','priority':10},'geometry':{'type':'Point','coordinates':[-63,-4]}},
                  {'type':'Feature','properties':{'name':'São Paulo','priority':5},'geometry':{'type':'Point','coordinates':[-47,-23]}}]},fontsize=8,leader=True)
    a.legend(loc='lower right',fontsize=8);a.scale_bar(length=1000,fontsize=7);a.north_arrow(size=22)
    b.set_extent((0,16,0,12));b.set_title('Labels, hatches and equations',fontsize=11)
    b.set_xlabel('Longitude',labelpad=6);b.set_ylabel('Latitude',labelpad=6)
    provenance=azl.Provenance('examples/finishing_atlas.py','BSD-3-Clause','Copyright (c) 2026 Kernerian',
                             license_text=(Path(__file__).resolve().parents[1]/'LICENSE').read_text('utf8'))
    pattern=azl.HatchPattern([[(0,.2),(.25,.45),(.5,.2),(.75,.45),(1,.2)]],provenance)
    district={'type':'Feature','properties':{'name':'District'},'geometry':{'type':'Polygon','coordinates':[[[1,6],[8,6],[8,11],[1,11],[1,6]],[[3,7],[4,7],[4,8],[3,8],[3,7]]]}}
    b.geojson(district,facecolor='#e5efe7',edgecolor='#639978',hatch=pattern,hatch_spacing=10,hatch_linewidth=.45)
    b.labels(district,fontsize=11,priority=10)
    river={'type':'Feature','properties':{'name':'Curved River'},'geometry':{'type':'LineString','coordinates':[[i,3+.6*math.sin(i/2)] for i in range(17)]}}
    b.geojson(river,color='#258bb0',linewidth=1.5)
    b.labels(river,placement='curve',repeat=125,fontsize=9,color='#145f80',halo_width=1.5)
    icon_file=output/'original-station.svg'
    icon_file.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><path d="M 0 5 L 5 0 L 10 5 L 5 10 Z"/></svg>',encoding='utf8')
    icon=azl.read_svg_symbol(icon_file,provenance=provenance)
    b.scatter([11,13],[8,9],marker=icon,s=90,color='#9360a8',label='Original station symbol')
    b.text(10,6,r'$\sigma^2 = \frac{x_0^2}{2}$',fontsize=14,ha='center',halo='white')
    b.text(10,4.5,r'$d=\sqrt{x^2+y^2}$',fontsize=12,ha='center',halo='white')
    b.legend(loc='lower right',fontsize=8)
    for extension in ('png','svg','pdf'):f.savefig(output/f'finishing-atlas.{extension}')
    (output/'finishing-atlas.html').write_text(f.to_html(),encoding='utf8')
    azl.close(f)
    return output/'finishing-atlas.png'

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    make_atlas(p.parse_args().output)

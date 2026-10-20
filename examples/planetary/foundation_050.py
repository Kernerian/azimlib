"""Four Phase A demonstrations; all non-Earth geography is synthetic/angular.

Run: python examples/planetary/foundation_050.py --output OUTPUT_DIRECTORY
Only Azimlib is used for plotting. PNG additionally requires the existing
optional Pillow backend; SVG does not require an external plotting library.
"""
import argparse
from pathlib import Path
import azimlib as azl


def terrestrial():
    fig,ax=azl.subplots(figsize=(8,5),dpi=120)
    ax.map('brazil');ax.states(linewidth=.35)
    ax.plot([-60,-50,-42],[-8,-18,-12],color='#c35445',marker='o',label='Synthetic route')
    ax.set_title('Earth · preserved cartographic defaults')
    ax.subtitle('Bundled Natural Earth base · illustrative route')
    ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
    ax.scale_bar();ax.north_arrow();ax.legend(loc='lower right')
    assert ax.get_body() is azl.EARTH
    return fig


def mars():
    fig,ax=azl.subplots(body=azl.MARS,projection='angular',figsize=(8,5),dpi=120)
    ax.set_extent((-30,80,-30,45));ax.set_facecolor('#fbf5ed')
    area=ax.polygon([(-15,-15),(30,-20),(65,15),(20,30)],facecolor='#d9ac82',edgecolor='#966d51',label='Synthetic region')
    line,=ax.plot([-10,20,55],[-5,18,6],color='#874f45',marker='o',label='Angular path')
    group=ax.group(name='Illustration',style={'alpha':.8});group.add(area);group.add(line)
    ax.text(18,28,'Synthetic coordinates',ha='center',halo='white',halo_width=1)
    ax.set_title('Mars · explicit Body context')
    ax.subtitle('Nonmetric planetocentric angular chart · no physical terrain/projection claim')
    ax.set_xlabel('East longitude (degrees)');ax.set_ylabel('Planetocentric latitude')
    ax.grid(True,step=20,labels=True);ax.legend(loc='lower right')
    assert line.get_body() is azl.MARS
    return fig


def comparison():
    fig=azl.figure(figsize=(10,5),dpi=120)
    earth=fig.add_subplot(121);planet=fig.add_subplot(122,body=azl.MARS,projection='angular')
    earth.map('brazil');earth.states(linewidth=.3);earth.set_title('Earth · existing map')
    planet.set_extent((-30,80,-30,45));planet.set_facecolor('#fbf5ed')
    planet.polygon([(-15,-15),(30,-20),(65,15),(20,30)],facecolor='#d9ac82',edgecolor='#966d51')
    planet.plot([-10,20,55],[-5,18,6],color='#874f45',marker='o')
    planet.set_title('Mars · synthetic angular chart')
    for ax in (earth,planet):ax.set_xlabel('East longitude');ax.set_ylabel('Latitude')
    fig.suptitle('One Figure · independent Earth and Mars contexts',fontsize=14)
    fig.text(.5,.015,'Visual layout only: panel sizes do not compare physical body dimensions.',ha='center',fontsize=9)
    assert earth.get_body()!=planet.get_body()
    return fig


def groups():
    fig,axes=azl.subplots(1,3,figsize=(12,4),dpi=120)
    source=azl.read_geojson({'type':'FeatureCollection','features':[
        {'type':'Feature','geometry':{'type':'Polygon','coordinates':[[[-1,-1],[1,-1],[1,1],[-1,1],[-1,-1]]]},'properties':{}}]})
    first=axes[0];root=first.group(name='Shared definition',style={'alpha':.75})
    nested=first.group(name='Area',parent=root)
    leaf=azl.Layer('geometry',source,{'facecolor':'#448f94','edgecolor':'#244f54'})
    first.add_collection(leaf);nested.add(leaf)
    fresh=root.instantiate(axes[1]);fresh.get_children()[0].get_children()[0].set_facecolor('#d5a44c')
    hidden=root.instantiate(axes[2]);hidden.set_visible(False)
    for ax,title in zip(axes,('Original · visible','Independent style','Group hidden')):
        ax.set_extent((-2,2,-2,2));ax.set_title(title);ax.grid(True,step=1)
    fig.suptitle('Layer groups · shared immutable data, separate visual state',fontsize=13)
    fig.text(.5,.02,'Synthetic geometry · no historical or scientific interpretation',ha='center',fontsize=9)
    assert leaf.get_facecolor()=='#448f94' and leaf.get_visible()
    return fig


def main(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    for name,build in (('earth',terrestrial),('mars-context',mars),('comparison',comparison),('groups',groups)):
        fig=build()
        try:
            fig.savefig(output/(name+'.svg'))
            fig.savefig(output/(name+'.png'))
            fig.savefig(output/(name+'.pdf'))
        finally:azl.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    main(parser.parse_args().output)

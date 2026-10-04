"""Build-independent offline core smoke in a new environment from dist/*.whl.

No source directory is added to sys.path; the child environment has no optional
dependencies. Tests the package that users install, not the working checkout.
"""
import argparse
import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

CHECK=r'''
import importlib.util,io,sys
from pathlib import Path
import azimlib as azl
from azimlib.backend_bases import MouseButton
from azimlib.renderers import render_image
from azimlib.scene import Scene
try:render_image(Scene(2,2))
except ImportError:pass
else:raise AssertionError('Raster requires optional Pillow; core import must not load it')
assert MouseButton.LEFT==1 and MouseButton.RIGHT==3
with azl.rc_context({'keymap.pan':['ctrl+p']}):assert azl.rcParams['keymap.pan']==['ctrl+p']
assert azl.rcParams['keymap.pan']==['p']
assert Path(azl.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
for name in ('PIL','matplotlib','cartopy','geopandas','shapely','pyproj'):
    assert importlib.util.find_spec(name) is None,name
fig,ax=azl.subplots(figsize=(4,3))
constant=ax.contour([-54,-44],[-26,-18],[[5,5],[5,5]])
assert constant.levels==(5.,) and constant.allsegs==[[]] and constant.clabel()==[]
bar=fig.colorbar(constant,orientation='horizontal',label='Constant field')
assert 'Constant field' in fig.to_svg()
bar.remove();constant.remove()
ax.map('brazil');ax.states();ax.set_title('Installed package')
line,=ax.plot([-52,-46],[-25,-20],label='Route')
ax.legend();ax.scale_bar();ax.north_arrow();ax.compass();ax.overview()
text=ax.text(-50,-22,'City');text.set(position=(-49,-21),ha='right')
note=ax.annotate('Note',xy=(-48,-22),xytext=(10,8),textcoords='offset points')
note.xy=(-47,-21)
points=ax.scatter(lon=[-52,-46],lat=[-25,-20],c=[0,1])
bar=fig.colorbar(points,orientation='horizontal');bar.set_label('Value')
points.set_clim(-1,2)
fig.supxlabel('Longitude');fig.supylabel('Latitude')
scene=fig.canvas.draw();assert not fig.stale
assert scene.maps and '<svg' in fig.to_svg() and 'Figure navigation' in fig.to_html()
stream=io.StringIO();fig.savefig(stream,format='svg');assert not stream.closed
assert '<script' not in stream.getvalue() and 'Installed package' in stream.getvalue()
azl.close(fig)
from azimlib.colors import Normalize
fig,ax=azl.subplots();ax.set_extent((-54,-42,-28,-16))
image=ax.imshow([[1,2],[3,4]],extent=(-47,-43,-25,-20))
assert ax.get_extent()==(-54,-42,-28,-16)
line,=ax.plot([-52,-48],[-25,-21],lw=.7)
frame=ax.legend([line],['Route']).get_frame();frame.set(fc='white',ec='red',lw=.4)
assert azl.getp(line,'lw')==.7 and azl.getp(frame,'lw')==.4
ax.spines['left'].set(lw=.4,ec='red')
assert '<svg' in fig.to_svg()
azl.close(fig)
fig,ax=azl.subplots()
first=azl.cm.ScalarMappable(Normalize(0,100));second=azl.cm.ScalarMappable(Normalize(0,200))
oldbar=ax.colorbar(first);current=ax.colorbar(second,orientation='horizontal')
assert oldbar.get_figure() is None
oldticks=ax.set_xticks([-50],['Old']);ax.set_xticks([-45],['Current'])
fig.canvas.draw();first.set_clim(0,300);oldticks[0].set_text('Discarded')
assert oldticks[0].get_figure() is None and not fig.stale
ax.clear();fig.canvas.draw();second.set_clim(0,300)
assert current.get_figure() is None and not fig.stale
azl.close(fig)
fig,ax=azl.subplots()
fig.set_size_inches(5,4,forward=False);fig.set_dpi(150)
assert fig.get_size_inches()==(5.,4.) and fig.get_dpi()==150
for loc in ('left','center','right'):ax.set_title(loc,loc=loc,pad=8)
assert all(ax.get_title(loc)==loc for loc in ('left','center','right'))
assert fig.canvas.get_width_height()==(750,600)
assert '<svg' in fig.to_svg() and ax._grid_config is None
azl.close(fig)
with azl.style.context(['dark_background',{'axes.prop_cycle':azl.cycler(color=['red','blue'])}]):
    fig,ax=azl.subplots()
    lines=ax.plot([-52,-48],[[-25,-24],[-22,-21]],label=['A','B'])
    legend=ax.legend()
assert len(lines)==2 and [line.get_color() for line in lines]==['red','blue']
assert legend.get_frame().get_facecolor()=='black' and legend.get_texts()[0].get_color()=='white'
assert 'A' in fig.to_svg()
azl.close(fig)
from azimlib.ticker import EngFormatter
fig,ax=azl.subplots();ax.set_extent((-54,-42,-28,-16))
ax.set_xlabel('Longitude',labelpad=8);ax.set_ylabel('Latitude',labelpad=8)
points=ax.scatter([-52,-48],[-24,-20],c=[0,2e6],marker='d')
bar=fig.colorbar(points,ax=ax,orientation='horizontal')
assert '1e6' in fig.to_svg()
offset=bar.ax.xaxis.get_offset_text();assert offset.get_figure() is fig
bar.ax.ticklabel_format(style='plain',useOffset=False);fig.to_svg();assert offset.get_text()==''
assert EngFormatter(unit='m')(1500)=='1.5 km'
assert not any(name.split('.')[0] in ('matplotlib','cartopy','geopandas','shapely','pyproj','fontTools') for name in sys.modules)
azl.close(fig)
fig,ax=azl.subplots();ax.set_extent((-54,-42,-28,-16))
line,=ax.plot([-52,-48],[-25,-21],linewidth='1.2',linestyle=(v for v in (4,2)),label='Route')
legend=ax.legend();frame=legend.get_frame();scale=ax.scale_bar(length=100,fontsize='9')
title=ax.set_title('Valid',fontsize='12');fig.canvas.draw();before=fig.to_svg()
for attempt in (lambda:title.set(text='Invalid',fontstyle='sideways'),
                lambda:frame.set(facecolor='red',linewidth=-1),
                lambda:ax.spines['left'].set(color='red',linewidth=-1),
                lambda:scale.set(length=50,fontsize=0)):
    try:attempt()
    except ValueError:pass
    else:raise AssertionError('invalid edit accepted')
assert not fig.stale and fig.to_svg()==before and line.get_linestyle()==(4.,2.)
azl.close(fig)
fig,ax=azl.subplots()
layer=ax.state('SP',fc='white',ec='black',lw=.3)
title=ax.set_title('Aliases',size=12,c='red');fig.canvas.draw();before=fig.to_svg()
try:ax.set_title('Ambiguous',fontsize=12,size=12)
except TypeError:pass
else:raise AssertionError('ambiguous aliases accepted')
assert title.get_text()=='Aliases' and not fig.stale and before==fig.to_svg()
assert layer.style['linewidth']==.3
from azimlib.components import MapComponent
assert not MapComponent(visible=False).get_visible()
azl.close(fig)
print('Installed wheel: SVG/HTML, data/fonts, artists, styles/aliases, scientific text and prevalidated edits; no optional/GIS/reference libraries.')
'''


def run(wheel):
    with tempfile.TemporaryDirectory(prefix='azimlib-installed-') as folder:
        target=Path(folder)/'environment'
        venv.EnvBuilder(with_pip=True).create(target)
        python=target/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
        environment=os.environ.copy();environment.pop('PYTHONPATH',None)
        environment.pop('PYTHONHOME',None)
        subprocess.run([str(python),'-m','pip','install','--no-index','--no-deps',str(wheel.resolve())],
                       check=True,env=environment,cwd=folder)
        subprocess.run([str(python),'-I','-c',CHECK],check=True,env=environment,cwd=folder)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheel',type=Path)
    args=parser.parse_args()
    if args.wheel:wheel=args.wheel
    else:
        wheels=list((Path(__file__).resolve().parents[1]/'dist').glob('azimlib-*.whl'))
        if len(wheels)!=1:parser.error('Provide --wheel when dist does not contain exactly one Azimlib wheel.')
        wheel=wheels[0]
    run(wheel)

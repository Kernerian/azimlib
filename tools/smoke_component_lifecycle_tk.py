"""Own component lifecycle in real withdrawn Tk, with programmatic edits."""
import argparse,json,platform,sys,tkinter
from pathlib import Path
from unittest.mock import patch
import azimlib as azl
from azimlib.colors import Normalize
from azimlib.scene import Text


def run():
    azl.ioff();checks=[];original=tkinter.Tk
    def hidden_root(*args,**kwargs):
        root=original(*args,**kwargs);root.withdraw();return root
    fig,ax=azl.subplots(figsize=(6,4.5),layout='tight')
    ax.set_extent((-55,-42,-28,-16))
    ax.plot([-52,-48,-44],[-25,-22,-20],label='Route')
    legend=ax.legend(title='Layers');scale=ax.scale_bar(length=100)
    first=azl.cm.ScalarMappable(Normalize(0,100));bar=ax.colorbar(first,orientation='horizontal')
    bar.set_label('Initial intensity');bar.set_ticks([0,100],labels=['Low','High'])
    drawings=[];fig.canvas.mpl_connect('draw_event',drawings.append)
    viewer=None
    try:
        with patch.object(tkinter,'Tk',hidden_root):viewer=fig.show(block=False)
        viewer.draw()  # Observe an explicit draw after callback transfer.
        viewer.flush_events()
        assert not fig.stale and drawings,(fig.stale,len(drawings),viewer._pending,viewer._resize_pending)
        checks.append('real Tk window, optional components and explicit draw after callback transfer')
        text=legend.get_texts()[0];before=len(drawings)
        with azl.ion():
            text.set_visible(False);legend.get_title().set_visible(False)
            bar.label_artist.set_visible(False)
        viewer.flush_events();assert len(drawings)==before+1
        texts=[i.text for i in viewer.scene.items if isinstance(i,Text)]
        assert all(label not in texts for label in ('Route','Layers','Initial intensity'))
        checks.append('one redraw hides legend entry/title and colorbar label')
        oldbar,oldscale=bar,scale;before=len(drawings)
        second=azl.cm.ScalarMappable(Normalize(0,200))
        with azl.ion():
            bar=ax.colorbar(second,orientation='horizontal');bar.set_label('Current intensity')
            scale=ax.scale_bar(length=200)
        viewer.flush_events();assert len(drawings)==before+1
        assert oldbar.get_figure() is None and oldscale.get_figure() is None
        assert 'Current intensity' in [i.text for i in viewer.scene.items if isinstance(i,Text)]
        checks.append('one redraw replaces local colorbar/scale after registration')
        before=len(drawings)
        with azl.ion():
            first.set_clim(0,300);oldscale.set_visible(True);oldbar.set_label('Discarded')
        viewer.flush_events();assert len(drawings)==before and not fig.stale
        checks.append('discarded mapping/components do not schedule a redraw')
        bar.set_ticks([0,200],labels=['A','B']);viewer.draw()
        oldticks=list(bar._ticklabels);before=len(drawings)
        with azl.ion():second.set_norm(Normalize(0,10))
        viewer.flush_events();assert len(drawings)==before+1
        before=len(drawings)
        with azl.ion():
            for tick in oldticks:
                assert tick.get_figure() is None
                tick.set_text('Discarded tick')
        viewer.flush_events();assert len(drawings)==before and not fig.stale
        checks.append('norm replacement updates current bar and detaches previous ticks')
        before=len(drawings)
        with azl.ion():ax.clear()
        viewer.flush_events();assert len(drawings)==before+1
        before=len(drawings)
        with azl.ion():second.set_clim(0,50)
        viewer.flush_events();assert len(drawings)==before and not fig.stale
        assert not ax.layers and ax._colorbar is None
        checks.append('clear removes local bar and disconnects its mapping')
        viewer.close();assert viewer.closed and viewer._image is None
        checks.append('close releases current owned raster')
        assert not any(name.split('.')[0] in ('matplotlib','geopandas','cartopy','shapely','pyproj') for name in sys.modules)
        return dict(python=platform.python_version(),platform=platform.platform(),tk=tkinter.TkVersion,
                    checks=checks,scope='real withdrawn Tk; programmatic edits; no physical input or visible OS comparison')
    finally:
        azl.close(fig);azl.ioff()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path)
    args=parser.parse_args();report=run()
    if args.output:args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2,ensure_ascii=False))

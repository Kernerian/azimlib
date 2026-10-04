"""Record component lifecycle contracts directly, without a runtime dependency."""
import argparse,json,platform
from pathlib import Path

COMMON=('child_remove','legend_visibility','colorbar_label_visibility',
        'clim_preserves_locator','norm_resets_locator')


def contracts(module):
    own=module.__name__=='azimlib'
    if own:
        from azimlib.cm import ScalarMappable
        from azimlib.colors import Normalize
        from azimlib.ticker import MultipleLocator
    else:
        from matplotlib.cm import ScalarMappable
        from matplotlib.colors import Normalize
        from matplotlib.ticker import MultipleLocator
    result={}
    f,a=module.subplots()
    try:
        a.plot([-52,-48],[-25,-22],label='Route')
        legend=a.legend(title='Routes');text=legend.get_texts()[0]
        f.canvas.draw()
        try:text.remove();error=None
        except Exception as exc:error=type(exc).__name__
        result['child_remove']=[error,text.get_visible(),f.stale]
        text.set_visible(False);legend.get_title().set_visible(False);legend.get_frame().set_visible(False)
        result['legend_visibility']=[text.get_visible(),legend.get_title().get_visible(),legend.get_frame().get_visible(),legend.get_visible()]
        old=a.legend();new=a.legend(title='Replacement');old.remove()
        result['old_legend_remove_preserves_current']=a.get_legend() is new
        oldtick=a.set_xticks([-50],['Old'])[0];a.set_xticks([-50],['New'])
        result['replaced_tick_keeps_figure']=oldtick.get_figure() is f
        mapping=ScalarMappable(Normalize(0,100));bar=f.colorbar(mapping,ax=a)
        bar.set_label('Intensity')
        label=bar.label_artist if own else bar.ax.yaxis.label
        label.set_visible(False);result['colorbar_label_visibility']=label.get_visible()
        locator=MultipleLocator(25);bar.locator=locator
        mapping.set_clim(0,200);f.canvas.draw()
        result['clim_preserves_locator']=[bar.locator is locator,float(bar.vmin),float(bar.vmax)]
        mapping.set_norm(Normalize(0,10));f.canvas.draw()
        result['norm_resets_locator']=[bar.locator is locator,float(bar.vmin),float(bar.vmax)]
        bar.remove();f.canvas.draw();mapping.set_clim(0,20)
        result['removed_bar_stale']=f.stale
        bar=f.colorbar(mapping,ax=a);a.clear()
        result['clear_keeps_colorbar']=(a._colorbar is bar) if own else bar.ax in f.axes
    finally:module.close(f)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'docs/component-lifecycle-reference.json')
    args=parser.parse_args()
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as mpl
    import azimlib as azl
    report=dict(matplotlib_version=matplotlib.__version__,python=platform.python_version(),platform=platform.platform(),
                common=list(COMMON),matplotlib=contracts(mpl),azimlib=contracts(azl),
                notes=['Direct local Agg reference; Matplotlib is imported only by this development command.',
                       'Azimlib local colorbar occupies its Axes component slot; Matplotlib colorbar has a separate Axes.',
                       'Discarded tick texts detach in Azimlib; Matplotlib reuses/retains tick handles.',
                       'The measured Matplotlib figure became stale after editing the standalone mappable of a removed bar; Azimlib stayed clean.',
                       'Removing a superseded legend does not clear the current legend in Azimlib.'])
    assert all(report['matplotlib'][key]==report['azimlib'][key] for key in COMMON)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2,ensure_ascii=False))


if __name__=='__main__':main()

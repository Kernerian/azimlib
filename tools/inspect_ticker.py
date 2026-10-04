"""Compare own numeric ticker contracts with isolated Matplotlib, not a backend."""
from pathlib import Path
import json,math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as mpl
from matplotlib import ticker as mt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from azimlib import ticker as at

def compare():
    records=[]
    cases=(('MultipleLocator',dict(base=5),-10,10),('MultipleLocator',dict(base=5,offset=2),3,13),
           ('MultipleLocator',dict(base=.1),-.3,.3),('MaxNLocator',dict(nbins=4),0,100),
           ('MaxNLocator',dict(nbins=4,prune='both'),0,100),('MaxNLocator',dict(nbins=4),-60,-40),
           ('MaxNLocator',dict(nbins=10,integer=True),0,3),('LogLocator',dict(base=10),1,1000))
    for name,kwargs,low,high in cases:
        expected=[float(v) for v in getattr(mt,name)(**kwargs).tick_values(low,high)]
        actual=list(getattr(at,name)(**kwargs).tick_values(low,high))
        assert len(expected)==len(actual),(name,kwargs,expected,actual)
        error=max((abs(a-b) for a,b in zip(expected,actual)),default=0)
        assert error<1e-9,(name,kwargs,expected,actual)
        records.append(dict(locator=name,parameters=kwargs,limits=[low,high],matplotlib=expected,azimlib=actual,max_error=error))
    formats=[]
    for name,argument in (('StrMethodFormatter','{x:.1f} [{pos}]'),('FormatStrFormatter','%.2f'),('FuncFormatter',lambda x,pos:f'{pos}: {x:g}')):
        expected=getattr(mt,name)(argument)(2.25,3);actual=getattr(at,name)(argument)(2.25,3)
        assert expected==actual
        formats.append(dict(formatter=name,matplotlib=expected,azimlib=actual))
    fig,ax=mpl.subplots();mapped=ScalarMappable(norm=Normalize(0,100));bar=fig.colorbar(mapped,ax=ax)
    locator=mt.MultipleLocator(25);formatter=mt.StrMethodFormatter('{x:.0f}%')
    bar.locator=locator;bar.formatter=formatter;bar.update_ticks()
    mapped.set_clim(0,200);preserved=bar.locator is locator and bar.formatter is formatter
    mapped.set_norm(Normalize(0,1));reset=bar.locator is not locator and bar.formatter is not formatter
    assert preserved and reset;mpl.close(fig)
    return dict(matplotlib_version=matplotlib.__version__,locators=records,formatters=formats,
                colorbar=dict(clim_preserves_objects=preserved,new_norm_resets_objects=reset))

if __name__=='__main__':
    target=Path(__file__).resolve().parents[1]/'docs/ticker-reference.json'
    target.write_text(json.dumps(compare(),indent=2),encoding='utf-8');print(target)

"""Numerical reference only: Matplotlib never renders for Azimlib runtime."""
import json,math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as mpl
from matplotlib import ticker as mt
from matplotlib.cm import ScalarMappable as MM
from matplotlib.colors import Normalize as MN,LogNorm as ML
import azimlib as azl
from azimlib import ticker as at
from azimlib.cm import ScalarMappable as AM
from azimlib.colors import Normalize as AN,LogNorm as AL


def compare():
    records=[]
    for step,n,limits in ((5,None,(-10,10)),(2,None,(-3,9)),(2.5,'auto',(-4,7)),
                          (.1,2,(-.23,.31)),(5,4,(-7.2,8.1)),(1,'auto',(-.04,1.96))):
        mf,ma=mpl.subplots();af,aa=azl.subplots()
        for axes,t in ((ma,mt),(aa,at)):
            axes.set_xlim(*limits);axes.xaxis.set_major_locator(t.MultipleLocator(step))
            axes.xaxis.set_minor_locator(t.AutoMinorLocator(n))
        expected=[float(v) for v in ma.get_xticks(minor=True)];actual=list(aa.get_xticks(minor=True))
        assert len(expected)==len(actual),(step,n,expected,actual)
        error=max((abs(a-b) for a,b in zip(actual,expected)),default=0)
        assert error<1e-9,(step,n,expected,actual)
        records.append(dict(step=step,n=n,limits=limits,matplotlib=expected,azimlib=actual,max_error=error))
        mpl.close(mf);azl.close(af)
    bars=[]
    for orientation in ('vertical','horizontal'):
        for logarithmic in (False,True):
            mf,ma=mpl.subplots();af,aa=azl.subplots()
            mb=mf.colorbar(MM((ML if logarithmic else MN)(1,1000) if logarithmic else MN(0,100)),ax=ma,orientation=orientation)
            ab=af.colorbar(AM(AL(1,1000) if logarithmic else AN(0,100)),ax=aa,orientation=orientation)
            if not logarithmic:
                mb.locator=mt.MultipleLocator(25);ab.locator=at.MultipleLocator(25)
            mb.minorticks_on();ab.minorticks_on()
            expected=[float(v) for v in mb.get_ticks(minor=True)];actual=list(ab.get_ticks(minor=True))
            assert len(expected)==len(actual),(orientation,logarithmic,expected,actual)
            assert all(math.isclose(a,b,abs_tol=1e-9) for a,b in zip(expected,actual))
            mb.minorticks_off();ab.minorticks_off();assert len(mb.get_ticks(minor=True))==len(ab.get_ticks(minor=True))==0
            bars.append(dict(orientation=orientation,logarithmic=logarithmic,matplotlib=expected,azimlib=actual,off_empty=True))
            mpl.close(mf);azl.close(af)
    return dict(matplotlib_version=matplotlib.__version__,axis=records,colorbars=bars)


if __name__=='__main__':
    target=Path(__file__).resolve().parents[1]/'docs/minor-ticker-reference.json'
    target.write_text(json.dumps(compare(),indent=2),encoding='utf-8');print(target)

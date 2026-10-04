"""Development reference: numeric labels and marker bounds from real Matplotlib."""
import json,platform
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CASES=[
    ('integers',[0,2,4,6,8],{}),('decimals',[-.5,-.25,0,.25,.5],{}),
    ('million',[0,500000,1000000,1500000,2000000],{}),
    ('tiny',[0,2e-6,4e-6,6e-6,8e-6],{}),
    ('positive_offset',[100000,100002,100004,100006,100008],{}),
    ('negative_offset',[-100008,-100006,-100004,-100002,-100000],{}),
    ('geographic_offset',[-46.000008,-46.000006,-46.000004,-46.000002,-46.0],{}),
    ('straddle',[99999,99999.5,100000,100000.5,100001],{}),
    ('no_offset',[100000,100002,100004,100006,100008],{'useOffset':False}),
    ('forced_offset',[-46.5,-46.25,-46,-45.75,-45.5],{'useOffset':-46}),
    ('force_power',[0,2000,4000,6000,8000],{'powerlimits':(3,3)}),
    ('plain',[0,500000,1000000,1500000,2000000],{'scientific':False}),
    ('zero',[0,0],{}),('small_plain',[0,.0002,.0004,.0006,.0008],{}),
]

class Interval:
    def __init__(self,values):self.values=values
    def get_view_interval(self):return min(self.values),max(self.values)
    def _changed(self):pass

def contracts(ticker):
    result={}
    for name,values,options in CASES:
        options=dict(options);power=options.pop('powerlimits',None);scientific=options.pop('scientific',None)
        fmt=ticker.ScalarFormatter(**options);fmt.set_axis(Interval(values))
        if power is not None:fmt.set_powerlimits(power)
        if scientific is not None:fmt.set_scientific(scientific)
        labels=fmt.format_ticks(values)
        result[name]=dict(labels=labels,offset=fmt.get_offset())
    result['engineering']={}
    for places in (None,0,2):
        fmt=ticker.EngFormatter(unit='m',places=places)
        result['engineering'][str(places)]=[fmt(v) for v in (-2e9,0,2e-6,.001,999.999,1000,2e6)]
    return result

def marker_bounds(ticker=None):
    from matplotlib.markers import MarkerStyle
    return {name:list(map(float,MarkerStyle(name).get_path().transformed(MarkerStyle(name).get_transform()).get_extents().bounds))
            for name in ('o','s','^','v','D','d','*','p','h','+','x')}

def text_contracts():
    import matplotlib.pyplot as plt
    fig=plt.figure(figsize=(4,4));renderer=fig.canvas.get_renderer();rows=[]
    try:
        for size in (10,12):
            for weight in ('normal','bold'):
                for text in ('Latitude','Água e gp','Título\nFoco geográfico'):
                    for rotation in (0,90):
                        for va in ('top','center','bottom','baseline'):
                            artist=fig.text(.5,.5,text,fontsize=size,fontweight=weight,ha='center',va=va,rotation=rotation,rotation_mode='anchor')
                            bounds=artist.get_window_extent(renderer)
                            rows.append(dict(text=text,fontsize=size,fontweight=weight,rotation=rotation,va=va,
                                             bounds=[float(bounds.x0-200),float(200-bounds.y1),float(bounds.width),float(bounds.height)]))
                            artist.remove()
    finally:plt.close(fig)
    return rows

def main():
    import matplotlib,matplotlib.ticker as mpl
    from azimlib import ticker as own
    report=dict(matplotlib_version=matplotlib.__version__,python=platform.python_version(),
                matplotlib=contracts(mpl),azimlib=contracts(own),marker_bounds=marker_bounds(),text_layout=text_contracts())
    (ROOT/'docs/numeric-formatting-reference.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    differences=[key for key in report['matplotlib'] if report['matplotlib'][key]!=report['azimlib'][key]]
    print('Numeric contract differences:',differences)
    if differences:raise AssertionError(differences)

if __name__=='__main__':main()

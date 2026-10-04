"""Selected series/cycle/style contracts from the installed Matplotlib."""
import argparse,json,platform
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def canonical_color(value):
    if isinstance(value,(tuple,list)):return '#'+''.join(f'{round(v*255):02x}' for v in value[:3])
    return {'red':'#ff0000','blue':'#0000ff','black':'#000000','white':'#ffffff'}.get(value,value)


def contracts(module,make_cycle):
    fig,ax=module.subplots();result={}
    x=[-52,-49,-45];a=[-25,-23,-20];b=[-24,-22,-19]
    def state(lines):
        return [dict(x=list(map(float,line.get_xdata())),y=list(map(float,line.get_ydata())),
                     color=line.get_color(),marker=line.get_marker(),linestyle=line.get_linestyle(),
                     linewidth=float(line.get_linewidth()),label=line.get_label()) for line in lines]
    try:
        result['multi']=state(ax.plot(x,a,'--',x,b,':',label='route'))
        result['columns']=state(ax.plot(x,list(zip(a,b)),label=['A','B']))
        result['broadcast_x']=state(ax.plot(list(zip(x,[-51,-48,-44])),a,label=['X1','X2']))
        result['matrix_pair']=state(ax.plot(list(zip(x,[-51,-48,-44])),list(zip(a,b)),label=['P1','P2']))
        result['data']=state(ax.plot('lon','lat',data={'lon':x,'lat':a}))
        result['implicit']=state(ax.plot([3,5,7],label='index'))
        ax.clear();ax.set_prop_cycle(color=['red','blue'],marker=['o','s'],linestyle=['--',':'])
        result['cycle']=state(ax.plot(x,a,label='first')+ax.plot(x,b,color='black',marker='^',linestyle='-',label='explicit')+
                              ax.plot(x,a,color='black',label='partial')+ax.plot(x,b,label='wrap'))
        ax.set_prop_cycle(make_cycle(color=['red','blue'])+make_cycle(linewidth=[.8,1.2]))
        result['added']=state(ax.plot(x,a,label='C1')+ax.plot(x,b,label='C2'))
        ax.set_prop_cycle(color=['red','blue'],marker=['o','s'],linestyle=['--',':'])
        result['formats_cycle']=state(ax.plot(x,a,'--',label='dash')+ax.plot(x,b,'r',label='color')+
                                      ax.plot(x,a,'',label='empty format')+ax.plot(x,b,label='no format'))
        ax.set_prop_cycle(make_cycle(color=['red','blue'])*make_cycle(linestyle=['--',':']))
        result['product']=state(ax.plot(x,a,x,b,x,a,x,b,label='cartesian'))
        ax.set_prop_cycle(color=['red','blue'])
        line1=ax.plot(x,a,label='L1');ax.scatter(x,a,color='black')
        points1=ax.scatter(x,a);line2=ax.plot(x,b,label='L2');points2=ax.scatter(x,b)
        if module.__name__.startswith('azimlib'):point_colors=[points1.get_color(),points2.get_color()]
        else:
            from matplotlib.colors import to_hex
            point_colors=[to_hex(p.get_facecolors()[0],keep_alpha=False) for p in (points1,points2)]
        result['separate_cycles']=dict(lines=state(line1+line2),points=point_colors)
        # Canonicalize color spelling only; the original libraries retain spellings.
        def colors(node):
            if isinstance(node,dict):return {k:canonical_color(v) if k=='color' else colors(v) for k,v in node.items()}
            if isinstance(node,list):return [canonical_color(v) if isinstance(v,str) else colors(v) for v in node]
            return node
        return colors(result)
    finally:module.close(fig)


def style_contracts(module,make_cycle):
    result={};before=float(module.rcParams['lines.linewidth'])
    with module.style.context(['dark_background',{'lines.linewidth':.9,'axes.prop_cycle':make_cycle(color=['red','blue'])}]):
        fig,ax=module.subplots(figsize=(5,4));line,=ax.plot([-52,-48],[-25,-22],label='route')
        legend=ax.legend(title='Routes')
        result['inside']=dict(width=float(line.get_linewidth()),size=list(map(float,fig.get_size_inches())),
                              face=canonical_color(ax.get_facecolor()),frame=canonical_color(legend.get_frame().get_facecolor()),
                              alpha=float(legend.get_frame().get_alpha()))
        with module.style.context({'figure.dpi':150},after_reset=True):
            result['reset']=dict(dpi=float(module.rcParams['figure.dpi']),width=float(module.rcParams['lines.linewidth']),
                                 face=canonical_color(module.rcParams['axes.facecolor']))
    try:
        result['after']=dict(text=canonical_color(legend.get_texts()[0].get_color()),
                             title=canonical_color(legend.get_title().get_color()),
                             width_restored=float(module.rcParams['lines.linewidth'])==before)
    finally:module.close(fig)
    with module.style.context(ROOT/'examples/styles/routes.mplstyle'):
        fig,ax=module.subplots();lines=ax.plot([-52,-48],[-25,-22],[-52,-48],[-24,-21],label='file')
        try:result['file']=[dict(color=canonical_color(line.get_color()),marker=line.get_marker(),linestyle=line.get_linestyle(),linewidth=float(line.get_linewidth())) for line in lines]
        finally:module.close(fig)
    return result


def failed_group(module):
    fig,ax=module.subplots();ax.set_prop_cycle(color=['red','blue'])
    try:
        try:ax.plot([-52,-49],[-25,-23],[-51,-48],[1])
        except ValueError:error='ValueError'
        else:error=None
        attached=len(ax.layers) if module.__name__.startswith('azimlib') else len(ax.lines)
        line,=ax.plot([-52,-49],[-25,-23])
        return dict(error=error,attached=attached,next_color=canonical_color(line.get_color()))
    finally:module.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=ROOT/'docs/series-styles-reference.json')
    args=parser.parse_args()
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as mpl
    from cycler import cycler as native_cycle
    import azimlib as azl
    own=contracts(azl,azl.cycler)
    from azimlib.cycles import AZIM10
    with mpl.rc_context({'axes.prop_cycle':native_cycle(color=AZIM10)}):
        reference=contracts(mpl,native_cycle)
    own_styles=style_contracts(azl,azl.cycler);native_styles=style_contracts(mpl,native_cycle)
    report=dict(matplotlib_version=matplotlib.__version__,python=platform.python_version(),platform=platform.platform(),
                azimlib=own,matplotlib=reference,
                styles_azimlib=own_styles,styles_matplotlib=native_styles,
                failed_group_azimlib=failed_group(azl),failed_group_matplotlib=failed_group(mpl),
                notes=['Explicitly labelled line states; color spelling canonicalized, no pixel equivalence.',
                       'Nx2 single-input geographic shorthand differs from Matplotlib y matrices.',
                       'Both attach zero lines after the recorded later shape error; Matplotlib consumes the first cycle entry, Azimlib preserves it.',
                       'Finite unmasked coordinates only; masked/NaN gaps and unit converters are unsupported.',
                       'Marker-only fmt retains legacy zero linewidth in Azimlib.'])
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    assert own==reference,(own,reference)
    assert own_styles==native_styles,(own_styles,native_styles)
    print('Series/matrices/named data and cycle contracts match the selected Matplotlib reference.')

"""Direct development reference for Figure dimensions and independent titles."""
import argparse,json,platform
from pathlib import Path


def contracts(module):
    cases=[]
    for method,args,kwargs in [('set_size_inches',[7.2,4.6],{}),('set_size_inches',[[8,5.4]],{'forward':False}),
                               ('set_figwidth',[6.7],{}),('set_figheight',[4.2],{}),('set_dpi',[150],{}),
                               ('set',[],{'size_inches':[5,4],'dpi':200})]:
        fig,ax=module.subplots()
        try:
            getattr(fig,method)(*args,**kwargs)
            cases.append(dict(method=method,args=args,kwargs=kwargs,size=list(fig.get_size_inches()),
                width=float(fig.get_figwidth()),height=float(fig.get_figheight()),dpi=float(fig.get_dpi()),
                pixels=list(fig.canvas.get_width_height()),stale=fig.stale))
        finally:module.close(fig)
    fig,ax=module.subplots();titles=[]
    try:
        for loc in ('left','center','right'):
            artist=ax.set_title(loc,fontdict={'fontsize':11,'color':'red'},loc=loc,pad=10)
            titles.append(dict(loc=loc,text=ax.get_title(loc=loc),ha=artist.get_ha(),va=artist.get_va(),
                               fontsize=float(artist.get_fontsize()),reused=artist is ax.set_title('Edited '+loc,loc=loc,fontsize=11)))
        center=ax.set_title('Anchor',loc='center',ha='left')
        return dict(dimensions=cases,titles=titles,independent=[ax.get_title(loc=loc) for loc in ('left','center','right')],
                    center_ha=center.get_ha())
    finally:module.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'docs/sizing-titles-reference.json')
    args=parser.parse_args()
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as mpl
    import azimlib as azl
    report=dict(matplotlib_version=matplotlib.__version__,python=platform.python_version(),platform=platform.platform(),
                matplotlib=contracts(mpl),azimlib=contracts(azl),
                differences=['Azimlib rejects zero dimensions/DPI; minimum drawable map area still applies.',
                             'get_size_inches returns an immutable tuple, not a NumPy array.',
                             'Title y/transform overrides and the full Matplotlib Transform system remain unsupported.'])
    assert report['matplotlib']==report['azimlib']
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Figure dimensions and title contracts match the installed Matplotlib reference.')

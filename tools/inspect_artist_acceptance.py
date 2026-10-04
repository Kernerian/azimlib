"""Development-only installed Matplotlib setter/alias reference for checklist 1.11."""
import json
from pathlib import Path


def inspect(module):
    fig,ax=module.subplots();line,=ax.plot([-52,-48],[-25,-21]);legend=ax.legend([line],['Route'])
    spine=ax.spines['left'];frame=legend.get_frame();text=ax.text(-50,-23,'Text')
    result={}
    for name,artist,kwargs in (
        ('line',line,dict(lw=.6,ls='--',ms=4,mfc='white',mec='red')),
        ('spine',spine,dict(lw=.6,ec='red')),
        ('frame',frame,dict(lw=.6,ec='red',fc='white'))):
        artist.set(**kwargs)
        result[name]=dict(linewidth=float(artist.get_linewidth()),lw=float(module.getp(artist,'lw')))
        if name!='line':result[name]['ec_matches']=module.getp(artist,'ec')==artist.get_edgecolor()
    errors={}
    for name,artist,kwargs in (
        ('line-conflict',line,dict(lw=.4,linewidth=.8)),
        ('spine-conflict',spine,dict(ec='red',edgecolor='blue')),
        ('frame-conflict',frame,dict(fc='red',facecolor='blue')),
        ('alignment',text,dict(ha='wrong')),
        ('unknown',line,dict(azimlib_unknown=1))):
        try:artist.set(**kwargs)
        except (TypeError,ValueError,AttributeError):errors[name]='rejected'
        else:errors[name]='accepted'
    result['errors']=errors;module.close(fig)
    views=[]
    for manual_x,manual_y in ((True,True),(True,False),(False,True)):
        fig,ax=module.subplots()
        if manual_x:ax.set_xlim(-54,-42)
        if manual_y:ax.set_ylim(-28,-16)
        ax.imshow([[0,1],[2,3]],extent=(-47,-43,-25,-20))
        views.append(dict(manual_x=manual_x,manual_y=manual_y,
            xlim=list(ax.get_xlim()),ylim=list(ax.get_ylim())))
        module.close(fig)
    result['manual_image_views']=views
    return result


if __name__=='__main__':
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    target=Path(__file__).resolve().parents[1]/'docs/artist-acceptance-reference.json'
    target.write_text(json.dumps(dict(matplotlib=matplotlib.__version__,reference=inspect(plt)),indent=2)+'\n',encoding='utf-8')
    print(target)

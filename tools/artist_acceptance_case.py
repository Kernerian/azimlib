"""Own reproducible 0.2.0 Artist integration; geography real, values synthetic."""
import azimlib as azl
from azimlib import datasets
from azimlib.colors import Normalize


def build(*,dpi=100,orientation='horizontal',projection='mercator',figsize=(4.8,4.2)):
    fig,ax=azl.subplots(figsize=figsize,dpi=dpi,projection=projection,layout='constrained')
    ax.set_extent((-54,-42,-28,-16))
    norm=Normalize(0,4)
    states=datasets.load('states','brazil')
    theme=ax.choropleth(states,[i%5 for i in range(len(states['features']))],bins=None,
        norm=norm,cmap='viridis',alpha=.3,linewidth=.4,zorder=1)
    scatter=ax.scatter([-52,-48,-44],[-25,-22,-19],s=[18,32,48],c=[.5,2,3.5],norm=norm,zorder=6)
    mesh=ax.pcolormesh([-53,-50,-47],[-27,-24,-21],[[.5,1],[2,3]],norm=norm,alpha=.25,zorder=2)
    image=ax.imshow([[.5,2],[3,1]],extent=(-47,-43,-25,-20),norm=norm,alpha=.25,zorder=2)
    vector=ax.quiver([-51,-48,-45],[-24,-21,-18],[.5,1,.5],[1,.5,1],C=[1,2,3],norm=norm,scale=8,zorder=5)
    contour=ax.contour([-54,-48,-42],[-28,-22,-16],[[0,2,4]]*3,
        levels=[1,2,3],norm=norm,linewidths=[.4,.7,1],zorder=4)
    labels=contour.clabel(fmt='%g',fontsize=7,inline=True)
    line,=ax.plot([-52,-48,-44],[-26,-23,-20],'D--',color='#bd3131',label='Synthetic route',zorder=7)
    title=ax.set_title('Artist integration — synthetic values',fontsize=10)
    ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
    legend=ax.legend(handles=[line,scatter],labels=['Synthetic route','Synthetic stations'],loc='upper left',fontsize=7)
    bar=fig.colorbar(theme,ax=ax,orientation=orientation,label='Shared synthetic values')
    scale=ax.scale_bar(length=100,fontsize=7);north=ax.north_arrow(size=24);compass=ax.compass(size=26,loc='lower right')
    return dict(fig=fig,ax=ax,norm=norm,theme=theme,scatter=scatter,mesh=mesh,image=image,
        vector=vector,contour=contour,labels=labels,line=line,title=title,legend=legend,bar=bar,
        scale=scale,north=north,compass=compass)


def mappables(case):return [case[name] for name in ('theme','scatter','mesh','image','vector','contour')]


def edit(case):
    """A sequence of per-Artist validated edits, not an all-Artist transaction."""
    case['theme'].set(array=[(i+1)%5 for i in range(len(case['theme'].data))],cmap='plasma',alpha=.45)
    case['scatter'].set(offsets=[[-51,-24],[-47,-21],[-43,-18]],sizes=[24,42,58],array=[1,2.5,4],cmap='plasma')
    case['mesh'].set(array=[[1,2],[3,4]],cmap='plasma',alpha=.4)
    case['image'].set(data=[[1,3],[4,2]],cmap='plasma')
    case['vector'].set(UVC=([1,.5,1],[.5,1,.5],[1.5,2.5,3.5]),cmap='plasma',scale=10)
    case['contour'].set(array=[1.5,2.5,3.5],cmap='plasma',linewidths=[.6,1,1.4],linestyles=['--',':','-'])
    case['line'].set(data=([-51,-47,-43],[-26,-23,-20]),lw=.9,ms=4,mfc='white',mec='#bd3131')
    case['title'].set_text('Edited Artists — synthetic values')
    case['norm'].vmax=5


def dispose(case):
    case['bar'].remove()
    for artist in mappables(case):artist.remove()
    case['line'].remove()


def audited_families(case):
    ax=case['ax'];fig=case['fig']
    text=ax.text(-49,-22,'Text');annotation=ax.annotate('Note',(-49,-22),xytext=(8,8),textcoords='offset points')
    labels=ax.labels({'type':'Feature','properties':{'name':'Point'},'geometry':{'type':'Point','coordinates':[-48,-21]}})
    figtext=fig.text(.5,.01,'Figure text',ha='center')
    tick=ax.set_xticks([-52,-48,-44],['A','B','C'])[0]
    overview=ax.overview(context='brazil',width=70)
    inset=ax.inset_axes((.7,.7,.2,.2));inset.set_extent((-54,-42,-28,-16))
    return dict(figure=fig,axes=ax,line=case['line'],geometry=case['theme'],scatter=case['scatter'],
        image=case['image'],mesh=case['mesh'],vectors=case['vector'],contour=case['contour'],
        contour_label=case['labels'][0],labels=labels,text=text,annotation=annotation,
        title=case['title'],figure_text=figtext,tick=tick,spine=ax.spines['left'],
        legend=case['legend'],legend_text=case['legend'].get_texts()[0],legend_frame=case['legend'].get_frame(),
        colorbar=case['bar'],colorbar_label=case['bar'].label_artist,colorbar_outline=case['bar'].outline,
        scale=case['scale'],north=case['north'],compass=case['compass'],overview=overview,inset=inset)

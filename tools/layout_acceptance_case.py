"""Bounded layout scenarios; real bundled boundaries, synthetic route."""
import azimlib as azl
from azimlib.colors import Normalize
from azimlib.cm import ScalarMappable
from azimlib.layout_engine import primitive_bounds,item_bounds
from azimlib.scene import Text

KINDS=('regional','atlas','nested')
SIZES={'regional':(4.6,5.8),'atlas':(6.6,11),'nested':(11,12)}


def build(kind='regional',orientation='horizontal',*,fontsize=14,dpi=100,data=True):
    if kind=='regional':
        fig,ax=azl.subplots(figsize=SIZES[kind],dpi=dpi,layout='constrained');axes=[ax]
    elif kind=='atlas':
        fig,aa=azl.subplots(2,1,figsize=SIZES[kind],dpi=dpi,layout='constrained');axes=list(aa)
    elif kind=='nested':
        fig=azl.figure(figsize=SIZES[kind],dpi=dpi,layout='constrained')
        root=fig.add_gridspec(1,2);child=root[1].subgridspec(2,1)
        axes=[fig.add_subplot(root[0]),fig.add_subplot(child[0]),fig.add_subplot(child[1])]
    else:raise ValueError('Unknown scenario')
    legends=[]
    for index,ax in enumerate(axes):
        ax.set_extent((-54,-42,-28,-16))
        if data:ax.states(fc='#f4f4f4',ec='#999999',lw=.3)
        ax.set_title(f'Região {index+1}\nDados sintéticos',fontsize=fontsize)
        ax.set_xlabel('Longitude',fontsize=fontsize);ax.set_ylabel('Latitude',fontsize=fontsize)
        # Fixed ticks stay fixed, as in Matplotlib; choose fewer explicitly
        # when deliberately testing very large fonts in small panels.
        ax.set_xticks([-52,-44] if fontsize==18 else [-52,-48,-44])
        ax.set_yticks([-26,-18] if fontsize==18 else [-26,-22,-18])
        ax.tick_params(labelsize=fontsize,labelrotation=35)
        ax.plot([-52,-48,-44],[-26,-22,-18],'D--',c='#9467bd',lw=1.2,ms=5,label='Rota sintética')
        legends.append(ax.legend(loc='upper left',fontsize=9))
    # Ornaments are deliberately added here; none are viewer defaults.
    scale=axes[0].scale_bar(length=100,fontsize=7,facecolor='white')
    north=axes[0].north_arrow(loc='upper right',size=25)
    compass=axes[0].compass(loc='lower right',size=25)
    overview=axes[-1].overview(context='brazil',width=60,loc='lower right') if len(axes)>1 and data else None
    bar=fig.colorbar(ScalarMappable(norm=Normalize(0,100)),ax=axes,orientation=orientation,label='Índice sintético')
    bar.set_ticks([0,50,100],labels=['0','50','100'],rotation=35)
    bar.ax.tick_params(labelsize=fontsize)
    bar.set_label('Índice sintético',fontsize=fontsize,labelpad=8)
    heading=fig.suptitle('Atlas regional',fontsize=fontsize+2)
    globalx=fig.supxlabel('Longitude global',fontsize=fontsize)
    globaly=fig.supylabel('Latitude global',fontsize=fontsize)
    return dict(fig=fig,axes=axes,bar=bar,legends=legends,scale=scale,north=north,
                compass=compass,overview=overview,heading=heading,globalx=globalx,globaly=globaly)


def overlaps(a,b,tolerance=.2):
    return min(a[0]+a[2],b[0]+b[2])-max(a[0],b[0])>tolerance and min(a[1]+a[3],b[1]+b[3])-max(a[1],b[1])>tolerance


def audit(scene):
    """Canvas bounds and inter-panel/global-label clearance, in device pixels.

    Group envelopes include blank interiors. In-panel legends, annotations and
    ornaments are not universal text-collision guarantees.
    """
    outside=[]
    for item in scene.items:
        if not isinstance(item,Text):continue
        box=primitive_bounds(item)
        if box is not None and (min(box[:2])<-.2 or box[0]+box[2]>scene.width+.2 or box[1]+box[3]>scene.height+.2):outside.append(item.text)
    groups=[item_bounds(scene,start,end) for owners,start,end,slot in scene._layout_groups]
    groups=[b for b in groups if b is not None]
    globals_=[getattr(scene,'_layout'+name) for name in ('_suptitle','_supxlabel','_supylabel')]
    globals_=[b for b in globals_ if b is not None]
    boxes=groups+globals_
    collisions=[(i,j) for i,a in enumerate(boxes) for j,b in enumerate(boxes[i+1:],i+1) if overlaps(a,b)]
    text_collisions=[];crowded_ticks=[]
    for panel,metadata in enumerate(scene.maps):
        ticks=[i for i in metadata['tick_indices'] if isinstance(scene.items[i],Text)]
        labels=[i for anchor in metadata['anchor_ranges'] if anchor['kind'] in ('xlabel','ylabel','title')
                for i in anchor['indices'] if isinstance(scene.items[i],Text)]
        for i in labels:
            for j in ticks:
                if overlaps(primitive_bounds(scene.items[i]),primitive_bounds(scene.items[j])):
                    text_collisions.append((panel,scene.items[i].text,scene.items[j].text))
        for n,i in enumerate(ticks):
            for j in ticks[n+1:]:
                if overlaps(primitive_bounds(scene.items[i]),primitive_bounds(scene.items[j])):
                    crowded_ticks.append((panel,scene.items[i].text,scene.items[j].text))
    return dict(outside=outside,collisions=collisions,text_collisions=text_collisions,crowded_ticks=crowded_ticks,
                panels=len(scene.maps),groups=groups,global_labels=globals_)

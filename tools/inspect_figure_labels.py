"""Development-only direct Figure label contracts and independent Axes examples."""
from pathlib import Path
import hashlib,json,platform,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as mpl
from matplotlib.patches import Polygon
from matplotlib.cm import ScalarMappable as MplMappable
from matplotlib.colors import Normalize as MplNormalize
from matplotlib.ticker import MultipleLocator as MplLocator
from PIL import Image,ImageDraw
import azimlib as azl
from azimlib.cm import ScalarMappable
from azimlib.colors import Normalize
from azimlib.ticker import MultipleLocator
from azimlib.layout_engine import item_bounds


def state(artist):
    return dict(position=list(artist.get_position()),text=artist.get_text(),fontsize=artist.get_fontsize(),
                weight=artist.get_fontweight(),ha=artist.get_ha(),va=artist.get_va(),rotation=artist.get_rotation(),
                rotation_mode=artist.get_rotation_mode(),visible=artist.get_visible(),in_layout=artist.get_in_layout())


def contracts():
    cases=[]
    for name in ('suptitle','supxlabel','supylabel'):
        call=dict(kind='call',method=name,text='Initial',kwargs={})
        cases += [dict(name=name+' defaults',operations=[call]),
                  dict(name=name+' explicit',operations=[dict(call,kwargs=dict(x=.3,y=.2,size=15,weight='bold',horizontalalignment='right',verticalalignment='top'))]),
                  dict(name=name+' reuse',operations=[dict(call,kwargs=dict(x=.3,y=.2,size=15,weight='bold')),dict(call,text='Reused')]),
                  dict(name=name+' edit',operations=[call,dict(kind='set',kwargs=dict(position=[.7,.3],text='Edited',rotation=25,ha='right',va='bottom'))]),
                  dict(name=name+' hidden/excluded',operations=[call,dict(kind='set',kwargs=dict(visible=False,in_layout=False))])]
    cases.append(dict(name='Figure text',operations=[dict(kind='call',method='text',text='Note',kwargs=dict(x=.2,y=.3)),
                                                    dict(kind='set',kwargs=dict(position=[.8,.1],color='red',rotation='vertical',rotation_mode='anchor'))]))
    for case in cases:
        fig=mpl.figure();artist=None
        for op in case['operations']:
            if op['kind']=='call':
                kwargs=dict(op['kwargs'])
                if op['method']=='text':artist=fig.text(kwargs.pop('x'),kwargs.pop('y'),op['text'],**kwargs)
                else:artist=getattr(fig,op['method'])(op['text'],**kwargs)
            else:artist.set(**op['kwargs'])
        case['state']=state(artist);mpl.close(fig)
    return cases


def atlas(module,layout,nested):
    own=module is azl
    f=module.figure(figsize=(10,7 if nested else 6),layout=layout)
    if nested:
        root=f.add_gridspec(2,1);child=root[1].subgridspec(1,2)
        axes=[f.add_subplot(root[0]),f.add_subplot(child[0]),f.add_subplot(child[1])]
    else:axes=list(f.subplots(1,2).flat)
    states=azl.datasets.load('states',country='brazil')
    for i,a in enumerate(axes):
        if own:a.states(facecolor='#eeeeee',edgecolor='#777777',linewidth=.35,fit=False)
        else:
            for feature in states['features']:
                g=feature['geometry'];polygons=[g['coordinates']] if g['type']=='Polygon' else g['coordinates']
                for p in polygons:a.add_patch(Polygon(p[0],facecolor='#eeeeee',edgecolor='#777777',linewidth=.35))
            a.set_aspect('equal')
        a.set_xlim(-54,-42);a.set_ylim(-28,-16)
        locator=MultipleLocator if own else MplLocator
        a.xaxis.set_major_locator(locator(4));a.yaxis.set_major_locator(locator(4))
        a.tick_params(labelsize=9,labelrotation=25)
        a.plot([-52,-48,-44],[-25,-22,-20],color='#d65f45',linestyle='--',linewidth=1.,label='Rota demonstrativa')
        a.set_title(f'Área {i+1}',fontsize=11)
    axes[-1].legend(loc='center left',bbox_to_anchor=(1.02,.5),fontsize=8)
    mappable=ScalarMappable(Normalize(0,100)) if own else MplMappable(MplNormalize(0,100),cmap='viridis')
    if layout!='tight':
        bar=f.colorbar(mappable,ax=axes[1:] if nested else axes,orientation='horizontal',label='Indicador sintético',fraction=.07,pad=.12)
        bar.ax.tick_params(labelsize=9)
    f.suptitle('Atlas regional\nRótulos globais e componentes opcionais',fontsize=14)
    f.supxlabel('Longitude geográfica',fontsize=12);f.supylabel('Latitude geográfica',fontsize=12)
    return f,axes


def main():
    report=dict(matplotlib=matplotlib.__version__,python=platform.python_version(),platform=platform.platform(),
                own_source_sha256={name:hashlib.sha256((ROOT/'src/azimlib'/name).read_bytes()).hexdigest() for name in
                                   ('figure.py','figure_text.py','layout_engine.py','nested_layout.py','config.py','scene.py')},
                contracts=contracts(),layouts=[],
                notes=['Independent Matplotlib Axes/layout vs own cartographic engine with same geographic data, sizes and styles.',
                       'Contract states are compared exactly; font/raster/layout bounds are diagnostic, not pixel equality.',
                       'Generic Figure text is not an automatic obstacle. Explicit constrained global label positions are not automatically reserved.',
                       'Tight example has no colorbar; shared colorbars are demonstrated with constrained. Nested comparison shares a bar only within the child grid.'])
    for layout,nested,name in (('tight',False,'figure-labels-tight'),('constrained',False,'figure-labels-constrained'),('constrained',True,'figure-labels-nested')):
        images=[]
        for module,key in ((mpl,'matplotlib'),(azl,'azimlib')):
            fig,axes=atlas(module,layout,nested)
            path=ROOT/'gallery'/f'{name}-{key}.png';fig.savefig(path,dpi=100)
            fig.canvas.draw()
            if key=='azimlib':
                fig.savefig(ROOT/'gallery'/f'{name}.svg');fig.show(backend='browser',open_browser=False,path=ROOT/'gallery'/f'{name}.html')
                scene=fig.to_scene();bounds=[item_bounds(scene,s,e) for _,s,e,_ in scene._layout_groups]
                labels={name:getattr(scene,'_layout'+name) for name in ('_suptitle','_supxlabel','_supylabel')}
            else:
                renderer=fig.canvas.get_renderer();H=fig.get_size_inches()[1]*100
                def box(artist):
                    b=artist.get_tightbbox(renderer);return (float(b.x0),float(H-b.y1),float(b.width),float(b.height))
                bounds=[box(a) for a in axes]+[box(bar) for bar in fig.axes if bar not in axes]
                labels={name:box(getattr(fig,name)) for name in ('_suptitle','_supxlabel','_supylabel')}
            report['layouts'].append(dict(example=name,library=key,label_states={name:state(getattr(fig,name)) for name in labels},
                                          label_bounds=labels,decoration_bounds=bounds))
            images.append(Image.open(path).convert('RGB'));module.close(fig)
        canvas=Image.new('RGB',(sum(im.width for im in images),max(im.height for im in images)+30),'white')
        draw=ImageDraw.Draw(canvas);draw.text((10,8),f'Matplotlib {matplotlib.__version__} / independent Axes',fill='black')
        draw.text((images[0].width+10,8),'Azimlib / own layout and renderer',fill='black')
        x=0
        for im in images:canvas.paste(im,(x,30));x+=im.width
        canvas.save(ROOT/'gallery'/f'{name}-comparison.png')
    (ROOT/'docs/figure-labels-reference.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f"Recorded {len(report['contracts'])} Matplotlib contracts and {len(report['layouts'])} independent layouts.")


if __name__=='__main__':main()

"""Record Matplotlib text/annotation contracts; compare independent map examples."""
from pathlib import Path
import hashlib,json,platform,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as mpl
from matplotlib.patches import Polygon
from PIL import Image,ImageDraw
import azimlib as azl


def state(text,annotation=False):
    result=dict(text=text.get_text(),position=list(text.get_position()),color=text.get_color(),
                fontsize=text.get_fontsize(),weight=text.get_fontweight(),fontstyle=text.get_fontstyle(),
                ha=text.get_ha(),va=text.get_va(),rotation=text.get_rotation(),visible=text.get_visible(),in_layout=text.get_in_layout())
    if annotation:result.update(xy=list(text.xy),xyann=list(text.xyann),anncoords=text.get_anncoords())
    return result


def contracts():
    tests=[]
    operations=[[],[dict(method='set_position',args=[[-46,-20]])],
                [dict(method='set',kwargs=dict(position=[-46,-20],text='Edited',fontsize=14,color='red',ha='center',va='top',rotation=25))],
                [dict(method='set_x',args=[-45]),dict(method='set_y',args=[-19])],
                [dict(method='set_horizontalalignment',args=['right']),dict(method='set_verticalalignment',args=['bottom'])],
                [dict(method='set_fontstyle',args=['italic']),dict(method='set_weight',args=['bold']),dict(method='set_size',args=[13])],
                [dict(method='set_rotation',args=[-25])],
                [dict(method='set_visible',args=[False]),dict(method='set_in_layout',args=[False])]]
    for annotation in (False,True):
        for i,ops in enumerate(operations):tests.append(dict(name=f"{'annotation' if annotation else 'text'}-{i}",annotation=annotation,operations=ops))
    for coords,pair in (('data',[-46,-20]),('axes fraction',[.4,.6]),('offset points',[30,12])):
        tests.append(dict(name='annotation coords '+coords,annotation=True,operations=[dict(attribute='xy',value=[-46,-21]),
                         dict(attribute='xyann',value=pair),dict(method='set_anncoords',args=[coords])]))
    for test in tests:
        f,a=mpl.subplots()
        text=a.annotate('Initial',xy=(-48,-22),xytext=(12,8),textcoords='offset points') if test['annotation'] else a.text(-48,-22,'Initial')
        for op in test['operations']:
            if 'attribute' in op:setattr(text,op['attribute'],op['value'])
            else:getattr(text,op['method'])(*op.get('args',[]),**op.get('kwargs',{}))
        test['state']=state(text,test['annotation']);mpl.close(f)
    return tests


def example(module):
    own=module is azl
    f,a=module.subplots(figsize=(6.4,5.2),layout='tight')
    if own:a.states(facecolor='#eeeeee',edgecolor='#999999',linewidth=.35,fit=False)
    else:
        for feature in azl.datasets.load('states',country='brazil')['features']:
            g=feature['geometry'];polygons=[g['coordinates']] if g['type']=='Polygon' else g['coordinates']
            for p in polygons:a.add_patch(Polygon(p[0],facecolor='#eeeeee',edgecolor='#999999',linewidth=.35))
        a.set_aspect('equal')
    a.set_xlim(-54,-42);a.set_ylim(-28,-16)
    a.set_title('Textos e annotations editáveis',fontsize=13)
    line,=a.plot([-52,-48,-44],[-25,-22,-20],color='#d65f45',linewidth=1,label='Rota de estudo')
    label=a.text(-49,-23,'Local inicial',fontsize=10,color='#115577',ha='center')
    note=a.annotate('Destino inicial',xy=(-48,-22),xytext=(18,20),textcoords='offset points',
                    color='#553377',fontsize=10,**({} if own else dict(arrowprops=dict(arrowstyle='->',color='#553377',lw=.8))))
    return f,a,label,note


def main():
    report=dict(matplotlib=matplotlib.__version__,python=platform.python_version(),platform=platform.platform(),contracts=contracts(),
                own_source_sha256={name:hashlib.sha256((ROOT/'src/azimlib'/name).read_bytes()).hexdigest() for name in
                                   ('text_artists.py','components.py','axes.py','render_map.py','colorbar.py')},
                notes=['Matplotlib is a development reference only; text states are compared in runtime-independent tests.',
                       'MapText positions are lon/lat or Axes fractions; annotation.xy is geographic, xyann follows anncoords.',
                       'offset points uses physical points and positive y upward. Legacy offset pixels remains logical 100-DPI screen units with positive y downward.',
                       'Independent Axes composition/fonts/arrows/clipping can differ; example images are not pixel-equality fixtures.',
                       'Generic transforms, annotation arrowprops/FancyArrowPatch and rotation_mode for map layers are not implemented.'])
    for module,key in ((mpl,'matplotlib'),(azl,'azimlib')):
        f,a,label,note=example(module)
        for phase in ('before','after'):
            if phase=='after':
                label.set(position=(-51,-24),text='Local editado',color='#1f77b4',fontsize=11,ha='right',va='top')
                note.xy=(-44,-20);note.xyann=(-100,-26);note.set(text='Destino editado',color='#553377',weight='bold')
            f.savefig(ROOT/'gallery'/f'text-edits-{phase}-{key}.png',dpi=100)
            if key=='azimlib':
                f.savefig(ROOT/'gallery'/f'text-edits-{phase}.svg')
                f.show(backend='browser',open_browser=False,path=ROOT/'gallery'/f'text-edits-{phase}.html')
        module.close(f)
    for phase in ('before','after'):
        images=[Image.open(ROOT/'gallery'/f'text-edits-{phase}-{name}.png').convert('RGB') for name in ('matplotlib','azimlib')]
        canvas=Image.new('RGB',(1280,550),'white');draw=ImageDraw.Draw(canvas)
        draw.text((10,8),f'Matplotlib {matplotlib.__version__} / independent Axes',fill='black')
        draw.text((650,8),'Azimlib / own geographic text and annotations',fill='black')
        for i,im in enumerate(images):canvas.paste(im,(i*640,30))
        canvas.save(ROOT/'gallery'/f'text-edits-{phase}-comparison.png')
    (ROOT/'docs/text-edits-reference.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(f"Recorded {len(report['contracts'])} direct Matplotlib contracts; two before/after map comparisons.")


if __name__=='__main__':main()

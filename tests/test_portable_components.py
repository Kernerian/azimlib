"""Portable scale measurement/typography and independent orientation anchors."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path as FilePath
import azimlib as azl
from azimlib.projections import Equirectangular, Mercator
from azimlib.scene import Scene, Rect, Text, Path
from azimlib.viewport import Viewport
from azimlib.render_map import _scale, _anchor
from azimlib.styles import text_style
from azimlib.typography import _export_metrics, text_baseline_offset

PROJECT=FilePath(__file__).resolve().parents[1]
NODE=shutil.which('node')

def fixtures():
    scales=[]
    fig,ax=azl.subplots()
    for projection in (Equirectangular(),Mercator(central_longitude=-40,central_latitude=5)):
        for units in ('km','m','mi'):
            for loc in ('upper left','upper right','lower left','lower right'):
                for pixels in (25,70,300):
                    for ratio in (1,2):
                        options=dict(ax.scale_bar(units=units,loc=loc,fontsize=9))
                        vp=Viewport(projection,(-54,-28,-42,-16),(20,30,pixels,350))
                        scene=Scene(400,500)
                        case=dict(component=dict(options=options,metrics=_export_metrics('0123456789.e+- '+units,text_style({}))),
                                  meta=dict(projection=dict(projection.__dict__,name=projection.name),pixel_ratio=ratio),
                                  view=dict(box=[v*ratio for v in vp.box],ox=vp.ox*ratio,oy=vp.oy*ratio,scale=vp.scale*ratio))
                        try:_scale(options,vp,scene)
                        except ValueError:case['error']=True
                        else:
                            items=[]
                            for p in scene.scaled(ratio).items:
                                item={key:p.style[key] for key in ('fill','stroke','stroke_width','opacity') if key in p.style}
                                if isinstance(p,Rect):item.update(kind='rect',x=p.x,y=p.y,width=p.width,height=p.height)
                                elif isinstance(p,Path):item.update(kind='path',points=p.paths[0])
                                elif isinstance(p,Text):item.update(kind='text',x=p.x,y=p.y+text_baseline_offset(p.text,p.style),size=p.style['font_size'],text=p.text)
                                items.append(item)
                            case['items']=items
                        scales.append(case)
    # Explicit too-long distance must fail rather than stretching to fit.
    for length in (10,50,10000000):
        options=dict(ax.scale_bar(length=length,frameon=False,fontsize=13,color='blue'))
        vp=Viewport(Equirectangular(),(-54,-28,-42,-16),(20,30,180,350));scene=Scene(400,500)
        case=dict(component=dict(options=options,metrics=_export_metrics('0123456789.e+- km',text_style({}))),
                  meta=dict(projection=dict(vp.projection.__dict__,name=vp.projection.name)),
                  view=dict(box=vp.box,ox=vp.ox,oy=vp.oy,scale=vp.scale))
        try:_scale(options,vp,scene)
        except ValueError:case['error']=True
        else:
            case['items']=[]
            for p in scene.items:
                item={key:p.style[key] for key in ('fill','stroke','stroke_width','opacity') if key in p.style}
                if isinstance(p,Rect):item.update(kind='rect',x=p.x,y=p.y,width=p.width,height=p.height)
                else:item.update(kind='text',x=p.x,y=p.y+text_baseline_offset(p.text,p.style),size=p.style['font_size'],text=p.text)
                case['items'].append(item)
        scales.append(case)
    orientations=[]
    for loc in ('upper left','upper right','lower left','lower right'):
        for ratio in (1,2):
            old=[10*ratio,20*ratio,300*ratio,400*ratio];new=[50*ratio,60*ratio,150*ratio,200*ratio]
            a=_anchor(old,loc,70*ratio,70*ratio,10*ratio);b=_anchor(new,loc,70*ratio,70*ratio,10*ratio)
            orientations.append(dict(component=dict(options=dict(loc=loc)),meta=dict(box=old),view=dict(box=new),offset=[b[i]-a[i] for i in (0,1)]))
    azl.close(fig)
    values=(0,1,1.25,.0001,.00001,1000000,1234567,.123456789,1e-9,500,500000)
    return dict(scales=scales,orientations=orientations,formats=[(v,f'{v:g}') for v in values])

class PortableComponentTests(unittest.TestCase):
    def tearDown(self):azl.close('all')

    def test_metadata_only_contains_visible_explicit_components(self):
        fig,ax=azl.subplots();ax.set_extent((-54,-42,-28,-16))
        self.assertEqual(fig.to_scene().maps[0]['components'],[])
        scale=ax.scale_bar();north=ax.north_arrow();rose=ax.compass(loc='lower right')
        scene=fig.to_scene();records=scene.maps[0]['components']
        self.assertEqual([r['kind'] for r in records],['scale','north','compass'])
        self.assertLess(len(json.dumps(records[0]['metrics'])),12000)
        fig.dpi=200;second=fig.to_scene()
        self.assertEqual(records,second.maps[0]['components'])
        north.set_visible(False);scale.set_visible(False)
        self.assertEqual([r['kind'] for r in fig.to_scene().maps[0]['components']],['compass'])
        rose.remove();self.assertEqual(fig.to_scene().maps[0]['components'],[])
        self.assertIn('AzimlibComponents',fig.to_html())
        self.assertNotIn('AzimlibComponents',fig.to_svg())

    @unittest.skipUnless(NODE,'Node is optional for portable component development tests')
    def test_actual_js_matches_own_python_scale_composition_and_anchors(self):
        with tempfile.TemporaryDirectory() as folder:
            data=FilePath(folder)/'components.json';data.write_text(json.dumps(fixtures()),encoding='utf-8')
            result=subprocess.run([NODE,str(PROJECT/'tools/test_portable_components.js'),str(data)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertGreater(json.loads(result.stdout)['checks'],1000)

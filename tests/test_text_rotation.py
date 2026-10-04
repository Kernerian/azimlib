"""Public rotation/anchor behavior against direct Matplotlib Text measurements."""
import importlib.util,json,unittest,shutil,subprocess,math
from pathlib import Path
import azimlib as azl
from azimlib.scene import Scene,Text
from azimlib.styles import text_style
from azimlib.render_map import _text
from azimlib.layout_engine import primitive_bounds,item_bounds
from azimlib.renderers import render_svg
from azimlib.typography import _export_metrics,text_baseline_offset

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('rotation_tool',ROOT/'tools/inspect_text_rotation.py')
tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)


class TextRotationTests(unittest.TestCase):
    def tearDown(self):azl.close('all');azl.rcdefaults()

    def test_768_reference_bounds_match_with_fractional_font_tolerance(self):
        report=json.loads((ROOT/'docs/text-rotation-reference.json').read_text(encoding='utf-8'))
        self.assertEqual(len(report['cases']),768)
        for row in report['cases']:
            with self.subTest(case=row['case']):
                actual=tool.own(row['case'])
                # Agg hints glyph advances; our portable metrics remain fractional.
                # Use the existing 1.5 logical-pixel font tolerance at 100 DPI.
                for a,b in zip(actual,row['matplotlib']):self.assertLessEqual(abs(a-b),1.5)

    def test_default_rotates_then_aligns_anchor_rotates_pre_aligned_box(self):
        for angle in (35,90,-35,180):
            for ha,fraction in (('left',0),('center',.5),('right',1)):
                with self.subTest(angle=angle,ha=ha):
                    style=text_style(dict(rotation=angle,ha=ha,va='top',fontsize=12))
                    scene=Scene(400,400);_text(scene,200,200,'Longitude',style)
                    x,y,w,h=item_bounds(scene)
                    self.assertAlmostEqual(x+fraction*w,200);self.assertAlmostEqual(y,200)
                    other=Scene(400,400);_text(other,200,200,'Longitude',dict(style,rotation_mode='anchor'))
                    self.assertNotEqual(scene.items,other.items)
                    self.assertEqual(other.items[0].x,200);self.assertEqual(other.items[0].y,200)

    def test_direct_scene_text_bakes_once_and_scaling_does_not_realign(self):
        style=text_style(dict(rotation=35,ha='center',va='top'))
        primitive=Text(200,200,'Latitude',style);scene=Scene(400,400);scene.add(primitive)
        box=primitive_bounds(primitive);self.assertAlmostEqual(box[0]+box[2]/2,200);self.assertAlmostEqual(box[1],200)
        scaled=scene.scaled(2);self.assertEqual((scaled.items[0].x,scaled.items[0].y),(primitive.x*2,primitive.y*2))
        self.assertEqual(scaled.items[0].style['rotation_mode'],'anchor')
        self.assertNotIn('<script',render_svg(scene))

    def test_map_figure_title_annotation_and_axis_text_share_editable_modes(self):
        fig,ax=azl.subplots();ax.set_extent((-54,-42,-28,-16))
        artists=[ax.text(-48,-22,'Map'),ax.annotate('Annotation',(-48,-22)),ax.set_title('Title'),
                 fig.text(.5,.5,'Figure'),ax.set_xlabel('Longitude'),ax.set_ylabel('Latitude')]
        self.assertEqual(artists[-1].get_rotation_mode(),'anchor')
        for artist in artists:
            with self.subTest(artist=type(artist).__name__):
                artist.set_rotation_mode('default');artist.set_rotation(35)
                self.assertEqual(artist.get_rotation_mode(),'default')
                fig.canvas.draw();before=artist.get_rotation_mode()
                with self.assertRaises(ValueError):artist.set(rotation_mode='wrong',visible=False)
                self.assertTrue(artist.get_visible());self.assertEqual(artist.get_rotation_mode(),before);self.assertFalse(fig.stale)
                artist.set(rotation='vertical',rotation_mode='anchor');self.assertEqual(artist.get_rotation(),90)

    def test_tick_params_modes_rotations_minor_colorbar_and_rejections_preserve_state(self):
        fig,ax=azl.subplots();ax.set_extent((-54,-42,-28,-16))
        ax.set_xticks([-52,-44],labels=['West','East']);ax.set_yticks([-26,-18],labels=['South','North'])
        ax.tick_params(axis='x',labelrotation=35,labelrotation_mode='xtick')
        ax.tick_params(axis='y',labelrotation=-35,labelrotation_mode='ytick')
        self.assertEqual(ax._tick_labels['x'][0].get_rotation_mode(),'xtick')
        self.assertEqual(ax._tick_labels['y'][0].get_rotation_mode(),'ytick')
        bar=fig.colorbar(azl.cm.ScalarMappable(azl.colors.Normalize(0,1)),ax=ax,orientation='horizontal')
        bar.set_ticks([0,1],labels=['Low','High']);bar.set_ticks([.5],labels=['Middle'],minor=True)
        bar.ax.tick_params(which='both',labelrotation=35,labelrotation_mode='xtick')
        self.assertTrue(all(a.get_rotation_mode()=='xtick' and a.get_rotation()==35 for a in (*bar._ticklabels,*bar._minor_ticklabels)))
        for controller in (ax,bar.ax):
            fig.canvas.draw();before=fig.to_svg()
            with self.assertRaises(ValueError):controller.tick_params(labelrotation=75,labelrotation_mode='invalid')
            self.assertEqual(fig.to_svg(),before);self.assertFalse(fig.stale)

    @unittest.skipUnless(shutil.which('node'),'Node is optional for portable viewer tests')
    def test_portable_viewer_text_plan_matches_python_at_two_pixel_ratios(self):
        cases=json.loads((ROOT/'docs/text-rotation-reference.json').read_text(encoding='utf-8'))['cases']
        records=[]
        for row in cases:
            case=row['case'];style=text_style({k:v for k,v in case.items() if k!='text'})
            scene=Scene(400,400);_text(scene,200,200,case['text'],style)
            for ratio in (1,2):
                scaled=scene.scaled(ratio);box=item_bounds(scaled)
                items=[]
                for p in scaled.items:
                    offset=text_baseline_offset(p.text,p.style);angle=math.radians(p.style.get('rotation',0))
                    items.append(dict(text=p.text,x=p.x-math.sin(angle)*offset-200*ratio,
                                      y=p.y+math.cos(angle)*offset-200*ratio))
                records.append(dict(case=case,ratio=ratio,metrics=_export_metrics(case['text'],style),
                                    anchor=style['anchor'],baseline=style['baseline'],size=style['font_size']*ratio,
                                    items=items,box=[box[0]-200*ratio,box[1]-200*ratio,box[2],box[3]]))
        js="const api=require(process.argv[1]);let input='';process.stdin.on('data',d=>input+=d);process.stdin.on('end',()=>{process.stdout.write(JSON.stringify(JSON.parse(input).map(r=>api.textPlan(r.case.text,r.metrics,r.size,r.anchor,r.baseline,r.case.rotation,r.case.rotation_mode))));});"
        result=subprocess.run(['node','-e',js,str(ROOT/'src/azimlib/assets/components.js')],input=json.dumps(records),capture_output=True,text=True,encoding='utf-8',check=True)
        for record,plan in zip(records,json.loads(result.stdout)):
            with self.subTest(case=record['case'],ratio=record['ratio']):
                self.assertEqual(len(plan['rows']),len(record['items']))
                for expected,actual in zip(record['items'],plan['rows']):
                    self.assertEqual(actual['text'],expected['text'])
                    for k in ('x','y'):self.assertAlmostEqual(actual[k],expected[k],places=9)
                for actual,expected in zip(plan['box'],record['box']):self.assertAlmostEqual(actual,expected,places=9)


if __name__=='__main__':unittest.main()

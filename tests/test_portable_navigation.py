"""Shipped JS integration with real own metadata; optional Node development tests."""
import json,shutil,subprocess,tempfile,unittest
from pathlib import Path
import azimlib as azl

PROJECT=Path(__file__).resolve().parents[1]
NODE=shutil.which('node')


def fixtures():
    fig,axes=azl.subplots(1,2,sharex=True,figsize=(8,4))
    for ax in axes:ax.set_extent((-60,-40,-30,-10))
    axes[1].set_ylim(-20,0);maps=fig.to_scene().maps
    fig.dpi=200;double=fig.to_scene().maps
    cases=[]
    for x in (False,True,'all','none','row','col'):
        for y in (False,True,'all','none','row','col'):
            f,a=azl.subplots(2,3,sharex=x,sharey=y)
            for ax in a.flat:ax.set_extent((-60,-40,-30,-10))
            cases.append(dict(x=x,y=y,maps=f.to_scene().maps));azl.close(f)
    m=azl.figure(figsize=(8,5));a=m.add_subplot(121);b=m.add_subplot(122,projection='mercator',sharex=a,sharey=a)
    a.set_extent((-60,-40,-30,-10));mixed=m.to_scene().maps
    u=azl.figure();a=u.add_subplot(121);b=u.add_subplot(122,projection='orthographic',projection_kw={'central_longitude':-50},sharex=a)
    a.set_extent((-60,-40,-30,-10));unsupported=u.to_scene().maps
    nested,named=azl.subplot_mosaic([['A',[['B','C'],['D','C']]]],sharex=True,sharey=True)
    named['A'].set_extent((-60,-40,-30,-10));nested_maps=nested.to_scene().maps
    sparse,a=azl.subplots(1,3,sharex=True,sharey=True)
    a[0].set_extent((-60,-40,-30,-10));a[1].set_visible(False);sparse_maps=sparse.to_scene().maps
    result=dict(maps=maps,double=double,cases=cases,mixed=mixed,unsupported=unsupported,nested=nested_maps,sparse=sparse_maps,
        reference=json.loads((PROJECT/'docs/portable-navigation-reference.json').read_text()))
    azl.close('all');return result


class PortableMetadataTests(unittest.TestCase):
    def tearDown(self):azl.close('all')

    def test_navigation_metadata_dpi_groups_frame_and_anchor_indices(self):
        fig,a=azl.subplots(1,2,sharex=True)
        for ax in a:ax.set_extent((-60,-40,-30,-10));ax.set_title('Map');ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
        first=fig.to_scene();fig.dpi=200;second=fig.to_scene()
        for original,scaled in zip(first.maps,second.maps):
            self.assertEqual(original['shared_axes']['x'],[0,1]);self.assertEqual(original['shared_axes']['y'],[])
            self.assertEqual(scaled['navigation_box'],tuple(v*2 for v in original['navigation_box']))
            self.assertEqual(scaled['tick_area'],tuple(v*2 for v in original['tick_area']))
            self.assertEqual(scaled['frame_indices'],original['frame_indices'])
            self.assertEqual(scaled['anchor_ranges'],original['anchor_ranges'])
            self.assertEqual({r['kind'] for r in original['anchor_ranges']},{'title','xlabel','ylabel'})
            self.assertEqual(original['portable_ticks']['x']['locator']['kind'],'auto')
            self.assertLess(original['background_index'],original['start'])

    def test_export_contains_own_model_and_static_save_has_no_scripts(self):
        fig,ax=azl.subplots();ax.map('brazil')
        html=fig.to_html();self.assertIn('AzimlibNavigation',html);self.assertIn('Linked navigation requires cylindrical',html)
        self.assertNotIn('<script',fig.to_svg());self.assertNotIn('navigation_box',fig.to_svg())


@unittest.skipUnless(NODE,'Node.js is optional for JavaScript development integration tests')
class PortableJavaScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.file=Path(cls.temp.name)/'metadata.json'
        cls.file.write_text(json.dumps(fixtures()),encoding='utf-8')
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def run_case(self,name):
        result=subprocess.run([NODE,str(PROJECT/'tools/test_portable_navigation.js'),str(self.file),name],capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertGreater(json.loads(result.stdout)['checks'],0)
    def test_rectangle_and_figure_history_match_installed_matplotlib_reference(self):self.run_case('reference')
    def test_36_group_combinations_keep_geography_and_equal_aspect(self):self.run_case('groups')
    def test_zoom_anchor_and_dimension_constraints(self):self.run_case('anchor')
    def test_pan_history_branch_and_cancelled_preview(self):self.run_case('pan')
    def test_mixed_cylindrical_projections_and_shared_domain(self):self.run_case('mixed')
    def test_dpi_doubles_screen_units_and_preserves_geography(self):self.run_case('dpi')
    def test_invalid_inputs_unsupported_groups_and_external_members(self):self.run_case('invalid')
    def test_world_bounds_and_extreme_zoom_remain_finite(self):self.run_case('world')
    def test_nested_mosaics_and_hidden_axes_indices(self):self.run_case('nested')

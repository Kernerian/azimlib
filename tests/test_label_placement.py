"""Legibility, clipping, priorities and explicit collision/scale controls."""
import math,unittest
import azimlib as azl
from azimlib.scene import Text
from azimlib.viewport import Viewport
from azimlib.label_layout import plan_labels,obstacle_boxes
from azimlib.line_labels import clip_segment,visible_paths


def feature(name,kind='Point',coordinates=(0,0),**properties):
    return {'type':'Feature','properties':dict(name=name,**properties),
            'geometry':{'type':kind,'coordinates':coordinates}}


class LabelPlacementTests(unittest.TestCase):
    def setUp(self):
        self.fig,self.ax=azl.subplots(figsize=(6,6))
        self.ax.set_extent((-10,10,-10,10))
    def tearDown(self):azl.close('all')
    def viewport(self):return Viewport(self.ax.projection,self.ax._get_extent(),(0,0,400,400))
    def texts(self):return [p for p in self.fig.to_scene().items if isinstance(p,Text)]
    def test_annotations_reserve_space_and_visibility_releases_it(self):
        self.ax.labels(feature('Automatic'),offsets=[(0,0)])
        note=self.ax.annotate('Explicit note',(0,0),xytext=(0,0),arrow=False,
                              fontsize=22,ha='center',va='center',background='white')
        self.assertNotIn('Automatic',[p.text for p in self.texts()])
        note.set_visible(False)
        self.assertIn('Automatic',[p.text for p in self.texts()])
    def test_visible_annotations_block_even_when_excluded_from_layout(self):
        label=self.ax.labels(feature('Automatic'),offsets=[(0,0)])
        note=self.ax.annotate('Note',(0,0),xytext=(0,0),arrow=False,ha='center',va='center')
        note.set_in_layout(False)
        self.assertNotIn('Automatic',[p.text for p in self.texts()])
        label.options['avoid_overlap']=False
        self.assertIn('Automatic',[p.text for p in self.texts()])
    def test_inset_and_overview_are_obstacles_only_when_visible(self):
        self.ax.labels(feature('Center'),offsets=[(0,0)])
        child=self.ax.inset_axes((.4,.4,.2,.2));child.set_extent((-1,1,-1,1))
        self.assertNotIn('Center',[p.text for p in self.texts()])
        child.set_visible(False);self.assertIn('Center',[p.text for p in self.texts()])
        self.ax.labels(feature('Corner',coordinates=(7,7)),offsets=[(0,0)])
        mini=self.ax.overview(loc='upper right',width=100)
        self.assertNotIn('Corner',[p.text for p in self.texts()])
        mini.set_visible(False);self.assertIn('Corner',[p.text for p in self.texts()])
    def test_alternate_position_keeps_label_clear_of_annotation(self):
        self.ax.annotate('Note',(0,0),xytext=(0,0),arrow=False,ha='center',va='center')
        self.ax.labels(feature('City'),leader=True)
        vp=self.viewport();plan=plan_labels(self.ax,vp)
        self.assertEqual(len(plan),1)
        placement=next(iter(plan.values()))
        self.assertNotEqual(placement.position,placement.anchor)
        from azimlib.render_map import _overlap
        self.assertTrue(all(not _overlap(placement.box,b) for b in obstacle_boxes(self.ax,vp)))
    def test_custom_priority_field_and_constant_priority_across_layers(self):
        self.ax.labels(feature('Low',importance=1),priority_field='importance',offsets=[(0,0)])
        self.ax.labels(feature('High',importance=9),priority_field='importance',offsets=[(0,0)])
        texts=[p.text for p in self.texts()]
        self.assertIn('High',texts);self.assertNotIn('Low',texts)
        self.ax.clear();self.ax.set_extent((-10,10,-10,10))
        self.ax.labels(feature('Constant',priority=-100),priority=20,priority_field=None,offsets=[(0,0)])
        self.ax.labels(feature('Other',priority=10),offsets=[(0,0)])
        self.assertIn('Constant',[p.text for p in self.texts()])
        self.assertNotIn('Other',[p.text for p in self.texts()])
    def test_span_visibility_recalculates_on_zoom_without_hiding_layer(self):
        labels=self.ax.labels(feature('Detailed'),max_span=12)
        self.assertNotIn('Detailed',[p.text for p in self.texts()]);self.assertTrue(labels.get_visible())
        self.ax.zoom(2);self.assertIn('Detailed',[p.text for p in self.texts()])
        labels.options['min_span']=8
        self.ax.zoom(2);self.assertNotIn('Detailed',[p.text for p in self.texts()])
    def test_line_label_uses_visible_section_when_original_midpoint_is_outside(self):
        self.ax.set_extent((-90,-80,-4,6))
        self.ax.labels(feature('River','LineString',[(-100,1),(60,1)]))
        texts=[p for p in self.texts() if p.text=='River']
        self.assertEqual(len(texts),1)
        scene=self.fig.to_scene();x,y,w,h=scene.maps[0]['box']
        self.assertTrue(x<=texts[0].x<=x+w and y<=texts[0].y<=y+h)
    def test_tangent_is_readable_independent_of_vertex_order(self):
        angles=[]
        for coordinates in ([(-8,-8),(8,8)],[(8,8),(-8,-8)]):
            self.ax.clear();self.ax.set_extent((-10,10,-10,10))
            self.ax.labels(feature('River','LineString',coordinates),placement='line')
            text=next(p for p in self.texts() if p.text=='River');angles.append(text.style['rotation'])
        self.assertAlmostEqual(angles[0],-45);self.assertAlmostEqual(angles[1],-45)
    def test_explicit_rotation_overrides_tangent_and_point_mode_stays_horizontal(self):
        geometry=feature('River','LineString',[(-8,-8),(8,8)])
        self.ax.labels(geometry,rotation=15)
        self.assertEqual(next(p for p in self.texts() if p.text=='River').style['rotation'],-15)
        self.ax.clear();self.ax.set_extent((-10,10,-10,10))
        self.ax.labels(geometry,placement='point')
        self.assertEqual(next(p for p in self.texts() if p.text=='River').style['rotation'],0)
    def test_short_line_and_blank_names_do_not_create_labels(self):
        self.ax.labels(feature('Long river name','LineString',[(0,0),(.1,.1)]),fontsize=14)
        self.ax.labels(feature(''),offsets=[(0,0)],priority=100)
        self.ax.labels(feature('Visible'),offsets=[(0,0)])
        texts=[p.text for p in self.texts()]
        self.assertNotIn('Long river name',texts);self.assertIn('Visible',texts)
    def test_polygon_text_footprint_does_not_cross_a_hole(self):
        polygon=[[(-8,-8),(8,-8),(8,8),(-8,8),(-8,-8)],
                 [(-1,-1),(-1,1),(1,1),(1,-1),(-1,-1)]]
        self.ax.labels(feature('Region','Polygon',polygon),fontsize=12)
        vp=self.viewport();plan=plan_labels(self.ax,vp)
        self.assertEqual(len(plan),1)
        p=next(iter(plan.values()));hole=[vp.project(-1,-1),vp.project(1,1)]
        hx0,hx1=sorted(q[0] for q in hole);hy0,hy1=sorted(q[1] for q in hole)
        x,y,w,h=p.box
        self.assertFalse(x<hx1 and x+w>hx0 and y<hy1 and y+h>hy0)
    def test_invalid_options_do_not_add_partial_layers(self):
        for kwargs in ({'placement':'curve'},{'max_span':-1},{'min_span':20,'max_span':10},
                       {'priority_field':2},{'placement':'line'}):
            with self.assertRaises((TypeError,ValueError)):self.ax.labels(feature('City'),**kwargs)
            self.assertEqual(len(self.ax.layers),0)
        with self.assertRaises(ValueError):self.ax.labels(feature('City',priority=float('nan')))
        self.assertEqual(len(self.ax.layers),0)
    def test_segment_clipping_seams_and_projection_domain(self):
        self.assertEqual(clip_segment((-1,5),(11,5),(0,0,10,10)),((0,5),(10,5)))
        self.assertIsNone(clip_segment((-1,-1),(11,-1),(0,0,10,10)))
        from azimlib.io import read_geojson
        line=read_geojson(feature('Seam','LineString',[(170,0),(-170,0)]))[0].geometry
        self.ax.set_extent((-180,180,-20,20))
        paths=visible_paths(line,self.viewport())
        self.assertTrue(paths)
        self.assertTrue(all(math.dist(a,b)<100 for path in paths for a,b in zip(path,path[1:])))


if __name__=='__main__':unittest.main()

"""Mutable geographic scatter collections and coherent scene consumers."""
import io
import json
import math
from pathlib import Path
import unittest
import azimlib as azl
from azimlib.colors import Normalize
from azimlib.scene import Circle
from azimlib.typography import POINT


class ScatterCollectionTests(unittest.TestCase):
    def setUp(self):
        azl.ioff();self.fig,self.ax=azl.subplots()
        self.points=self.ax.scatter([-52,-48],[-25,-21],s=36,c=[20,80],norm=Normalize(0,100))
    def tearDown(self):azl.close('all');azl.ioff();azl.rcdefaults()

    def test_editing_protocol_matches_installed_matplotlib(self):
        cases=[]
        def snapshot(name):
            self.fig.canvas.draw()
            cases.append(dict(name=name,offsets=self.points.get_offsets(),sizes=self.points.get_sizes(),
                              array=self.points.get_array(),view=[*self.ax.get_xlim(),*self.ax.get_ylim()],
                              clim=list(self.points.get_clim())))
        snapshot('initial')
        self.points.set_offsets([[-54,-28],[-43,-18]]);snapshot('moved-fixed-view')
        self.points.set_sizes([25,100]);snapshot('areas')
        self.points.set(offsets=[-46.63,-23.55],array=[50]);snapshot('one-point')
        self.points.set(offsets=[[-52,-25],[-48,-21],[-44,-19]],sizes=[16,64],array=[0,50,100]);snapshot('three-points-cycled-sizes')
        self.points.set(offsets=[],sizes=[],array=[]);snapshot('empty')
        reference=json.loads((Path(__file__).resolve().parents[1]/'docs/scatter-reference.json').read_text())
        for own,expected in zip(cases,reference['cases']):
            with self.subTest(case=own['name']):
                for key in ('name','offsets','sizes','array','clim'):self.assertEqual(own[key],expected[key])
                for actual,wanted in zip(own['view'],expected['view']):self.assertAlmostEqual(actual,wanted,places=9)

    def test_offsets_and_areas_are_copies_and_inputs_are_not_mutated(self):
        offsets=[[-51,-24],[-46,-22]];sizes=[25,100]
        self.points.set(offsets=offsets,sizes=sizes)
        offsets[0][0]=0;sizes[0]=999
        returned=self.points.get_offsets();returned[0][0]=1
        returned_sizes=self.points.get_sizes();returned_sizes[0]=1000
        self.assertEqual(self.points.get_offsets(),[[-51,-24],[-46,-22]])
        self.assertEqual(self.points.get_sizes(),[25,100])
        self.assertIsInstance(self.points,azl.ScatterCollection)
        self.assertIsInstance(self.points,azl.Layer)

    def test_setp_coalesces_updates_and_marks_owners_dirty(self):
        self.fig.canvas.draw();events=[]
        self.points.add_callback(lambda p:events.append((p.get_offsets(),p.get_sizes(),p.get_array(),self.fig.stale)))
        azl.setp(self.points,offsets=[[-53,-26],[-47,-20]],sizes=[16,64],array=[30,70],color='red',visible=False)
        self.assertEqual(len(events),1)
        self.assertEqual(events[0],([[-53,-26],[-47,-20]],[16,64],[30,70],True))
        self.assertTrue(self.points.stale and self.ax.stale)
        self.assertEqual(azl.getp(self.points,'sizes'),[16,64])
        props=azl.getp(self.points)
        self.assertIn('offsets',props);self.assertIn('sizes',props);self.assertNotIn('xdata',props)

    def test_invalid_edits_do_not_change_points_style_or_visibility(self):
        bad=[dict(offsets=[[0,91],[1,2]]),dict(offsets=[[1,2,3],[4,5,6]]),
             dict(offsets=[[math.nan,0],[0,0]]),dict(offsets=[[0,0]]),
             dict(offsets=[[0,0],[1,1]],array=['bad',1]),dict(sizes=[-1,20]),
             dict(sizes=[math.inf]),dict(sizes=25),dict(offsets=[[1,1],[2,2]],linewidth=-1),
             dict(offsets=[[1,1],[2,2]],unknown='value')]
        for kwargs in bad:
            with self.subTest(kwargs=kwargs):
                self.fig.canvas.draw();events=[];cid=self.points.add_callback(events.append)
                with self.assertRaises((ValueError,TypeError)):self.points.set(visible=False,**kwargs)
                self.assertEqual(self.points.get_offsets(),[[-52,-25],[-48,-21]])
                self.assertEqual(self.points.get_sizes(),[36])
                self.assertTrue(self.points.get_visible());self.assertFalse(self.fig.stale);self.assertFalse(events)
                self.points.remove_callback(cid)

    def test_numeric_count_change_is_explicit_and_atomic(self):
        with self.assertRaises(ValueError):self.points.set_offsets([-46,-23])
        self.points.set(offsets=[-46,-23],array=[50])
        self.assertEqual(self.points.get_array(),[50])
        self.points.set_array(None)
        self.points.set_offsets([[-50,-25],[-46,-23],[-44,-19]])
        self.assertEqual(len(self.points.get_offsets()),3)
        self.fig.to_scene()

    def test_sizes_cycle_and_zero_or_empty_areas_have_no_marks(self):
        self.points.set(offsets=[[-52,-25],[-48,-21],[-46,-22]],array=[0,50,100],sizes=[16,64])
        marks=[p for p in self.fig.to_scene().items if isinstance(p,Circle)]
        self.assertEqual([p.r for p in marks],[2*POINT,4*POINT,2*POINT])
        self.points.set_sizes([0,64])
        self.assertEqual(len([p for p in self.fig.to_scene().items if isinstance(p,Circle)]),1)
        self.points.set_sizes(None)
        self.assertFalse(any(isinstance(p,Circle) for p in self.fig.to_scene().items))
        self.points.set_sizes([36],dpi=144)
        self.assertEqual(self.points.get_sizes(),[36])
        with self.assertRaises(ValueError):self.points.set_sizes([25],dpi=0)
        self.assertEqual(self.points.get_sizes(),[36])

    def test_explicit_colors_cycle_after_offset_count_change(self):
        colors=self.ax.scatter([-52,-48],[-25,-21],c=['red','blue'],s=[25,100])
        colors.set_offsets([[-52,-25],[-48,-21],[-46,-23]])
        self.points.set_visible(False)
        marks=[p for p in self.fig.to_scene().items if isinstance(p,Circle)]
        self.assertEqual([p.style['fill'] for p in marks],['red','blue','red'])
        self.assertEqual([p.r for p in marks],[2.5*POINT,5*POINT,2.5*POINT])

    def test_mapped_colors_and_linewidth_are_used_by_scene_and_legend(self):
        self.points.set(offsets=[[-52,-25],[-48,-21]],sizes=[25,100],linewidth=.4,label='Cities')
        self.ax.legend(loc='upper right')
        marks=[p for p in self.fig.to_scene().items if isinstance(p,Circle)]
        self.assertGreaterEqual(len(marks),3)
        self.assertEqual(marks[0].style['fill'],self.points.to_color(20))
        self.assertEqual(marks[-1].style['fill'],self.points.to_color(20))
        self.assertTrue(all(abs(p.style['stroke_width']-.4*POINT)<1e-9 for p in marks))

    def test_relim_and_manual_view_rules_apply_to_edited_scatter(self):
        initial=self.ax.get_extent()
        self.points.set_offsets([[-54,-28],[-43,-18]])
        self.assertEqual(self.ax.get_extent(),initial)
        self.ax.relim();self.assertEqual(self.ax.get_extent(),initial)
        self.ax.autoscale_view();self.assertEqual(self.ax.get_xlim(),(-54.55,-42.45))
        self.ax.set_extent((-55,-42,-29,-17));fixed=self.ax.get_extent()
        self.points.set_offsets([[-50,-24],[-46,-22]])
        self.ax.relim();self.ax.autoscale_view();self.assertEqual(self.ax.get_extent(),fixed)

    def test_empty_points_export_and_removed_collection_detaches(self):
        self.points.set(offsets=[],array=[],sizes=[])
        self.fig.savefig(io.StringIO(),format='svg');self.fig.to_html()
        self.points.remove();self.fig.canvas.draw()
        self.points.set(offsets=[[0,0]],array=[1],sizes=[16])
        self.assertFalse(self.fig.stale);self.assertIsNone(self.points.get_figure())

    def test_zero_size_markers_do_not_reserve_label_space(self):
        self.points.set_visible(False)
        mark=self.ax.scatter([-50],[-23],s=0)
        city={'type':'Feature','properties':{'name':'City'},'geometry':{'type':'Point','coordinates':[-50,-23]}}
        self.ax.labels(city,offsets=[(0,0)])
        self.assertIn('City',self.fig.to_svg())
        mark.set_sizes([10000])
        self.assertNotIn('>City<',self.fig.to_svg())

    def test_new_scalar_sizes_preserve_one_value_and_invalid_initial_lengths_fail(self):
        for count in (0,1,3):
            with self.subTest(count=count):
                p=self.ax.scatter([0]*count,[0]*count,s=49)
                self.assertEqual(p.get_sizes(),[49]);self.assertEqual(len(p.get_offsets()),count)
        before=len(self.ax.layers)
        with self.assertRaises(ValueError):self.ax.scatter([0,1],[0,1],s=[25,100,225])
        self.assertEqual(len(self.ax.layers),before)

    def test_invalid_initial_mapping_does_not_add_layers_or_change_bounds(self):
        before=(len(self.ax.layers),self.ax._bounds,self.ax.get_extent())
        for kwargs in (dict(norm='foreign'),dict(norm=Normalize(0,1),vmin=0),
                       dict(cmap='missing-palette'),dict(vmin=10,vmax=1)):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((ValueError,TypeError)):self.ax.scatter([0,1],[0,1],c=[0,1],**kwargs)
                self.assertEqual((len(self.ax.layers),self.ax._bounds,self.ax.get_extent()),before)

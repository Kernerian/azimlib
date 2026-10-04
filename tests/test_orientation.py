"""Independent optional compass and north-arrow handles across scene consumers."""
import math
import unittest
import azimlib as azl
from azimlib.components import OrientationIndicator
from azimlib.scene import Text,Path
from azimlib.label_layout import obstacle_boxes
from azimlib.navigation import viewport_from_metadata

class OrientationTests(unittest.TestCase):
    def setUp(self):
        azl.ioff();self.fig,self.ax=azl.subplots(figsize=(7,7))
        self.ax.set_extent((-60,-40,-30,-10))
    def tearDown(self):azl.close('all');azl.ioff()
    def letters(self):return [p for p in self.fig.to_scene().items if isinstance(p,Text) and p.text in ('N','S','E','W')]

    def test_both_creation_orders_preserve_independent_handles(self):
        for order in (('compass','north_arrow'),('north_arrow','compass')):
            with self.subTest(order=order):
                self.ax.clear();self.ax.set_extent((-60,-40,-30,-10))
                handles={name:getattr(self.ax,name)() for name in order}
                self.assertIs(self.ax._north,handles['north_arrow']);self.assertIs(self.ax._compass,handles['compass'])
                self.assertIsNot(self.ax._north,self.ax._compass)
                letters=self.letters();self.assertEqual([p.text for p in letters].count('N'),2)
                self.assertEqual(len(letters),5)
                norths=[p.x for p in letters if p.text=='N'];self.assertGreater(abs(norths[0]-norths[1]),100)

    def test_visibility_and_removal_never_modify_the_other(self):
        arrow=self.ax.north_arrow();rose=self.ax.compass()
        rose.set_visible(False);self.assertEqual([p.text for p in self.letters()],['N'])
        self.assertTrue(arrow.get_visible());rose.set_visible(True)
        arrow.set_visible(False);self.assertEqual(len(self.letters()),4)
        arrow.remove();self.assertIsNone(self.ax._north);self.assertIs(self.ax._compass,rose)
        self.assertEqual(len(self.letters()),4);self.assertIsNone(arrow.get_figure())
        rose.remove();self.assertFalse(self.letters());self.assertIsNone(self.ax._compass)

    def test_editing_and_setp_validate_before_mutation(self):
        arrow=self.ax.north_arrow();rose=self.ax.compass();events=[]
        rose.add_callback(events.append);self.fig.canvas.draw()
        azl.setp(rose,loc='lower left',size=28,color='red',in_layout=False)
        self.assertEqual(len(events),1);self.assertTrue(self.fig.stale)
        self.assertEqual(rose.get_loc(),'lower left');self.assertEqual(azl.getp(rose,'size'),28)
        self.assertFalse(rose.get_in_layout());self.assertEqual(arrow.get_color(),'black')
        before=dict(rose)
        for kwargs in (dict(size=0),dict(size=math.inf),dict(loc='bad'),dict(compass=False),dict(unknown=1)):
            with self.subTest(kwargs=kwargs):
                self.fig.canvas.draw();events.clear()
                with self.assertRaises((ValueError,TypeError)):rose.set(visible=False,**kwargs)
                self.assertEqual(dict(rose),before);self.assertFalse(events);self.assertFalse(self.fig.stale)

    def test_same_kind_replacement_detaches_only_previous_instance(self):
        first=self.ax.compass();arrow=self.ax.north_arrow()
        second=self.ax.compass(size=24)
        self.assertIs(self.ax._compass,second);self.assertIs(self.ax._north,arrow)
        self.assertIsNone(first.axes);self.assertIsNone(first.get_figure())
        self.fig.canvas.draw();first.set_color('red');self.assertFalse(self.fig.stale)
        with self.assertRaises(ValueError):self.ax.compass(size=-1)
        self.assertIs(self.ax._compass,second)

    def test_artist_tree_clear_and_default_optional(self):
        self.assertIsNone(self.ax._north);self.assertIsNone(self.ax._compass)
        arrow=self.ax.north_arrow();rose=self.ax.compass()
        self.assertEqual(len(self.fig.findobj(OrientationIndicator)),2)
        self.assertIn(rose,self.ax.get_children());self.assertIn(arrow,self.ax.get_children())
        self.ax.clear();self.assertIsNone(self.ax._north);self.assertIsNone(self.ax._compass)
        self.fig.canvas.draw();rose.set_size(30);arrow.set_loc('lower right')
        self.assertFalse(self.fig.stale)

    def test_both_ornaments_reserve_space_for_labels_and_best_legend(self):
        from azimlib.legend_layout import obstacles
        scene=self.fig.to_scene();vp=viewport_from_metadata(self.ax.projection,scene.maps[0])
        baseline=len(obstacle_boxes(self.ax,vp))
        arrow=self.ax.north_arrow();rose=self.ax.compass()
        boxes=obstacle_boxes(self.ax,vp)
        self.assertGreater(len(boxes),baseline)
        shapes=obstacles(self.ax,vp)
        self.assertGreaterEqual(len(shapes),23)
        rose.set_visible(False);reduced=len(obstacle_boxes(self.ax,vp))
        self.assertLess(reduced,len(boxes));arrow.set_visible(False)
        self.assertEqual(len(obstacle_boxes(self.ax,vp)),baseline)

    def test_overview_excludes_both_and_html_has_shared_decoration_range(self):
        self.ax.north_arrow();self.ax.compass();overview=self.ax.overview(context='brazil',loc='lower right')
        self.assertIsNone(overview.context_axes._north);self.assertIsNone(overview.context_axes._compass)
        scene=self.fig.to_scene();meta=scene.maps[0]
        letters=[p.text for p in scene.items[meta['decoration_start']:meta['decoration_end']] if isinstance(p,Text)]
        self.assertEqual(letters.count('N'),2)
        html=self.fig.to_html();self.assertIn('decoration_start',html);self.assertIn('decoration_end',html)

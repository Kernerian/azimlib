"""Group ownership, deterministic style inheritance, scene, picking and removal."""
import io
from types import SimpleNamespace
import unittest
import azimlib as azl


class Groups050(unittest.TestCase):
    def setUp(self):
        self.fig,self.ax=azl.subplots(figsize=(4,3));self.ax.set_extent((-2,2,-2,2))
        self.line,=self.ax.plot([-1,1],[-1,1],color='red',label='Route')
    def tearDown(self):azl.close('all')

    def test_nested_visibility_preserves_local_decisions_and_draw(self):
        outer=self.ax.group(name='outer');inner=self.ax.group(name='inner',parent=outer)
        inner.add(self.line)
        before=self.fig.to_svg();self.fig.canvas.draw();self.assertFalse(self.fig.stale)
        outer.set_visible(False);self.assertTrue(self.fig.stale);self.assertFalse(self.line.get_visible())
        hidden=self.fig.to_svg();self.assertNotEqual(before,hidden)
        outer.set_visible(True);self.assertEqual(before,self.fig.to_svg())
        self.line.set_visible(False);outer.set_visible(False);outer.set_visible(True)
        self.assertFalse(self.line.get_local_visible());self.assertFalse(self.line.get_visible())
        self.line.set_visible(True);self.assertTrue(self.line.get_visible())

    def test_cycles_multiple_membership_and_foreign_axes_are_blocked(self):
        first=self.ax.group();second=self.ax.group(parent=first);second.add(self.line)
        for action in (lambda:second.add(first),lambda:first.add(first),lambda:first.add(self.line)):
            with self.assertRaises(ValueError):action()
        _,other=azl.subplots()
        with self.assertRaises(ValueError):other.group().add(self.line)
        with self.assertRaises(ValueError):other.add_collection(self.line)
        self.assertEqual(second.get_children(),[self.line])

    def test_local_style_wins_then_nearest_group(self):
        outer=self.ax.group(style={'alpha':.2,'color':'blue'})
        inner=self.ax.group(parent=outer,style={'alpha':.5})
        inner.add(self.line)
        self.assertEqual(self.line.get_color(),'red');self.assertEqual(self.line.get_alpha(),.5)
        self.line.set_alpha(.8);inner.set_style(alpha=.6)
        self.assertEqual(self.line.get_alpha(),.8)
        self.line.set_alpha(None);self.assertEqual(self.line.get_alpha(),.6)
        outer.set_style(alpha=.1);self.assertEqual(self.line.get_alpha(),.6)
        with self.assertRaises(TypeError):inner.set_style(body=azl.MARS)
        with self.assertRaises(ValueError):inner.set_style(alpha=2)
        self.assertEqual(self.line.get_alpha(),.6)

    def test_additive_zorder_and_axes_clip_policy(self):
        outer=self.ax.group(zorder=10,clip_on=True)
        inner=self.ax.group(parent=outer,zorder=2,clip_on=False)
        inner.add(self.line);self.line.set_clip_on(False)
        self.assertEqual(self.line.get_zorder(),14)
        self.assertTrue(self.line.get_clip_on())
        outer.set_clip_on(False);self.assertFalse(self.line.get_clip_on())
        inner.set_zorder(-1);self.assertEqual(self.line.get_zorder(),11)

    def test_unimplemented_group_controls_are_not_silently_ignored(self):
        group=self.ax.group();group.add(self.line)
        with self.assertRaises(NotImplementedError):group.set_transform(self.ax.transAxes)
        with self.assertRaises(NotImplementedError):group.set_picker(5)
        self.assertIsNone(getattr(group,'_transform',None))
        self.assertEqual(group.get_children(),[self.line])

    def test_findobj_body_and_callbacks_are_owned_once(self):
        group=self.ax.group();group.add(self.line);calls=[]
        self.line.add_callback(lambda artist:calls.append(artist.get_body()))
        self.line.set_linewidth(2)
        self.assertEqual(calls,[azl.EARTH])
        objects=self.fig.findobj()
        self.assertEqual(sum(o is self.line for o in objects),1)
        self.assertEqual(sum(o is group for o in objects),1)
        self.assertIs(self.line.get_figure(),self.fig)

    def test_group_changes_invalidate_leaf_cache_serials(self):
        group=self.ax.group();group.add(self.line)
        self.fig.canvas.draw();serial=self.line._change_serial
        group.set_style(alpha=.2)
        self.assertGreater(self.line._change_serial,serial);self.assertTrue(self.fig.stale)

    def test_picking_reports_original_leaf_and_hidden_group_has_no_hit(self):
        group=self.ax.group();group.add(self.line);self.line.set_picker(8)
        scene=self.fig.canvas.draw();x,y,w,h=scene.maps[0]['box'];events=[]
        self.fig.canvas.mpl_connect('pick_event',events.append)
        event=SimpleNamespace(canvas=self.fig.canvas,x=x+w/2,y=scene.height-y-h/2)
        self.fig.canvas.pick(event);self.assertIs(events[-1].artist,self.line)
        events.clear();group.set_visible(False);self.fig.canvas.pick(event);self.assertEqual(events,[])

    def test_discard_preserves_leaf_and_removes_inheritance(self):
        group=self.ax.group(style={'alpha':.2},visible=False);group.add(self.line)
        group.discard(self.line)
        self.assertTrue(self.line.get_visible());self.assertIsNone(self.line.get_alpha())
        self.assertIs(self.line.axes,self.ax);self.assertIs(self.line._artist_parent,self.ax)

    def test_leaf_removal_updates_hierarchy(self):
        group=self.ax.group();group.add(self.line);self.line.remove()
        self.assertEqual(group.get_children(),[]);self.assertIsNone(self.line.axes)
        self.assertNotIn(self.line,self.ax.layers);self.assertIsNone(self.line.get_figure())

    def test_group_recursive_removal_clear_and_axes_removal(self):
        for operation in ('group','clear','axes'):
            with self.subTest(operation=operation):
                _,ax=azl.subplots();root=ax.group();child=ax.group(parent=root)
                line,=ax.plot([0,1],[0,1]);child.add(line)
                root.remove() if operation=='group' else ax.clear() if operation=='clear' else ax.remove()
                self.assertIsNone(line.axes);self.assertIsNone(child.axes);self.assertIsNone(root.axes)
                self.assertIsNone(line.get_figure());self.assertEqual(ax._groups,[])
                root.remove()

    def test_instances_share_only_immutable_data_not_visual_state(self):
        plain=azl.Layer('geometry',azl.read_geojson({'type':'LineString','coordinates':[[0,0],[1,1]]}),{'color':'blue'})
        self.ax.add_collection(plain);group=self.ax.group(style={'alpha':.5});group.add(plain)
        _,other=azl.subplots();copy=group.instantiate(other);fresh=copy.get_children()[0]
        self.assertIsNot(fresh,plain);self.assertIs(fresh.data,plain.data)
        fresh.set_color('green');copy.set_visible(False)
        self.assertEqual(plain.get_color(),'blue');self.assertTrue(plain.get_visible())
        self.assertIs(fresh.axes,other);self.assertIs(plain.axes,self.ax)
        fresh.add_callback(lambda artist:None)
        self.assertIsNot(fresh._artist_callbacks,plain._artist_callbacks)

    def test_unsupported_clone_is_explicit_and_atomic(self):
        group=self.ax.group();group.add(self.line)
        _,other=azl.subplots();before=len(other._groups)
        with self.assertRaises(NotImplementedError):group.instantiate(other)
        self.assertEqual(len(other._groups),before)
        _,mars=azl.subplots(body=azl.MARS)
        with self.assertRaises(ValueError):group.instantiate(mars)

    def test_cpu_svg_png_pdf_and_gpu_refusal(self):
        group=self.ax.group(style={'alpha':.5});group.add(self.line)
        self.assertIn('<svg',self.fig.to_svg())
        for fmt,signature in (('png',b'\x89PNG'),('pdf',b'%PDF')):
            stream=io.BytesIO();self.fig.savefig(stream,format=fmt)
            self.assertTrue(stream.getvalue().startswith(signature))
        with self.assertRaises(azl.UnsupportedBodyOperation):self.fig.savefig(io.BytesIO(),format='png',renderer='gpu')

    def test_planetary_instances_and_epoch_mismatch_are_atomic(self):
        from dataclasses import replace
        fig=azl.figure(body=azl.MARS);first=fig.add_subplot(121);second=fig.add_subplot(122)
        source=azl.read_geojson({'type':'LineString','coordinates':[[0,0],[1,1]]},context=first.get_context())
        leaf=first.geojson(source);group=first.group();group.add(leaf)
        copy=group.instantiate(second);fresh=copy.get_children()[0]
        self.assertIs(fresh.get_body(),azl.MARS);self.assertIsNot(fresh,leaf)
        copy.set_visible(False);self.assertTrue(leaf.get_visible());self.assertFalse(fresh.get_visible())
        other=fig.add_axes((.1,.1,.2,.2),context=replace(first.get_context(),epoch='static snapshot'))
        with self.assertRaises(ValueError):group.instantiate(other)
        self.assertEqual(other._groups,[]);self.assertEqual(other.layers,[])


if __name__=='__main__':unittest.main()

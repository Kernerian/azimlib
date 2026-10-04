"""Integration contracts for discarded decorations and their live replacements."""
import io,json,unittest
from pathlib import Path
import azimlib as azl
from azimlib.colors import Normalize
from azimlib.scene import Text
from azimlib.ticker import MultipleLocator,FormatStrFormatter


class ComponentLifecycleTests(unittest.TestCase):
    def setUp(self):
        azl.ioff()
        self.fig,self.ax=azl.subplots()
        self.ax.set_extent((-55,-42,-28,-16))
        self.ax.plot([-52,-48,-44],[-25,-22,-20],label='Route')

    def tearDown(self):
        azl.ioff();azl.close('all');azl.rcdefaults()

    def assert_detached(self,artists):
        self.fig.canvas.draw()
        for artist in artists:
            self.assertIsNone(artist.get_figure())
            artist.set_visible(False)
        self.assertFalse(self.fig.stale)

    def test_child_text_remove_is_explicit_and_non_mutating(self):
        legend=self.ax.legend();bar=self.ax.colorbar(azl.cm.ScalarMappable(Normalize(0,100)))
        bar.set_ticks([0,100],labels=['Low','High'])
        ticks=self.ax.set_xticks([-50],['West'])
        for text in [legend.get_title(),*legend.get_texts(),bar.label_artist,*bar._ticklabels,*ticks]:
            with self.subTest(text=text.get_text()):
                self.fig.canvas.draw();events=[];text.add_callback(events.append)
                with self.assertRaises(NotImplementedError):text.remove()
                self.assertTrue(text.get_visible());self.assertIs(text.get_figure(),self.fig)
                self.assertFalse(events);self.assertFalse(self.fig.stale)
        free=self.fig.text(.2,.2,'Free');free.remove()
        self.assertNotIn('Free',self.fig.to_svg());self.assertIsNone(free.get_figure())

    def test_hidden_child_texts_disappear_from_static_exports_and_scene(self):
        legend=self.ax.legend(title='Routes')
        bar=self.ax.colorbar(azl.cm.ScalarMappable(Normalize(0,100)))
        bar.set_label('Intensity');bar.set_ticks([0,100],labels=['Low','High'])
        texts=[legend.get_title(),legend.get_texts()[0],bar.label_artist,bar._ticklabels[0]]
        initial=self.fig.to_svg()
        for label in ('Routes','Route','Intensity','Low'):self.assertIn('>'+label+'<',initial)
        for text in texts:text.set_visible(False)
        self.fig.canvas.draw()
        values=[item.text for item in self.fig.to_scene().items if isinstance(item,Text)]
        for label in ('Routes','Route','Intensity','Low'):self.assertNotIn(label,values)
        output=io.StringIO();self.fig.savefig(output,format='svg')
        self.assertIn('>High<',output.getvalue())
        for label in ('Routes','Route','Intensity','Low'):self.assertNotIn('>'+label+'<',output.getvalue())
        for text in texts:text.set_visible(True)
        self.assertEqual(self.fig.to_svg(),initial)

    def test_local_colorbar_replacement_disconnects_only_previous(self):
        mapping=azl.cm.ScalarMappable(Normalize(0,100))
        old=self.ax.colorbar(mapping);previous=old.get_children()
        new=self.ax.colorbar(mapping,orientation='horizontal');new.set_label('Current')
        self.assertIsNone(old.get_figure());self.assertFalse(old.get_visible())
        self.assertTrue(all(a.get_figure() is None for a in previous))
        self.fig.canvas.draw();old.set_label('Discarded');self.assertFalse(self.fig.stale)
        mapping.set_clim(0,200)
        self.assertTrue(self.fig.stale);self.assertEqual(new.vmax,200)
        self.assertNotIn('Discarded',self.fig.to_svg());self.assertIn('Current',self.fig.to_svg())
        old.remove();self.assertIs(self.ax._colorbar,new)

    def test_clear_local_colorbar_disconnects_mapping_but_preserves_shared_bar(self):
        other=self.fig.add_subplot(122)
        mapping=azl.cm.ScalarMappable(Normalize(0,100))
        local=self.ax.colorbar(mapping)
        shared=self.fig.colorbar(mapping,ax=[self.ax,other],orientation='horizontal')
        self.ax.clear();self.assertIsNone(local.get_figure())
        self.fig.canvas.draw();mapping.set_clim(0,200)
        self.assertTrue(self.fig.stale);self.assertEqual(shared.vmax,200)
        shared.remove();self.fig.canvas.draw();mapping.set_clim(0,300)
        self.assertFalse(self.fig.stale)

    def test_replacements_validate_first_and_detach_scale_overview_orientation(self):
        constructors=[('scale',lambda:self.ax.scale_bar(length=200),lambda:self.ax.scale_bar(length=-1)),
                      ('overview',lambda:self.ax.overview(width=90),lambda:self.ax.overview(width=20)),
                      ('north',self.ax.north_arrow,lambda:self.ax.north_arrow(size=-1)),
                      ('compass',self.ax.compass,lambda:self.ax.compass(size=-1))]
        for name,create,invalid in constructors:
            with self.subTest(component=name):
                old=create();self.fig.canvas.draw()
                with self.assertRaises(ValueError):invalid()
                self.assertIs(old.get_figure(),self.fig);self.assertFalse(self.fig.stale)
                current=create();self.assertIsNone(old.get_figure());self.assertFalse(old.get_visible())
                self.fig.canvas.draw();old.set_visible(True)
                self.assertFalse(self.fig.stale);self.assertIs(current.get_figure(),self.fig)

    def test_invalid_colorbar_replacement_retains_existing_callback(self):
        mapping=azl.cm.ScalarMappable(Normalize(0,100));bar=self.ax.colorbar(mapping)
        self.fig.canvas.draw()
        with self.assertRaises(ValueError):self.ax.colorbar(mapping,orientation='horizontal',location='right')
        self.assertIs(self.ax._colorbar,bar);self.assertFalse(self.fig.stale)
        mapping.set_clim(0,200);self.assertTrue(self.fig.stale);self.assertEqual(bar.vmax,200)

    def test_axis_tick_replacement_and_formatter_detach_old_text_handles(self):
        for axis in ('x','y'):
            for minor in (False,True):
                with self.subTest(axis=axis,minor=minor):
                    ticks=[-50,-45] if axis=='x' else [-25,-20]
                    setter=getattr(self.ax,'set_'+axis+'ticks');controller=getattr(self.ax,axis+'axis')
                    old=setter(ticks,['Old 1','Old 2'],minor=minor)
                    current=setter(ticks,['New 1','New 2'],minor=minor)
                    self.assert_detached(old)
                    self.assertTrue(all(a.get_figure() is self.fig for a in current))
                    (controller.set_minor_formatter if minor else controller.set_major_formatter)(FormatStrFormatter('%g'))
                    self.assert_detached(current)
                    self.assertNotIn('New 1',self.fig.to_svg())

    def test_shared_ticker_sync_and_group_join_detach_discarded_labels(self):
        other=self.fig.add_subplot(122)
        for minor in (False,True):
            with self.subTest(minor=minor):
                old=other.set_xticks([-50],['Old shared'],minor=minor)
                other.sharex(self.ax);self.assert_detached(old)
                old=other.set_xticks([-50],['Discard shared'],minor=minor)
                self.ax.set_xticks([-50],['Current shared'],minor=minor)
                self.assert_detached(old)
                self.assertNotIn('Discard shared',self.fig.to_svg())

    def test_colorbar_ticks_norm_and_orientation_reset_detach_only_discarded_handles(self):
        mapping=azl.cm.ScalarMappable(Normalize(0,100));bar=self.ax.colorbar(mapping)
        for minor in (False,True):
            with self.subTest(minor=minor):
                bar.set_ticks([25,75],labels=['Old 1','Old 2'],minor=minor)
                old=list(bar._minor_ticklabels if minor else bar._ticklabels)
                bar.set_ticks([20,80],labels=['New 1','New 2'],minor=minor)
                self.assert_detached(old)
        current=[*bar._ticklabels,*bar._minor_ticklabels]
        bar.set(orientation='horizontal',location='bottom')
        self.assertTrue(all(a.get_figure() is self.fig for a in current))
        mapping.set_clim(0,200)
        self.assertTrue(all(a.get_figure() is self.fig for a in current))
        mapping.set_norm(Normalize(0,10));self.assert_detached(current)

    def test_local_colorbar_addition_and_replacement_request_one_draw_each(self):
        mapping=azl.cm.ScalarMappable(Normalize(0,100));calls=[]
        self.fig.canvas.draw_idle=lambda:calls.append(True)
        with azl.ion():
            self.ax.colorbar(mapping);self.assertEqual(len(calls),1)
            self.ax.colorbar(mapping);self.assertEqual(len(calls),2)

    def test_recorded_reference_common_contracts(self):
        from importlib.util import spec_from_file_location,module_from_spec
        project=Path(__file__).resolve().parents[1]
        spec=spec_from_file_location('component_reference_tool',project/'tools/inspect_component_lifecycle.py')
        module=module_from_spec(spec);spec.loader.exec_module(module)
        reference=json.loads((project/'docs/component-lifecycle-reference.json').read_text(encoding='utf-8'))
        self.assertEqual(module.contracts(azl),reference['azimlib'])
        for name in reference['common']:
            self.assertEqual(reference['azimlib'][name],reference['matplotlib'][name])

    def test_interactive_draw_observes_registered_replacement_and_completed_clear(self):
        mapping=azl.cm.ScalarMappable(Normalize(0,100));observed=[]
        self.fig.canvas.mpl_connect('draw_event',lambda event:observed.append((self.ax._colorbar,len(self.ax.layers))))
        with azl.ion():
            first=self.ax.colorbar(mapping)
            second=self.ax.colorbar(mapping,orientation='horizontal')
            self.ax.clear()
        self.assertEqual(observed,[(first,1),(second,1),(None,0)])
        self.assertFalse(self.fig.stale)

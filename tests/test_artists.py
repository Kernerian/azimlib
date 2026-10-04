"""Artist ownership, invalidation and editing contracts without Matplotlib."""
import gc
import io
import json
from pathlib import Path
import unittest
import weakref
from unittest.mock import patch
import azimlib as azl
from azimlib.artist import Artist
from azimlib.callbacks import CallbackRegistry
from azimlib.components import TextArtist
from azimlib.colors import Normalize
from azimlib.ticker import MultipleLocator


class ArtistTests(unittest.TestCase):
    def setUp(self):
        azl.ioff()
        self.fig,self.ax=azl.subplots()
        self.ax.set_extent((-55,-42,-28,-16))
        self.line,=self.ax.plot([-52,-48,-44],[-25,-22,-20],label='Route')
    def tearDown(self):
        azl.ioff();azl.close('all');azl.rcdefaults()

    def test_dirty_state_propagates_and_draw_acknowledges(self):
        self.fig.canvas.draw()
        self.assertFalse(any(a.stale for a in self.fig.findobj()))
        self.line.set_linewidth(2)
        self.assertTrue(all(a.stale for a in (self.line,self.ax,self.fig)))
        self.line.stale=False
        self.assertTrue(self.fig.stale)  # Cleaning one child does not clean its parent.
        self.fig.to_scene()
        self.fig.savefig(io.StringIO(),format='svg')
        self.assertTrue(self.fig.stale)  # Exports are independent of the displayed canvas.
        events=[]
        self.fig.canvas.mpl_connect('draw_event',lambda e:events.append((e.canvas,self.fig.stale)))
        self.fig.canvas.draw_idle()
        self.assertEqual(events,[(self.fig.canvas,False)])

    def test_nested_setters_notify_once_after_valid_commit(self):
        events=[]
        cid=self.line.add_callback(lambda a:events.append((a.get_color(),a.get_visible(),self.fig.stale)))
        self.fig.canvas.draw()
        self.line.set(color='red',visible=False,linewidth=1.2)
        self.assertEqual(events,[('red',False,True)])
        self.line.remove_callback(cid)
        self.line.set_visible(True)
        self.assertEqual(len(events),1)
        calls=[]
        self.line.stale_callback=lambda a,stale:calls.append((a,stale))
        self.line.set_alpha(.5)
        self.assertEqual(calls,[(self.line,True)])

    def test_invalid_style_edit_does_not_partially_change_control_properties(self):
        title=self.ax.set_title('Before')
        for artist,kwargs in ((self.line,dict(visible=False,linewidth=-1)),
                              (title,dict(text='After',visible=False,fontsize=-1))):
            with self.subTest(type=type(artist).__name__):
                self.fig.canvas.draw();events=[];artist.add_callback(events.append)
                with self.assertRaises(ValueError):artist.set(**kwargs)
                self.assertTrue(artist.get_visible())
                self.assertFalse(self.fig.stale)
                self.assertFalse(events)
        self.assertEqual(title.get_text(),'Before')

    def test_removal_and_clear_detach_old_handles(self):
        title=self.ax.set_title('Title');legend=self.ax.legend();scale=self.ax.scale_bar(length=200)
        title.remove();scale.remove();self.line.remove()
        self.fig.canvas.draw()
        for artist in (title,scale,self.line):
            self.assertIsNone(artist.get_figure())
            artist.set_visible(False)
        self.assertFalse(self.fig.stale)
        old_spine=self.ax.spines['left'];old_label=legend.get_title()
        self.ax.clear();self.fig.canvas.draw()
        old_spine.set_color('red');old_label.set_text('Detached')
        self.assertIsNone(old_spine.get_figure())
        self.assertIsNone(old_label.get_figure())
        self.assertFalse(self.fig.stale)

    def test_text_identity_and_graph_include_hidden_components(self):
        title=self.ax.set_title('A',color='red')
        self.assertIs(title,self.ax.set_title('B'))
        self.assertEqual(title.get_color(),'red')
        supertitle=self.fig.suptitle('A')
        self.assertIs(supertitle,self.fig.suptitle('B'))
        label=self.ax.set_ylabel('Latitude')
        self.assertIs(label,self.ax.set_ylabel('Degrees'))
        legend=self.ax.legend();frame=legend.get_frame()
        self.assertIs(frame,legend.get_frame())
        scale=self.ax.scale_bar(length=200);scale.set_visible(False)
        children=self.ax.get_children()
        self.assertTrue(any(a is scale for a in children))
        objects=self.fig.findobj()
        self.assertEqual(len(objects),len({id(a) for a in objects}))
        self.assertTrue(all(isinstance(a,Artist) and a.get_figure() is self.fig for a in objects))
        texts=self.fig.findobj(TextArtist)
        self.assertIn(title,texts)
        self.assertTrue(all(isinstance(a,TextArtist) for a in texts))
        self.assertNotIn(self.fig,self.fig.findobj(include_self=False))

    def test_optional_components_and_ticks_dirty_the_figure(self):
        legend=self.ax.legend(title='Routes');scale=self.ax.scale_bar(length=200)
        compass=self.ax.compass();overview=self.ax.overview()
        labels=self.ax.set_xticks([-50,-45],['West','East'])
        bar=self.fig.colorbar(azl.cm.ScalarMappable(Normalize(0,100)),ax=self.ax)
        bar.set_ticks([0,50,100],labels=['Low','Middle','High'])
        edits=[lambda:legend.get_title().set_color('red'),lambda:legend.get_frame().set_alpha(.5),
               lambda:scale.set_length(100),lambda:compass.set_visible(False),lambda:overview.set_visible(False),
               lambda:labels[0].set_text('W'),lambda:bar.outline.set_color('red'),
               lambda:bar.label_artist.set_text('Intensity'),lambda:bar._ticklabels[0].set_color('red'),
               lambda:self.ax.xaxis.set_minor_locator(MultipleLocator(.5)),
               lambda:self.ax.tick_params(which='minor',length=3)]
        for edit in edits:
            self.fig.canvas.draw();edit()
            self.assertTrue(self.fig.stale)

    def test_setp_getp_and_alpha_none(self):
        second,=self.ax.plot([-53,-46],[-26,-21])
        azl.setp([[self.line],[second]],'linewidth',1.1,color='red',alpha=.3)
        self.assertEqual(azl.getp(second,'color'),'red')
        self.assertEqual(azl.getp(second)['linewidth'],1.1)
        self.line.set_alpha(None)
        self.assertIsNone(self.line.get_alpha())
        self.assertNotIn('alpha',self.line.style)
        self.assertIn('<svg',self.fig.to_svg())
        polygon=self.ax.polygon([[-52,-25],[-50,-25],[-50,-23],[-52,-23]])
        self.assertNotIn('data',azl.getp(polygon))
        with self.assertRaises(AttributeError):azl.getp(self.line,'made_up')
        with self.assertRaises(ValueError):azl.setp(self.line,'color')

    def test_line_data_edit_preserves_view_and_immutable_source(self):
        source=self.line.data;extent=self.ax.get_extent()
        self.fig.canvas.draw()
        self.line.set_data(([-51,-49,-46],[-26,-23,-19]))
        self.assertTrue(self.fig.stale)
        self.assertEqual(self.ax.get_extent(),extent)
        self.assertEqual(self.line.get_data(),([-51,-49,-46],[-26,-23,-19]))
        self.assertEqual(source[0].geometry.coordinates[0],(-52,-25))
        data=self.line.get_xdata();data[0]=0
        self.assertEqual(self.line.get_xdata()[0],-51)
        old=self.line.data;self.fig.canvas.draw()
        for x,y in (([0],[0,1]),([0,1],[91,0])):
            with self.assertRaises(ValueError):self.line.set_data(x,y)
            self.assertIs(self.line.data,old);self.assertFalse(self.fig.stale)
        self.line.set_data([0],[0]);self.assertEqual(self.line.data[0].geometry.type,'MultiPoint')
        self.line.set_data([],[]);self.assertEqual(self.line.get_data(),([],[]))

    def test_interactive_mode_context_and_composition_guard(self):
        calls=[];self.fig.canvas.draw_idle=lambda:calls.append(True)
        self.line.set_color('red');self.assertFalse(calls)
        with azl.ion():
            self.assertTrue(azl.isinteractive())
            self.line.set_color('blue');self.assertEqual(calls,[True])
            self.fig._composing=True
            self.line.set_color('green');self.assertEqual(calls,[True])
            self.fig._composing=False
            with azl.ioff():self.assertFalse(azl.isinteractive())
            self.assertTrue(azl.isinteractive())
        self.assertFalse(azl.isinteractive())

    def test_scalar_changed_notifies_colorbars_without_owning_axes(self):
        mapping=azl.cm.ScalarMappable(Normalize(0,100))
        bar=self.fig.colorbar(mapping,ax=self.ax);bar.locator=MultipleLocator(25)
        self.fig.canvas.draw();seen=[]
        cid=mapping.callbacks.connect('changed',lambda m:seen.append(m.get_clim()))
        mapping.set_clim(0,200)
        self.assertEqual(seen,[(0,200)]);self.assertTrue(self.fig.stale)
        self.assertIsInstance(bar.locator,MultipleLocator)
        mapping.set_norm(Normalize(0,10))
        self.assertNotIsInstance(bar.locator,MultipleLocator)
        replacement=azl.cm.ScalarMappable(Normalize(1,3))
        bar.update_normal(replacement);self.fig.canvas.draw()
        mapping.set_clim(0,9);self.assertFalse(self.fig.stale)
        replacement.set_cmap('gray');self.assertTrue(self.fig.stale)
        bar.remove();self.fig.canvas.draw()
        replacement.set_clim(1,4);self.assertFalse(self.fig.stale)
        mapping.callbacks.disconnect(cid)

    def test_inset_parent_and_shared_bar_graph(self):
        inset=self.ax.inset();line,=inset.plot([-50,-46],[-24,-21])
        self.fig.canvas.draw();line.set_color('red')
        self.assertTrue(inset.stale and self.ax.stale and self.fig.stale)
        inset.remove();self.fig.canvas.draw();line.set_color('blue')
        self.assertIsNone(line.get_figure());self.assertFalse(self.fig.stale)
        other=self.fig.add_axes((.1,.1,.2,.2))
        bar=self.fig.colorbar(azl.cm.ScalarMappable(Normalize(0,1)),ax=[self.ax,other])
        self.assertIs(bar.get_figure(),self.fig)
        self.assertEqual(sum(a is bar for a in self.fig.findobj()),1)

    def test_callback_registry_weak_methods_blocking_and_dispatch_edits(self):
        registry=CallbackRegistry(('change',));events=[]
        class Owner:
            def callback(self,value):events.append(value)
        owner=Owner();ref=weakref.ref(owner)
        cid=registry.connect('change',owner.callback)
        self.assertEqual(cid,registry.connect('change',owner.callback))
        with registry.blocked(signal='change'):
            registry.process('change',0)
            with registry.blocked():registry.process('change',1)
        registry.process('change',2);self.assertEqual(events,[2])
        del owner;gc.collect();self.assertIsNone(ref())
        registry.process('change',3);self.assertEqual(events,[2])
        registry.disconnect(cid)
        def first(value):
            registry.disconnect(second)
            registry.connect('change',events.append)
        registry.connect('change',first);second=registry.connect('change',lambda v:events.append('removed'))
        registry.process('change',4);self.assertEqual(events,[2])
        registry.process('change',5);self.assertEqual(events,[2,5])
        with self.assertRaises(ValueError):registry.process('unknown')
        with self.assertRaises(TypeError):registry.connect('change',0)

    def test_installed_matplotlib_protocol_fixture(self):
        reference=json.loads((Path(__file__).resolve().parents[1]/'docs/artist-reference.json').read_text(encoding='utf-8'))
        self.fig.canvas.draw()
        actual={'after_draw':[self.line.stale,self.ax.stale,self.fig.stale]}
        self.line.set_visible(False)
        actual['after_edit']=[self.line.stale,self.ax.stale,self.fig.stale]
        self.line.stale=False;actual['after_child_clean']=[self.line.stale,self.ax.stale,self.fig.stale]
        self.line.set_alpha(None);actual['alpha_none']=self.line.get_alpha()
        a=self.ax.set_title('A');actual['title_reused']=a is self.ax.set_title('B')
        self.line.remove();actual['removed_figure']=self.line.get_figure() is None
        self.assertEqual(actual,reference['protocol'])

    def test_failed_draw_preserves_dirty_state_and_can_retry(self):
        self.fig.canvas.draw();self.line.set_color('red')
        with patch.object(self.fig,'to_scene',side_effect=ValueError('Invalid scene')):
            with self.assertRaises(ValueError):self.fig.canvas.draw()
        self.assertTrue(self.fig.stale)
        self.fig.canvas.draw();self.assertFalse(self.fig.stale)

    def test_draw_callback_edit_is_dirty_and_does_not_recurse(self):
        events=[]
        def callback(event):
            events.append(self.fig.stale)
            self.line.set_color('red')
        self.fig.canvas.mpl_connect('draw_event',callback)
        with azl.ion():self.fig.canvas.draw()
        self.assertEqual(events,[False])
        self.assertTrue(self.fig.stale)

    def test_interactive_headless_draw_does_not_create_a_window(self):
        with azl.ion():
            self.line.set_color('red')
            self.assertFalse(self.fig.stale)
        self.assertFalse(hasattr(self.fig,'_viewer'))

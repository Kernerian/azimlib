"""Shared normalizers and geographic autoscaling, independently implemented."""
import gc
import io
import json
import math
from pathlib import Path
import unittest
import weakref
import azimlib as azl
from azimlib.colors import Normalize,LogNorm,TwoSlopeNorm
from azimlib.cm import ScalarMappable
from azimlib.ticker import MultipleLocator,AutoMinorLocator
from azimlib.navigation import Navigation

REFERENCE=Path(__file__).resolve().parents[1]/'docs/norm-limits-reference.json'

class SharedNormalizationTests(unittest.TestCase):
    def tearDown(self):azl.close('all');azl.ioff();azl.rcdefaults()

    def test_norm_signal_protocol_matches_installed_matplotlib(self):
        norm=Normalize(0,10);first=ScalarMappable(norm);second=ScalarMappable(norm);events=[]
        for name,mapping in (('first',first),('second',second)):
            mapping.callbacks.connect('changed',lambda m,name=name:events.append([name,list(m.get_clim()),bool(m.norm.clip)]))
        norm.vmax=20;norm.vmax=20;norm.clip=True;norm.clip=True
        first.set_clim(30,50);first.set_norm(Normalize(-1,1));first.norm=first.norm;norm.vmax=60
        self.assertEqual(events,json.loads(REFERENCE.read_text())['normalization']['signals'])

    def test_shared_norm_updates_different_figures_and_retains_tickers(self):
        norm=Normalize(0,100);items=[]
        for i in range(2):
            fig,ax=azl.subplots();layer=ax.scatter([-50,-46],[-25,-21],c=[20,80],norm=norm)
            bar=fig.colorbar(layer);bar.locator=MultipleLocator(25);bar.minorlocator=AutoMinorLocator(5)
            fig.canvas.draw();items.append((fig,layer,bar,bar.locator,bar.minorlocator))
        norm.vmax=200
        for fig,layer,bar,major,minor in items:
            self.assertTrue(fig.stale and layer.stale and bar.stale)
            self.assertEqual(layer.get_clim(),(0,200))
            self.assertIs(bar.locator,major);self.assertIs(bar.minorlocator,minor)
            self.assertIn(175,bar.get_ticks())
            fig.canvas.draw()
        norm.clip=True
        self.assertTrue(all(fig.stale for fig,*_ in items))

    def test_pair_updates_and_autoscale_emit_only_final_limits(self):
        norm=Normalize(0,10);mapping=ScalarMappable(norm);mapping.set_array([32,35,45]);events=[]
        mapping.callbacks.connect('changed',lambda m:events.append(list(m.get_clim())))
        mapping.set_clim(30,50);self.assertEqual(events,[[30,50]])
        events.clear();mapping.autoscale()
        self.assertEqual(events,json.loads(REFERENCE.read_text())['normalization']['autoscale'])
        events.clear();mapping.autoscale_None();self.assertFalse(events)
        mapping.set_clim(32,45);self.assertFalse(events)

    def test_array_scaling_coalesces_own_signal_and_updates_other_mappables(self):
        norm=Normalize();first=ScalarMappable(norm);second=ScalarMappable(norm);events=[]
        first.callbacks.connect('changed',lambda m:events.append(('first',m.get_clim(),m.get_array())))
        second.callbacks.connect('changed',lambda m:events.append(('second',m.get_clim(),m.get_array())))
        first.set_array([2,4])
        self.assertEqual(events,[('second',(2,4),None),('first',(2,4),[2,4])])
        self.assertTrue(norm.scaled())

    def test_norm_replacement_disconnects_old_signals_and_weak_owners(self):
        old=Normalize(0,1);mapping=ScalarMappable(old);events=[]
        mapping.callbacks.connect('changed',lambda m:events.append(m.get_clim()))
        new=Normalize(1,3);mapping.norm=new;events.clear()
        old.vmax=2;self.assertFalse(events)
        new.vmax=4;self.assertEqual(events,[(1,4)])
        ref=weakref.ref(mapping);del mapping;gc.collect();self.assertIsNone(ref())
        new.vmax=5;self.assertEqual(len(events),1)

    def test_invalid_property_assignments_leave_values_and_signals_unchanged(self):
        norm=Normalize(0,1);events=[];norm.callbacks.connect('changed',lambda:events.append(True))
        for attribute,value in (('vmin',math.nan),('vmax',math.inf),('vmin','invalid')):
            with self.subTest(attribute=attribute,value=value):
                with self.assertRaises(ValueError):setattr(norm,attribute,value)
                self.assertEqual((norm.vmin,norm.vmax),(0,1));self.assertFalse(events)
        mapping=ScalarMappable(norm)
        with self.assertRaises(ValueError):mapping.set_clim(2,1)
        self.assertEqual(mapping.get_clim(),(0,1))
        with self.assertRaises(TypeError):mapping.norm='foreign'
        self.assertIs(mapping.norm,norm)

    def test_center_clip_missing_values_and_blocked_callbacks(self):
        norm=TwoSlopeNorm(0,-2,5);mapping=ScalarMappable(norm);events=[]
        mapping.callbacks.connect('changed',lambda m:events.append(m.norm.vcenter))
        norm.vcenter=1;norm.vcenter=1
        self.assertEqual(events,[1])
        for actual,expected in zip(norm([-2,0,1,3,5]),json.loads(REFERENCE.read_text())['normalization']['slope']):self.assertAlmostEqual(actual,expected)
        log=LogNorm();events=[];log.callbacks.connect('changed',lambda:events.append((log.vmin,log.vmax)))
        log.autoscale([None,math.nan,-2,0,1,100]);self.assertEqual(events,[(1,100)])
        self.assertAlmostEqual(log(10),.5)
        norm=Normalize(0,1);mapping=ScalarMappable(norm);mapping.cmap.set_over('red')
        self.assertEqual(mapping.to_color(2),'red');norm.clip=True
        self.assertEqual(mapping.to_color(2),mapping.cmap(1.0))
        log=ScalarMappable(LogNorm(1,100,clip=True))
        self.assertEqual(log.to_color(1000),log.cmap(1.0))
        events=[];mapping.callbacks.connect('changed',lambda m:events.append(True))
        with norm.callbacks.blocked():norm.vmax=3
        self.assertFalse(events)
        norm.callbacks.process('changed');self.assertEqual(events,[True])

    def test_reset_unscaled_norm_and_empty_colorbar_have_valid_limits(self):
        fig,ax=azl.subplots();mapping=ScalarMappable();bar=fig.colorbar(mapping,ax=ax)
        self.assertEqual(mapping.get_clim(),(0,1))
        mapping.norm=None;self.assertIs(bar.norm,mapping.norm);self.assertEqual(mapping.get_clim(),(0,1))
        mapping.norm.vmin=None;self.assertEqual(mapping.get_clim(),(0,1))
        self.assertIn('<svg',fig.to_svg())
        data=ax.scatter([0,1],[0,1],c=[2,8]);bar=fig.colorbar(data)
        data.set_norm(None);self.assertEqual(data.get_clim(),(2,8))
        data.norm.vmin=None;self.assertEqual(data.get_clim(),(2,8))

    def test_interactive_shared_norm_composes_final_values_without_recursion(self):
        norm=Normalize(0,10);fig,axs=azl.subplots(1,2);layers=[]
        for ax in axs:
            layers.append(ax.scatter([0,1],[0,1],c=[2,8],norm=norm))
        bar=fig.colorbar(layers[0],ax=axs)
        with azl.ion():layers[0].set_clim(30,50)
        self.assertFalse(fig.stale);self.assertEqual(layers[1].get_clim(),(30,50))
        self.assertIs(bar.norm,norm)
        fig.savefig(io.StringIO(),format='svg')

class DataLimitTests(unittest.TestCase):
    def tearDown(self):azl.close('all');azl.ioff();azl.rcdefaults()
    def test_limits_and_flags_match_matplotlib_fixture(self):
        fig,ax=azl.subplots();line,=ax.plot([-52,-48],[-25,-21]);cases=[]
        def snapshot(name):
            cases.append(dict(name=name,extent=[*ax.get_xlim(),*ax.get_ylim()],flags=[ax.get_autoscalex_on(),ax.get_autoscaley_on()],margins=list(ax.margins())))
        snapshot('initial');line.set_data([-50,-42],[-24,-18]);snapshot('edit-preserves-view')
        ax.relim();snapshot('relim-preserves-view');ax.autoscale_view();snapshot('fit-edited-data')
        ax.set_xlim(-54,-44);line.set_data([-50,-40],[-24,-16]);ax.relim();ax.autoscale_view();snapshot('manual-x-auto-y')
        ax.autoscale(axis='x',tight=True);snapshot('tight-x');ax.margins(x=.1,y=-.1);snapshot('positive-and-negative-margins')
        ax.autoscale(False,tight=True);snapshot('disabled')
        hidden,=ax.plot([-60,-55],[-32,-28]);hidden.set_visible(False)
        ax.relim(visible_only=True);ax.autoscale(tight=True);snapshot('visible-only')
        expected=json.loads(REFERENCE.read_text())['limits']
        self.assertEqual(len(cases),len(expected))
        for actual,reference in zip(cases,expected):
            with self.subTest(name=actual['name']):
                self.assertEqual(actual['name'],reference['name']);self.assertEqual(actual['flags'],reference['flags'])
                self.assertEqual(actual['margins'],reference['margins'])
                for value,want in zip(actual['extent'],reference['extent']):self.assertAlmostEqual(value,want,places=9)

    def test_manual_view_survives_relim_and_explicit_autoscale_restores_fit(self):
        fig,ax=azl.subplots();line,=ax.plot([-52,-48],[-25,-21]);ax.set_extent((-54,-44,-27,-19))
        line.set_data([-50,-40],[-24,-16]);ax.relim();ax.autoscale_view()
        self.assertEqual(ax.get_extent(),(-54,-44,-27,-19))
        ax.autoscale(tight=True);self.assertEqual(ax.get_extent(),(-50,-40,-24,-16))

    def test_relim_shrinks_after_remove_and_excludes_unfitted_background(self):
        fig,ax=azl.subplots();ax.map('brazil',fit=False)
        line,=ax.plot([-52,-48],[-25,-21]);extra,=ax.plot([-60,-55],[-32,-28])
        extra.remove();ax.relim();ax.autoscale(tight=True)
        self.assertEqual(ax.get_extent(),(-52,-48,-25,-21))
        self.assertEqual(ax._bounds,(-52,-25,-48,-21))
        line.remove();before=ax.get_extent();ax.relim();ax.autoscale_view()
        self.assertIsNone(ax._bounds);self.assertEqual(ax.get_extent(),before)

    def test_geographic_points_mesh_vectors_and_annotations(self):
        fig,ax=azl.subplots();points=ax.scatter([-5,2],[-4,6]);vectors=ax.quiver([3],[7],[100],[100])
        ax.pcolormesh([-2,0,2],[-2,0,2],[[0,1],[2,3]])
        ax.text(80,80,'Outside');ax.relim();self.assertEqual(ax._bounds,(-5,-4,3,7))
        points.set_visible(False);vectors.set_visible(False);ax.relim(visible_only=True)
        ax.autoscale(tight=True);self.assertEqual(ax.get_extent(),(-2,2,-2,2))

    def test_query_margins_is_read_only_and_invalid_edits_are_atomic(self):
        fig,ax=azl.subplots();ax.plot([0,10],[0,10]);fig.canvas.draw()
        self.assertEqual(ax.margins(),(.05,.05));self.assertFalse(fig.stale)
        for args,kwargs in (((-.5,),{}),((.1,),dict(x=.2)),((),dict(x=.1,y=math.nan))):
            with self.assertRaises((ValueError,TypeError)):ax.margins(*args,**kwargs)
            self.assertEqual(ax.margins(),(.05,.05));self.assertFalse(fig.stale)

    def test_one_automatic_axis_updates_on_new_data_and_auto_none_preserves_flag(self):
        fig,ax=azl.subplots();ax.plot([-52,-48],[-25,-21]);ax.set_xlim(-54,-44)
        ax.plot([-50,-42],[-24,-18]);self.assertEqual(ax.get_xlim(),(-54,-44))
        self.assertEqual(ax.get_ylim(),(-25.35,-17.65))
        ax.set_xlim(-55,-43,auto=None);self.assertFalse(ax.get_autoscalex_on());self.assertTrue(ax.get_autoscaley_on())
        ax.set_ylim(-30,-10,auto=True);self.assertTrue(ax.get_autoscaley_on())

    def test_initial_disabled_axis_and_clear_restore_defaults(self):
        with azl.rc_context({'axes.xmargin':.1,'axes.ymargin':0}):
            fig,ax=azl.subplots();ax.set_autoscalex_on(False);ax.plot([-52,-48],[-25,-21])
            self.assertEqual(ax.get_xlim(),(-180,180));self.assertEqual(ax.get_ylim(),(-25,-21))
            ax.clear();self.assertTrue(ax.get_autoscale_on());self.assertEqual(ax.margins(),(.1,0))
        with self.assertRaises(ValueError):azl.rcParams['axes.xmargin']=-.5

    def test_geographic_domain_singular_and_hidden_data_are_finite(self):
        for lon,lat in ((180,90),(-180,-90),(0,0),(270,0)):
            with self.subTest(lon=lon,lat=lat):
                fig,ax=azl.subplots();ax.scatter([lon],[lat]);ax.relim();ax.autoscale_view()
                w,e,s,n=ax.get_extent();self.assertTrue(-180<=w<e<=180 and -90<=s<n<=90)
                self.assertIn('<svg',fig.to_svg())

    def test_history_restores_autoscale_flags_with_view(self):
        fig,ax=azl.subplots();ax.plot([-52,-48],[-25,-21]);nav=Navigation(fig)
        before=ax.get_extent();ax.zoom(2);nav.push();self.assertFalse(ax.get_autoscale_on())
        nav.home();self.assertEqual(ax.get_extent(),before);self.assertTrue(ax.get_autoscale_on())
        nav.back();self.assertFalse(ax.get_autoscale_on());nav.forward();self.assertTrue(ax.get_autoscale_on())

"""Sharing groups, own view history, ticker state and outer-label reference."""
import json,unittest
from pathlib import Path
import azimlib as azl
from azimlib.ticker import FixedLocator,FixedFormatter,MultipleLocator,NullFormatter
from azimlib.navigation import Navigation

REFERENCE=json.loads((Path(__file__).resolve().parents[1]/'docs/shared-axes-reference.json').read_text())


class SharedAxesTests(unittest.TestCase):
    def setUp(self):azl.close('all');azl.ioff()
    def tearDown(self):azl.close('all');azl.rcdefaults()

    def test_36_factory_modes_membership_and_outer_labels_match_matplotlib(self):
        for case in REFERENCE['cases']:
            with self.subTest(x=case['sharex'],y=case['sharey']):
                fig,axes=azl.subplots(2,3,sharex=case['sharex'],sharey=case['sharey'])
                flat=list(axes.flat)
                for index,ax in enumerate(flat):
                    self.assertEqual([i for i,b in enumerate(flat) if ax.get_shared_x_axes().joined(ax,b)],case['xgroups'][index])
                    self.assertEqual([i for i,b in enumerate(flat) if ax.get_shared_y_axes().joined(ax,b)],case['ygroups'][index])
                    self.assertEqual([ax._tick_params['x']['labelbottom'],ax._tick_params['y']['labelleft']],case['labels'][index])
                azl.close(fig)

    def test_autofit_uses_group_union_but_independent_other_dimension(self):
        fig,a=azl.subplots(2,2,sharex='col',sharey='row')
        a[0,0].plot([1,2],[3,4]);a[1,0].plot([8,9],[20,30])
        for ax,expected in zip(a.flat,REFERENCE['data']):
            # Empty geographic axes retain own world defaults, unlike Cartesian 0..1.
            if ax in (a[0,0],a[1,0]):self.assertEqual(list(ax.get_xlim()),expected['x'])
            self.assertEqual(list(ax.get_ylim()),expected['y'])
        a[0,0].set_autoscalex_on(False)
        self.assertEqual([x.get_autoscalex_on() for x in a.flat],REFERENCE['flags_local'])
        a[0,0].set_xlim(0,12)
        self.assertEqual([x.get_autoscalex_on() for x in a.flat],REFERENCE['flags_limits'])
        a[1,0].plot([30,40],[25,35])
        self.assertEqual(a[0,0].get_xlim(),(0,12));self.assertEqual(a[1,0].get_xlim(),(0,12))
        a[0,0].autoscale(axis='x');self.assertAlmostEqual(a[0,0].get_xlim()[0],-.95);self.assertAlmostEqual(a[0,0].get_xlim()[1],41.95)
        self.assertEqual(a[1,0].get_xlim(),a[0,0].get_xlim())

    def test_emit_false_and_auto_none_preserve_other_axes_and_flags(self):
        _,a=azl.subplots(1,2,sharex=True)
        a[0].set_xlim(-60,-40);a[1].set_autoscalex_on(True)
        events=[]
        for ax in a:ax.callbacks.connect('xlim_changed',lambda changed:events.append(changed))
        a[0].set_xlim(-55,-45,emit=False,auto=None)
        self.assertEqual(a[1].get_xlim(),(-60,-40));self.assertEqual(events,[])
        a[0].set_xlim(-54,-44,auto=None)
        self.assertEqual(set(events),set(a));self.assertFalse(a[0].get_autoscalex_on());self.assertTrue(a[1].get_autoscalex_on())

    def test_tickers_shared_but_label_styles_and_visibility_local(self):
        _,a=azl.subplots(1,2,sharex=True,sharey=True)
        a[0].set_extent((-60,-40,-30,-10));a[0].set_xticks([-60,-50,-40],['W','M','E'],color='red')
        self.assertIs(a[0].xaxis.get_major_locator(),a[1].xaxis.get_major_locator())
        self.assertIs(a[0].xaxis.get_major_formatter(),a[1].xaxis.get_major_formatter())
        self.assertEqual(a[1].xaxis.get_major_formatter()(-50,1),'M')
        self.assertIsNone(a[1]._tick_labels['x'])
        a[1].tick_params(axis='x',labelbottom=False,labelcolor='blue')
        self.assertTrue(a[0]._tick_params['x']['labelbottom']);self.assertEqual(a[0]._tick_labels['x'][0].get_color(),'red')
        locator=MultipleLocator(5);a[1].xaxis.set_minor_locator(locator)
        self.assertIs(a[0].xaxis.get_minor_locator(),locator)
        a[1].xaxis.set_major_formatter(NullFormatter())
        self.assertIsNone(a[0]._tick_labels['x'])

    def test_group_change_invalidates_all_owned_figures(self):
        f,a=azl.subplots();g,b=azl.subplots();b.sharex(a)
        f.canvas.draw();g.canvas.draw();self.assertFalse(f.stale);self.assertFalse(g.stale)
        a.set_xlim(-60,-40)
        self.assertTrue(f.stale);self.assertTrue(g.stale);self.assertEqual(b.get_xlim(),a.get_xlim())

    def test_manual_sharing_construction_and_reject_retarget(self):
        f,a=azl.subplots();a.set_extent((-60,-40,-30,-10))
        b=f.add_subplot(122,sharex=a);c=f.add_axes((.2,.2,.3,.3),sharey=a)
        self.assertEqual(b.get_xlim(),a.get_xlim());self.assertEqual(c.get_ylim(),a.get_ylim())
        b.sharex(a)
        with self.assertRaises(ValueError):b.sharex(c)
        before=list(f.axes)
        with self.assertRaises(TypeError):f.add_subplot(111,sharex=object())
        self.assertEqual(f.axes,before)

    def test_pyplot_reuses_subplots_with_the_same_explicit_sharing_parent(self):
        import azimlib.pyplot as plt
        first=plt.subplot(121);second=plt.subplot(122,sharex=first)
        self.assertIs(plt.subplot(122,sharex=first),second)
        first.set_xlim(-60,-40);self.assertEqual(second.get_xlim(),first.get_xlim())
        self.assertIs(plt.subplot(122),second)

    def test_navigation_history_restores_groups_and_individual_auto_flags(self):
        f,a=azl.subplots(1,2,sharex=True,sharey=False)
        for ax in a:ax.set_extent((-60,-40,-30,-10))
        a[1].set_autoscalex_on(True)
        nav=Navigation(f);a[0].zoom(2);nav.push()
        self.assertEqual(a[1].get_xlim(),(-55,-45));self.assertEqual(a[1].get_ylim(),(-30,-10))
        self.assertTrue(nav.back());self.assertEqual(a[0].get_extent(),(-60,-40,-30,-10))
        self.assertTrue(a[1].get_autoscalex_on());self.assertFalse(a[0].get_autoscalex_on())
        self.assertTrue(nav.forward());self.assertEqual(a[0].get_extent(),(-55,-45,-25,-15))
        nav.home();self.assertEqual(a[1].get_extent(),(-60,-40,-30,-10))

    def test_nested_mosaic_outer_labels_match_local_matplotlib_rules(self):
        _,axes=azl.subplot_mosaic([['A',[['B','C'],['D','E']]]],sharex=True,sharey=True)
        first=axes['A']
        for key,ax in axes.items():
            self.assertEqual([ax._tick_params['x']['labelbottom'],ax._tick_params['y']['labelleft']],REFERENCE['nested'][key])
            self.assertTrue(ax.get_shared_x_axes().joined(ax,first));self.assertTrue(ax.get_shared_y_axes().joined(ax,first))
        axes['E'].set_extent((-55,-40,-28,-15))
        self.assertTrue(all(ax.get_extent()==(-55,-40,-28,-15) for ax in axes.values()))

    def test_child_grid_sharing_does_not_include_parent_neighbor(self):
        f=azl.figure();root=f.add_gridspec(1,2);neighbor=f.add_subplot(root[0])
        child=root[1].subgridspec(2,2);a=child.subplots(sharex='col',sharey='row')
        a[0,0].set_xlim(-60,-40)
        self.assertEqual(a[1,0].get_xlim(),(-60,-40));self.assertEqual(neighbor.get_xlim(),(-180,180))
        self.assertFalse(a[0,0].get_shared_x_axes().joined(a[0,0],neighbor))

    def test_label_outer_removes_labels_optionally_ticks_not_data_or_grid(self):
        _,a=azl.subplots(2,2)
        for ax in a.flat:
            ax.set_xlabel('Longitude');ax.set_ylabel('Latitude');ax.tick_params(which='both',top=True,right=True,labeltop=True,labelright=True);ax.grid(True)
            ax.label_outer(remove_inner_ticks=True)
        self.assertEqual(a[0,0].get_xlabel(),'');self.assertEqual(a[0,1].get_ylabel(),'')
        self.assertEqual(a[1,0].get_xlabel(),'Longitude');self.assertEqual(a[1,0].get_ylabel(),'Latitude')
        self.assertFalse(a[0,0]._tick_params['x']['bottom']);self.assertTrue(a[1,0]._tick_params['x']['bottom'])
        self.assertFalse(a[1,1]._minor_tick_params['y']['left']);self.assertTrue(a[0,0]._minor_tick_params['y']['left'])
        self.assertTrue(all(ax._grid_configs['major'] for ax in a.flat))
        a[0,0].tick_params(axis='x',labelbottom=True);self.assertTrue(a[0,0]._tick_params['x']['labelbottom'])

    def test_clear_preserves_sharing_and_remove_detaches_membership(self):
        f,a=azl.subplots(1,2,sharex=True,sharey=True)
        a[0].set_extent((-60,-40,-30,-10));a[1].clear()
        self.assertEqual(a[1].get_extent(),a[0].get_extent())
        a[0].set_xlim(-58,-42);self.assertEqual(a[1].get_xlim(),(-58,-42))
        removed=a[1];removed.remove();self.assertFalse(a[0].get_shared_x_axes().joined(a[0],removed))
        a[0].set_xlim(-57,-43);self.assertEqual(removed.get_xlim(),(-58,-42));self.assertIsNone(removed.get_figure())

    def test_remove_root_rebinds_tickers_and_clear_does_not_restore_removed_parent(self):
        f,a=azl.subplots(1,3,sharex=True)
        a[0].set_xlim(-60,-40);a[0].xaxis.set_major_locator(MultipleLocator(5))
        removed=a[0];removed.remove()
        a[1].set_xlim(-58,-42)
        self.assertEqual(a[2].get_xlim(),(-58,-42));self.assertEqual(removed.get_xlim(),(-60,-40))
        self.assertIn(a[1].xaxis.get_major_locator().axis.owner,[a[1],a[2]])
        a[1].clear();a[1].set_xlim(-57,-43);self.assertEqual(a[2].get_xlim(),(-57,-43))

    def test_shared_ticker_can_be_assigned_from_a_sibling_but_not_independent_axes(self):
        f,a=azl.subplots(1,2,sharex=True)
        ticker=MultipleLocator(5);a[0].xaxis.set_major_locator(ticker)
        a[1].xaxis.set_major_locator(ticker);self.assertIs(ticker.axis,a[1].xaxis)
        b=f.add_axes((.2,.2,.3,.3))
        with self.assertRaises(ValueError):b.xaxis.set_major_locator(ticker)

    def test_automatic_ticks_consistent_in_different_sized_shared_maps_and_repeat_renders(self):
        f=azl.figure(figsize=(10,5));grid=f.add_gridspec(1,2,width_ratios=[1,3])
        small=f.add_subplot(grid[0]);large=f.add_subplot(grid[1]);small.sharex(large)
        small.set_xlim(-75,-35);small.set_ylim(-35,5);large.set_ylim(-35,5)
        # The ticker belongs to the later-rendered larger axes.
        first=f.to_svg();second=f.to_svg();self.assertEqual(first,second)
        self.assertEqual(small.get_xticks(),large.get_xticks())
        f.figsize=(8,6);self.assertEqual(small.get_xticks(),large.get_xticks())

    def test_overview_clone_does_not_change_shared_main_views(self):
        _,a=azl.subplots(1,2,sharex=True,sharey=True)
        a[0].set_extent((-55,-40,-28,-15));before=[ax.get_extent() for ax in a]
        locator=a[0].overview(context='brazil')
        self.assertEqual([ax.get_extent() for ax in a],before)
        self.assertFalse(a[0].get_shared_x_axes().joined(a[0],locator.context_axes))
        a[1].pan(1,1)
        self.assertNotEqual(locator.context_axes.get_extent(),a[0].get_extent())

    def test_invalid_modes_do_not_create_partial_existing_figure(self):
        f=azl.figure()
        for value in ('diagonal',None,[],2):
            with self.subTest(mode=str(value)):
                with self.assertRaises(ValueError):f.subplots(sharex=value)
                self.assertEqual(f.axes,[]);self.assertEqual(f._gridspecs,[])
        with self.assertRaises(TypeError):f.subplot_mosaic('AB',sharex='col')
        self.assertEqual(f.axes,[])

    def test_svg_and_scene_follow_shared_limits_after_edit(self):
        f,a=azl.subplots(1,2,sharex=True,sharey=True)
        for ax in a:ax.map('brazil')
        a[0].set_extent((-60,-40,-30,-10));scene=f.to_scene()
        self.assertEqual([m['extent'] for m in scene.maps],[(-60.,-30.,-40.,-10.)]*2)
        svg=f.to_svg();self.assertIn('<svg',svg);self.assertNotIn('toolbar',svg)
        self.assertIn('data-dynamic-ticks',f.to_html())

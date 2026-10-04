"""Layout gate: narrow maps, nested atlas, large fonts, 200 DPI and manual anchors."""
import importlib.util,warnings,unittest
from pathlib import Path
import azimlib as azl
from azimlib.scene import Text
from azimlib.layout_engine import primitive_bounds,union_bounds
from azimlib.typography import POINT
from azimlib.cm import ScalarMappable
from azimlib.colors import Normalize

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('layout_case',ROOT/'tools/layout_acceptance_case.py')
factory=importlib.util.module_from_spec(spec);spec.loader.exec_module(factory)


class LayoutAcceptanceTests(unittest.TestCase):
    def tearDown(self):azl.close('all');azl.rcdefaults()

    def test_24_narrow_large_font_dpi_orientation_cases_fit_without_warnings_or_panel_collisions(self):
        for kind in factory.KINDS:
            for orientation in ('horizontal','vertical'):
                for fontsize in (14,18):
                    for dpi in (100,200):
                        with self.subTest(kind=kind,orientation=orientation,fontsize=fontsize,dpi=dpi):
                            case=factory.build(kind,orientation,fontsize=fontsize,dpi=dpi,data=False)
                            with warnings.catch_warnings(record=True) as caught:
                                warnings.simplefilter('always');scene=case['fig'].to_scene()
                            self.assertFalse(caught,[str(w.message) for w in caught])
                            report=factory.audit(scene);self.assertFalse(report['outside']);self.assertFalse(report['collisions'])
                            self.assertFalse(report['text_collisions']);self.assertFalse(report['crowded_ticks'])
                            self.assertEqual(report['panels'],len(case['axes']))
                            self.assertEqual((scene.width,scene.height),tuple(v*dpi for v in factory.SIZES[kind]))
                            self.assertNotIn('<script',case['fig'].to_svg());azl.close(case['fig'])

    def test_colorbar_labelpad_measures_rotated_multiline_major_minor_ticks_on_all_sides(self):
        for location in ('left','right','top','bottom'):
            for rotation in (0,35,75):
                for dpi in (100,200):
                    with self.subTest(location=location,rotation=rotation,dpi=dpi):
                        fig,ax=azl.subplots(figsize=(6,6),dpi=dpi,layout='constrained')
                        ax.set_extent((-54,-42,-28,-16))
                        bar=fig.colorbar(ScalarMappable(Normalize(0,100)),ax=ax,location=location)
                        bar.set_ticks([0,100],labels=['Baixo','Muito\nalto'],rotation=rotation)
                        bar.set_ticks([50],labels=['Intermediário'],minor=True,rotation=rotation)
                        bar.set_label('Índice\nsintético',fontsize=14,labelpad=8)
                        scene=fig.to_scene();items=[p for p in scene.items if isinstance(p,Text)]
                        ticks=union_bounds(primitive_bounds(p) for p in items if p.text in ('Baixo','Muito','alto','Intermediário'))
                        label=union_bounds(primitive_bounds(p) for p in items if p.text in ('Índice','sintético'))
                        gap={'left':ticks[0]-label[0]-label[2],'right':label[0]-ticks[0]-ticks[2],
                             'top':ticks[1]-label[1]-label[3],'bottom':label[1]-ticks[1]-ticks[3]}[location]
                        self.assertAlmostEqual(gap,8*dpi/72,places=8);azl.close(fig)

    def test_colorbar_negative_labelpad_and_hidden_ticklabels_keep_user_control(self):
        fig,ax=azl.subplots(figsize=(5,5));bar=fig.colorbar(ScalarMappable(Normalize(0,1)),ax=ax,orientation='horizontal')
        bar.set_ticks([0,1],labels=['Low','High'],rotation=75)
        bar.set_label('Label',labelpad=-3);first=fig.to_scene()
        tick=max(primitive_bounds(p)[1]+primitive_bounds(p)[3] for p in first.items if isinstance(p,Text) and p.text in ('Low','High'))
        label=next(primitive_bounds(p) for p in first.items if isinstance(p,Text) and p.text=='Label')
        self.assertAlmostEqual(label[1]-tick,-3*POINT)
        for artist in bar._ticklabels:artist.set_visible(False)
        scene=fig.to_scene();self.assertFalse(any(isinstance(p,Text) and p.text in ('Low','High') for p in scene.items))
        self.assertNotEqual(first.items,scene.items)

    def test_dpi_scales_final_layout_and_all_opt_in_components_exactly(self):
        for kind in factory.KINDS:
            with self.subTest(kind=kind):
                case=factory.build(kind,fontsize=18);fig=case['fig'];scene=fig.to_scene(cull=True)
                fig.set_dpi(200);scaled=fig.to_scene(cull=True)
                self.assertEqual(scaled.items,scene.scaled(2).items);self.assertEqual(scaled.maps,scene.scaled(2).maps)
                self.assertFalse(factory.audit(scaled)['collisions']);azl.close(fig)

    def test_toggles_restore_scene_and_manual_anchors_survive_resize(self):
        case=factory.build('atlas');fig=case['fig'];original=fig.to_svg()
        for artist in (*case['legends'],case['bar'],case['scale'],case['north'],case['compass'],case['overview'],case['heading'],case['globalx'],case['globaly']):
            with self.subTest(artist=type(artist).__name__):
                artist.set_visible(False);self.assertNotEqual(original,fig.to_svg())
                artist.set_visible(True);self.assertEqual(original,fig.to_svg())
        heading=fig.suptitle('Posição manual',x=.45,y=.97)
        case['globalx']=fig.supxlabel('Longitude global',x=.4,y=.015)
        case['globaly']=fig.supylabel('Latitude global',x=.015,y=.4)
        legend=case['legends'][0];legend.set_bbox_to_anchor((.05,.95))
        inset=case['axes'][0].inset((.7,.2,.2,.25));inset.set_axis_off()
        manual=fig.add_axes((.2,.4,.1,.1));manual.set_axis_off()
        before=(heading.get_position(),case['globalx'].get_position(),case['globaly'].get_position(),legend['bbox_to_anchor'],inset.position,manual.position)
        for size,dpi in (((5.8,8.5),100),((6.8,9.5),200)):
            with self.subTest(size=size,dpi=dpi):
                fig.set_size_inches(size);fig.set_dpi(dpi);fig.to_scene()
                self.assertEqual(before,(heading.get_position(),case['globalx'].get_position(),case['globaly'].get_position(),legend['bbox_to_anchor'],inset.position,manual.position))

    def test_unfit_layout_warns_restores_positions_and_recovers_when_enlarged(self):
        case=factory.build('nested',fontsize=18,data=False);fig=case['fig'];fig.to_scene()
        prior=([ax.position for ax in fig.axes],dict(fig.subplotpars),[case[k].get_position() for k in ('heading','globalx','globaly')])
        fig.set_size_inches(1,1)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always');result=fig.get_layout_engine().execute(fig)
        self.assertFalse(result);self.assertTrue(caught)
        self.assertEqual(prior,([ax.position for ax in fig.axes],dict(fig.subplotpars),[case[k].get_position() for k in ('heading','globalx','globaly')]))
        fig.set_size_inches(factory.SIZES['nested']);self.assertFalse(factory.audit(fig.to_scene())['collisions'])

    def test_empty_map_has_no_automatic_cartographic_ornaments_or_grid(self):
        fig,ax=azl.subplots(layout='constrained');scene=fig.to_scene()
        self.assertFalse(scene.maps[0]['components']);self.assertFalse(scene.maps[0]['grid_specs'])
        self.assertNotIn('overview_map',scene.maps[0]);self.assertFalse(fig._colorbars)

    def test_axis_labelpad_uses_full_rotated_tick_bounds_instead_of_box_side_filter(self):
        for angle in (0,35,75,90):
            for dpi in (100,200):
                with self.subTest(angle=angle,dpi=dpi):
                    fig,ax=azl.subplots(figsize=(6,6),dpi=dpi,layout='constrained')
                    ax.set_extent((-54,-42,-28,-16))
                    ax.set_xticks([-52,-48,-44],labels=['x-low','x-mid','x-high'])
                    ax.set_yticks([-26,-22,-18],labels=['y-low','y-mid','y-high'])
                    ax.tick_params(labelsize=18,labelrotation=angle)
                    ax.set_xlabel('Longitude',labelpad=12);ax.set_ylabel('Latitude',labelpad=12)
                    scene=fig.to_scene();items=[p for p in scene.items if isinstance(p,Text)]
                    xb=union_bounds(primitive_bounds(p) for p in items if p.text.startswith('x-'))
                    yb=union_bounds(primitive_bounds(p) for p in items if p.text.startswith('y-'))
                    xlabel=next(primitive_bounds(p) for p in items if p.text=='Longitude')
                    ylabel=next(primitive_bounds(p) for p in items if p.text=='Latitude')
                    self.assertAlmostEqual(xlabel[1]-xb[1]-xb[3],12*dpi/72,places=8)
                    self.assertAlmostEqual(yb[0]-ylabel[0]-ylabel[2],12*dpi/72,places=8)
                    azl.close(fig)

    def test_overview_can_shrink_below_30px_without_reprojecting_data_during_measurement(self):
        from unittest.mock import patch
        from azimlib.render_map import render_axes
        from azimlib.scene import Scene
        fig,ax=azl.subplots();ax.set_extent((-54,-42,-28,-16))
        overview=ax.overview(context='brazil',width=60)
        from azimlib import render_map
        with patch.object(render_map,'_geometry',side_effect=AssertionError('Layout must not project overview data')):
            scene=Scene(100,100);render_axes(ax,scene,(10,10,50,50),measure_layout=True)
        mini=scene.maps[0]['overview_map'];self.assertLess(mini['box'][2],30)
        self.assertEqual(scene.items[mini['focus_index']].style['stroke'],'black')
        complete=Scene(100,100);render_axes(ax,complete,(10,10,50,50))
        self.assertEqual(complete.maps[0]['overview_map']['box'],mini['box'])
        self.assertGreater(len(complete.items),len(scene.items))

    def test_automatic_bar_clearance_does_not_rewrite_pad_or_move_explicit_cax(self):
        fig,axes=azl.subplots(1,2,figsize=(8,3),layout='constrained')
        for ax in axes:
            ax.set_extent((-54,-42,-28,-16));ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
        bar=fig.colorbar(ScalarMappable(Normalize(0,100)),ax=list(axes),orientation='horizontal',fraction=.03,pad=0)
        bar.set_label('Índice',labelpad=8)
        scene=fig.to_scene()
        self.assertEqual(bar['pad'],0);self.assertGreater(bar._layout_clearance,0)
        barbox=next(union_bounds(primitive_bounds(scene.items[i]) for i in range(s,e))
                    for owners,s,e,_ in scene._layout_groups if len(owners)==2)
        parentbox=union_bounds(primitive_bounds(scene.items[i])
                    for owners,s,e,_ in scene._layout_groups if len(owners)==1 for i in range(s,e))
        self.assertFalse(factory.overlaps(barbox,parentbox))
        clearance=bar._layout_clearance;prior=[ax.position for ax in axes]
        fig.set_size_inches(1,1)
        with self.assertWarns(UserWarning):self.assertFalse(fig.get_layout_engine().execute(fig))
        self.assertEqual(bar._layout_clearance,clearance);self.assertEqual([ax.position for ax in axes],prior)
        fig2=azl.figure(figsize=(6,6),layout='constrained');ax=fig2.add_subplot(111)
        cax=fig2.add_axes((.92,.2,.025,.6))
        explicit=fig2.colorbar(ScalarMappable(Normalize(0,100)),ax=ax,cax=cax,pad=0)
        fig2.to_scene();self.assertEqual(cax.position,(.92,.2,.025,.6));self.assertEqual(explicit._layout_clearance,0)


if __name__=='__main__':unittest.main()

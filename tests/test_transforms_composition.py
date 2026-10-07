"""Public-contract integration checks for the own 0.3 composition foundation."""
import datetime as dt
import math
import unittest
import warnings
import azimlib as az
from azimlib.transforms import Affine2D,IdentityTransform,PhysicalTransform,blended_transform_factory,offset_copy
from azimlib.navigation import Navigation,viewport_from_metadata
from azimlib.render_map import graticule_intersections
from azimlib.scene import Path as ScenePath,Text

class FoundationTests(unittest.TestCase):
    def tearDown(self):az.close('all')
    def assertPair(self,a,b,places=7):
        for x,y in zip(a,b):self.assertAlmostEqual(x,y,places=places)

    def test_affine_order_inverse_singular_and_batch(self):
        t=Affine2D().scale(2,3).translate(5,-4).rotate_deg(90)
        self.assertPair(t.transform_point((1,2)),(-2,7))
        for p in ((0,0),(1,2),(-100,.001)):
            with self.subTest(p=p):self.assertPair(t.inverted().transform_point(t.transform_point(p)),p)
        self.assertEqual(len(t.transform([(0,0),(1,2)])),2)
        with self.assertRaises(ValueError):Affine2D().scale(0).inverted()
        with self.assertRaises(ValueError):Affine2D().translate(float('nan'),0)

    def test_composition_live_figure_dpi_size_and_physical_offset(self):
        fig,ax=az.subplots(figsize=(8,6),dpi=100);t=fig.transFigure
        self.assertPair(t.transform_point((.5,.5)),(400,300))
        self.assertPair(t.inverted().transform_point((400,300)),(.5,.5))
        off=offset_copy(t,fig=fig,x=72,y=36,units='points')
        self.assertPair(off.transform_point((0,0)),(100,50))
        fig.set_dpi(200);fig.set_size_inches(10,7)
        self.assertPair(t.transform_point((.5,.5)),(1000,700))
        self.assertPair(off.transform_point((0,0)),(200,100))
        self.assertPair(PhysicalTransform(fig,'mm').transform_point((25.4,25.4)),(200,200))
        self.assertPair(off.inverted().transform_point(off.transform_point((.4,.3))),(.4,.3))

    def test_axes_geo_projected_and_fraction_roundtrips_after_edits(self):
        for projection in ('equirectangular','mercator','stereographic','orthographic','tmerc'):
            with self.subTest(projection=projection):
                fig,ax=az.subplots(projection=projection,projection_kw={'central_longitude':-45,'central_latitude':-20})
                ax.set_extent((-50,-40,-25,-15));p=(-46,-22)
                self.assertPair(ax.transData.inverted().transform_point(ax.transData.transform_point(p)),p,6)
                self.assertPair(ax.transAxes.inverted().transform_point(ax.transAxes.transform_point((.2,.7))),(.2,.7))
                xy=ax.projection.forward(*p)
                self.assertPair(ax.transProjection.transform_point(xy),ax.transData.transform_point(p))
                ax.set_bearing(33)
                self.assertPair(ax.transData.inverted().transform_point(ax.transData.transform_point(p)),p,6)

    def test_mixed_transforms_text_artist_ownership_and_atomic_edits(self):
        fig,ax=az.subplots();ax.set_extent((-50,-40,-25,-15))
        mixed=blended_transform_factory(ax.transData,ax.transAxes)
        text=ax.text(-45,.9,'mixed',transform=mixed,clip_on=False)
        scene=fig.to_scene();q=next(p for p in scene.items if isinstance(p,Text) and p.text=='mixed')
        target=mixed.transform_point((-45,.9))
        self.assertPair((q.x*fig.dpi/100,(scene.height-q.y)*fig.dpi/100),target)
        text.set(position=(-43,.8),transform=mixed,fontsize=12)
        self.assertTrue(fig.stale)
        other,_=az.subplots();before=text.get_position()
        with self.assertRaises(ValueError):text.set(position=(-40,.7),transform=other.transFigure)
        self.assertEqual(text.get_position(),before)
        with self.assertRaises(NotImplementedError):blended_transform_factory(Affine2D().rotate_deg(45),IdentityTransform()).inverted()

    def test_transform_assigned_to_existing_layer_and_scatter(self):
        fig,ax=az.subplots();ax.set_extent((-50,-40,-25,-15))
        line,=ax.plot([0,1],[0,1],fit=False);line.set_transform(ax.transAxes)
        scatter=ax.scatter([.2],[.7]);scatter.set_transform(ax.transAxes)
        svg=fig.to_svg();self.assertIn('<svg',svg)
        self.assertIs(line.get_transform().axes,ax)

    def test_nan_gaps_no_bridges_getters_and_editing(self):
        fig,ax=az.subplots();line,=ax.plot([-48,-47,float('nan'),-45,-44],[-23,-22,float('nan'),-20,-19],color='red')
        scene=fig.to_scene();paths=[p for p in scene.items if isinstance(p,ScenePath) and p.style.get('stroke') in ('red','#ff0000')]
        self.assertEqual(len(paths),2)
        self.assertTrue(math.isnan(line.get_xdata()[2]))
        line.set_data([-49,-48,float('nan'),-46],[-24,-23,float('nan'),-21])
        self.assertTrue(math.isnan(line.get_ydata()[2]));self.assertIn('<svg',fig.to_svg())
        before=line.get_data()
        with self.assertRaises(ValueError):line.set_data([0,float('inf')],[0,1])
        self.assertEqual(line.get_data(),before)
        empty,=ax.plot([float('nan')],[float('nan')]);self.assertIn('<svg',fig.to_svg())

    def test_numpy_masks_if_available_without_runtime_numpy_import(self):
        try:import numpy as np
        except ImportError:self.skipTest('numpy optional input')
        fig,ax=az.subplots();x=np.ma.array([-48,-47,-46,-45],mask=[0,0,1,0]);line,=ax.plot(x,[-24,-23,-22,-21])
        self.assertTrue(math.isnan(line.get_xdata()[2]));self.assertIn('<svg',fig.to_svg())

    def test_public_paths_compound_holes_bezier_gap_and_readonly(self):
        p=az.Path([(0,0),(1,0),(1,1),(0,1),(0,0),(.2,.2),(.8,.2),(.8,.8),(.2,.8),(0,0)],
                  [1,2,2,2,79,1,2,2,2,79])
        self.assertEqual(len(p.to_polylines()),2)
        with self.assertRaises(AttributeError):p.vertices=()
        curve=az.Path([(0,0),(.3,.8),(1,1)],[1,3,3]);self.assertGreater(len(curve.to_polylines()[0][0]),2)
        with self.assertRaises(ValueError):az.Path([(0,0),(1,1)],[1,4])
        fig,ax=az.subplots();patch=ax.add_patch(az.PathPatch(p,transform=ax.transAxes,facecolor='orange',hatch='//'))
        svg=fig.to_svg();self.assertIn('fill-rule="evenodd"',svg)
        patch.set_path(curve);patch.set_visible(False);self.assertFalse(patch.get_visible())

    def test_line_collection_batch_edits_and_style_cycles(self):
        fig,ax=az.subplots();ax.set_extent((-50,-40,-25,-15))
        c=az.LineCollection([[(-49,-24),(-48,-23)],[(-46,-21),(-44,-19)]],colors=['red','blue'],linewidths=[1,2],linestyles=['-','--'])
        ax.add_collection(c);self.assertIn('<svg',fig.to_svg())
        old=c.get_segments()
        with self.assertRaises(ValueError):c.set_segments([[(0,0),(1,2,3)]])
        self.assertEqual(c.get_segments(),old)
        c.set_segments([[(-49,-24),(-43,-18)]]);c.set_colors(['green']);c.set_linewidths([3])
        self.assertEqual(c._segment_style(0)['color'],'green')
        c.remove();self.assertNotIn(c,ax.layers)

    def test_family_cycles_fill_patches_and_independence(self):
        fig,ax=az.subplots();ax.set_prop_cycle(color=['red','blue'])
        a,=ax.fill([-49,-48,-49],[-24,-24,-23]);b,=ax.fill([-47,-46,-47],[-22,-22,-21])
        self.assertEqual((a.style['facecolor'],b.style['facecolor']),('red','blue'))
        patch=ax.add_patch(az.PathPatch(az.Path([(0,0),(1,0),(0,1),(0,0)],[1,2,2,79]),transform=ax.transAxes))
        self.assertEqual(patch.get_color(),'red')
        line,=ax.plot([-49,-48],[-24,-23]);self.assertEqual(line.get_color(),'red')
        self.assertIn('<svg',fig.to_svg())

    def test_calendar_ticks_timezones_leap_months_and_fractional_dates(self):
        from azimlib import dates as d
        local=dt.datetime(2024,2,29,12,tzinfo=dt.timezone(dt.timedelta(hours=-3)))
        n=d.date2num(local);self.assertEqual(d.num2date(n),local.astimezone(d.UTC))
        self.assertEqual(d.DateFormatter('%Y-%m-%d %H:%M')(n),'2024-02-29 15:00')
        lo,hi=d.date2num(dt.date(2024,1,31)),d.date2num(dt.date(2024,4,2))
        ticks=d.MonthLocator().tick_values(lo,hi)
        self.assertEqual([d.num2date(v).month for v in ticks],[2,3,4])
        self.assertLessEqual(len(d.AutoDateLocator(maxticks=7).tick_values(lo,hi)),7)
        self.assertGreater(len(d.AutoDateLocator().tick_values(n,n+.1)),1)
        with self.assertRaises(ValueError):d.DayLocator(interval=0)

    def test_numeric_scales_logs_and_map_coordinates_remain_degrees(self):
        from azimlib.scale import LinearScale,LogScale,SymLogScale
        for scale,values in ((LinearScale(),(-2,0,5)),(LogScale(),(.01,1,1000)),(SymLogScale(linthresh=2),(-100,-1,0,1,100))):
            for value in values:
                with self.subTest(scale=scale.name,value=value):self.assertAlmostEqual(scale.inverse(scale.forward(value)),value)
        with self.assertRaises(ValueError):LogScale().forward(-1)
        fig,ax=az.subplots();before=ax.get_extent()
        with self.assertRaises(ValueError):ax.set_yscale('log')
        self.assertEqual(ax.get_extent(),before);self.assertEqual(ax.get_yscale(),'linear')
        self.assertEqual(az.ticker.LogFormatterSciNotation()(1000),'10^3')

    def test_date_and_log_tickers_on_editable_colorbar(self):
        fig,ax=az.subplots();m=ax.scatter([-49,-45],[-23,-20],c=[1,100],norm=az.colors.LogNorm(1,100))
        bar=fig.colorbar(m,ax=ax);bar.locator=az.ticker.LogLocator();bar.formatter=az.ticker.LogFormatterSciNotation();bar.update_ticks()
        self.assertIn('10^',fig.to_svg())
        from azimlib.dates import MonthLocator,DateFormatter,date2num
        a,b=date2num(dt.date(2024,1,1)),date2num(dt.date(2024,4,1))
        m.set_norm(az.colors.Normalize(a,b));m.set_array([a,b]);bar.locator=MonthLocator();bar.formatter=DateFormatter('%b');bar.update_ticks()
        self.assertIn('Feb',fig.to_svg())

    def test_bearing_north_compass_history_and_cursor_inverse(self):
        fig,ax=az.subplots();ax.set_extent((-55,-35,-33,-3));ax.map('brazil',fit=False)
        north=ax.north_arrow();rose=ax.compass();nav=Navigation(fig)
        a,b=north.get_angle(),rose.get_angle();ax.set_bearing(40);nav.push()
        self.assertAlmostEqual(north.get_angle()-a,40,places=5);self.assertAlmostEqual(rose.get_angle()-b,40,places=5)
        meta=fig.to_scene().maps[0];self.assertEqual(meta['bearing'],40)
        from azimlib.viewport import Viewport
        vp=viewport_from_metadata(ax.projection,meta);p=(-45,-20)
        self.assertPair(vp.inverse(*vp.project(*p)),p)
        self.assertTrue(nav.back());self.assertEqual(ax.get_bearing(),0)
        self.assertTrue(nav.forward());self.assertEqual(ax.get_bearing(),40)
        self.assertIn('m.bearing',fig.to_html())
        before=ax.get_bearing()
        with self.assertRaises(ValueError):ax.set_bearing(float('nan'))
        self.assertEqual(ax.get_bearing(),before)

    def test_graticule_intersections_curved_and_rotated_frames(self):
        from azimlib.viewport import Viewport
        for p,bearing in ((az.Mercator(),30),(az.Stereographic(central_longitude=0),0),(az.Orthographic(),0)):
            with self.subTest(p=p.name):
                vp=Viewport(p,(-80,-60,80,60),(0,0,500,500),bearing=bearing)
                border=graticule_intersections(vp,'x',0)
                points=[q for values in border.values() for q in values]
                self.assertTrue(points)
                self.assertTrue(all(vp.inside(q) for q in points))

    def test_multiple_roots_layout_manual_axes_preserved_and_rollback(self):
        fig=az.figure(figsize=(12,5),layout='constrained')
        left=fig.add_gridspec(1,1,left=.02,right=.48,bottom=.12,top=.88);right=fig.add_gridspec(1,1,left=.52,right=.98,bottom=.12,top=.88)
        axes=[fig.add_subplot(left[0]),fig.add_subplot(right[0])]
        for i,ax in enumerate(axes):ax.set_extent((-55,-35,-33,-3));ax.set_title('Region '+str(i));ax.set_ylabel('Latitude')
        manual=fig.add_axes((.01,.01,.05,.08));old=manual.position
        self.assertIn('<svg',fig.to_svg());self.assertEqual(manual.position,old)
        self.assertLess(axes[0].position[0]+axes[0].position[2],axes[1].position[0])
        before=[a.position for a in axes];axes[1].set_title('W'*1000)
        with warnings.catch_warnings(record=True) as messages:
            warnings.simplefilter('always');fig.to_scene()
        self.assertTrue(messages);self.assertEqual([a.position for a in axes],before)

    def test_subfigures_regions_hierarchy_titles_shared_export_and_clear(self):
        fig=az.figure(figsize=(12,5),layout='constrained');left,right=fig.subfigures(1,2)
        a,b=left.subplots(),right.subplots();a.set_extent((-55,-35,-33,-3));b.set_extent((-60,-40,-35,-5))
        left.suptitle('West');right.suptitle('East')
        self.assertIs(a.figure,fig);self.assertIs(a.get_figure(root=True),fig)
        self.assertIs(left.canvas,fig.canvas);self.assertIn('West',fig.to_svg());self.assertIn('East',fig.to_svg())
        self.assertLess(a.position[0]+a.position[2],b.position[0])
        q=left.transSubfigure.transform_point((.5,.5));self.assertPair(left.transSubfigure.inverted().transform_point(q),(.5,.5))
        self.assertIn(left,fig.findobj());self.assertEqual(left.axes,[a])
        left.clear();self.assertNotIn(a,fig.axes);self.assertIn(b,fig.axes)
        fig.clear();self.assertEqual(fig.subfigs,[])

    def test_nested_subfigures_and_explicit_positions(self):
        fig=az.figure(figsize=(10,7));outer=fig.subfigures();top,bottom=outer.subfigures(2,1)
        a=top.add_axes((.1,.2,.7,.6));b=bottom.subplots()
        self.assertLess(b.position[1]+b.position[3],a.position[1])
        before=a.position;fig.set_size_inches(12,8);fig.to_scene();self.assertEqual(a.position,before)

    def test_compressed_layout_releases_equal_aspect_gaps(self):
        fig,axes=az.subplots(1,2,figsize=(12,4),layout='constrained')
        for ax in axes:ax.set_extent((-50,-45,-30,-10));ax.set_title('Regional map')
        a=fig.to_scene().maps;gap=a[1]['box'][0]-sum((a[0]['box'][0],a[0]['box'][2]))
        fig.set_layout_engine('compressed');b=fig.to_scene().maps;new=b[1]['box'][0]-b[0]['box'][0]-b[0]['box'][2]
        self.assertLess(new,gap);self.assertGreaterEqual(new,0)

    def test_free_text_edge_obstacle_and_opt_out(self):
        fig,ax=az.subplots(figsize=(6,5),layout='constrained');ax.set_extent((-50,-40,-25,-15))
        text=fig.text(.5,.96,'Fixed editorial caption',ha='center',va='top',fontsize=20)
        scene=fig.to_scene();top=scene.maps[0]['box'][1]
        text.set_in_layout(False);other=fig.to_scene().maps[0]['box'][1]
        self.assertGreater(top,other)

    def test_custom_legend_handler_symbol_live_edit_and_visibility(self):
        from azimlib.legend_handler import HandlerSymbol
        symbol=az.Symbol(az.Path([(0,0),(.5,1),(1,0),(0,0)],[1,2,2,79]))
        fig,ax=az.subplots();ax.set_extent((-50,-40,-25,-15))
        legend=ax.legend(handles=[symbol],labels=['Station'],handler_map={az.Symbol:HandlerSymbol(facecolor='purple')})
        svg=fig.to_svg();self.assertIn('Station',svg);self.assertIn('purple',svg)
        legend.set_visible(False);self.assertNotIn('Station',fig.to_svg())
        legend.set_visible(True);legend.get_texts()[0].set_text('New station');self.assertIn('New station',fig.to_svg())
        with self.assertRaises(TypeError):ax.legend(handles=[object()],labels=['bad'])

    def test_rotated_pan_preserves_span_and_collections_commit_atomically(self):
        from azimlib.navigation import drag_extent
        fig,ax=az.subplots();ax.set_extent((-50,-40,-25,-15));ax.set_bearing(45)
        vp=ax._transform_viewport();x,y,w,h=vp.box
        result=drag_extent(ax,vp,(x+w/2,y+h/2),(x+w/2+10,y+h/2+20))
        self.assertAlmostEqual(result[1]-result[0],10);self.assertAlmostEqual(result[3]-result[2],10)
        c=ax.add_collection(az.LineCollection([[(-49,-24),(-48,-23)]]));events=[];c.add_callback(lambda a:events.append(a))
        c.set(segments=[[(-46,-21),(-45,-20)]],colors=['green'],linewidths=[2])
        self.assertEqual(len(events),1);before=c.get_segments()
        with self.assertRaises(ValueError):c.set(segments=[[(-1,-1),(0,0)]],linewidths=[-1])
        self.assertEqual(c.get_segments(),before);self.assertEqual(len(events),1)

    def test_scientific_offsets_share_visible_scene_without_touching_crs(self):
        fig,ax=az.subplots();ax.set_extent((-46.630001,-46.629999,-23.550001,-23.549999))
        ax.xaxis.set_major_formatter(az.ticker.ScalarFormatter(useOffset=True))
        scene=fig.to_scene();offset=ax.xaxis.get_offset_text().get_text()
        self.assertTrue(offset);self.assertTrue(any(isinstance(p,Text) and p.text==offset for p in scene.items))
        self.assertEqual(ax.get_xlim(),(-46.630001,-46.629999))

    def test_default_light_view_is_clean_optional_and_respects_global_context(self):
        with az.style.context('default'):
            fig,ax=az.subplots();ax.map('brazil',facecolor='#f2f3f4',edgecolor='#75818c',linewidth=.6)
            self.assertEqual(fig.facecolor,'white');self.assertEqual(ax.facecolor,'white')
            self.assertFalse(any(l.kind=='grid' for l in ax.layers))
            for name in ('_legend','_scale_bar','_north','_compass','_overview','_colorbar'):self.assertIsNone(getattr(ax,name))
            self.assertIn('<svg',fig.to_svg())



    def test_inset_transforms_annotations_and_vector_cycles(self):
        fig,ax=az.subplots(figsize=(8,6));ax.set_extent((-54,-42,-28,-16))
        other=fig.add_axes((.01,.01,.1,.1));other.set_extent((-54,-42,-28,-16))
        ax.text(.5,.5,'Other axes',transform=other.transAxes);self.assertIn('Other axes',fig.to_svg())
        child=ax.inset((.6,.6,.3,.3));child.set_extent((-49,-45,-25,-21))
        q=child.transAxes.transform_point((.5,.5))
        self.assertPair(child.transAxes.inverted().transform_point(q),(.5,.5))
        note=child.annotate('Fractional',(.5,.5),xytext=(0,5),textcoords='offset points',transform=child.transAxes)
        note.set(xy=(.3,.3));self.assertIn('Fractional',fig.to_svg())
        note.set_transform(ax.transAxes);self.assertIn('Fractional',fig.to_svg())
        ax.set_prop_cycle(color=['red','green'])
        first=ax.quiver([-50],[-24],[1],[1]);ax.quiver([-50],[-24],[1],[1],color='black')
        second=ax.quiver([-50],[-24],[1],[1]);self.assertEqual([first.get_color(),second.get_color()],['red','green'])

    def test_line_collection_scalar_mapping_and_atomic_length(self):
        fig,ax=az.subplots();ax.set_extent((-50,-40,-25,-15))
        c=ax.add_collection(az.LineCollection([[(-49,-24),(-48,-23)],[(-47,-22),(-46,-21)]]))
        c.set(array=[0,1],cmap='viridis');self.assertNotEqual(c._segment_style(0)['color'],c._segment_style(1)['color'])
        bar=fig.colorbar(c);self.assertIn('<svg',fig.to_svg())
        before=c.get_segments()
        with self.assertRaises(ValueError):c.set(segments=[[(-49,-24),(-48,-23)]])
        self.assertEqual(c.get_segments(),before);bar.remove()

    def test_pending_rotated_tk_viewport_and_right_drag_keep_spans(self):
        from types import SimpleNamespace
        from azimlib.backends.tk import FigureWindow
        from azimlib.navigation import drag_extent
        fig,ax=az.subplots();ax.set_extent((-54,-42,-28,-16));ax.set_bearing(35)
        scene=fig.to_scene();window=object.__new__(FigureWindow);window.figure=fig;window.scene=scene
        ax.set_xlim(-53,-41);vp=window._viewport(0)
        self.assertEqual(vp.bearing,35);q=vp.project(-47,-22);self.assertPair(vp.inverse(*q),(-47,-22))
        ax.set_bearing(60);self.assertEqual(window._viewport(0).bearing,60)
        x,y,w,h=vp.box;start=(x+w/2,y+h/2)
        result=drag_extent(ax,vp,start,(start[0]+10,start[1]-10),button=3)
        self.assertLess(result[1]-result[0],12);self.assertLess(result[3]-result[2],12)
        for locator in (az.dates.DayLocator(),az.dates.AutoDateLocator()):
            with self.assertRaises(ValueError):locator.tick_values(0,float('inf'))

if __name__=='__main__':unittest.main()

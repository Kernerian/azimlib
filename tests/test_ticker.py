"""Own numeric tick algorithms, geographic labels and live axis contracts."""
import io,math,unittest
import azimlib as az
from azimlib import ticker as t
from azimlib.cm import ScalarMappable
from azimlib.colors import Normalize,LogNorm
from azimlib.scene import Text,Path

class TickerTests(unittest.TestCase):
    def tearDown(self):az.close('all')
    def test_regular_locators_include_outer_ticks(self):
        self.assertEqual(t.MultipleLocator(5).tick_values(-10,10),(-15,-10,-5,0,5,10,15))
        self.assertEqual(t.MultipleLocator(5,offset=2).tick_values(3,13),(2,7,12,17))
        self.assertEqual(t.MaxNLocator(4).tick_values(0,100),(0,25,50,75,100))
        self.assertEqual(t.MaxNLocator(4,prune='both').tick_values(0,100),(25,50,75))
        self.assertEqual(t.MaxNLocator(10,integer=True).tick_values(0,3),(0,1,2,3))
        self.assertEqual(t.FixedLocator([3,1]).tick_values(0,5),(3,1))
        self.assertEqual(t.NullLocator().tick_values(0,5),())
    def test_small_and_shifted_ranges_do_not_accumulate_drift(self):
        values=t.MultipleLocator(.1).tick_values(-.3,.3)
        self.assertAlmostEqual(values[4],0);self.assertEqual(len(values),9)
        values=t.MaxNLocator(4).tick_values(1_000_000,1_000_001)
        self.assertEqual(values,(1_000_000,1_000_000.25,1_000_000.5,1_000_000.75,1_000_001))
        self.assertTrue(all(math.isfinite(v) for v in t.MaxNLocator().tick_values(0,0)))
    def test_invalid_parameters_and_excessive_ticks_fail_before_allocation(self):
        for make in (lambda:t.MultipleLocator(0),lambda:t.FixedLocator([float('nan')]),lambda:t.MaxNLocator(0),lambda:t.MaxNLocator(steps=[2,1]),lambda:t.LogLocator(1)):
            with self.assertRaises(ValueError):make()
        with self.assertRaises(ValueError):t.MultipleLocator(.00001).tick_values(-180,180)
        with self.assertRaises(ValueError):t.LogLocator().tick_values(-1,10)
        locator=t.MultipleLocator(5)
        with self.assertRaises(ValueError):locator.set_params(base=0)
        self.assertEqual(locator.base,5)
    def test_formatters_have_value_position_and_context_contract(self):
        self.assertEqual(t.StrMethodFormatter('{x:.1f} [{pos}]')(2.25,3),'2.2 [3]')
        self.assertEqual(t.FormatStrFormatter('%.2f')(2.25),'2.25')
        self.assertEqual(t.FuncFormatter(lambda x,pos:f'{pos}: {x:g}')(2,1),'1: 2')
        self.assertEqual(t.FixedFormatter(['A','B']).format_ticks([10,20,30]),['A','B',''])
        self.assertEqual(t.NullFormatter()(0),'')
        self.assertEqual(t.ScalarFormatter()(-2),'−2')
    def test_geographic_dms_handles_rollover_and_hemispheres(self):
        longitude=t.LongitudeFormatter();latitude=t.LatitudeFormatter()
        self.assertEqual(longitude(-46.5),'46.5°W');self.assertEqual(latitude(-23.5),'23.5°S')
        self.assertEqual(longitude(0),'0°');self.assertEqual(longitude(180),'180°')
        self.assertEqual(t.LongitudeFormatter(dateline_direction_label=True)(-180),'180°W')
        self.assertEqual(t.LatitudeFormatter(dms=True)(-23.5),'23°30′S')
        self.assertEqual(t.LongitudeFormatter(dms=True)(46+59/60+59.99999/3600),'47°E')
        self.assertEqual(t.LatitudeFormatter(direction_label=False)(-2),'−2°')
    def test_live_locator_recomputes_on_zoom_and_grid_follows_ticks(self):
        fig,ax=az.subplots();ax.set_extent((-60,-40,-30,-10))
        locator=t.MultipleLocator(5);ax.xaxis.set_major_locator(locator)
        ax.yaxis.set_major_locator(t.MultipleLocator(5));ax.grid(labels=False)
        ax.xaxis.set_major_formatter(t.LongitudeFormatter())
        scene=fig.to_scene();self.assertIn('55°W',fig.to_svg())
        self.assertEqual(ax.get_xticks(),(-65,-60,-55,-50,-45,-40,-35))
        ax.set_xlim(-54,-46);self.assertEqual(ax.get_xticks(),(-55,-50,-45))
        locator.set_params(base=2);self.assertIn('52°W',fig.to_svg())
        self.assertEqual(len(scene.maps[0]['grid_indices']),10)
    def test_explicit_labels_and_formatter_replacement_are_consistent(self):
        fig,ax=az.subplots();ax.set_extent((-10,10,-10,10))
        labels=ax.set_xticks([-5,5],labels=['Left','Right'])
        self.assertIsInstance(ax.xaxis.get_major_locator(),t.FixedLocator)
        self.assertIsInstance(ax.xaxis.get_major_formatter(),t.FixedFormatter)
        labels[0].set_visible(False);self.assertNotIn('Left</text>',fig.to_svg())
        ax.xaxis.set_major_formatter('{x:.1f}°');self.assertNotIn('Right</text>',fig.to_svg())
        self.assertIn('5.0°',fig.to_svg())
        ax.xaxis.set_major_locator(t.NullLocator());self.assertEqual(ax.get_xticks(),())
        ax.yaxis.set_major_formatter(t.NullFormatter());self.assertNotIn('−10</text>',fig.to_svg())
    def test_objects_are_axis_owned_and_invalid_replacement_is_atomic(self):
        fig,axs=az.subplots(1,2);first,second=axs.flat;locator=t.MultipleLocator(5)
        first.xaxis.set_major_locator(locator)
        with self.assertRaises(ValueError):second.xaxis.set_major_locator(locator)
        self.assertIs(first.xaxis.get_major_locator(),locator)
        before=first.xaxis.get_major_formatter()
        with self.assertRaises(TypeError):first.xaxis.set_major_formatter(object())
        self.assertIs(before,first.xaxis.get_major_formatter())
    def test_colorbar_custom_objects_survive_clim_and_reset_on_new_norm(self):
        fig,ax=az.subplots();layer=ax.scatter([0,1],[0,1],c=[0,100],norm=Normalize(0,100))
        bar=fig.colorbar(layer);locator=t.MultipleLocator(25);formatter=t.StrMethodFormatter('{x:.0f}%')
        bar.locator=locator;bar.formatter=formatter;self.assertIn('25%',fig.to_svg())
        layer.set_clim(0,200);self.assertIs(bar.locator,locator);self.assertIn('175%',fig.to_svg())
        bar.set(orientation='horizontal',location='bottom');self.assertIs(bar.ax.xaxis.get_major_formatter(),formatter)
        bar.update_normal(ScalarMappable(Normalize(0,1)))
        self.assertIsNot(bar.locator,locator);self.assertIsInstance(bar.formatter,t.ScalarFormatter)
        self.assertNotIn('25%',fig.to_svg())
        bar.update_normal(layer);bar.locator=t.MultipleLocator(50)
        previous=bar.locator;layer.set_norm(LogNorm(1,1000))
        self.assertIsNot(bar.locator,previous);self.assertIsInstance(bar.locator,t.LogLocator)
        self.assertEqual(bar.ax.yaxis.get_majorticklocs(),())  # Horizontal bar has a short Y axis.
    def test_log_colorbar_cax_and_legacy_formats_work(self):
        fig,ax=az.subplots();cax=fig.add_axes((.9,.2,.03,.6))
        bar=fig.colorbar(ScalarMappable(LogNorm(1,1000)),cax=cax)
        self.assertIsInstance(bar.locator,t.LogLocator)
        cax.yaxis.set_major_formatter(t.FuncFormatter(lambda x,pos:f'{x:g} units'))
        self.assertIn('100 units',fig.to_svg());self.assertIs(bar.formatter,cax.yaxis.get_major_formatter())
        bar.formatter='%.1f';self.assertIn('100.0',fig.to_svg())
        bar.formatter=lambda x:f'{x:g}U';self.assertIn('10U',fig.to_svg())
        bar.formatter='.2f';self.assertIn('10.00',fig.to_svg())
        cax.yaxis.set_major_locator(t.NullLocator());self.assertEqual(bar.get_ticks(),())
    def test_exports_preserve_geographic_labels(self):
        fig,ax=az.subplots(figsize=(4,4));ax.state('SP')
        ax.xaxis.set_major_locator(t.MultipleLocator(2));ax.yaxis.set_major_locator(t.MultipleLocator(2))
        ax.xaxis.set_major_formatter(t.LongitudeFormatter());ax.yaxis.set_major_formatter(t.LatitudeFormatter())
        output=io.BytesIO();fig.savefig(output,format='png')
        self.assertTrue(output.getvalue().startswith(b'\x89PNG'));self.assertIn('°W',fig.to_svg())
    def test_filled_states_do_not_cover_the_grid_or_a_later_state_highlight(self):
        fig,ax=az.subplots();states=ax.states(facecolor='#eeeeee');highlight=ax.state('SP',facecolor='red')
        grid=ax.grid(step=2)
        self.assertEqual(states.zorder,highlight.zorder)
        self.assertLess(states.zorder,grid.zorder)
        scene=fig.to_scene();grid_start=min(scene.maps[0]['grid_indices'])
        red=[i for i,item in enumerate(scene.items) if isinstance(item,Path) and item.style.get('fill')=='red']
        self.assertTrue(red);self.assertLess(max(red),grid_start)
        override=ax.states(fc='white',zorder=7);self.assertEqual(override.zorder,7)
    def test_portable_tick_export_is_serializable_and_excludes_python_callbacks(self):
        import json
        fig,ax=az.subplots();ax.set_extent((-60,-40,-30,-10))
        ax.xaxis.set_major_locator(t.MultipleLocator(2))
        ax.xaxis.set_major_formatter(t.LongitudeFormatter(dms=True))
        metadata=fig.to_scene().maps[0]
        self.assertIn('portable_ticks',metadata);json.dumps(metadata)
        self.assertIn('portable_ticks',fig.to_html())
        ax.xaxis.set_major_formatter(lambda x,pos:str(x))
        self.assertNotIn('portable_ticks',fig.to_scene().maps[0])
        self.assertIn('custom_ticks',fig.to_html())

if __name__=='__main__':unittest.main()

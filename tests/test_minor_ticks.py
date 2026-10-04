"""Minor positions, independent styling/grids and live colorbar contracts."""
import io,json,math,unittest
from pathlib import Path as FilePath
import azimlib as azl
from azimlib import ticker as t
from azimlib.colors import Normalize,LogNorm
from azimlib.cm import ScalarMappable
from azimlib.scene import Path,Text


class MinorTickTests(unittest.TestCase):
    def setUp(self):
        self.fig,self.ax=azl.subplots(figsize=(6,6))
        self.ax.set_extent((-10,10,-10,10))
        self.ax.xaxis.set_major_locator(t.MultipleLocator(5))
        self.ax.yaxis.set_major_locator(t.MultipleLocator(5))
    def tearDown(self):azl.close('all')
    def test_defaults_are_off_and_on_does_not_enable_grid_or_labels(self):
        self.assertIsInstance(self.ax.xaxis.get_minor_locator(),t.NullLocator)
        before=[p.text for p in self.fig.to_scene().items if isinstance(p,Text)]
        self.ax.minorticks_on()
        self.assertEqual(self.ax.get_xticks(minor=True),(-9,-8,-7,-6,-4,-3,-2,-1,1,2,3,4,6,7,8,9))
        self.assertEqual(before,[p.text for p in self.fig.to_scene().items if isinstance(p,Text)])
        self.assertFalse(any(l.kind=='grid' for l in self.ax.layers))
        self.ax.minorticks_off();self.assertEqual(self.ax.get_yticks(minor=True),())
    def test_positions_match_saved_matplotlib_reference(self):
        fixture=json.loads((FilePath(__file__).resolve().parents[1]/'docs/minor-ticker-reference.json').read_text())
        for case in fixture['axis']:
            with self.subTest(case=case):
                self.ax.set_xlim(*case['limits'])
                self.ax.xaxis.set_major_locator(t.MultipleLocator(case['step']))
                self.ax.xaxis.set_minor_locator(t.AutoMinorLocator(case['n']))
                actual=self.ax.get_xticks(minor=True)
                self.assertEqual(len(actual),len(case['matplotlib']))
                for a,b in zip(actual,case['matplotlib']):self.assertAlmostEqual(a,b)
    def test_initial_axis_queries_use_the_actual_equal_aspect_tick_space(self):
        fig,ax=azl.subplots(figsize=(3,6));ax.set_extent((-10,10,-10,10))
        ax.minorticks_on()
        direct=ax.xaxis.get_majorticklocs()
        self.assertEqual(direct,ax.get_xticks())
        self.assertEqual(ax.xaxis.get_minorticklocs(),ax.get_xticks(minor=True))
    def test_major_changes_zoom_and_clear_recalculate_minor_positions(self):
        self.ax.minorticks_on();self.ax.set_xlim(-3,3)
        self.assertEqual(self.ax.get_xticks(minor=True),(-3,-2,-1,1,2,3))
        self.ax.xaxis.set_major_locator(t.MultipleLocator(2))
        self.assertTrue(all(any(math.isclose(v,k/2) for k in range(-6,7)) for v in self.ax.get_xticks(minor=True)))
        self.ax.clear();self.assertEqual(self.ax.get_xticks(minor=True),())
    def test_overlapping_ticks_removed_with_configurable_tolerance(self):
        self.ax.xaxis.set_minor_locator(t.FixedLocator([0,1,5+1e-6]))
        self.assertEqual(self.ax.get_xticks(minor=True),(1,))
        self.ax.xaxis.remove_overlapping_locs=False
        self.assertEqual(self.ax.get_xticks(minor=True),(0,1,5+1e-6))
    def test_minor_styles_are_independent_both_updates_both(self):
        self.ax.minorticks_on();self.ax.tick_params(which='minor',length=2,color='red',width=.5)
        scene=self.fig.to_scene()
        red=[p for p in scene.items if isinstance(p,Path) and p.style.get('stroke')=='red']
        self.assertEqual(len(red),32)
        self.assertTrue(all(math.isclose(math.dist(*p.paths[0]),2*100/72) for p in red))
        self.assertEqual(self.ax._tick_params['x']['color'],'black')
        self.ax.tick_params(which='both',color='blue');self.assertEqual(self.ax._minor_tick_params['y']['color'],'blue')
    def test_fixed_minor_labels_edit_and_formatter_replacement(self):
        labels=self.ax.set_xticks([0,1,2],labels=['Overlap','One','Two'],minor=True)
        self.assertNotIn('Overlap</text>',self.fig.to_svg());self.assertIn('One</text>',self.fig.to_svg())
        labels[1].set_text('Changed');self.assertIn('Changed</text>',self.fig.to_svg())
        labels[2].set_visible(False);self.assertNotIn('Two</text>',self.fig.to_svg())
        self.ax.xaxis.set_minor_formatter(lambda x,pos:f'm{x:g}')
        self.assertNotIn('Changed</text>',self.fig.to_svg());self.assertIn('m1</text>',self.fig.to_svg())
        self.assertIsInstance(self.ax.xaxis.get_major_formatter(),t.ScalarFormatter)
    def test_grid_groups_axes_and_visibility_remain_independent(self):
        self.ax.minorticks_on()
        major=self.ax.grid(True,which='major',axis='x',color='red')
        minor=self.ax.grid(True,which='minor',axis='y',color='blue',linewidth=.3)
        scene=self.fig.to_scene();specs=scene.maps[0]['grid_specs']
        self.assertEqual([(s['which'],s['axis'],len(s['indices'])) for s in specs],[('major','x',5),('minor','y',16)])
        self.ax.grid(False,which='minor');self.assertIn(major,self.ax.layers);self.assertNotIn(minor,self.ax.layers)
        self.ax.grid(which='major',axis='y');self.assertEqual(set(self.ax.layers[-1].options['axes_config']),{'x','y'})
        self.ax.grid(False,which='both');self.assertFalse(any(l.kind=='grid' for l in self.ax.layers))
        with self.assertWarns(UserWarning):self.ax.grid(False,which='minor',color='gray')
        self.assertTrue(any(l.kind=='grid' and l.options['which']=='minor' for l in self.ax.layers))
    def test_minor_grid_does_not_create_minor_ticks_and_fixed_step_is_explicit(self):
        self.ax.grid(True,which='minor',labels=False)
        self.assertEqual(self.fig.to_scene().maps[0]['grid_indices'],[])
        self.assertEqual(self.ax.get_xticks(minor=True),())
        self.ax.grid(True,which='minor',axis='x',step=1)
        specs=self.fig.to_scene().maps[0]['grid_specs'];self.assertEqual(len(specs[0]['indices']),16)
        self.ax.layers[-1].set(color='purple')
        self.assertTrue(all(s['style']['stroke']=='purple' for s in self.fig.to_scene().maps[0]['grid_specs']))
    def test_minor_locator_ownership_and_invalid_configuration_are_atomic(self):
        locator=t.AutoMinorLocator(4);self.ax.xaxis.set_minor_locator(locator)
        with self.assertRaises(ValueError):self.ax.yaxis.set_minor_locator(locator)
        for n in (0,-1,True,1.5,'bad'):
            with self.assertRaises(ValueError):t.AutoMinorLocator(n)
        before=self.ax._tick_params['x'].copy()
        with self.assertRaises(ValueError):self.ax.tick_params(which='both',length=-1)
        self.assertEqual(before,self.ax._tick_params['x'])
        with self.assertRaises(NotImplementedError):locator.tick_values(-1,1)
        with self.assertRaises(ValueError):self.ax.grid(which='bad')
    def test_minor_rc_defaults_and_grid_scope_apply_after_clear(self):
        with azl.rc_context({'xtick.minor.visible':True,'xtick.minor.ndivs':2,'xtick.minor.size':1.5,
                             'axes.grid':True,'axes.grid.which':'minor','axes.grid.axis':'x'}):
            fig,ax=azl.subplots();ax.set_extent((-10,10,-10,10));ax.xaxis.set_major_locator(t.MultipleLocator(5))
            self.assertEqual(ax.get_xticks(minor=True),(-7.5,-2.5,2.5,7.5))
            self.assertEqual(ax.get_yticks(minor=True),())
            self.assertEqual(ax._minor_tick_params['x']['length'],1.5)
            ax.clear();self.assertEqual(set(ax.layers[-1].options['axes_config']),{'x'})
            self.assertEqual(ax.layers[-1].options['which'],'minor')
    def test_colorbar_minor_contracts_and_saved_reference(self):
        fixture=json.loads((FilePath(__file__).resolve().parents[1]/'docs/minor-ticker-reference.json').read_text())
        for case in fixture['colorbars']:
            fig,ax=azl.subplots();bar=fig.colorbar(ScalarMappable(LogNorm(1,1000) if case['logarithmic'] else Normalize(0,100)),ax=ax,orientation=case['orientation'])
            if not case['logarithmic']:bar.locator=t.MultipleLocator(25)
            bar.minorticks_on();actual=bar.get_ticks(minor=True)
            self.assertEqual(len(actual),len(case['matplotlib']))
            for a,b in zip(actual,case['matplotlib']):self.assertAlmostEqual(a,b)
            short=bar.ax.xaxis if bar.orientation=='vertical' else bar.ax.yaxis
            self.assertEqual(short.get_minorticklocs(),())
            bar.minorticks_off();self.assertEqual(bar.get_ticks(minor=True),())
    def test_colorbar_minor_labels_cax_orientation_clim_norm_and_styles(self):
        cax=self.fig.add_axes((.9,.2,.03,.6));mapped=ScalarMappable(Normalize(0,10))
        bar=self.fig.colorbar(mapped,cax=cax);bar.locator=t.MultipleLocator(5)
        cax.set_yticks([0,1,2],labels=['Overlap','Small','Medium'],minor=True)
        self.assertIn('Small</text>',self.fig.to_svg());self.assertNotIn('Overlap</text>',self.fig.to_svg())
        locator=bar.minorlocator;mapped.set_clim(0,20);self.assertIs(bar.minorlocator,locator)
        bar.set(orientation='horizontal',location='bottom');self.assertIs(bar.ax.xaxis.get_minor_locator(),locator)
        bar.ax.tick_params(which='minor',color='red',length=2,direction='inout')
        scene=self.fig.to_scene();red=[p for p in scene.items if isinstance(p,Path) and p.style.get('stroke')=='red']
        self.assertEqual(len(red),2);self.assertTrue(all(math.isclose(math.dist(*p.paths[0]),2*100/72) for p in red))
        mapped.set_norm(LogNorm(1,1000));self.assertIsInstance(bar.minorlocator,t.LogLocator)
        self.assertIsNot(bar.minorlocator,locator);self.assertNotIn('Small</text>',self.fig.to_svg())
        mapped.set_norm(Normalize(0,1));self.assertIsInstance(bar.minorlocator,t.NullLocator)
    def test_png_svg_html_and_dpi_preserve_minor_metadata(self):
        self.ax.minorticks_on();self.ax.grid(which='both',labels=False)
        output=io.BytesIO();self.fig.savefig(output,format='png',dpi=150)
        self.assertTrue(output.getvalue().startswith(b'\x89PNG'))
        self.assertIn('portable_minor_ticks',self.fig.to_html())
        meta=self.fig.to_scene().scaled(1.5).maps[0];self.assertEqual(meta['pixel_ratio'],1.5)
        self.assertEqual(meta['tick_settings']['minor']['x']['length'],2)
        self.ax.xaxis.set_minor_formatter(lambda x,pos:str(x))
        self.assertNotIn('portable_ticks',self.fig.to_scene().maps[0])


if __name__=='__main__':unittest.main()

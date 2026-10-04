"""Scientific labels, editable offset artists and physical marker/layout rules."""
import importlib.util,json,math,unittest
from pathlib import Path
import azimlib as azl
from azimlib import ticker as t
from azimlib.cm import ScalarMappable
from azimlib.colors import Normalize
from azimlib.scene import Scene,Path as ScenePath,Text
from azimlib.typography import POINT,text_vertical_bounds
from azimlib.styles import text_style
from azimlib.layout_engine import primitive_bounds,union_bounds
from azimlib.render_map import _marker,_text

ROOT=Path(__file__).resolve().parents[1]

class NumericFormattingTests(unittest.TestCase):
    def setUp(self):azl.ioff();azl.rcdefaults();self.fig,self.ax=azl.subplots()
    def tearDown(self):azl.close('all');azl.rcdefaults();azl.ioff()
    def texts(self):return [item for item in self.fig.to_scene().items if isinstance(item,Text)]
    def test_recorded_actual_matplotlib_numeric_contracts(self):
        spec=importlib.util.spec_from_file_location('numeric_reference',ROOT/'tools/inspect_numeric_formatting.py')
        tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)
        report=json.loads((ROOT/'docs/numeric-formatting-reference.json').read_text(encoding='utf-8'))
        for name,contract in tool.contracts(t).items():
            with self.subTest(name=name):self.assertEqual(contract,report['matplotlib'][name])
    def test_marker_geometry_matches_native_bounds_without_a_backend(self):
        report=json.loads((ROOT/'docs/numeric-formatting-reference.json').read_text(encoding='utf-8'))
        for marker,bounds in report['marker_bounds'].items():
            with self.subTest(marker=marker):
                scene=Scene(100,100);_marker((0,0),1/POINT,dict(marker=marker),scene,None)
                item=scene.items[0]
                if isinstance(item,ScenePath):
                    points=[p for part in item.paths for p in part]
                    left=min(p[0] for p in points);top=min(p[1] for p in points)
                    own=(left,top,max(p[0] for p in points)-left,max(p[1] for p in points)-top)
                else:own=(-item.r,-item.r,2*item.r,2*item.r)
                expected=(bounds[0],-bounds[1]-bounds[3],bounds[2],bounds[3])
                for a,b in zip(own,expected):self.assertAlmostEqual(a,b,places=7)
    def test_font_linebox_titles_accents_alignment_rotation_against_reference(self):
        report=json.loads((ROOT/'docs/numeric-formatting-reference.json').read_text(encoding='utf-8'))
        self.assertEqual(len(report['text_layout']),96)
        for row in report['text_layout']:
            with self.subTest(text=row['text'],size=row['fontsize'],weight=row['fontweight'],rotation=row['rotation'],va=row['va']):
                scene=Scene(400,400);style=text_style({key:row[key] for key in ('fontsize','fontweight','rotation','va')})
                # This older fixture explicitly requests rotation_mode=anchor
                # in Matplotlib; now specify that same mode in the own API.
                style.update(anchor='middle',rotation_mode='anchor');_text(scene,0,0,row['text'],style)
                actual=union_bounds(primitive_bounds(p) for p in scene.items)
                # FT hinted advance widths and our unhinted metrics differ;
                # vertical font metrics and block anchoring are the target.
                # Accented glyph hinting produces up to 1.34 logical pixels
                # of difference in these recorded Agg states.
                horizontal=0 if row['rotation']==90 else 1
                dimension=2 if row['rotation']==90 else 3
                self.assertAlmostEqual(actual[horizontal],row['bounds'][horizontal],delta=1.5)
                self.assertAlmostEqual(actual[dimension],row['bounds'][dimension],delta=1.5)
    def test_multiline_baseline_places_last_line_at_anchor(self):
        scene=Scene(400,400);_text(scene,100,100,'Título\nFoco',text_style({'fontsize':12,'va':'baseline'}))
        self.assertAlmostEqual(scene.items[-1].y,100)
        self.assertLess(scene.items[0].y,100)
    def test_rebuilt_legend_copies_hidden_symbol_but_preserves_label(self):
        from azimlib.legend_layout import entries
        line=self.ax.plot([-52,-48],[-24,-20],marker='D',label='Trajeto C')[0]
        first=self.ax.legend();line.set_visible(False)
        self.assertTrue(entries(first)[0][1][0][0]['_legend_visible'])
        second=self.ax.legend();self.assertFalse(entries(second)[0][1][0][0]['_legend_visible'])
        self.assertEqual(second.get_texts()[0].get_text(),'Trajeto C')
        line.set_visible(True);self.assertFalse(entries(second)[0][1][0][0]['_legend_visible'])
    def test_diamond_narrow_diamond_rotation_and_edges(self):
        for marker,rotation,ratio in [('D',0,1),('d',0,.6),('d',90,1/.6)]:
            with self.subTest(marker=marker,rotation=rotation):
                scene=Scene(100,100);_marker((30,40),8,dict(marker=marker,rotation=rotation,markeredgewidth=.25),scene,None)
                item=scene.items[0];xs,ys=zip(*item.paths[0])
                self.assertAlmostEqual((max(xs)-min(xs))/(max(ys)-min(ys)),ratio)
        for marker in ('+','x'):
            scene=Scene(100,100);_marker((0,0),6,dict(marker=marker,markeredgewidth=.25,markeredgecolor='red'),scene,None)
            self.assertAlmostEqual(scene.items[0].style['stroke_width'],.25*POINT)
            self.assertEqual(scene.items[0].style['stroke'],'red')
        line=self.ax.plot([-52,-48],[-24,-20],'d')[0];self.assertEqual(line.get_marker(),'d')
    def test_axis_labels_defaults_and_labelpad_scale_in_points(self):
        self.ax.set_extent((-54,-42,-28,-16));x=self.ax.set_xlabel('Longitude');y=self.ax.set_ylabel('Latitude')
        self.assertEqual((x.get_ha(),x.get_va()),('center','top'))
        self.assertEqual((y.get_ha(),y.get_va()),('center','bottom'))
        before={item.text:item for item in self.texts() if item.text in ('Longitude','Latitude')}
        self.ax.set_xlabel('Longitude',labelpad=10);self.ax.set_ylabel('Latitude',labelpad=10)
        after={item.text:item for item in self.texts() if item.text in before}
        self.assertAlmostEqual(after['Longitude'].y-before['Longitude'].y,6*POINT)
        self.assertAlmostEqual(before['Latitude'].x-after['Latitude'].x,6*POINT)
        self.fig.set_dpi(200)
        doubled={item.text:item for item in self.texts() if item.text in before}
        self.assertAlmostEqual(doubled['Latitude'].x,2*after['Latitude'].x)
        self.assertAlmostEqual(doubled['Longitude'].y,2*after['Longitude'].y)
    def test_both_axis_labels_reserve_font_linebox_space(self):
        self.ax.set_extent((-54,-42,-28,-16));self.ax.set_xlabel('Longitude');self.ax.set_ylabel('Latitude')
        self.ax.set_xticks([-52,-48,-44],['52°W','48°W','44°W']);self.ax.set_yticks([-26,-22,-18],['26°S','22°S','18°S'])
        texts=self.texts();label=next(item for item in texts if item.text=='Latitude')
        ticks=[primitive_bounds(item) for item in texts if item.text.endswith('°S')]
        gap=min(box[0] for box in ticks)-(primitive_bounds(label)[0]+primitive_bounds(label)[2])
        self.assertAlmostEqual(gap,4*POINT)
        xlabel=next(item for item in texts if item.text=='Longitude')
        tick=next(item for item in texts if item.text=='48°W')
        xlabelbox=primitive_bounds(xlabel);tickbox=primitive_bounds(tick)
        self.assertAlmostEqual(xlabelbox[1]-tickbox[1]-tickbox[3],4*POINT)
    def test_rc_labelpad_and_formatter_configuration_are_snapshots(self):
        with azl.rc_context({'axes.labelpad':8,'axes.formatter.limits':(-3,4),'axes.formatter.useoffset':False}):
            fig,ax=azl.subplots()
        self.assertEqual(ax._labelpad,{'x':8,'y':8})
        self.assertEqual(ax.xaxis.get_major_formatter()._powerlimits,(-3,4))
        self.assertFalse(ax.xaxis.get_major_formatter().get_useOffset())
        for changes in ({'axes.labelpad':math.nan},{'axes.formatter.limits':(1,)},{'axes.formatter.offset_threshold':0}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):azl.rcParams.update(changes)
    def test_scalar_offset_artist_updates_and_hides_independently(self):
        self.ax.set_extent((-46.000008,-46,-23.000008,-23))
        self.ax.set_xticks([-46.000008,-46.000004,-46]);offset=self.ax.xaxis.get_offset_text()
        offset.set(color='red',fontsize=8)
        texts=self.texts();self.assertTrue(offset.get_text());self.assertIn(offset.get_text(),[p.text for p in texts])
        self.assertIs(offset.get_figure(),self.fig);self.assertIn(offset,self.fig.findobj())
        offset.set_visible(False);self.assertNotIn(offset.get_text(),[p.text for p in self.texts()])
        self.ax.ticklabel_format(axis='x',style='plain',useOffset=False)
        self.texts();self.assertEqual(offset.get_text(),'')
        self.assertIn('-46.000004'.replace('-','−'),[p.text for p in self.texts()])
    def test_ticklabel_format_validates_all_axes_before_mutation(self):
        original=self.ax.xaxis.get_major_formatter();self.fig._draw_complete()
        self.ax.yaxis.set_major_formatter(t.FuncFormatter(lambda value,pos:str(value)))
        self.fig._draw_complete()
        with self.assertRaises(AttributeError):self.ax.ticklabel_format(style='plain',useOffset=False)
        self.assertTrue(original._scientific);self.assertTrue(original.get_useOffset());self.assertFalse(self.fig.stale)
        with self.assertRaises(ValueError):self.ax.ticklabel_format(axis='x',style='plain',scilimits=(1,))
        self.assertTrue(original._scientific)
        with self.assertRaises(NotImplementedError):self.ax.ticklabel_format(axis='x',style='plain',useMathText=True)
        self.assertTrue(original._scientific)
    def test_direct_formatter_edits_notify_shared_axis_and_pyplot(self):
        import azimlib.pyplot as plt
        fig,axes=azl.subplots(1,2,sharex=True)
        fig._draw_complete();fmt=axes[0].xaxis.get_major_formatter();fmt.set_useOffset(False)
        self.assertTrue(fig.stale);self.assertIs(fmt,axes[1].xaxis.get_major_formatter())
        self.assertTrue(axes[1].xaxis.formatter_explicit)
        azl.sca(axes[0]);plt.ticklabel_format(axis='x',scilimits=(3,3))
        self.assertEqual(fmt._powerlimits,(3,3))
    def test_colorbars_all_locations_offsets_editing_and_clim(self):
        for location in ('left','right','top','bottom'):
            with self.subTest(location=location):
                fig,ax=azl.subplots();ax.set_extent((-54,-42,-28,-16))
                mapped=ScalarMappable(norm=Normalize(0,2e6));bar=fig.colorbar(mapped,ax=ax,location=location,label='Valor sintético')
                axis=bar.ax.yaxis if bar.orientation=='vertical' else bar.ax.xaxis
                offset=axis.get_offset_text();offset.set(color='purple',fontsize=8)
                self.assertIn('1e6',[p.text for p in fig.to_scene().items if isinstance(p,Text)])
                self.assertEqual(offset.get_text(),'1e6');self.assertIs(offset.get_figure(),fig)
                mapped.set_clim(0,2e7);fig.to_scene();self.assertEqual(offset.get_text(),'1e7')
                bar.ax.ticklabel_format(style='plain',useOffset=False);fig.to_scene();self.assertEqual(offset.get_text(),'')
                azl.close(fig)
    def test_colorbar_cax_and_orientation_keep_owned_offset_handle(self):
        self.ax.set_extent((-54,-42,-28,-16));cax=self.fig.add_axes((.85,.2,.03,.6))
        mapped=ScalarMappable(norm=Normalize(0,2e6));bar=self.fig.colorbar(mapped,cax=cax,ax=self.ax)
        self.assertIs(cax.yaxis.get_offset_text(),bar.ax.yaxis.get_offset_text())
        cax.set_ylabel('Valor',labelpad=9);self.assertEqual(bar.labelpad,9)
        offset=bar.ax.yaxis.get_offset_text();offset.set(color='purple');bar.set(orientation='horizontal',location='bottom')
        self.assertIs(offset,bar.ax.xaxis.get_offset_text());self.fig.to_scene();self.assertEqual(offset.text,'1e6')
        mapped.set_norm(Normalize(0,1));self.fig.to_scene();self.assertEqual(offset.text,'')
        bar.remove();self.assertIsNone(offset.get_figure())
    def test_tick_params_changes_offset_style_and_clear_detaches(self):
        offset=self.ax.yaxis.get_offset_text();self.ax.tick_params(axis='y',labelsize=8,labelcolor='red')
        self.assertEqual((offset.get_fontsize(),offset.get_color()),(8,'red'))
        self.ax.clear();self.assertIsNone(offset.get_figure());self.assertIsNot(offset,self.ax.yaxis.get_offset_text())
    def test_engineering_formatter_units_and_validation(self):
        self.assertEqual(t.EngFormatter(unit='m')(1500),'1.5 km')
        self.assertEqual(t.EngFormatter()(0),'0');self.assertEqual(t.EngFormatter(sep='')(2e6),'2M')
        for kwargs in ({'useOffset':True},{'useMathText':True},{'usetex':True}):
            with self.assertRaises(NotImplementedError):t.EngFormatter(**kwargs)
        for places in (-1,True,31):
            with self.assertRaises(ValueError):t.EngFormatter(places=places)
    def test_locale_unicode_minus_and_explicit_unsupported_typesetting(self):
        fmt=t.ScalarFormatter(useLocale=True,useOffset=False)
        self.assertEqual(fmt.format_ticks([0,.25,.5]),['0.00','0.25','0.50'])
        with azl.rc_context({'axes.unicode_minus':False}):self.assertEqual(t.ScalarFormatter()(-2),'-2')
        for kwargs in ({'useMathText':True},{'usetex':True}):
            with self.assertRaises(NotImplementedError):t.ScalarFormatter(**kwargs)
    def test_scientific_html_retains_static_labels_and_export_has_no_ui(self):
        self.ax.set_extent((-46.000008,-46,-23.000008,-23));scene=self.fig.to_scene()
        self.assertTrue(scene.maps[0]['custom_ticks']);self.assertNotIn('portable_ticks',scene.maps[0])
        svg=self.fig.to_svg();self.assertIn('1e',svg);self.assertNotIn('<script',svg)
        self.assertIn('1e',self.fig.to_html())

if __name__=='__main__':unittest.main()

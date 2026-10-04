"""Fail-before-commit and own representation invariants across editable artists."""
import importlib.util,io,json,unittest
from pathlib import Path
import azimlib as azl
from azimlib.colors import Normalize
from azimlib.styles import style_dict,path_style
from azimlib.scene import Text

ROOT=Path(__file__).resolve().parents[1]


class ArtistValidationTests(unittest.TestCase):
    def setUp(self):
        azl.ioff();self.fig,self.ax=azl.subplots(figsize=(4,4))
        self.ax.set_extent((-54,-42,-28,-16))
    def tearDown(self):azl.close('all');azl.ioff()

    def test_selected_setter_states_match_actual_reference(self):
        spec=importlib.util.spec_from_file_location('artist_probe',ROOT/'tools/inspect_artist_validation.py')
        probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
        report=json.loads((ROOT/'docs/artist-validation-reference.json').read_text(encoding='utf-8'))
        self.assertEqual(probe.inspect(azl),report['reference'])

    def test_numeric_style_values_have_owned_renderable_representation(self):
        keys=('linewidth','arrowsize','markersize','fontsize','halo_width','markeredgewidth','hatch_linewidth',
              'hatch_spacing','alpha','fill_alpha','edge_alpha','zorder','rotation','priority','curved')
        for key in keys:
            with self.subTest(key=key):
                result=style_dict({key:'0.5'})
                self.assertIsInstance(result[key],float);self.assertEqual(result[key],.5)
                for bad in ('nan','inf','-inf'):
                    with self.assertRaises(ValueError):style_dict({key:bad})

    def test_line_generator_dash_is_copied_once_and_external_lists_do_not_mutate_style(self):
        lengths=[3,2,1,2]
        line,=self.ax.plot([-52,-48],[-25,-21],linestyle=lengths)
        lengths[0]=99;self.assertEqual(line.get_linestyle(),(3.,2.,1.,2.))
        line.set(linestyle=(v for v in (4,2)),linewidth='1.2')
        first=self.fig.to_svg();self.assertEqual(first,self.fig.to_svg())
        self.assertIn('stroke-dasharray',first);self.assertEqual(line.get_linestyle(),(4.,2.))

    def test_contour_per_level_dash_patterns_are_detached_from_input(self):
        lengths=[3,2]
        contour=self.ax.contour([-54,-48,-42],[-28,-22,-16],[[0,1,2]]*3,levels=[.5,1.5],linestyles=[lengths])
        lengths[0]=99;self.assertEqual(contour.get_linestyles(),[(3.,2.),(3.,2.)])
        contour.set(linestyles=[(v for v in (4,1))]);self.assertEqual(contour.get_linestyles(),[(4.,1.),(4.,1.)])
        self.fig.to_svg()

    def test_font_failures_preserve_text_positions_contents_and_dirty_state(self):
        artists=[self.ax.set_title('Before'),self.ax.text(-50,-22,'Before'),
                 self.ax.annotate('Before',(-50,-22),xytext=(10,10)),self.fig.text(.5,.04,'Before')]
        for artist in artists:
            for option in (dict(fontsize=0),dict(fontstyle='sideways'),dict(fontweight='unknown'),dict(fontfamily=42),dict(fontfamily='')):
                with self.subTest(kind=type(artist).__name__,option=option):
                    self.fig.canvas.draw();before=(artist.get_text(),dict(artist.style));events=[]
                    cid=artist.add_callback(events.append)
                    with self.assertRaises(ValueError):artist.set(text='After',visible=False,**option)
                    self.assertEqual((artist.get_text(),dict(artist.style)),before)
                    self.assertTrue(artist.get_visible());self.assertFalse(self.fig.stale);self.assertEqual(events,[])
                    artist.remove_callback(cid)

    def test_invalid_mapped_batches_do_not_commit_data_norm_or_callbacks(self):
        norm=Normalize(0,5)
        artists=[self.ax.scatter([-52,-48],[-25,-21],c=[1,2],norm=norm),
                 self.ax.imshow([[1,2]],extent=(-54,-42,-28,-16),norm=norm),
                 self.ax.pcolormesh([-54,-48,-42],[-28,-16],[[1,2]],norm=norm),
                 self.ax.quiver([-52,-48],[-25,-21],[1,1],[0,0],[1,2],norm=norm),
                 self.ax.contour([-54,-48,-42],[-28,-22,-16],[[0,1,2]]*3,levels=[.5,1.5],norm=norm)]
        for artist in artists:
            with self.subTest(kind=type(artist).__name__):
                bar=self.fig.colorbar(artist,ax=self.ax)
                self.fig.canvas.draw();before=(artist.data,dict(artist.style),artist.get_array(),artist.norm,artist.cmap)
                events=[];cid=artist.callbacks.connect('changed',events.append)
                with self.assertRaises(ValueError):artist.set(norm=Normalize(0,50),clim=(0,100),cmap='plasma',visible=False,fontstyle='sideways')
                self.assertEqual((artist.data,dict(artist.style),artist.get_array(),artist.norm,artist.cmap),before)
                self.assertIs(bar.norm,norm);self.assertFalse(self.fig.stale);self.assertTrue(artist.get_visible());self.assertEqual(events,[])
                artist.callbacks.disconnect(cid)

    def test_spine_and_colorbar_outline_batches_validate_before_commit(self):
        points=self.ax.scatter([-52,-48],[-25,-21],c=[1,2]);bar=self.fig.colorbar(points)
        for artist in (self.ax.spines['left'],bar.outline):
            with self.subTest(kind=type(artist).__name__):
                self.fig.canvas.draw();before=(artist.get_color(),artist.get_linewidth(),artist.get_visible())
                events=[];cid=artist.add_callback(events.append)
                with self.assertRaises(ValueError):artist.set(color='red',visible=False,linewidth=-1)
                self.assertEqual((artist.get_color(),artist.get_linewidth(),artist.get_visible()),before)
                self.assertFalse(self.fig.stale);self.assertEqual(events,[])
                artist.set(color='red',linewidth='1.2',visible=False)
                self.assertEqual(len(events),1);self.assertEqual(artist.get_linewidth(),1.2);artist.remove_callback(cid)

    def test_legend_frame_invalid_batch_preserves_owner_and_frame(self):
        self.ax.plot([-52,-48],[-25,-21],label='Route');legend=self.ax.legend();frame=legend.get_frame()
        self.fig.canvas.draw();before=dict(legend);events=[];frame.add_callback(events.append)
        with self.assertRaises(ValueError):frame.set(facecolor='red',visible=False,linewidth=-1,in_layout=False)
        self.assertEqual(dict(legend),before);self.assertTrue(frame.get_in_layout());self.assertFalse(self.fig.stale);self.assertEqual(events,[])
        frame.set(facecolor='white',edgecolor='black',linewidth=.6,alpha=.9,visible=True)
        self.assertEqual(len(events),1);self.assertEqual(frame.get_linewidth(),.6)

    def test_invalid_scale_creation_preserves_previous_handle(self):
        previous=self.ax.scale_bar(length=100)
        for fontsize in (0,-1,'nan','inf'):
            with self.subTest(fontsize=fontsize):
                self.fig.canvas.draw()
                with self.assertRaises(ValueError):self.ax.scale_bar(fontsize=fontsize)
                self.assertIs(self.ax._scale_bar,previous);self.assertIs(previous.get_figure(),self.fig);self.assertFalse(self.fig.stale)

    def test_scale_numeric_edits_are_normalized_and_invalid_batch_is_atomic(self):
        scale=self.ax.scale_bar(length=100,fontsize='9');self.assertEqual(scale.get_fontsize(),9)
        self.fig.canvas.draw();before=dict(scale)
        with self.assertRaises(ValueError):scale.set(length=50,visible=False,fontsize=0)
        self.assertEqual(dict(scale),before);self.assertFalse(self.fig.stale)
        scale.set(length='50',fontsize='12',framealpha='0.9');self.assertEqual(scale.get_fontsize(),12);self.fig.to_svg()

    def test_invalid_tick_font_size_never_changes_settings_or_texts(self):
        points=self.ax.scatter([-52,-48],[-25,-21],c=[1,2]);bar=self.fig.colorbar(points)
        self.ax.set_xticks([-52,-48],['A','B']);bar.set_ticks([1,2],labels=['Low','High'])
        for owner in (self.ax,bar.ax):
            for which in ('major','minor','both'):
                with self.subTest(owner=type(owner).__name__,which=which):
                    self.fig.canvas.draw();before=self.fig.to_svg()
                    with self.assertRaises(ValueError):owner.tick_params(which=which,labelsize=0,colors='red')
                    self.assertEqual(before,self.fig.to_svg());self.assertFalse(self.fig.stale)
        self.ax.tick_params(labelsize='9',pad='5');bar.ax.tick_params(labelsize='8',length='4')
        self.fig.to_svg()

    def test_all_numeric_edits_export_static_png_svg_and_portable_html(self):
        line,=self.ax.plot([-52,-48],[-25,-21],'o-',linewidth='1.3',markersize='5',alpha='0.7')
        title=self.ax.set_title('Edited',fontsize='12',rotation='0')
        scale=self.ax.scale_bar(length=100,fontsize='9')
        self.ax.legend();self.fig.canvas.draw()
        self.assertIn('Edited',self.fig.to_svg());self.assertNotIn('<script',self.fig.to_svg())
        self.assertIn('AzimlibComponents',self.fig.to_html())
        try:import PIL
        except ImportError:return
        output=io.BytesIO();self.fig.savefig(output,format='png');self.assertTrue(output.getvalue().startswith(b'\x89PNG'))


if __name__=='__main__':unittest.main()

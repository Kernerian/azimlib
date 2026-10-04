import unittest
import azimlib as az
from azimlib.scene import Text,Circle,Path
from azimlib.typography import POINT,text_width,font_path
from azimlib.styles import text_style

class ComponentTests(unittest.TestCase):
    def setUp(self):
        self.fig,self.ax=az.subplots()
        self.ax.set_extent((-60,-40,-30,-10))
    def tearDown(self):az.close('all');az.rcdefaults()

    def test_text_artist_remains_live(self):
        title=self.ax.set_title('Before')
        title.set_text('After');title.set_color('red');title.set_fontsize(16)
        rendered=next(i for i in self.fig.to_scene().items if isinstance(i,Text) and i.text=='After')
        self.assertEqual(rendered.style['fill'],'red')
        self.assertEqual(rendered.style['font_size'],16*POINT)

    def test_public_rotation_is_counterclockwise_in_png_and_svg(self):
        import io,math
        from azimlib.scene import Scene
        from azimlib.render_map import _add_text
        from azimlib.renderers import render_png,render_svg
        from PIL import Image
        for angle in (25,-25):
            with self.subTest(angle=angle):
                scene=Scene(200,200,'white')
                _add_text(scene,100,100,'HHHHHH',text_style(dict(fontsize=16,rotation=angle,ha='center',va='center')))
                item=next(i for i in scene.items if isinstance(i,Text))
                self.assertEqual(item.style['rotation'],-angle)
                self.assertIn(f'rotate({-angle} 100 100)',render_svg(scene))
                target=io.BytesIO();render_png(scene,target)
                image=Image.open(target).convert('RGB');pixels=image.load()
                ink=[(x,y) for y in range(200) for x in range(200) if sum(pixels[x,y])<300]
                mx=sum(x for x,y in ink)/len(ink);my=sum(y for x,y in ink)/len(ink)
                xx=sum((x-mx)**2 for x,y in ink);yy=sum((y-my)**2 for x,y in ink)
                xy=sum((x-mx)*(y-my) for x,y in ink)
                rendered=math.degrees(.5*math.atan2(2*xy,xx-yy))
                self.assertAlmostEqual(rendered,-angle,delta=2)
        label=self.ax.set_ylabel('Latitude')
        self.assertEqual(label.get_rotation(),90)
        label.set_rotation(-25);self.assertEqual(label.get_rotation(),335)
        text=next(i for i in self.fig.to_scene().items if isinstance(i,Text) and i.text=='Latitude')
        self.assertEqual(text.style['rotation'],25)

    def test_custom_ticks_and_top_labels(self):
        self.ax.set_xticks([-55,-45],['West','East'])
        self.ax.tick_params(axis='x',bottom=False,labelbottom=False,top=True,labeltop=True,colors='red',labelrotation=20)
        scene=self.fig.to_scene()
        labels=[i for i in scene.items if isinstance(i,Text) and i.text in ('West','East')]
        self.assertEqual(len(labels),2)
        self.assertTrue(all(i.y<scene.maps[0]['box'][1] for i in labels))
        self.assertTrue(all(i.style['rotation']==-20 and i.style['fill']=='red' for i in labels))
        with self.assertRaises(ValueError):self.ax.set_xticks([1,2],['mismatch'])

    def test_spine_visibility_does_not_hide_ticks(self):
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color('magenta')
        scene=self.fig.to_scene()
        spines=[i for i in scene.items if isinstance(i,Path) and i.style.get('linecap')=='square']
        self.assertEqual(len(spines),3)
        self.assertEqual(sum(i.style['stroke']=='magenta' for i in spines),1)
        self.assertTrue(scene.maps[0]['tick_indices'])

    def test_legend_uses_live_handle_marker_and_explicit_label(self):
        line,=self.ax.plot([-58,-42],[-28,-12],'o--',color='red',label='Old')
        self.ax.legend([line],['Route'],loc='upper left')
        line.set_color('blue')
        scene=self.fig.to_scene()
        markers=[i for i in scene.items if isinstance(i,Circle) and i.clip is None]
        self.assertEqual(len(markers),1)
        self.assertEqual(markers[0].style['fill'],'blue')
        self.assertTrue(any(isinstance(i,Text) and i.text=='Route' for i in scene.items))

    def test_legend_text_fits_frame_with_unicode(self):
        self.ax.plot([-58,-42],[-28,-12],'o-',label='Navegação: WWW áéç')
        self.ax.legend(loc='upper left')
        scene=self.fig.to_scene()
        frame=next(i for i in scene.items if isinstance(i,Path) and i.style.get('opacity')==.8 and i.closed)
        right=max(x for x,y in frame.paths[0])
        label=next(i for i in scene.items if isinstance(i,Text) and i.text.startswith('Navegação'))
        self.assertLess(label.x+text_width(label.text,label.style),right)

    def test_rc_context_restores_on_exception_and_existing_figure_keeps_style(self):
        before=dict(az.rcParams)
        with self.assertRaises(RuntimeError):
            with az.rc_context({'axes.titlesize':19,'lines.linewidth':3,'figure.dpi':120}):
                f,a=az.subplots();a.set_title('Configured')
                line,=a.plot([-55,-45],[-25,-15])
                self.assertEqual(f.dpi,120)
                self.assertEqual(line.get_linewidth(),3)
                raise RuntimeError('exit')
        self.assertEqual(dict(az.rcParams),before)
        self.assertEqual(a._title.get_fontsize(),19)
        with self.assertRaises(KeyError):az.rcParams.update({'lines.linewidth':8,'unimplemented':True})
        self.assertEqual(az.rcParams['lines.linewidth'],before['lines.linewidth'])

    def test_font_metrics_use_glyphs_not_character_count(self):
        style=text_style({})
        self.assertGreater(text_width('WWW',style),text_width('iii',style)*3)
        self.assertTrue(font_path(style).is_file())
        self.assertIn('@font-face',self.fig.to_svg())

    def test_clear_resets_ticks_and_spines(self):
        self.ax.set_xticks([-50]);self.ax.spines['top'].set_visible(False)
        self.ax.clear()
        self.assertIsNone(self.ax._ticks['x'])
        self.assertTrue(self.ax.spines['top'].get_visible())
        self.assertEqual(self.ax.facecolor,'white')

if __name__=='__main__':unittest.main()

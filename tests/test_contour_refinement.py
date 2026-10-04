"""Per-level mapping, unfilled contour bars and reversible display-only cuts."""
import io,json,math
from pathlib import Path as FilePath
import unittest
from unittest.mock import patch
import azimlib as azl
from azimlib.colors import Normalize,NoNorm,ListedColormap,LogNorm
from azimlib.cm import ScalarMappable
from azimlib.scene import Path,Rect,Text,Scene
from azimlib.contour_inline import cut_path,label_cuts,_interval
from azimlib.label_layout import plan_labels
from azimlib.viewport import Viewport
from azimlib.typography import text_bounds,POINT
from azimlib.colorbar_render import render_colorbar,contour_position
from azimlib.projected_paths import _paths
from azimlib.renderers import render_png
from azimlib.ticker import FixedLocator,FormatStrFormatter


def pixels(scene):
    buffer=io.BytesIO();render_png(scene,buffer);return buffer.getvalue()


class ContourRefinementTests(unittest.TestCase):
    def tearDown(self):azl.close('all');azl.ioff();azl.rcdefaults()

    def create(self,dpi=100,projection='equirectangular',**kwargs):
        fig,ax=azl.subplots(figsize=(3,3),dpi=dpi,projection=projection)
        ax.set_extent((-54,-44,-26,-18))
        cs=ax.contour([-54,-49,-44],[-26,-22,-18],[[0,1,2]]*3,
                      levels=[.5,1.5],**kwargs)
        return fig,ax,cs

    def test_twelve_bar_states_positions_and_defaults_match_matplotlib(self):
        reference=json.loads((FilePath(__file__).resolve().parents[1]/'docs/contour-bars-reference.json').read_text())
        for case in reference['cases']:
            with self.subTest(kind=case['kind'],orientation=case['orientation'],spacing=case['spacing']):
                fig,ax=azl.subplots();options=dict(levels=[.2,.7,1.8],linewidths=[.4,.8,1.2]);z=[[0,1,2]]*3
                if case['kind']=='explicit':options['colors']=['red','blue']
                if case['kind']=='log':options.update(levels=[1,10,100],norm=LogNorm(1,100));z=[[1,10,100]]*3
                cs=ax.contour([-54,-49,-44],[-26,-22,-18],z,**options)
                bar=fig.colorbar(cs,orientation=case['orientation'],spacing=case['spacing'])
                for key,actual in dict(array=cs.get_array(),norm=type(cs.norm).__name__,clim=list(cs.get_clim()),
                        boundaries=list(bar.boundaries),values=list(bar.values),ticks=list(bar.get_ticks()),
                        linewidths=cs.get_linewidths()).items():self.assertEqual(actual,case[key])
                for value,expected in zip(cs.levels,case['positions']):self.assertAlmostEqual(contour_position(bar,value),expected)
                labels=ax.clabel(cs)
                self.assertTrue(all(t.get_inline()==reference['defaults']['inline'] and
                                    t.get_inline_spacing()==reference['defaults']['inline_spacing'] for t in labels))
                scene=Scene(120,120);render_colorbar(bar,(20,20,60,60),scene)
                self.assertFalse(any(isinstance(p,Rect) and p.style.get('shape_rendering')=='crispEdges' for p in scene.items))
                self.assertFalse(case['solids']);azl.close(fig)

    def test_per_level_values_with_disconnected_and_empty_paths(self):
        fig,ax=azl.subplots()
        cs=ax.contour([-54,-52,-50,-48,-46],[-26,-18],[[0,2,0,2,0]]*2,levels=[.5,1.5,3])
        self.assertEqual(cs.get_array(),[.5,1.5,3]);self.assertEqual(len(cs.data),8)
        self.assertEqual(len(cs.allsegs[-1]),0)
        cs.set(array=[10,20,30],norm=Normalize(0,30),cmap='plasma')
        for i,feature in enumerate(cs.data):
            with self.subTest(path=i):
                level=cs.levels.index(feature.properties['level'])
                self.assertEqual(cs._feature_style(i,feature)['color'],cs.to_color([10,20,30][level]))
        cs.set_array(None);self.assertEqual(cs.cvalues,[.5,1.5,3]);self.assertIsNone(cs.get_array())
        with self.assertRaises(ValueError):cs.set_array(list(range(8)))
        empty=ax.contour([-54,-44],[-26,-18],[[0,0],[0,0]],levels=[1,2])
        self.assertEqual(empty.get_array(),[1,2]);bar=fig.colorbar(empty)
        self.assertEqual(bar.get_ticks(),(1,2));fig.to_svg()

    def test_no_norm_single_palette_indices_missing_under_over(self):
        norm=NoNorm();self.assertEqual(norm([-1,0,1,2]),[-1,0,1,2])
        self.assertEqual(norm.inverse([1,2]),[1,2]);self.assertIsNone(norm(float('nan')))
        palette=ListedColormap(['red']);self.assertEqual(palette.N,1)
        palette.set_under('blue');palette.set_over('green')
        self.assertEqual([palette(i) for i in (-1,0,1)],['blue','red','green'])
        self.assertEqual(palette.reversed()(0),'red')
        with self.assertRaises(ValueError):ListedColormap([])
        fig,ax,cs=self.create(colors='black')
        self.assertIsInstance(cs.norm,NoNorm);self.assertEqual(cs.get_array(),[0,1])
        self.assertEqual(cs.get_color(),['black','black'])
        one=ax.contour([-54,-44],[-26,-18],[[0,1],[0,1]],levels=[.5],colors='red')
        bar=fig.colorbar(one);self.assertEqual(bar.get_ticks(),(.5,))
        self.assertEqual(contour_position(bar,.5),.5);fig.to_svg()

    def test_bar_lines_follow_mapping_widths_and_ticks_but_manual_color_is_separate(self):
        fig,ax,cs=self.create(colors=['red','blue'],linewidths=[.4,.8])
        bar=fig.colorbar(cs,orientation='horizontal');bar.set_ticks([.5,1,1.5],labels=['Low','Middle','High'])
        locator=bar.locator;before=fig.to_svg()
        cs.set_color('green');self.assertEqual(cs.get_color(),['green','green'])
        self.assertEqual([cs._mapped_color(i) for i in range(2)],['red','blue'])
        cs.set(cmap='plasma',clim=(0,3),linewidths=[1,2])
        self.assertIs(bar.locator,locator);self.assertEqual(bar.boundaries,(.5,1.5))
        self.assertEqual(bar._long_axis.get_view_interval(),(.5,1.5))
        self.assertIn('Middle',fig.to_svg());self.assertNotEqual(fig.to_svg(),before)
        cs.set_norm(Normalize(0,3));self.assertIsNot(bar.locator,locator)
        self.assertEqual(bar.get_ticks(),(.5,1.5))
        replacement=ScalarMappable(Normalize(0,10));bar.update_normal(replacement)
        self.assertIsNone(bar.boundaries);self.assertIsNone(bar.values)
        self.assertEqual(bar._long_axis.get_view_interval(),(0,10));fig.to_svg()

    def test_spacing_custom_ticks_horizontal_vertical_and_cax(self):
        for location in ('left','right','top','bottom'):
            for spacing in ('uniform','proportional'):
                with self.subTest(location=location,spacing=spacing):
                    fig,ax=azl.subplots()
                    cs=ax.contour([-54,-44],[-26,-18],[[0,2],[0,2]],levels=[.2,.7,1.8],colors=['red','blue'])
                    bar=fig.colorbar(cs,location=location,spacing=spacing)
                    bar.set_ticks([.2,.45,.7,1.8]);bar.formatter=FormatStrFormatter('%.2f')
                    self.assertAlmostEqual(contour_position(bar,.45),.25 if spacing=='uniform' else .15625)
                    self.assertLess(contour_position(bar,-1),0);self.assertGreater(contour_position(bar,2),1)
                    self.assertIn('0.45',fig.to_svg());bar.remove();azl.close(fig)
        fig,ax,cs=self.create();cax=fig.add_axes((.9,.2,.03,.6))
        bar=fig.colorbar(cs,cax=cax);cax.set_yticks([.5,1.5],labels=['A','B'])
        self.assertIn('A',fig.to_svg());self.assertIs(bar.ax,cax)

    def test_cut_path_intervals_rotation_union_and_endpoints(self):
        for reverse in (False,True):
            for angle in (0,30,90,-40):
                with self.subTest(reverse=reverse,angle=angle):
                    rad=math.radians(angle)
                    def turn(x):return (x*math.cos(rad),x*math.sin(rad))
                    path=[turn(-10),turn(0),turn(10)]
                    if reverse:path.reverse()
                    parts=cut_path(path,[((0,0),angle,(-2,-1,4,2))])
                    self.assertEqual(len(parts),2);self.assertEqual(parts[0][0],path[0]);self.assertEqual(parts[-1][-1],path[-1])
                    self.assertAlmostEqual(math.dist(parts[0][-1],parts[1][0]),4)
        self.assertEqual(cut_path([(-10,0),(10,0)],[((0,0),0,(-2,-1,4,2)),((0,0),0,(-1,-1,4,2))]),
                         [[(-10.,0.),(-2.,0.)],[(3.,0.),(10.,0.)]])
        self.assertEqual(cut_path([(-1,0),(1,0)],[((0,0),0,(-2,-1,4,2))]),[])
        self.assertEqual(cut_path([(1,1),(1,1),(2,2)],[]),[[(1,1),(1,1),(2,2)]])

    def test_inline_cuts_are_display_only_reversible_and_placed(self):
        fig,ax,cs=self.create(colors='red');source=cs.data;segments=cs.allsegs
        labels=ax.clabel(cs,fmt='%.1f',fontsize=9,halo=None)
        self.assertEqual(cs.allsegs,segments);scene=fig.to_scene()
        contour_paths=[p for p in scene.items if isinstance(p,Path) and p.style.get('stroke')=='red' and p.clip]
        self.assertTrue(contour_paths);self.assertTrue(all(len(p.paths)==2 for p in contour_paths))
        for label in labels:label.set_inline(False)
        whole=fig.to_scene();whole_paths=[p for p in whole.items if isinstance(p,Path) and p.style.get('stroke')=='red' and p.clip]
        self.assertTrue(all(len(p.paths)==1 for p in whole_paths))
        labels.set_visible(False);self.assertEqual([p for p in fig.to_scene().items if isinstance(p,Path) and p.style.get('stroke')=='red' and p.clip],whole_paths)
        labels.set_visible(True);azl.setp(labels,inline=True);self.assertEqual(cs.data,source)
        self.assertEqual(cs.allsegs,segments)
        labels.remove();restored=fig.to_scene();self.assertEqual([p for p in restored.items if isinstance(p,Path) and p.style.get('stroke')=='red' and p.clip],whole_paths)

    def test_spacing_and_font_edits_change_gap_size_preserve_source(self):
        fig,ax,cs=self.create(colors='red');labels=ax.clabel(cs,fmt='%.1f',fontsize=9)
        def gap():
            paths=[p for p in fig.to_scene().items if isinstance(p,Path) and p.style.get('stroke')=='red' and p.clip]
            return math.dist(paths[0].paths[0][-1],paths[0].paths[1][0])
        # This field's isolines are vertical; the text rotates with the tangent.
        a=gap();azl.setp(labels,inline_spacing=10);b=gap();self.assertAlmostEqual(b-a,10,places=7)
        azl.setp(labels,fontsize=12);self.assertGreater(gap(),b)
        for props in (dict(inline=2),dict(inline_spacing=-1),dict(inline_spacing=float('nan'))):
            with self.subTest(props=props):
                fig.canvas.draw();text=labels[0].get_text();spacing=labels[0].get_inline_spacing()
                with self.assertRaises((ValueError,TypeError)):labels[0].set(text='Bad',visible=False,**props)
                self.assertTrue(labels[0].visible);self.assertEqual(labels[0].get_text(),text)
                self.assertEqual(labels[0].get_inline_spacing(),spacing);self.assertFalse(fig.stale)

    def test_unplaced_transparent_or_offline_labels_never_cut(self):
        fig,ax,cs=self.create(colors='red');labels=ax.clabel(cs,fmt=lambda x:'X'*200,fontsize=20)
        def uncut():
            return all(len(p.paths)==1 for p in fig.to_scene().items if isinstance(p,Path) and p.style.get('stroke')=='red' and p.clip)
        self.assertTrue(uncut());labels.remove();labels=ax.clabel(cs,alpha=0)
        self.assertTrue(uncut());labels.remove()
        labels=ax.clabel(cs,offsets=[(40,0)]);self.assertTrue(uncut())

    def test_only_own_paths_cut_and_detached_labels_cannot_cut(self):
        fig,ax,cs=self.create(colors='red')
        second=ax.contour([-54,-49,-44],[-26,-22,-18],[[0,1,2]]*3,levels=[.5,1.5],colors='blue')
        labels=ax.clabel(cs)
        scene=fig.to_scene();blue=[p for p in scene.items if isinstance(p,Path) and p.style.get('stroke')=='blue' and p.clip]
        self.assertTrue(all(len(p.paths)==1 for p in blue))
        labels[0].remove();cs.remove();fig.canvas.draw();azl.setp(labels,inline_spacing=9)
        self.assertFalse(fig.stale);second.remove()

    def test_dpi_zoom_culling_png_svg_and_cached_geometry(self):
        for projection in ('equirectangular','mercator'):
            for dpi in (72,100,200):
                with self.subTest(projection=projection,dpi=dpi):
                    fig,ax,cs=self.create(dpi=dpi,projection=projection,colors='red')
                    ax.clabel(cs,fontsize=8,inline_spacing=5,halo=None)
                    before=cs.allsegs;scene=fig.to_scene();hits=_paths.info().hits
                    self.assertEqual(scene.items,fig.to_scene().items);self.assertGreater(_paths.info().hits,hits)
                    self.assertEqual(pixels(fig.to_scene(cull=False)),pixels(fig.to_scene(cull=True)))
                    self.assertIn('<svg',fig.to_svg());self.assertIn('Figure',fig.to_html())
                    ax.zoom(1.3);self.assertTrue(fig.to_scene().items);self.assertEqual(cs.allsegs,before)
                    azl.close(fig)


if __name__=='__main__':unittest.main()

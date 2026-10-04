"""Adaptive scale captions preserve distance, font size and readable bounds."""
import unittest
import azimlib as azl
from azimlib.render_map import _scale
from azimlib.scene import Scene,Text,Rect,Path
from azimlib.layout_engine import primitive_bounds
from azimlib.viewport import Viewport
from azimlib.geometry import haversine
from azimlib.typography import POINT


class ScaleLabelTests(unittest.TestCase):
    def tearDown(self):azl.close('all')
    def render(self,width=500,length=100,fontsize=9,units='km',loc='lower left'):
        fig,ax=azl.subplots();ax.set_extent((-54,-43,-26,-19))
        scale=ax.scale_bar(length=length,fontsize=fontsize,units=units,loc=loc)
        vp=Viewport(ax.projection,ax._get_extent(),(10,10,width,400))
        scene=Scene(width+20,420);_scale(scale,vp,scene)
        return fig,ax,scale,vp,scene
    def assert_readable(self,scene):
        texts=[p for p in scene.items if isinstance(p,Text)]
        boxes=[primitive_bounds(p) for p in texts]
        for i,a in enumerate(boxes):
            for b in boxes[i+1:]:
                self.assertFalse(a[0]<b[0]+b[2] and a[0]+a[2]>b[0] and
                                 a[1]<b[1]+b[3] and a[1]+a[3]>b[1])
        frame=next(p for p in scene.items if isinstance(p,Path) and p.closed)
        x0=min(x for x,y in frame.paths[0]);x1=max(x for x,y in frame.paths[0])
        y0=min(y for x,y in frame.paths[0]);y1=max(y for x,y in frame.paths[0])
        for x,y,w,h in boxes:
            self.assertGreaterEqual(x,x0-.1);self.assertLessEqual(x+w,x1+.1)
            self.assertGreaterEqual(y,y0-.1);self.assertLessEqual(y+h,y1+.1)
        bars=[primitive_bounds(p) for p in scene.items if isinstance(p,Rect)]
        for x,y,w,h in boxes:
            for bx,by,bw,bh in bars:
                self.assertFalse(x<bx+bw and x+w>bx and y<by+bh and y+h>by)
    def test_width_reduces_graduations_then_uses_combined_caption(self):
        counts=[]
        for width in (700,350,140):
            _,_,_,_,scene=self.render(width=width)
            texts=[p.text for p in scene.items if isinstance(p,Text)]
            self.assert_readable(scene)
            counts.append(texts)
        self.assertEqual(counts,[['0','50','100','km'],['0','100','km'],['100 km']])
    def test_units_font_size_and_all_anchors_preserve_exact_geographic_distance(self):
        factors={'m':1,'km':1000,'mi':1609.344}
        for width in (700,350,140):
            for units,length in (('km',100),('m',100000),('mi',60)):
                for loc in ('upper left','upper right','lower left','lower right'):
                    with self.subTest(width=width,units=units,loc=loc):
                        _,_,_,vp,scene=self.render(width=width,units=units,length=length,fontsize=10,loc=loc)
                        self.assert_readable(scene)
                        bars=[p for p in scene.items if isinstance(p,Rect)]
                        self.assertEqual(len(bars),2)
                        start=vp.inverse(bars[0].x,bars[0].y)
                        end=vp.inverse(bars[1].x+bars[1].width,bars[1].y)
                        self.assertAlmostEqual(haversine(start,end)/(factors[units]*length),1,places=9)
                        for p in scene.items:
                            if isinstance(p,Text):self.assertEqual(p.style['font_size'],10*POINT)
    def test_resize_zoom_font_edits_and_visibility_recompute_labels(self):
        fig,ax=azl.subplots(figsize=(8,5));ax.set_extent((-54,-43,-26,-19))
        scale=ax.scale_bar(length=100)
        def items():
            scene=fig.to_scene();m=scene.maps[0]
            return [p for p in scene.items[m['decoration_start']:m['decoration_end']] if isinstance(p,Text)]
        before=[p.text for p in items()];fig.figsize=(3,5)
        compact=[p.text for p in items()];self.assertNotEqual(before,compact)
        ax.zoom(2.3);expanded=[p.text for p in items()];self.assertNotEqual(compact,expanded)
        scale.set_fontsize(14);large=[p.text for p in items()];self.assertNotEqual(large,expanded)
        self.assertTrue(all(p.style['font_size']==14*POINT for p in items()))
        scale.set_visible(False);self.assertEqual(items(),[])
        scale.set_visible(True);self.assertEqual([p.text for p in items()],large)
        initial=[(p.x,p.y,p.text) for p in items()];fig.dpi=200
        doubled=[(p.x,p.y,p.text) for p in items()]
        for a,b in zip(initial,doubled):
            self.assertEqual(a[2],b[2]);self.assertAlmostEqual(a[0]*2,b[0]);self.assertAlmostEqual(a[1]*2,b[1])
    def test_compact_caption_exports_once_and_manual_length_is_not_changed(self):
        fig,ax=azl.subplots(figsize=(2.5,4));ax.set_extent((-54,-43,-26,-19))
        scale=ax.scale_bar(length=100)
        svg=fig.to_svg();self.assertIn('100 km',svg);self.assertNotIn('>50<',svg)
        self.assertIn('100 km',fig.to_html());self.assertEqual(scale.get_length(),100)
    def test_compact_frame_removes_units_row_and_preserves_corner_padding(self):
        for loc in ('upper left','upper right','lower left','lower right'):
            with self.subTest(loc=loc):
                _,_,_,vp,scene=self.render(width=140,loc=loc)
                self.assert_readable(scene)
                frame=next(p for p in scene.items if isinstance(p,Path) and p.closed)
                top=min(y for x,y in frame.paths[0]);bottom=max(y for x,y in frame.paths[0])
                fs=9*POINT
                self.assertAlmostEqual(bottom-top,fs*2.58)
                bar=next(p for p in reversed(scene.items) if isinstance(p,Rect))
                self.assertAlmostEqual(bottom-(bar.y+bar.height),fs*.4)
                caption=next(p for p in scene.items if isinstance(p,Text))
                self.assertAlmostEqual(primitive_bounds(caption)[1]-top,fs*.4)
                expected=vp.box[1]+fs*.5 if loc.startswith('upper') else vp.box[1]+vp.box[3]-fs*.5
                self.assertAlmostEqual(top if loc.startswith('upper') else bottom,expected)
        _,_,_,_,wide=self.render(width=700)
        frame=next(p for p in wide.items if isinstance(p,Path) and p.closed)
        self.assertAlmostEqual(max(y for x,y in frame.paths[0])-min(y for x,y in frame.paths[0]),9*POINT*3.95)

    def test_vertical_padding_follows_measured_text_at_each_font_size(self):
        for fontsize in (7,9,16,24):
            for width in (140,700):
                for loc in ('upper left','upper right','lower left','lower right'):
                    with self.subTest(fontsize=fontsize,width=width,loc=loc):
                        _,_,_,_,scene=self.render(width=width,fontsize=fontsize,loc=loc)
                        self.assert_readable(scene)
                        frame=next(p for p in scene.items if isinstance(p,Path) and p.closed)
                        top=min(y for x,y in frame.paths[0]);bottom=max(y for x,y in frame.paths[0])
                        content=[primitive_bounds(p) for p in scene.items if isinstance(p,(Rect,Text))]
                        self.assertAlmostEqual(min(b[1] for b in content)-top,fontsize*POINT*.4)
                        # Compact content ends at the stroked bar, whose edge
                        # extends 0.3 point beyond its rectangle coordinates.
                        compact=not any(isinstance(p,Text) and p.text=='km' for p in scene.items)
                        self.assertAlmostEqual(bottom-max(b[1]+b[3] for b in content),fontsize*POINT*.4-(.3*POINT if compact else 0))
    def test_auto_length_keeps_readable_labels_for_small_and_large_views(self):
        for width in (140,350,700):
            for units in ('m','km','mi'):
                with self.subTest(width=width,units=units):
                    _,_,scale,_,scene=self.render(width=width,length=None,units=units)
                    self.assert_readable(scene);self.assertIsNone(scale.get_length())

    def test_horizontal_frame_centers_bar_with_short_symmetric_padding_in_all_modes(self):
        for width in (140,350,700):
            for units,length in (('km',100),('m',100000),('mi',60),('m',1)):
                for loc in ('upper left','upper right','lower left','lower right'):
                    with self.subTest(width=width,units=units,length=length,loc=loc):
                        _,_,_,_,scene=self.render(width=width,units=units,length=length,loc=loc)
                        self.assert_readable(scene)
                        frame=next(p for p in scene.items if isinstance(p,Path) and p.closed)
                        content=[primitive_bounds(p) for p in scene.items if isinstance(p,(Rect,Text))]
                        left=min(b[0] for b in content);right=max(b[0]+b[2] for b in content)
                        frameleft=min(x for x,y in frame.paths[0]);frameright=max(x for x,y in frame.paths[0])
                        bars=[p for p in scene.items if isinstance(p,Rect)]
                        barleft=bars[0].x;barright=bars[-1].x+bars[-1].width
                        self.assertAlmostEqual(barleft-frameleft,frameright-barright,places=8)
                        self.assertAlmostEqual((barleft+barright)/2,(frameleft+frameright)/2,places=8)
                        self.assertAlmostEqual(min(left-frameleft,frameright-right),9*POINT*.5,places=8)
                        if width==140 and units=='km' and length==100:
                            from azimlib.typography import text_width
                            caption=next(p for p in scene.items if isinstance(p,Text))
                            self.assertAlmostEqual(frameright-frameleft,text_width(caption.text,caption.style)+9*POINT,places=8)

    def test_tight_frame_retains_distance_in_cylindrical_and_conic_projections(self):
        for projection in ('equirectangular','mercator','albers','lambert'):
            for loc in ('upper left','upper right','lower left','lower right'):
                with self.subTest(projection=projection,loc=loc):
                    fig,ax=azl.subplots(projection=projection);ax.set_extent((-54,-43,-26,-19))
                    scale=ax.scale_bar(length=100,loc=loc,fontsize=10)
                    vp=Viewport(ax.projection,ax._get_extent(),(10,10,500,400))
                    scene=Scene(520,420);_scale(scale,vp,scene);self.assert_readable(scene)
                    bars=[p for p in scene.items if isinstance(p,Rect)]
                    distance=haversine(vp.inverse(bars[0].x,bars[0].y),
                                       vp.inverse(bars[1].x+bars[1].width,bars[1].y))
                    self.assertAlmostEqual(distance/100000,1,places=9)
                    self.assertEqual(scale.get_length(),100)


if __name__=='__main__':unittest.main()

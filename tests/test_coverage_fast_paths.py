"""Analytic coverage and transparency at boundaries used by raster shortcuts."""
import io
import unittest
from azimlib.renderers import render_png
from azimlib.renderers.coverage import CoverageDraw
from azimlib.scene import Scene,Rect

try:
    from PIL import Image
except ImportError:Image=None


@unittest.skipIf(Image is None,'Pillow is optional')
class CoverageFastPathTests(unittest.TestCase):
    def test_single_column_triangle_preserves_area_and_clipped_edges(self):
        # Area is 0.18 pixel; when half lies beyond the canvas it is 0.09.
        cases=[([(.2,.2),(.8,.2),(.5,.8)],46),
               ([(-.3,.2),(.3,.2),(0,.8)],23),
               ([(.7,.2),(1.3,.2),(1,.8)],23)]
        for polygon,expected in cases:
            with self.subTest(polygon=polygon):
                mask=Image.new('L',(1,1));CoverageDraw(mask).polygon(polygon)
                self.assertEqual(mask.getpixel((0,0)),expected)
    def test_one_column_multirow_coverage_and_union_do_not_overpaint(self):
        mask=Image.new('L',(2,3));draw=CoverageDraw(mask)
        polygon=[(.25,.25),(.75,.25),(.75,2.25),(.25,2.25)]
        draw.polygon(polygon)
        self.assertEqual([mask.getpixel((0,y)) for y in range(3)],[96,128,32])
        draw.polygon(polygon,fill=100)
        self.assertEqual([mask.getpixel((0,y)) for y in range(3)],[96,128,32])
        self.assertEqual([mask.getpixel((1,y)) for y in range(3)],[0,0,0])
    def test_repeated_alpha_tables_preserve_all_coverage_levels(self):
        scene=Scene(256,3,'none')
        for alpha in range(256):
            # Full-pixel rectangles isolate color and Artist opacity semantics
            # from antialiasing. Red uses color alpha; blue uses fill opacity.
            scene.add(Rect(alpha,0,1,1,dict(fill=f'#ff0000{alpha:02x}',opacity=.6,shape_rendering='crispEdges')))
            scene.add(Rect(alpha,1,1,1,dict(fill='blue',fill_opacity=alpha/255,opacity=.6,shape_rendering='crispEdges')))
        stream=io.BytesIO();render_png(scene,stream);stream.seek(0);image=Image.open(stream)
        for alpha in range(256):
            with self.subTest(alpha=alpha):
                expected=round(alpha*.6)
                self.assertEqual(image.getpixel((alpha,0))[3],expected)
                self.assertEqual(image.getpixel((alpha,1))[3],expected)


if __name__=='__main__':unittest.main()

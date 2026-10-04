"""Pixel and document assertions for the independent rendering backends."""
import io
import math
import unittest
import xml.etree.ElementTree as ET

from azimlib.scene import Circle, Path, Rect, Scene, Text
from azimlib.renderers import render_png, render_svg

try:
    from PIL import Image
except ImportError:
    Image = None


class SVGTests(unittest.TestCase):
    @unittest.skipIf(Image is None,'Pillow not installed')
    def test_svg_and_png_share_text_vertical_alignment(self):
        from azimlib.typography import text_vertical_bounds
        for baseline in ('top','middle','bottom','alphabetic'):
            style=dict(font_family='DejaVu Sans',font_size=24,baseline=baseline,fill='black')
            scene=Scene(200,120,background=None)
            scene.add(Text(20,60,'São Paulo 250',style))
            root=ET.fromstring(render_svg(scene))
            text=root.find('.//{http://www.w3.org/2000/svg}text')
            low,high=text_vertical_bounds(text.text,style)
            y=float(text.attrib['y'])
            output=io.BytesIO();render_png(scene,output)
            bounds=Image.open(output).getchannel('A').getbbox()
            self.assertAlmostEqual(bounds[1],y-high,delta=1.5)
            self.assertAlmostEqual(bounds[3],y-low,delta=1.5)

    def test_multipart_holes_escaping_and_deterministic_clipping(self):
        scene = Scene(100, 80)
        scene.add(Path([[(0, 0), (80, 0), (80, 80)], [(20, 20), (30, 20), (30, 30)]],
                       closed=True, style={"fill": "red", "stroke": "black", "dash": [3, 2],
                                           "linecap": "square", "linejoin": "bevel"}, clip=(4, 4, 90, 70)))
        scene.add(Text(10, 20, 'River <A> & "B"', {"font_family": 'An "odd" font', "rotation": 15}, (4, 4, 90, 70)))
        svg = render_svg(scene)
        self.assertEqual(svg, render_svg(scene))
        root = ET.fromstring(svg)
        ns = {"s": "http://www.w3.org/2000/svg"}
        self.assertEqual(len(root.findall(".//s:clipPath", ns)), 1)
        path = root.find("s:path", ns)
        self.assertEqual(path.attrib["fill-rule"], "evenodd")
        self.assertEqual(path.attrib["stroke-dasharray"], "3 2")
        self.assertEqual(path.attrib["stroke-linecap"], "square")
        self.assertEqual(path.attrib["stroke-linejoin"], "bevel")
        text = root.find(".//s:text", ns)
        self.assertEqual(text.text, 'River <A> & "B"')
        self.assertEqual(text.attrib["font-family"], 'An "odd" font')

    def test_rejects_invalid_and_unsupported_values(self):
        for style in ({"hatch": "//"}, {"opacity": 1.5}, {"dash": [2, 0]}, {"stroke_width": -1}, {"linecap": "invalid"}):
            scene = Scene(10, 10)
            scene.add(Rect(0, 0, 10, 10, style))
            with self.assertRaises(ValueError):
                render_svg(scene)
        with self.assertRaises(ValueError):
            render_svg(Scene(float("nan"), 100))
        scene = Scene(10, 10)
        scene.add(Path([[(0, float("nan"))]]))
        with self.assertRaises(ValueError):
            render_svg(scene)

    def test_transparent_scene_and_shapes(self):
        scene = Scene(90, 80, None)
        scene.add(Circle(20, 30, 4, {"fill": "blue"}))
        scene.add(Rect(40, 50, 10, 20, {"fill": "orange"}))
        root = ET.fromstring(render_svg(scene))
        self.assertEqual(len(list(root)), 2)


@unittest.skipIf(Image is None, "Pillow is an optional dependency")
class PNGTests(unittest.TestCase):
    @staticmethod
    def render(scene, scale=1):
        output = io.BytesIO()
        render_png(scene, output, scale=scale)
        output.seek(0)
        return Image.open(output).convert("RGBA")

    def test_evenodd_holes_and_clipping_are_real_pixels(self):
        scene = Scene(100, 100)
        scene.add(Path([[(5, 5), (95, 5), (95, 95), (5, 95)],
                        [(35, 35), (65, 35), (65, 65), (35, 65)]],
                       closed=True, style={"fill": "red"}, clip=(10, 10, 70, 80)))
        image = self.render(scene)
        self.assertEqual(image.getpixel((20, 20)), (255, 0, 0, 255))
        self.assertEqual(image.getpixel((50, 50)), (255, 255, 255, 255))
        self.assertEqual(image.getpixel((90, 20)), (255, 255, 255, 255))
        self.assertEqual(image.getpixel((6, 20)), (255, 255, 255, 255))

    def test_fractional_fills_conserve_area_at_multiple_resolutions(self):
        for scale in (1,1.5,2):
            for radius in (2.5,4,7,12):
                scene=Scene(60,60,None)
                scene.add(Circle(30.23,30.37,radius,dict(fill='black')))
                area=sum(self.render(scene,scale).getchannel('A').tobytes())/255
                self.assertAlmostEqual(area/(math.pi*(radius*scale)**2),1,delta=.006)
            for x,y,w,h in ((10.23,12.37,13.2,9.6),(10.2,12.4,.8,12.7)):
                scene=Scene(60,60,None);scene.add(Rect(x,y,w,h,dict(fill='black')))
                area=sum(self.render(scene,scale).getchannel('A').tobytes())/255
                self.assertAlmostEqual(area,w*h*scale**2,delta=.1)

    def test_fill_parity_handles_overlaps_concavity_and_duplicate_rings(self):
        a=[(10,10),(30,10),(30,30),(10,30)]
        b=[(20,10),(40,10),(40,30),(20,30)]
        cases=(([a,b],400),([a,a],0),([[(10,10),(50,10),(50,30),(30,30),(30,50),(10,50)]],1200),
               ([[(10,10),(50,50),(50,10),(10,50)]],800))
        for paths,expected in cases:
            scene=Scene(60,60,None);scene.add(Path(paths,True,dict(fill='black')))
            area=sum(self.render(scene).getchannel('A').tobytes())/255
            self.assertAlmostEqual(area,expected,delta=.2)

    def test_adjacent_scalar_cells_have_no_alpha_seams(self):
        scene=Scene(80,40,None)
        for i in range(10):
            scene.add(Rect(10.23+i*5.17,8.37,5.17,20.2,dict(fill='blue',opacity=.5,shape_rendering='crispEdges')))
        image=self.render(scene)
        for x in range(12,60):self.assertAlmostEqual(image.getpixel((x,15))[3],128,delta=1)

    def test_text_background_bounds_agree_with_svg_for_alignment_and_rotation(self):
        for rotation in (0,25,90):
            for anchor in ('start','middle','end'):
                for baseline in ('top','middle','bottom','alphabetic'):
                    style=dict(font_family='DejaVu Sans',font_size=18,baseline=baseline,anchor=anchor,
                               rotation=rotation,fill='black',background='#eef2f6')
                    scene=Scene(500,400,None);scene.add(Text(250,200,'São Paulo · 250',style))
                    root=ET.fromstring(render_svg(scene))
                    rect=root.find('.//{http://www.w3.org/2000/svg}g/{http://www.w3.org/2000/svg}rect')
                    x,y,w,h=(float(rect.attrib[key]) for key in ('x','y','width','height'))
                    theta=math.radians(rotation)
                    corners=[(250+(a-250)*math.cos(theta)-(b-200)*math.sin(theta),
                              200+(a-250)*math.sin(theta)+(b-200)*math.cos(theta)) for a,b in ((x,y),(x+w,y),(x+w,y+h),(x,y+h))]
                    expected=(min(p[0] for p in corners),min(p[1] for p in corners),max(p[0] for p in corners),max(p[1] for p in corners))
                    bounds=self.render(scene).getchannel('A').getbbox()
                    for actual,target in zip(bounds,expected):self.assertAlmostEqual(actual,target,delta=1.5)

    def test_thin_stroke_coverage_matches_physical_width_at_every_angle(self):
        # Physical ink area, not implementation shape: catches rasterizers
        # that add inclusive boundary pixels or dark halos to thin strokes.
        length=80
        for points in (.5,.8,1,1.5,2):
            width=points*100/72
            for angle in (0,30,45,75,90):
                with self.subTest(points=points,angle=angle):
                    radians=math.radians(angle)
                    a=(60-length/2*math.cos(radians),60-length/2*math.sin(radians))
                    b=(60+length/2*math.cos(radians),60+length/2*math.sin(radians))
                    scene=Scene(120,120)
                    scene.add(Path([[a,b]],style={'stroke':'black','stroke_width':width,'linecap':'butt'}))
                    image=self.render(scene)
                    measured=sum(255-image.getpixel((x,y))[0] for y in range(120) for x in range(120))/255/length
                    self.assertAlmostEqual(measured,width,delta=.012)

    def test_alpha_composition_and_export_scale(self):
        scene = Scene(40, 40, None)
        scene.add(Rect(5, 5, 30, 30, {"fill": "blue", "fill_opacity": .5, "opacity": .5}))
        image = self.render(scene, scale=2)
        self.assertEqual(image.size, (80, 80))
        self.assertEqual(image.getpixel((40, 40))[:3], (0, 0, 255))
        self.assertTrue(63 <= image.getpixel((40, 40))[3] <= 65)
        self.assertEqual(image.getpixel((0, 0))[3], 0)

    def test_dash_segments_caps_and_markers(self):
        scene = Scene(100, 60)
        scene.add(Path([[(10, 15), (90, 15)]], style={"stroke": "black", "stroke_width": 4, "dash": [10, 10]}))
        scene.add(Path([[(20, 40), (40, 40)]], style={"stroke": "black", "stroke_width": 10, "linecap": "square"}))
        scene.add(Circle(75, 40, 8, {"fill": "red"}))
        image = self.render(scene)
        self.assertLess(max(image.getpixel((15, 15))[:3]), 8)
        self.assertEqual(image.getpixel((25, 15))[:3], (255, 255, 255))
        self.assertLess(max(image.getpixel((17, 40))[:3]), 8)
        self.assertEqual(image.getpixel((75, 40))[:3], (255, 0, 0))

    def test_rotated_text_is_visible_and_clipped(self):
        scene = Scene(120, 100, None)
        scene.add(Text(60, 50, "MAP", {"font_size": 25, "font_weight": "bold", "rotation": 90,
                                         "anchor": "middle", "baseline": "middle", "fill": "black"}, (40, 10, 40, 80)))
        image = self.render(scene)
        bbox = image.getchannel("A").getbbox()
        self.assertIsNotNone(bbox)
        self.assertGreater(bbox[3] - bbox[1], bbox[2] - bbox[0])
        self.assertEqual(image.getpixel((15, 50))[3], 0)

    def test_missing_font_and_invalid_scale_are_clear(self):
        scene = Scene(20, 20)
        scene.add(Text(1, 10, "A", {"font_family": "DefinitelyNotAnInstalledFont12345"}))
        with self.assertRaisesRegex(ValueError, "unavailable"):
            self.render(scene)
        with self.assertRaisesRegex(ValueError, "scale"):
            self.render(Scene(10, 10), scale=0)


if __name__ == "__main__":
    unittest.main()

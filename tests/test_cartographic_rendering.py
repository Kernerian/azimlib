"""End-to-end regressions for projection, viewport, styles and scene assembly."""
import io
import unittest
import xml.etree.ElementTree as ET

from azimlib.axes import MapAxes
from azimlib.render_map import render_axes, _add_text
from azimlib.renderers import render_png, render_svg
from azimlib.scene import Scene, Path, Text, Circle
from azimlib.styles import text_style


class CartographicRenderingTests(unittest.TestCase):
    def scene(self, ax):
        scene = Scene(500, 380)
        render_axes(ax, scene, (65, 40, 380, 270))
        return scene

    def test_actual_brazil_and_bundled_layers_export_svg(self):
        ax = MapAxes(None, (0, 0, 1, 1), "mercator")
        ax.map("Brazil", facecolor="white", edgecolor="black")
        ax.states(linewidth=.6)
        ax.rivers(color="navy", linewidth=1.2)
        ax.scatter([-46.63, -43.17], [-23.55, -22.9], marker="^", s=[40, 80],
                   c=["red", "orange"], edgecolor="black", rotation=15)
        ax.title("Brasil")
        ax.grid(step=10)
        ax.scale_bar()
        ax.north_arrow()
        scene = self.scene(ax)
        svg = render_svg(scene)
        root = ET.fromstring(svg)
        ns = {"s": "http://www.w3.org/2000/svg"}
        self.assertGreater(len(root.findall("s:path", ns)), 30)
        self.assertIn("Brasil", svg)
        self.assertIn('>km</text>', svg)
        self.assertEqual(len(scene.maps), 1)
        self.assertEqual(scene.maps[0]["projection"]["name"], "mercator")
        self.assertGreater(scene.maps[0]["end"], scene.maps[0]["start"])

    def test_antimeridian_polygon_and_route_do_not_bridge_the_map(self):
        ax = MapAxes(None, (0, 0, 1, 1))
        ax.set_extent((-180, 180, -60, 60))
        ax.polygon([(170,-10),(-170,-10),(-170,10),(170,10)], facecolor="red", edgecolor="none")
        ax.line([(160,20),(-160,20)], color="black", arrow="both", arrowstyle="stealth")
        scene = self.scene(ax)
        polygons = [item for item in scene.items if isinstance(item, Path) and item.style.get("fill") == "red"]
        self.assertEqual(len(polygons), 2)
        routes = [item for item in scene.items if isinstance(item, Path) and not item.closed and item.clip is not None]
        self.assertEqual(len(routes), 2)
        for item in polygons + routes:
            points = [p for part in item.paths for p in part]
            self.assertLess(max(p[0] for p in points)-min(p[0] for p in points), 380*.12)
        arrowheads = [item for item in scene.items if isinstance(item, Path) and item.closed and item.style.get("fill") == "black"]
        self.assertEqual(len(arrowheads), 2, "Only original route endpoints receive arrowheads")
        ET.fromstring(render_svg(scene))

    def test_polygon_hole_survives_projection_and_png(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow is optional")
        ax = MapAxes(None, (0, 0, 1, 1), "mercator")
        ax.set_extent((-12, 12, -12, 12))
        ax.ocean("white")
        ax.polygon([(-10,-10),(10,-10),(10,10),(-10,10)],
                   holes=[[(-3,-3),(3,-3),(3,3),(-3,3)]], facecolor="red", edgecolor="none")
        scene = self.scene(ax)
        paths = [item for item in scene.items if isinstance(item, Path) and item.closed]
        self.assertEqual(len(paths), 1)
        self.assertEqual(len(paths[0].paths), 2)
        stream = io.BytesIO()
        render_png(scene, stream)
        stream.seek(0)
        image = Image.open(stream)
        self.assertEqual(image.getpixel((255,175))[:3], (255,255,255))
        self.assertEqual(image.getpixel((320,175))[:3], (255,0,0))

    def test_multiline_box_is_static_but_geographic_labels_move(self):
        ax = MapAxes(None, (0, 0, 1, 1))
        ax.set_extent((-10, 10, -10, 10))
        ax.info_box("Fonte\nDados de exemplo", background="white", halo="black")
        ax.text(0, 0, "Rio\nprincipal", ha="center", rotation=20)
        ax.grid(step=5)
        scene = self.scene(ax)
        metadata = scene.maps[0]
        static = [scene.items[i] for i in metadata["static_indices"]]
        self.assertEqual(len(static), 3)  # one shared box and two text lines
        self.assertEqual([item.text for item in static if isinstance(item,Text)], ["Fonte","Dados de exemplo"])
        self.assertTrue(metadata["tick_indices"])
        self.assertTrue(all(scene.items[i].clip is None for i in metadata["tick_indices"]))
        self.assertTrue(all("\n" not in item.text for item in scene.items if isinstance(item,Text)))
        ET.fromstring(render_svg(scene))

    def test_line_markers_and_rotated_multiline_block(self):
        ax = MapAxes(None, (0,0,1,1))
        ax.line([(0,0),(1,1),(2,0)], marker="o", color="blue", markersize=6)
        scene = self.scene(ax)
        self.assertEqual(len([item for item in scene.items if isinstance(item,Circle)]), 3)
        block=Scene(100,100)
        _add_text(block,50,50,"A\nB",text_style(dict(rotation=90,ha="center",va="center",background="white")))
        texts=[item for item in block.items if isinstance(item,Text)]
        self.assertAlmostEqual(texts[0].y,texts[1].y)
        self.assertLess(texts[0].x,texts[1].x)
        self.assertEqual(len([item for item in block.items if isinstance(item,Path)]),1)


if __name__ == "__main__":
    unittest.main()

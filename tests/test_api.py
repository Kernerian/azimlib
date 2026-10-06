"""Plotting API regression tests: overrides, layer state, themes and validation."""
from __future__ import annotations

import math
import unittest

from azimlib.axes import MapAxes
from azimlib.geometry import FeatureCollection
from azimlib.io import read_geojson


def regions():
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "id": name,
         "properties": {"name": name, "value": value, "group": group},
         "geometry": {"type": "Polygon", "coordinates": [
             [[x, 0], [x+1, 0], [x+1, 1], [x, 1], [x, 0]]
         ]}}
        for x, name, value, group in [(0, "A", 10, "north"), (2, "B", 20, "south"),
                                      (4, "C", 30, "north"), (6, "D", None, None)]
    ]}


class AxesTests(unittest.TestCase):
    def setUp(self):
        self.ax = MapAxes(None, (0, 0, 1, 1))

    def test_user_overrides_all_convenience_defaults(self):
        self.ax.map("Brazil", facecolor="white", linewidth=2, zorder=7)
        self.assertEqual(self.ax.layers[-1].style["facecolor"], "white")
        for method in (self.ax.countries, self.ax.states, self.ax.rivers,
                       self.ax.lakes, self.ax.coastlines, self.ax.borders):
            with self.subTest(method=method.__name__):
                layer = method(linewidth=2, zorder=6, fit=False)
                self.assertEqual(layer.style["linewidth"], 2)
                self.assertEqual(layer.zorder, 6)
        for method in (self.ax.roads, self.ax.municipalities):
            self.assertEqual(method(regions(), linewidth=2).style["linewidth"], 2)
        self.assertEqual(self.ax.line([(0, 0), (1, 1)], zorder=10).zorder, 10)
        self.assertFalse(self.ax.route([(0, 0), (1, 1)], arrow=False).style["arrow"])
        self.assertEqual(self.ax.scatter([0], [0], zorder=11).zorder, 11)
        self.assertEqual(self.ax.text(0, 0, "x", zorder=12).zorder, 12)
        self.assertEqual(self.ax.labels(regions(), fontsize=14).style["fontsize"], 14)
        self.assertEqual(self.ax.annotate("x", (0, 0), zorder=13).zorder, 13)
        self.assertEqual(self.ax.info_box("x", fontsize=15).style["fontsize"], 15)
        self.ax.title("Title", fontsize=28)
        self.ax.subtitle("Subtitle", color="red")
        self.assertEqual(self.ax._title[1]["fontsize"], 28)
        self.assertEqual(self.ax._subtitle[1]["color"], "red")
        self.assertEqual(self.ax.grid(alpha=.2).style["alpha"], .2)

    def test_style_aliases_override_defaults(self):
        self.assertEqual(self.ax.states(lw=3).style["linewidth"], 3)
        self.assertEqual(self.ax.map("Brazil", fc="white").style["facecolor"], "white")
        self.assertEqual(self.ax.grid(ls="--").style["linestyle"], "--")

    def test_native_collection_is_accepted(self):
        data = read_geojson(regions())
        self.assertIsInstance(data, FeatureCollection)
        self.assertIs(self.ax.geojson(data).data, data)
        self.assertIs(self.ax.choropleth(data, "value").data, data)
        self.assertIs(self.ax.categorical(data, "group").data, data)
        self.assertIs(self.ax.labels(self.ax.layers[0]).data, data)

    def test_styles_can_vary_per_feature(self):
        callback = lambda feature: {"facecolor": "red" if feature.id == "A" else "white"}
        layer = self.ax.geojson(regions(), style=callback)
        self.assertIs(layer.options["feature_style"], callback)
        with self.assertRaises(TypeError):
            self.ax.geojson(regions(), style={"facecolor": "red"})

    def test_failed_add_does_not_change_axes(self):
        for call in (
            lambda: self.ax.geojson(regions(), linewidth=-1),
            lambda: self.ax.geojson(regions(), misspelled_color="red"),
            lambda: self.ax.scatter([80], [20], linewidth=-1),
        ):
            with self.assertRaises((TypeError, ValueError)):
                call()
            self.assertIsNone(self.ax._bounds)
            self.assertEqual(self.ax.layers, [])

    def test_grid_replace_hide_and_invalid_preserves_old_grid(self):
        first = self.ax.grid(step=10)
        with self.assertRaises(ValueError):
            self.ax.grid(step=0)
        self.assertIn(first, self.ax.layers)
        second = self.ax.grid(step=5)
        self.assertNotIn(first, self.ax.layers)
        self.assertIsNone(first._axes)
        self.assertEqual([layer for layer in self.ax.layers if layer.kind == "grid"], [second])
        self.ax.grid(False)
        self.assertEqual(self.ax.layers, [])

    def test_layer_handles_mutate_visibility_and_remove(self):
        layer = self.ax.line([(0, 0), (1, 1)])
        self.assertIs(layer.set(color="red", linewidth=3), layer)
        self.assertEqual(layer.style["color"], "red")
        self.assertEqual(layer.style["linewidth"], 3)
        layer.set_visible(False)
        self.assertFalse(layer.visible)
        layer.remove()
        layer.remove()
        self.assertNotIn(layer, self.ax.layers)
        self.assertIsNone(layer._axes)

    def test_clear_resets_artists_decorations_and_bounds(self):
        layer = self.ax.geojson(regions())
        projection = self.ax.projection
        self.ax.title("Title")
        self.ax.scale_bar()
        self.ax.north_arrow()
        self.ax.set_axis_off()
        self.ax.inset()
        self.ax.clear()
        self.assertIs(self.ax.projection, projection)
        self.assertEqual(self.ax.layers, [])
        self.assertEqual(self.ax.insets, [])
        self.assertIsNone(layer._axes)
        self.assertIsNone(self.ax._bounds)
        self.assertIsNone(self.ax._title)
        self.assertIsNone(self.ax._scale_bar)
        self.assertTrue(self.ax._frame)

    def test_explicit_extent_and_fit_false(self):
        self.ax.set_extent((-5, 5, -3, 3))
        self.ax.map("Brazil", fit=False)
        self.assertEqual(self.ax.get_extent(), (-5, 5, -3, 3))
        self.assertIsNone(self.ax._bounds)
        for extent in ((180, -180, 0, 1), (-190, 10, 0, 1), (0, 1, 3, 3), (0, 1, 0, float("nan"))):
            with self.assertRaises(ValueError):
                self.ax.set_extent(extent)

    def test_point_at_pole_has_valid_extent(self):
        for latitude in (-90, 90):
            self.ax.clear()
            self.ax.scatter([0], [latitude])
            west, east, south, north = self.ax.get_extent()
            self.assertLess(west, east)
            self.assertLess(south, north)
            self.assertLessEqual(south, latitude)
            self.assertGreaterEqual(north, latitude)

    def test_scatter_broadcast_validation_and_polygon_closure(self):
        layer = self.ax.scatter([0, 1], [0, 1], s=[4, 9], c=["red", "blue"])
        self.assertEqual(layer.options["sizes"], [4, 9])
        self.assertEqual(layer.options["colors"], ["red", "blue"])
        for call in (lambda: self.ax.scatter([0], [0, 1]),
                     lambda: self.ax.scatter([0], [0], s=-1),
                     lambda: self.ax.scatter([0, 1], [0, 1], c=["red"]),
                     lambda: self.ax.scatter([0], [91])):
            with self.assertRaises(ValueError):
                call()
        polygon = self.ax.polygon([(0, 0), (1, 0), (1, 1)])
        ring = polygon.data[0].geometry.coordinates[0]
        self.assertEqual(ring[0], ring[-1])

    def test_choropleth_missing_mapping_and_constant(self):
        layer = self.ax.choropleth(regions(), {"A": 5, "B": 5, "C": 5}, missing_color="gray", linewidth=2)
        self.assertEqual(layer.options["color_scale"]["edges"], [5, 5])
        fills = [style["facecolor"] for style in layer.options["feature_styles"]]
        self.assertEqual(len(set(fills[:3])), 1)
        self.assertEqual(fills[3], "gray")
        self.assertEqual(layer.legend_entries[-1][0], "Sem dados")
        self.assertEqual(layer.style["linewidth"], 2)
        self.ax.colorbar(layer, label="Value")
        self.assertIs(self.ax._colorbar["layer"], layer)

    def test_choropleth_quantiles_and_extreme_finite_numbers(self):
        layer = self.ax.choropleth(regions(), [1, 1, 1, 9], scheme="quantile", bins=5)
        edges = layer.options["color_scale"]["edges"]
        self.assertEqual(edges, sorted(set(edges)))
        self.assertEqual(len(layer.legend_entries), len(edges)-1)
        layer = self.ax.choropleth(regions(), [-1e308, 0, 1e308, None])
        self.assertTrue(all(math.isfinite(edge) for edge in layer.options["color_scale"]["edges"]))

    def test_thematic_invalid_parameters(self):
        for options in ({"bins": 0}, {"bins": True}, {"bins": 2.5},
                        {"scheme": "invented"}, {"vmin": 5, "vmax": 1},
                        {"vmin": float("inf")}, {"cmap": "missing"}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.ax.choropleth(regions(), "value", **options)
        with self.assertRaises(ValueError):
            self.ax.choropleth(regions(), [None]*4)
        with self.assertRaises(ValueError):
            self.ax.choropleth(regions(), [1])
        with self.assertRaises(ValueError):
            self.ax.colorbar(self.ax.geojson(regions()))

    def test_categorical_palette_and_missing(self):
        layer = self.ax.categorical(regions(), [1, 2, 1, None], colors={1: "red", 2: "blue"}, missing_color="gray", linewidth=3)
        self.assertEqual([style["facecolor"] for style in layer.options["feature_styles"]], ["red", "blue", "red", "gray"])
        self.assertEqual(layer.style["linewidth"], 3)
        with self.assertRaises(ValueError):
            self.ax.categorical(regions(), "group", colors=[])
        with self.assertRaises(ValueError):
            self.ax.categorical(regions(), "group", colors={"north": "red"})

    def test_density_is_nonempty_with_coincident_and_polar_points(self):
        for latitudes in ([0, 0, 0], [89.9, 90, 90]):
            layer = self.ax.density([0, 0, 0], latitudes, bins=4, smoothing=0, linewidth=.4)
            self.assertGreater(len(layer.data), 0)
            self.assertTrue(all(feature.geometry.type == "Polygon" for feature in layer.data))
            self.assertEqual(layer.style["linewidth"], .4)
            self.assertGreater(layer.options["color_scale"]["vmax"], 0)
        for options in ({"bins": 1}, {"bins": 101}, {"smoothing": -1}, {"smoothing": float("nan")}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.ax.density([0], [0], **options)
        with self.assertRaises(ValueError):
            self.ax.density([], [])

    def test_decorations_validate_parameters(self):
        for call in (lambda: self.ax.legend(fontsize=-1),
                     lambda: self.ax.legend(loc="middle"),
                     lambda: self.ax.scale_bar(length=0),
                     lambda: self.ax.scale_bar(units="leagues"),
                     lambda: self.ax.north_arrow(size=float("nan")),
                     lambda: self.ax.inset((.9, .9, .5, .5)),
                     lambda: self.ax.text(0, 91, "invalid"),
                     lambda: self.ax.annotate("invalid", (0, 0), (0, 95), textcoords="data"),
                     lambda: self.ax.roads(), lambda: self.ax.municipalities()):
            with self.assertRaises(ValueError):
                call()

    def test_plot_formats_return_artist_list(self):
        artists = self.ax.plot([0, 1], [0, 1], "r--")
        self.assertIsInstance(artists, list)
        self.assertEqual(len(artists), 1)
        self.assertEqual(artists[0].style["color"], "#ff0000")
        self.assertEqual(artists[0].style["linestyle"], "--")
        artist, = self.ax.plot([0, 1], [0, 1], "bo-")
        self.assertEqual(artist.style["marker"], "o")
        self.assertEqual(artist.style["color"], "#0000ff")
        self.assertEqual(artist.style["linestyle"], "-")
        artist, = self.ax.plot([(0, 0), (1, 1)], "ko", color="green")
        self.assertEqual(artist.style["color"], "green")
        self.assertEqual(artist.style["linewidth"], 0)
        artist, = self.ax.plot([0], [0], "ro")
        self.assertEqual(artist.data[0].geometry.type, "MultiPoint")
        for fmt in ("rr-", "bo--:", "invalid", 42):
            with self.subTest(fmt=fmt), self.assertRaises(ValueError):
                self.ax.plot([0, 1], [0, 1], fmt)

    def test_plot_color_cycle_resets_on_clear(self):
        first, = self.ax.plot([0, 1], [0, 1])
        second, = self.ax.plot([0, 1], [0, 1])
        self.assertNotEqual(first.style["color"], second.style["color"])
        self.ax.clear()
        reset, = self.ax.plot([0, 1], [0, 1])
        self.assertEqual(reset.style["color"], first.style["color"])

    def test_matplotlib_style_limits_and_labels(self):
        self.assertEqual(self.ax.set_xlim(-50, -40), (-50, -40))
        self.assertEqual(self.ax.set_ylim((-30, -20)), (-30, -20))
        self.assertEqual(self.ax.get_xlim(), (-50, -40))
        self.assertEqual(self.ax.get_ylim(), (-30, -20))
        self.assertEqual(self.ax.set_xlim(right=-35), (-50, -35))
        self.assertEqual(self.ax.set_ylim(bottom=-35), (-35, -20))
        self.ax.set_xlabel("Longitude", fontsize=12)
        self.ax.set_ylabel("Latitude", color="red")
        self.assertEqual(self.ax.get_xlabel(), "Longitude")
        self.assertEqual(self.ax.get_ylabel(), "Latitude")
        self.assertEqual(self.ax._xlabel[1]["fontsize"], 12)
        self.assertEqual(self.ax._ylabel[1]["color"], "red")
        self.ax.clear()
        self.assertEqual(self.ax.get_xlabel(), "")
        self.assertEqual(self.ax.get_ylabel(), "")
        with self.assertRaises(ValueError):
            self.ax.set_ylim(-100, 50)

    def test_zoom_and_pan_preserve_expected_geographic_spans(self):
        self.ax.set_extent((-20, 20, -10, 10))
        self.assertIs(self.ax.zoom(), self.ax)
        self.assertEqual(self.ax.get_extent(), (-10, 10, -5, 5))
        self.assertIs(self.ax.pan(5, 3), self.ax)
        self.assertEqual(self.ax.get_extent(), (-5, 15, -2, 8))
        self.ax.zoom(2, center=(178, 89))
        west, east, south, north = self.ax.get_extent()
        self.assertEqual((west, east), (170, 180))
        self.assertEqual((south, north), (85, 90))
        self.ax.pan(-400, -200)
        self.assertEqual(self.ax.get_extent(), (-180, -170, -90, -85))
        self.ax.zoom(.001)
        self.assertEqual(self.ax.get_extent(), (-180, 180, -90, 90))
        for call in (lambda: self.ax.zoom(0), lambda: self.ax.zoom(-1),
                     lambda: self.ax.zoom(float("nan")),
                     lambda: self.ax.zoom(center=(200, 0)),
                     lambda: self.ax.pan(float("inf"), 0)):
            with self.assertRaises(ValueError):
                call()

    def test_overview_navigation_options(self):
        self.assertIsNone(self.ax._overview)
        self.assertIs(self.ax.overview(loc="lower left"), self.ax._overview)
        self.assertEqual(self.ax._overview['loc'], 'lower left')
        self.ax.overview(False)
        self.assertFalse(self.ax._overview.get_visible())
        with self.assertRaises(ValueError):
            self.ax.overview(loc="center")


class PublicFigureTests(unittest.TestCase):
    def test_subplot_shape_and_shared_figure(self):
        import azimlib as om
        fig, ax = om.subplots()
        self.assertIs(ax.figure, fig)
        fig, axes = om.subplots(2, 2)
        self.assertEqual(len(axes), 2)
        self.assertEqual(len(axes[0]), 2)
        self.assertTrue(all(ax.figure is fig for row in axes for ax in row))

    def test_single_dimension_subplot_squeeze(self):
        import azimlib as om
        fig, axes = om.subplots(1, 2)
        self.assertEqual(len(axes), 2)
        self.assertTrue(all(ax.figure is fig for ax in axes))
        fig, axes = om.subplots(1, 1, squeeze=False)
        self.assertIs(axes[0][0].figure, fig)


if __name__ == "__main__":
    unittest.main()

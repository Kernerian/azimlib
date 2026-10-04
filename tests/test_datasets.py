"""Offline geographic data integrity and public catalog behavior."""

import gzip
import hashlib
from importlib.resources import files
import json
import unittest
from unittest.mock import patch

from azimlib import datasets


class DatasetTests(unittest.TestCase):
    def test_real_brazil_states(self):
        states = datasets.load("states", country="Brasil")["features"]
        self.assertEqual(len(states), 27)
        self.assertEqual(len({state["properties"]["iso_3166_2"] for state in states}), 27)
        self.assertIn("BR-DF", {state["properties"]["iso_3166_2"] for state in states})
        self.assertIn("São Paulo", {state["properties"]["name"] for state in states})
        self.assertTrue(all(state["geometry"]["type"] in ("Polygon", "MultiPolygon") for state in states))

    def test_country_aliases_and_detail(self):
        brazil = datasets.country("Brazil")
        for alias in ("brasil", " BR ", "BRA", "bRaZiL"):
            self.assertEqual(datasets.country(alias), brazil)
        self.assertEqual(datasets.country("FR")["features"][0]["properties"]["adm0_a3"], "FRA")
        self.assertEqual(datasets.country("França"), datasets.country("France"))
        self.assertEqual(len(datasets.country("world")["features"]), 177)
        self.assertEqual(brazil["features"][0]["geometry"]["type"], "MultiPolygon")

    def test_no_shared_mutable_data(self):
        first = datasets.load("states")
        first["features"][0]["properties"]["name"] = "changed"
        first["features"].pop()
        again = datasets.load("states")
        self.assertEqual(len(again["features"]), 27)
        self.assertNotEqual(again["features"][0]["properties"]["name"], "changed")
        selected = datasets.country("FR")
        selected["features"][0]["geometry"]["coordinates"].clear()
        self.assertTrue(datasets.country("FR")["features"][0]["geometry"]["coordinates"])

    def test_unavailable_requests_are_explicit(self):
        for name in ("Atlantis", "", "not-a-country"):
            with self.assertRaises(ValueError):
                datasets.country(name)
        with self.assertRaisesRegex(ValueError, "Brazil only"):
            datasets.load("states", country="USA")
        with self.assertRaisesRegex(ValueError, "not bundled"):
            datasets.load("municipalities")

    def test_country_physical_layer_selection(self):
        rivers = datasets.load("rivers", country="BR")
        self.assertGreater(len(rivers["features"]), 10)
        self.assertLess(len(rivers["features"]), len(datasets.load("rivers")["features"]))
        self.assertTrue(all(feature["geometry"]["type"] in ("LineString", "MultiLineString") for feature in rivers["features"]))

    def test_archive_integrity_and_feature_counts(self):
        manifest = datasets.provenance()
        for name, entry in manifest["layers"].items():
            with self.subTest(layer=name):
                raw = files("azimlib").joinpath("data", entry["filename"]).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), entry["sha256"])
                payload = json.loads(gzip.decompress(raw))
                self.assertEqual(len(payload["features"]), entry["features"])
                self.assertEqual(payload["type"], "FeatureCollection")

    def test_polygon_rings_remain_closed(self):
        for name in ("countries", "brazil", "states", "lakes"):
            payload = datasets.country("Brazil") if name == "brazil" else datasets.load(name)
            for feature in payload["features"]:
                geometry = feature["geometry"]
                polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
                for polygon in polygons:
                    for ring in polygon:
                        self.assertGreaterEqual(len(ring), 4)
                        self.assertEqual(ring[0], ring[-1])

    def test_catalog_is_offline(self):
        with patch("socket.socket", side_effect=AssertionError("network unavailable")):
            self.assertEqual(len(datasets.load("countries")["features"]), 177)
            catalog = datasets.catalog()
            self.assertTrue(all(entry["available"] and entry["offline"] for entry in catalog.values()))
            self.assertEqual(catalog["states"]["coverage"], "Brazil")


if __name__ == "__main__":
    unittest.main()

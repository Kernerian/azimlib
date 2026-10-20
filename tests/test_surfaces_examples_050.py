"""The gallery exercises the existing Figure/Axes/Artists, never placeholders."""
import importlib.util
from pathlib import Path
import unittest
import azimlib as a


class SurfaceExamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=Path(__file__).resolve().parents[1]/'examples/planetary/surfaces_050.py'
        spec=importlib.util.spec_from_file_location('surface_example',path);cls.example=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.example)
    def tearDown(self):a.close('all')
    def test_small_preset_maps_render_as_real_scene(self):
        for b in (a.MOON,a.MARS,a.VENUS,a.MERCURY):
            f,meta=self.example.mapped(b);scene=f.to_scene()
            self.assertIs(f.axes[0].get_body(),b);self.assertGreater(len(scene.items),10)
            self.assertIn('Synthetic',f.to_svg());self.assertEqual(meta['model'],b.shape)
    def test_terrain_texture_and_lighting_use_existing_surface_artist(self):
        from azimlib.terrain_axes import SurfaceArtist
        for textured in (True,False):
            f,meta=self.example.terrain(a.MARS,textured=textured)
            ax=f.axes[0];self.assertIsInstance(ax.layers[0],SurfaceArtist)
            self.assertEqual(ax.vertical_exaggeration,4);self.assertGreater(len(f.to_scene().items),2)
            self.assertIs(ax.layers[0].axes,ax)
            if textured:self.assertIsNotNone(ax.layers[0].get_texture())
            else:self.assertIsNone(ax._solar_lighting.model)
    def test_profile_and_comparison_keep_context_and_units(self):
        f,meta=self.example.lunar_profile();self.assertIn('Surface geodesic distance',f.to_svg())
        f,meta=self.example.comparison();self.assertIs(f.axes[0].get_body(),a.EARTH);self.assertIs(f.axes[1].get_body(),a.MARS)
        self.assertNotEqual(f.axes[0].layers[0].get_context(),f.axes[1].layers[0].get_context())
    def test_incidence_does_not_construct_an_ephemeris(self):
        from unittest.mock import patch
        with patch('azimlib.lighting.SolarModel',side_effect=AssertionError('No ephemeris')):
            f,meta=self.example.incidence();self.assertIn('terminator',f.to_svg())


if __name__=='__main__':unittest.main()

"""Own toolbar artwork: transparent counters, symmetry and dependency boundary."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
import azimlib
from azimlib._toolbar_icons import NAMES,icon_image,icon_svg


class ToolbarIconTests(unittest.TestCase):
    def test_assets_match_original_geometry_manifest(self):
        root=Path(azimlib.__file__).parent
        manifest=json.loads((root/'assets/icons/manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['source'],'Original Azimlib geometry')
        self.assertEqual(manifest['license'],'BSD-3-Clause')
        self.assertEqual(manifest['geometry_sha256'],hashlib.sha256((root/'_toolbar_icons.py').read_bytes()).hexdigest())
        self.assertEqual(len(manifest['files_sha256']),21)
        for name,digest in manifest['files_sha256'].items():
            with self.subTest(name=name):self.assertEqual(hashlib.sha256((root/'assets/icons'/name).read_bytes()).hexdigest(),digest)

    def test_svg_uses_only_our_geometry_without_optional_imports(self):
        for name in NAMES:
            with self.subTest(name=name):
                svg=icon_svg(name);root=ET.fromstring(svg)
                self.assertEqual(root.get('viewBox'),'0 0 24 24')
                self.assertIn('Azimlib',svg)
                self.assertNotIn('matplotlib',svg.lower())
                self.assertNotIn('href=',svg)
                self.assertNotIn('<script',svg)
        code=f"import sys;sys.path.insert(0,{str(Path(azimlib.__file__).parent.parent)!r});from azimlib._toolbar_icons import icon_svg;assert '<svg' in icon_svg('home');assert 'PIL' not in sys.modules;assert 'matplotlib' not in sys.modules"
        result=subprocess.run([sys.executable,'-S','-c',code],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_directional_icons_are_balanced_after_rasterization(self):
        from PIL import Image,ImageOps,ImageChops
        with icon_image('back',48) as back,icon_image('forward',48) as forward:
            a=back.getchannel('A');b=ImageOps.mirror(forward.getchannel('A'))
            delta=ImageChops.difference(a,b)
            self.assertLess(sum(delta.tobytes())/sum(a.tobytes()),.035)
        with icon_image('move',48) as pan:
            a=pan.getchannel('A');b=a.transpose(Image.Transpose.ROTATE_90)
            delta=ImageChops.difference(a,b)
            self.assertLess(sum(delta.tobytes())/sum(a.tobytes()),.035)

    def test_transparent_counters_and_edge_sampling_survive_small_sizes(self):
        for size in (18,24,30,36,48):
            with self.subTest(size=size),icon_image('zoom_to_rect',size) as image:
                alpha=image.getchannel('A')
                self.assertEqual(alpha.getpixel((round(size*10/24),round(size*10/24))),0)
                self.assertTrue(any(0<value<255 for value in alpha.tobytes()))
                self.assertEqual(image.size,(size,size))
        with icon_image('filesave') as save:
            self.assertEqual(save.getpixel((12,6))[3],0)
            self.assertGreater(save.getpixel((8,6))[3],200)

    def test_unknown_icons_and_invalid_sizes_are_rejected(self):
        with self.assertRaises(ValueError):icon_svg('missing')
        for size in (0,-1,1.5):
            with self.subTest(size=size),self.assertRaises(ValueError):icon_image('home',size)

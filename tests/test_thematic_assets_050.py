"""Independent/adversarial contracts for own icons; no network or borrowed artwork."""
import dataclasses,hashlib,io,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import azimlib as a
from azimlib.thematic_assets import parse_svg
S=a.AssetSource('synthetic:test','BSD-3-Clause','Original test geometry')

class ThematicAssets(unittest.TestCase):
    def svg(self,body,extra=''):
        return parse_svg(('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 10" '+extra+'>'+body+'</svg>').encode(),name='test',source=S)
    def test_catalog_is_original_and_return_value_is_independent(self):
        required={'city','village','port','gold','salt','ivory','fortress','mine','monument','landing','rover','probe','instrument','battle','temple','base'}
        c=a.symbol_catalog();self.assertTrue(required<=c.keys())
        for definition in c.values():
            self.assertEqual(definition.source.license,'BSD-3-Clause');self.assertTrue(definition.source.origin.startswith('azimlib:'))
            with self.assertRaises(dataclasses.FrozenInstanceError):definition.name='changed'
        c.clear();self.assertGreater(len(a.symbol_catalog()),15)
    def test_custom_definition_freezes_input(self):
        p=[[(0,0),(1,0),(0,1)]];d=a.SymbolDefinition.from_paths('custom',p,source=S);p[0][0]=(2,2)
        self.assertEqual(d.parts[0].paths[0][0],(0,0))
    def test_provenance_and_budgets_reject_invalid(self):
        for values in (('', 'BSD','X'),('source','','X'),('source','BSD','')):
            with self.assertRaises(ValueError):a.AssetSource(*values)
        for sha in (None,'abc','g'*64):
            with self.assertRaises(ValueError):a.AssetSource('a','b','c',sha)
        with self.assertRaises(ValueError):a.SymbolDefinition('bad',(0,0,0,1),(a.SymbolPart((((0,0),(1,1)),)),),S)
        with self.assertRaises(ValueError):a.SymbolPart((tuple((i,0) for i in range(16385)),))
    def test_svg_shapes_and_aspect(self):
        d=self.svg('<rect x="1" y="1" width="5" height="4" fill="#f00"/><circle cx="12" cy="5" r="3"/><line x1="1" y1="8" x2="8" y2="8" stroke="black" stroke-width="1"/>')
        self.assertEqual(d.viewbox,(0,0,20,10));self.assertEqual(len(d.parts),3)
    def test_svg_affine_transform_and_inherited_opacity(self):
        d=self.svg('<g transform="translate(2 1) scale(2)"><rect width="3" height="2" opacity="0.5"/></g>')
        self.assertEqual(d.parts[0].paths[0][0],(2,1));self.assertEqual(dict(d.parts[0].style)['alpha'],.5)
    def test_svg_bezier_endpoints_and_hole_parity(self):
        d=self.svg('<path fill-rule="evenodd" d="M1 1 C3 2 5 2 7 1 L7 8 L1 8 Z M2 3 L2 6 L5 6 L5 3 Z"/>')
        self.assertEqual(len(d.parts[0].paths),2);self.assertEqual(d.parts[0].paths[0][0],(1,1));self.assertIn((7,1),d.parts[0].paths[0])
    def test_svg_relative_moves_quadratic_horizontal_vertical(self):
        d=self.svg('<path fill="none" d="M2 2 h4 v4 h-4 z m8 0 q2 4 4 0"/>')
        self.assertEqual(len(d.parts),2);self.assertIn((6,6),d.parts[0].paths[0])
    def test_svg_script_entity_external_and_active_resources_rejected(self):
        bad=['<script>alert(1)</script>','<image href="https://example.test/a.png"/>','<use href="#a"/>','<foreignObject/>','<text>active</text>','<path d="M0 0 L1 1" onclick="x()"/>','<path d="M0 0 L1 1" fill="url(https://x)"/>','<style>path{fill:red}</style>']
        for body in bad:
            with self.subTest(body=body),self.assertRaises((ValueError,TypeError)):self.svg(body)
        for raw in (b'<!DOCTYPE svg [<!ENTITY a "x">]><svg/>','<svg/>'.encode('utf-16')):
            with self.assertRaises(ValueError):parse_svg(raw,name='bad',source=S)
    def test_svg_unsupported_arc_css_and_outside_viewbox_fail_explicitly(self):
        for body in ('<path d="M0 0 A1 1 0 0 0 2 2"/>','<rect width="2" height="2" style="filter:blur(2)"/>','<g transform="skewX(3)"/>','<rect x="30" width="2" height="2"/>','<path d="M0 0 L1e309 1"/>'):
            with self.subTest(body=body),self.assertRaises(ValueError):self.svg(body)
    def test_svg_resource_budgets(self):
        for body in ('<g>'*10+'<rect width="2" height="2"/>'+'</g>'*10,'<rect width="1" height="1"/>'*260):
            with self.assertRaises(ValueError):self.svg(body)
        with self.assertRaises(ValueError):parse_svg(b' '*262145,name='x',source=S)
    def test_file_hash_and_no_network(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'x.svg';p.write_bytes(b'<svg viewBox="0 0 1 1"><rect width="1" height="1"/></svg>')
            with patch('urllib.request.urlopen',side_effect=AssertionError('implicit network')):
                icon=a.SymbolDefinition.from_svg(p,source=S);self.assertEqual(icon.source.sha256,hashlib.sha256(p.read_bytes()).hexdigest())
                with self.assertRaises(ValueError):a.SymbolDefinition.from_svg(p,source=a.AssetSource('x','BSD','y','0'*64))
    def test_png_preserves_pixels_and_partial_alpha(self):
        try:from PIL import Image
        except ImportError:self.skipTest('Optional PNG loader requires Pillow')
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'x.png';im=Image.new('RGBA',(8,4),(255,10,40,128));im.putpixel((0,0),(0,0,0,0));im.save(p);im.close()
            icon=a.SymbolDefinition.from_png(p,source=S);self.assertEqual(icon.kind,'png');self.assertEqual(icon.raster[:2],(8,4));self.assertEqual(icon.raster[2][7],128)
    def test_png_malformed_and_oversized_headers_rejected_before_decode(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'x.png'
            for raw in (b'not png',b'\x89PNG\r\n\x1a\n'+b'\0'*8+struct.pack('>II',100000,100000)+b'\0'*9):
                p.write_bytes(raw)
                with self.assertRaises(ValueError):a.SymbolDefinition.from_png(p,source=S)
    def test_png_transparent_and_animated_refused(self):
        try:from PIL import Image
        except ImportError:self.skipTest('Optional PNG loader requires Pillow')
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'x.png'
            with Image.new('RGBA',(4,4)) as im:im.save(p)
            with self.assertRaises(ValueError):a.SymbolDefinition.from_png(p,source=S)
            with Image.new('RGBA',(4,4),'red') as im,Image.new('RGBA',(4,4),'blue') as other:im.save(p,save_all=True,append_images=[other],duration=100)
            with self.assertRaises(ValueError):a.SymbolDefinition.from_png(p,source=S)

    def test_group_compositing_is_not_silently_approximated(self):
        with self.assertRaises(ValueError):parse_svg(b'<svg viewBox="0 0 10 10"><g opacity=".5"><rect width="5" height="5"/></g></svg>',name='x',source=S)
        icon=parse_svg(b'<svg viewBox="0 0 10 10" fill-opacity=".5"><rect width="5" height="5" fill-opacity=".8"/></svg>',name='x',source=S)
        self.assertEqual(dict(icon.parts[0].style)['fill_alpha'],.8)
        with self.assertRaises(ValueError):self.svg('<g transform="scale(2 1)"><line x1="1" y1="1" x2="2" y2="2" stroke="red" stroke-width="1"/></g>')
        with self.assertRaises(ValueError):self.svg('<g transform="scale(0)"><rect width="2" height="2"/></g>')

if __name__=='__main__':unittest.main()

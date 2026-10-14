"""Complex shaping contracts, independent oracles, backend/Artist integration."""
import copy
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import azimlib as azl
from azimlib.scene import Scene,Text
from azimlib.styles import text_style
from azimlib.typography import text_width,text_bounds
from azimlib.text_engine import (shape_text,cluster_units,register_font,text_context,
                                TextEngineError,MissingGlyphError,FontPermissionError)
from azimlib._unicode_icu import graphemes,visual_runs,unicode_version

AVAILABLE=all(importlib.util.find_spec(n) for n in ('uharfbuzz','fontTools','aggdraw','PIL'))
STYLE=dict(textengine='harfbuzz',font_size=20)
ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(AVAILABLE,'Optional text/PNG dependencies are not installed')
class TextEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:unicode_version()
        except RuntimeError as exc:raise unittest.SkipTest(str(exc))
    def tearDown(self):azl.close('all')

    def test_unicode_offsets_graphemes_isolates(self):
        self.assertEqual(graphemes('A\u0301😀Z'),((0,2),(2,3),(3,4)))
        self.assertEqual(graphemes('👩\u200d🔬'),((0,3),))
        runs=visual_runs('abc אבג 123','ltr')
        self.assertEqual(runs,((0,4,'ltr'),(8,11,'ltr'),(4,8,'rtl')))
        isolated=visual_runs('A\u2067אב\u2069Z')
        self.assertTrue(any(r[2]=='rtl' for r in isolated))
        self.assertEqual(sorted(i for a,b,d in isolated for i in range(a,b)),list(range(6)))
        self.assertGreater(shape_text('A\u2067אב\u2069Z',STYLE).width,0)

    def test_ligature_marks_and_arabic_context(self):
        lig=shape_text('office',STYLE)
        self.assertLess(len(lig.glyphs),6)
        self.assertGreater(len(shape_text('office',dict(STYLE,fontfeatures={'liga':0})).glyphs),len(lig.glyphs))
        self.assertAlmostEqual(shape_text('A\u0301',STYLE).width,shape_text('Á',STYLE).width)
        arabic=shape_text('العربية',STYLE)
        self.assertEqual(arabic.runs[0].direction,'rtl')
        self.assertGreater(arabic.glyphs[0].start,arabic.glyphs[-1].start)
        isolated=[shape_text(c,STYLE).glyphs[0].glyph for c in 'العربية']
        self.assertNotEqual([g.glyph for g in arabic.glyphs],isolated[::-1])
        self.assertTrue(all(0<=g.start<g.end<=len(arabic.text) for g in arabic.glyphs))

    def test_original_bidi_bracket_marks_overrides_depth_and_limits(self):
        from azimlib._bidi import resolved_levels
        # A mark on a paired bracket must retain its base's resolved direction.
        for text,direction in [('m(n)\u0331','rtl'),('א(ג)\u0331','ltr')]:
            with self.subTest(direction=direction):
                levels,_=resolved_levels(text,direction)
                self.assertEqual(levels[-1],levels[-2])
                self.assertEqual(sum(b-a for a,b,d in visual_runs(text,direction)),len(text))
        override='\u202eA\u2066B\u2069C\u202c'
        levels,_=resolved_levels(override,'ltr')
        self.assertEqual(levels[2]%2,1)
        self.assertEqual(levels[4]%2,1)
        deep='\u2067'*140+'אב'+'\u2069'*140
        levels,_=resolved_levels(deep,'ltr');self.assertLessEqual(max(levels),126)
        with self.assertRaises(ValueError):visual_runs('x','invalid')
        with self.assertRaises(ValueError):visual_runs('x'*4097)

    def test_direct_harfbuzz_oracle(self):
        import uharfbuzz as hb
        from azimlib.typography import font_path
        raw=font_path({}).read_bytes();face=hb.Face(raw);font=hb.Font(face);units=face.upem
        font.scale=(units,units);hb.ot_font_set_funcs(font)
        for text,direction,script in [('office','ltr','Latn'),('العربية','rtl','Arab'),('אבג','rtl','Hebr')]:
            with self.subTest(text=text):
                buffer=hb.Buffer();buffer.add_codepoints(list(map(ord,text)));buffer.direction=direction;buffer.script=script;buffer.language='und'
                hb.shape(font,buffer)
                actual=shape_text(text,STYLE)
                self.assertEqual([g.glyph for g in actual.glyphs],[g.codepoint for g in buffer.glyph_infos])
                self.assertEqual([g.start for g in actual.glyphs],[g.cluster for g in buffer.glyph_infos])
                self.assertAlmostEqual(actual.width,sum(p.x_advance for p in buffer.glyph_positions)/units)

    def test_validation_missing_and_no_silent_fallback(self):
        for text in ('中文','नमस्ते','\ud800','a\tb','a\u2029b','a'*4097):
            with self.subTest(text=ascii(text[:20])):
                with self.assertRaises((TextEngineError,UnicodeError)):shape_text(text,STYLE)
        for options in ({'direction':'bad'},{'language':'../ar'},{'fontfeatures':{'broken':1}},{'fontfallback':[None]}):
            with self.subTest(options=options):
                with self.assertRaises(TextEngineError):shape_text('abc',dict(STYLE,**options))
        with self.assertRaises(TextEngineError):text_style({'direction':'rtl'})
        with self.assertRaises(TextEngineError):shape_text('a',dict(STYLE,font_family='unknown'))

    def test_context_isolation_and_editable_artists(self):
        from concurrent.futures import ThreadPoolExecutor
        with text_context(direction='rtl',language='ar'):
            fig,ax=azl.subplots(figsize=(5,4))
            title=ax.set_title('العربية')
            label=ax.text(.5,.5,'abc אבג',transform='axes')
            ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
            ax.plot([0,1],[0,1],label='office')
            legend=ax.legend(title='العربية')
            with ThreadPoolExecutor(1) as executor:
                self.assertNotIn('textengine',executor.submit(text_style,{}).result())
        self.assertEqual(title.get_textengine(),'harfbuzz')
        label.set_language('he');label.set_direction('ltr');label.set_fontfeatures({'liga':0})
        self.assertEqual(label.get_language(),'he');self.assertEqual(label.get_direction(),'ltr')
        previous=copy.deepcopy(label.style)
        with self.assertRaises(TextEngineError):label.set_direction('invalid')
        self.assertEqual(label.style,previous)
        scene=fig.to_scene();self.assertTrue(any(isinstance(p,Text) and p.style.get('textengine')=='harfbuzz' for p in scene.items))
        svg=io.StringIO();fig.savefig(svg,format='svg');self.assertIn('data-azimlib-shaped',svg.getvalue())
        label.set_visible(False);self.assertFalse(label.get_visible())
        self.assertNotIn('textengine',text_style({}))
        self.assertTrue(all(p.style.get('textengine')=='harfbuzz' for p in scene.items if isinstance(p,Text)))
        self.assertFalse(any(layer.kind=='grid' and layer.get_visible() for layer in ax.layers))

    def test_shared_outlines_bounds_rotations_dpi_and_notices(self):
        from azimlib.text_engine import text_commands
        from azimlib.renderers import render_svg,render_pdf,render_image,render_png
        from azimlib.label_layout import text_box
        for angle in (0,33,90,180,270):
            for size in (12,24):
                with self.subTest(angle=angle,size=size):
                    style=dict(STYLE,font_size=size,rotation=angle,anchor='middle',baseline='middle',stroke='white',stroke_width=1)
                    item=Text(120,80,'Á office العربية',style,clip=(0,0,240,160));scene=Scene(240,160,items=[item])
                    cmds=list(text_commands(item));box=text_box(item.x,item.y,item.text,style,padding=2)
                    self.assertTrue(cmds);self.assertGreater(box[2],0)
                    svg=render_svg(scene);root=ET.fromstring(svg)
                    self.assertIn('aria-label=',svg);self.assertNotIn('C:\\',svg)
                    self.assertIn('azimlib-material-provenance',svg)
                    shaped=root.findall('.//{http://www.w3.org/2000/svg}g[@data-azimlib-shaped]')
                    self.assertEqual(len(shaped),1)
                    pdf=render_pdf(scene);self.assertIn(b'/ActualText <FEFF',pdf)
                    image=render_image(scene);self.assertEqual(image.size,(240,160));image.close()
        stream=io.BytesIO();render_png(scene,stream)
        from PIL import Image
        with Image.open(io.BytesIO(stream.getvalue())) as image:
            notices=json.loads(image.info['Azimlib material provenance'])
            self.assertEqual(notices[0]['kind'],'font');self.assertIn('license_text',notices[0])
        doubled=Scene(240,160,items=[Text(30,60,'office',STYLE)]).scaled(2)
        self.assertAlmostEqual(text_width(doubled.items[0].text,doubled.items[0].style),2*text_width('office',STYLE))

    def test_curved_clusters_preserve_context_and_marks(self):
        from azimlib.curved_text import curve_candidates
        from azimlib.viewport import Viewport
        from azimlib.render_map import _text
        from azimlib.text_engine import text_commands
        for text in ('office','Á test','العربية'):
            with self.subTest(text=text):
                units=list(cluster_units(text,STYLE));layout=shape_text(text,STYLE)
                self.assertEqual([g.glyph for t,w,k in units for g in t.layout.glyphs],[g.glyph for g in layout.glyphs])
                self.assertAlmostEqual(sum(w for t,w,k in units),text_width(text,STYLE))
                vp=Viewport(azl.Equirectangular(),(-20,-10,20,10),(0,0,600,300))
                poses=next(curve_candidates(azl.Geometry('LineString',((-18,0),(18,0))),vp,text,STYLE))
                self.assertEqual(len(poses),len(units))
                scene=Scene(600,300)
                for t,p,angle in poses:_text(scene,*p,t,dict(STYLE,rotation=angle,anchor='middle'))
                self.assertTrue(all(hasattr(p.text,'layout') for p in scene.items))
                self.assertEqual(sum(len(shape_text(p.text,p.style).glyphs) for p in scene.items),len(layout.glyphs))
                for p in scene.items:
                    if not p.text.isspace():self.assertTrue(list(text_commands(p)))

    def test_registry_provenance_immutable_restrictions(self):
        from azimlib.typography import font_path,FONTS
        license=(FONTS/'LICENSE_DEJAVU').read_text('utf8')
        options=dict(family='Test External DejaVu',source='https://dejavu-fonts.github.io/',license_id='LicenseRef-DejaVu',license_text=license)
        with self.assertRaises(FontPermissionError):register_font(font_path({}),**options)
        record=register_font(font_path({}),**options,allow_outlines=True)
        self.assertEqual(record.sha256,hashlib.sha256(font_path({}).read_bytes()).hexdigest())
        self.assertNotIn(str(font_path({})),json.dumps(record.notice()))
        self.assertEqual(register_font(font_path({}),**options,allow_outlines=True),record)
        with self.assertRaises(TextEngineError):register_font(font_path({'font_weight':'bold'}),**options,allow_outlines=True)
        from fontTools.ttLib import TTFont
        with tempfile.TemporaryDirectory() as folder:
            font=TTFont(font_path({}));font['OS/2'].fsType=2;path=Path(folder)/'restricted.ttf';font.save(path)
            with self.assertRaises(FontPermissionError):register_font(path,**dict(options,family='Restricted Test'),allow_outlines=True)

    def test_cache_and_browser_structure(self):
        from azimlib.backends._raster_cache import scene_key
        from azimlib.viewer import render_html
        a=Scene(100,100,items=[Text(10,30,'office',STYLE)])
        b=Scene(100,100,items=[Text(10,30,'office',dict(STYLE,fontfeatures={'liga':0}))])
        self.assertNotEqual(scene_key(a),scene_key(b))
        self.assertEqual(scene_key(a),scene_key(copy.deepcopy(a)))
        html=render_html(a);self.assertIn("['defs','metadata']",html)
        self.assertIn('data-azimlib-shaped',html);self.assertIn('s.shapedNodes.forEach',html)

    def test_navigation_process_consumes_prepared_glyphs_without_registry(self):
        from azimlib.backends._navigation_process import NavigationProcess
        from azimlib.renderers import render_image
        style=dict(STYLE,font_family='Private Worker Test')
        from azimlib.typography import font_path,FONTS
        register_font(font_path({}),family='Private Worker Test',source='https://dejavu-fonts.github.io/',
                      license_id='LicenseRef-DejaVu',license_text=(FONTS/'LICENSE_DEJAVU').read_text('utf8'),allow_outlines=True)
        scene=Scene(240,100,items=[Text(10,50,'office العربية',style)])
        worker=NavigationProcess()
        try:
            actual=worker.render(scene)
            expected=render_image(scene,_interactive=True)
            self.assertEqual(actual.tobytes(),expected.tobytes());actual.close();expected.close()
        finally:worker.close()


@unittest.skipUnless(AVAILABLE and os.environ.get('AZIMLIB_TEXT_FONTS'),'Explicit optional font fixtures not configured')
class OptionalFontTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import sys
        sys.path.insert(0,str(ROOT/'tools'))
        from acquire_text_fonts import register_acquired
        cls.records=register_acquired(os.environ['AZIMLIB_TEXT_FONTS'])

    def test_indic_cjk_cff_and_cluster_fallback(self):
        from azimlib.renderers import render_svg,render_pdf,render_image
        from azimlib.text_engine import cluster_units
        style=dict(STYLE,fontfallback=tuple(r.family for r in self.records))
        for text in ('नमस्ते भारत','प्रिया','中文地图','日本語','abc العربية नमस्ते 中文'):
            with self.subTest(text=text):
                line=shape_text(text,style);self.assertGreater(line.width,0)
                self.assertTrue(all(g.glyph>0 for g in line.glyphs))
                self.assertEqual([g.glyph for t,w,k in cluster_units(text,style) for g in t.layout.glyphs],[g.glyph for g in line.glyphs])
                scene=Scene(500,100,items=[Text(20,50,text,style)])
                self.assertIn('OFL-1.1',render_svg(scene));self.assertTrue(render_pdf(scene).startswith(b'%PDF'))
                image=render_image(scene);image.close()


if __name__=='__main__':unittest.main()

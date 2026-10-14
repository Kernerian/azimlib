"""Real TeX boundaries, common contours, cache/resource/privacy contracts."""
from dataclasses import replace
import importlib.util
import io
import os
from pathlib import Path
import pickle
import sys
import tempfile
import unittest
from unittest.mock import patch

import azimlib as azl
from azimlib.tex import (TexConfig,TexError,TexUnavailableError,TexResourceError,
                         TexLayout,TexText,tex_layout,_svg_commands,_resources,tex_cache_info)
from azimlib.scene import Text,Scene
from azimlib.styles import text_style,style_dict
from azimlib.typography import text_width,text_line_metrics

NOTICE=azl.Provenance('https://example.org/azimlib-test-outlines','BSD-3-Clause',
                     'Kernerian',license_text='Original synthetic test contours; BSD 3-Clause')
OUTLINE=(('M',(0.,-.8)),('L',(1.,-.8)),('L',(1.,.2)),('L',(0.,.2)),('Z',))
LAYOUT=TexLayout(1.,.8,.2,OUTLINE,(tuple(sorted(dict(kind='tex-font',license='BSD-3-Clause').items())),),'test-identity')
OPTIONAL=all(importlib.util.find_spec(n) for n in ('fontTools','psutil','PIL','aggdraw'))


def config(**kwargs):
    return TexConfig(cache_dir=Path.cwd(),trusted=True,allow_outlines=True,font_notices=(NOTICE,),**kwargs)


class TexContractTests(unittest.TestCase):
    def tearDown(self):azl.close('all')

    def test_explicit_trust_rights_resources_and_limits(self):
        for options in ({},{'trusted':True},{'trusted':True,'allow_outlines':True},
                        {'trusted':True,'allow_outlines':True,'cache_dir':'.'}):
            with self.assertRaises(TexError):TexConfig(**options)
        c=config()
        for change in ({'timeout':0},{'max_memory_bytes':1},{'max_temp_bytes':float('inf')},
                       {'fallback':True},{'font_notices':()}, {'executable':''}):
            with self.assertRaises(TexError):replace(c,**change)
        self.assertNotIn(str(Path.cwd()),repr(c))

    def test_no_tool_install_or_implicit_fallback(self):
        c=config(executable='azimlib-nonexistent-tex-engine')
        with self.assertRaises(TexUnavailableError):tex_layout('hello',dict(textengine='tex',texconfig=c))
        with self.assertWarns(RuntimeWarning):
            result=tex_layout('hello',dict(textengine='tex',texconfig=replace(c,fallback='basic')))
        self.assertIsNone(result)

    def test_configuration_and_context_capture(self):
        c=config()
        with self.assertRaises(ValueError):style_dict(textengine='tex')
        with self.assertRaises(ValueError):style_dict(texconfig=c)
        with self.assertRaises(ValueError):style_dict(textengine='tex',texconfig=c,direction='rtl')
        with azl.tex_context(c):
            fig,ax=azl.subplots();artist=ax.set_title(r'$\frac{1}{2}$')
            self.assertEqual(artist.get_textengine(),'tex')
            self.assertIs(artist.get_texconfig(),c)
            self.assertEqual(text_style({'textengine':'basic'}).get('textengine'),'basic')
        self.assertEqual(text_style({}).get('textengine','basic'),'basic')
        artist.set_texconfig(replace(c,preamble=r'\newcommand{\A}{A}'))
        self.assertIn('newcommand',artist.get_texconfig().preamble)

    def test_prepared_outlines_pickle_workers_metrics_rotation(self):
        prepared=TexText(r'$\notinternalcommand$',LAYOUT)
        item=Text(100,80,prepared,dict(textengine='tex',texconfig=config(),font_size=20,
                  anchor='middle',baseline='alphabetic',rotation=90))
        restored=pickle.loads(pickle.dumps(item))
        self.assertEqual(restored.text.tex_layout,LAYOUT)
        self.assertEqual(text_width(restored.text,restored.style),20)
        self.assertEqual(text_line_metrics(restored.text,restored.style),(16,4))
        from azimlib.font_outline import text_commands
        commands=tuple(text_commands(restored))
        self.assertEqual(commands[0][0],'M')
        self.assertAlmostEqual(commands[0][1][0],116)
        self.assertAlmostEqual(commands[0][1][1],70)
        scene=Scene(200,160);scene.add(restored)
        self.assertEqual(scene.items,[restored]) # limited parser must not run

    @unittest.skipUnless(OPTIONAL,'Optional TeX/PNG dependencies absent')
    def test_all_backends_share_prepared_geometry_and_notices(self):
        from azimlib.renderers import render_svg,render_pdf,render_png
        prepared=TexText(r'$\frac{a}{b}$',LAYOUT)
        s=Scene(160,100,background=None)
        s.add(Text(60,60,prepared,dict(textengine='tex',texconfig=config(),font_size=24,
                     fill='red',opacity=.5,rotation=25)))
        with patch('azimlib.tex._tool',side_effect=AssertionError('Workers must not invoke TeX')):
            svg=render_svg(s);pdf=render_pdf(s);png=io.BytesIO();render_png(s,png)
            self.assertIn('test',str(s.items[0].text.tex_layout.identity))
            self.assertIn('azimlib-material-provenance',svg)
            self.assertIn('/ActualText',pdf.decode('latin1'))
            self.assertTrue(png.getvalue().startswith(b'\x89PNG'))
            self.assertNotIn(str(Path.cwd()),svg)
            self.assertNotIn(str(Path.cwd()).encode(),pdf)
            self.assertNotIn(b'texconfig',png.getvalue())

    @unittest.skipUnless(importlib.util.find_spec('fontTools'),'fontTools absent')
    def test_svg_subset_curves_transforms_rules_and_references(self):
        raw=b'''<svg viewBox="0 0 30 20"><defs><g id="g"><path d="M 0 0 C 1 2 3 4 5 6 Z"/></g></defs><g fill="rgb(0%, 0%, 0%)" fill-opacity="1"><use href="#g" x="4" y="7"/></g><path fill="none" stroke="black" stroke-width="2" d="M 1 2 L 5 2" transform="matrix(1,0,0,1,2,3)"/></svg>'''
        cmds=_svg_commands(raw,30,20)
        self.assertEqual(cmds[0],('M',(4.,7.)))
        self.assertTrue(any(c[0]=='C' for c in cmds))
        self.assertEqual(cmds[-5],('M',(3.,6.)))
        self.assertEqual(cmds[-1],('Z',))

    @unittest.skipUnless(importlib.util.find_spec('fontTools'),'fontTools absent')
    def test_svg_rejects_external_active_color_bitmap_or_cycles(self):
        for child in ('<use href="https://example.org/a"/>','<image href="x"/>',
                      '<script/>','<path fill="red" d="M 0 0 L 1 1"/>',
                      '<g id="a"><use href="#a"/></g>',
                      '<path stroke="black" stroke-width="1" fill="none" d="M 0 0 C 1 1 2 2 3 3"/>'):
            with self.subTest(child=child),self.assertRaises(TexError):
                _svg_commands(('<svg viewBox="0 0 10 10">'+child+'</svg>').encode(),10,10)

    def test_resource_snapshot_hash_invalidates(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);font=root/'font';font.write_bytes(b'first')
            c=replace(config(),cache_dir=root)
            first=_resources(c);font.write_bytes(b'second')
            self.assertNotEqual(first,_resources(c))
            with self.assertRaises(TexResourceError):self._overflow_resource(root,c)

    def _overflow_resource(self,root,c):
        (root/'overflow').write_bytes(b'a'*2000);return _resources(replace(c,max_cache_bytes=1024))

    @unittest.skipUnless(importlib.util.find_spec('psutil'),'psutil absent')
    def test_process_timeout_disk_guard_cleanup_and_sanitized_errors(self):
        from azimlib._tex_process import run_tool
        with tempfile.TemporaryDirectory() as temporary:
            job=Path(temporary);c=replace(config(),cache_dir=job,timeout=.1)
            with self.assertRaises(TexResourceError):
                run_tool([sys.executable,'-c','import time;time.sleep(5)'],job,c,'timeout.log')
            c=replace(c,timeout=5,max_temp_bytes=1024)
            with self.assertRaises(TexResourceError):
                run_tool([sys.executable,'-c',"open('large','wb').write(b'a'*2000)"],job,c,'disk.log')
            (job/'large').unlink()
            with self.assertRaises(TexError) as caught:
                run_tool([sys.executable,'-c',"raise RuntimeError('PRIVATE-SENTINEL')"],job,c,'error.log')
            self.assertNotIn('PRIVATE-SENTINEL',str(caught.exception))
            self.assertNotIn(str(job),str(caught.exception))

    def test_missing_tools_report_honest_capability(self):
        from azimlib.renderers import get_capabilities
        c=config(executable='azimlib-nonexistent-tex-engine')
        self.assertFalse(get_capabilities('svg',textengine='tex',texconfig=c).full_tex)
        self.assertFalse(get_capabilities('svg').full_tex)

    def test_snapshot_checks_once_per_composition_and_rejects_change(self):
        from azimlib.tex import composition_resources
        c=config();style=dict(textengine='tex',texconfig=c,font_size=20)
        with patch('azimlib.tex._tool',return_value=('tool','a'*64)), \
             patch('azimlib.tex._resources',return_value='b'*64) as resources, \
             patch('azimlib.tex._compile',return_value=LAYOUT):
            with composition_resources():
                for _ in range(30):tex_layout('Text',style)
            self.assertEqual(resources.call_count,2)
        with patch('azimlib.tex._tool',return_value=('tool','a'*64)), \
             patch('azimlib.tex._resources',side_effect=['b'*64,'c'*64]), \
             patch('azimlib.tex._compile',return_value=LAYOUT):
            with self.assertRaises(TexError),composition_resources():tex_layout('Text',style)

    def test_bounded_fragment_cache_and_external_resource_identity(self):
        from azimlib.tex import _compile
        azl.clear_tex_cache();c=config()
        with patch('azimlib.tex._compile_uncached',return_value=LAYOUT):
            for i in range(140):_compile(str(i),10,'normal','normal',c,'engine','converter',('a','b','c'))
        info=tex_cache_info()
        self.assertEqual(info['entries'],128)
        self.assertLessEqual(info['payload_bytes'],info['max_payload_bytes'])
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);cache=root/'cache';cache.mkdir();(cache/'resource').write_bytes(b'font')
            outside=root/'external-font';outside.write_bytes(b'first')
            c=replace(c,cache_dir=cache,resource_files=(outside,))
            first=_resources(c);outside.write_bytes(b'second')
            self.assertNotEqual(first,_resources(c))
        azl.clear_tex_cache()


REAL=OPTIONAL and all(os.environ.get(k) for k in ('AZIMLIB_TEX_ENGINE','AZIMLIB_TEX_CONVERTER','AZIMLIB_TEX_CACHE'))


@unittest.skipUnless(REAL,'Explicit offline TeX toolchain not configured')
class RealTexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'examples'))
        from validate_tex import validation_config
        cls.config=validation_config(os.environ['AZIMLIB_TEX_ENGINE'],os.environ['AZIMLIB_TEX_CONVERTER'],os.environ['AZIMLIB_TEX_CACHE'])
    def tearDown(self):azl.close('all')

    def test_actual_tex_macros_math_cache_and_baseline(self):
        azl.clear_tex_cache()
        c=replace(self.config,preamble=r'\usepackage{amsmath}\newcommand{\area}{A}')
        text=r'Text $\displaystyle\area=\frac{1}{2}\int_0^{\infty}e^{-x^2}\,dx$'
        style=dict(textengine='tex',texconfig=c,font_size=100/7.2)
        result=tex_layout(text,style)
        self.assertGreater(len(result.commands),100)
        self.assertGreater(result.ascent,1)
        self.assertGreater(result.descent,.5)
        self.assertEqual(tex_layout(text,style),result)
        self.assertGreater(tex_cache_info()['hits'],0)
        self.assertEqual(tex_layout(TexText(text,result),style),result)

    def test_actual_edit_and_png_svg_pdf_html(self):
        from tex_cartography import make
        fig=make(self.config)
        for extension in ('png','svg','pdf'):
            output=io.BytesIO() if extension!='svg' else io.StringIO()
            fig.savefig(output,format=extension)
            self.assertGreater(len(output.getvalue()),1000)
        self.assertIn('data-azimlib-shaped',fig.to_html())
        title=fig.axes[0].get_title();artist=fig.axes[0].set_title(r'Updated $\sqrt{a^2+b^2}$')
        self.assertNotEqual(title,artist.get_text())
        self.assertIn('Updated',fig.to_svg())

    def test_actual_compile_error_and_infinite_macro_timeout(self):
        style=dict(textengine='tex',texconfig=self.config,font_size=100/7.2)
        with self.assertRaises(TexError):tex_layout(r'$\azimlibUndefinedCommand$',style)
        with self.assertRaises(TexResourceError):
            tex_layout(r'\loop\iftrue\repeat',dict(style,texconfig=replace(self.config,timeout=.2)))
        with self.assertRaises(TexError):
            tex_layout('Text',dict(style,texconfig=replace(self.config,
                preamble=r'\AtBeginDocument{\shipout\hbox{extra}}')))
        with self.assertRaises(TexError):tex_layout(r'\char"1F9ED',style)

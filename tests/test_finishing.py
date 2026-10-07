"""Independent geometry, font, privacy and export contracts for stage 6."""
import io
import math
from pathlib import Path
import struct
import tempfile
import unittest
import xml.etree.ElementTree as ET
import azimlib as azl
from azimlib.scene import Scene,Text,Path as ScreenPath,Rect,Circle
from azimlib.renderers import render_svg,render_pdf
from azimlib.typography import text_width,text_bounds,font_path,POINT
from azimlib.mathtext import layout
from azimlib.polygon_labels import leader_endpoint,interior_anchors
from azimlib.label_layout import plan_labels
from azimlib.viewport import Viewport

PROVENANCE=azl.Provenance('original test fixture','BSD-3-Clause','Copyright (c) 2026 Kernerian')
def collection(kind,coords,name='Name',priority=0):
    return azl.FeatureCollection([azl.Feature(azl.Geometry(kind,coords),dict(name=name,priority=priority))])

class FinishingTests(unittest.TestCase):
    def tearDown(self):azl.close('all')
    def test_adaptive_curve_analytic_error(self):
        p=azl.Path([(0,0),(0,100),(100,100),(100,0)],[1,4,4,4])
        line=p.to_polylines(tolerance=.05)[0][0]
        def dist(q,a,b):
            dx,dy=b[0]-a[0],b[1]-a[1];t=max(0,min(1,((q[0]-a[0])*dx+(q[1]-a[1])*dy)/(dx*dx+dy*dy)))
            return math.hypot(q[0]-a[0]-dx*t,q[1]-a[1]-dy*t)
        for i in range(1001):
            t=i/1000;q=(300*t*t-200*t**3,300*t*(1-t))
            with self.subTest(t=t):self.assertLessEqual(min(dist(q,a,b) for a,b in zip(line,line[1:])),.05)
        self.assertEqual(line[0],(0,0));self.assertEqual(line[-1],(100,0))
    def test_curve_transform_error_and_limit(self):
        p=azl.Path([(0,0),(1,2),(2,0)],[1,3,3])
        small=p.to_polylines(tolerance=.05);large=p.to_polylines(tolerance=.05,transform=lambda p:(p[0]*100,p[1]*100))
        self.assertGreater(len(large[0][0]),len(small[0][0]))
        for opts in (dict(tolerance=0),dict(tolerance=float('nan')),dict(max_depth=0),dict(tolerance=1e-12,max_depth=1),dict(tolerance=.1,transform=lambda p:None)):
            with self.subTest(opts=tuple(opts)),self.assertRaises(ValueError):p.to_polylines(**opts)
    def test_fractional_clip_svg_pdf(self):
        s=Scene(50,40,None);s.add(ScreenPath([[(-2,2.25),(60,2.25)]],False,dict(stroke='#ff0000',stroke_width=.75,linecap='round',linejoin='bevel',dash=(2.5,1.25)),(.25,.5,25.75,31.25)))
        svg=render_svg(s);ET.fromstring(svg)
        self.assertIn('x="0.25"',svg);self.assertIn('stroke-width="0.75"',svg)
        pdf=render_pdf(s);self.assertIn(b'0.25 0.5 25.75 31.25 re W n',pdf);self.assertIn(b'1 J',pdf);self.assertIn(b'2 j',pdf)
    def test_fractional_png_clip_and_caps(self):
        from azimlib.renderers import render_image
        try:from PIL import Image
        except ImportError:self.skipTest('Pillow optional')
        images=[]
        for cap in ('butt','round','square'):
            s=Scene(40,20,None);s.add(ScreenPath([[(10.25,10.25),(20.25,10.25)]],False,dict(stroke='red',stroke_width=4,linecap=cap),(.25,.25,30.5,18.5)))
            im=render_image(s);images.append(im);self.assertIsNone(im.getchannel('A').crop((32,0,40,20)).getbbox())
        self.assertGreater(images[1].getchannel('A').getbbox()[2],images[0].getchannel('A').getbbox()[2])
        for im in images:im.close()
    def test_subpixel_text_coverage(self):
        from azimlib.renderers import render_image
        try:from PIL import ImageChops
        except ImportError:self.skipTest('Pillow optional')
        images=[]
        for x in (10,10.25,10.5,10.75):
            s=Scene(120,35,None);s.add(Text(x,20,'Latitude',dict(font_size=12,fill='black')));images.append(render_image(s))
        self.assertTrue(all(ImageChops.difference(images[0].getchannel('A'),im.getchannel('A')).getbbox() for im in images[1:]))
        for im in images:im.close()
    def test_all_text_families_shared_scene(self):
        f,a=azl.subplots();a.set_extent((-55,-40,-28,-12));a.plot([-52,-44],[-24,-18],label='Route')
        a.set_title('Title');a.set_xlabel('Longitude');a.set_ylabel('Latitude');a.legend(title='Legend')
        a.scale_bar(length=100);a.north_arrow();a.compass();a.text(-48,-20,'Text');a.annotate('Annotation',(-50,-23))
        f.suptitle('Figure title');f.supxlabel('Figure X');f.supylabel('Figure Y')
        m=a.scatter([-47],[-19],c=[.5]);f.colorbar(m,label='Colorbar')
        texts=[p for p in f.to_scene().items if isinstance(p,Text)]
        for value in ('Title','Longitude','Latitude','Legend','Route','Text','Annotation','Figure title','Figure X','Figure Y','Colorbar','N','km'):
            with self.subTest(value=value):self.assertTrue(any(p.text==value for p in texts))
        for p in texts:
            with self.subTest(text=p.text):self.assertIsNotNone(font_path(p.style));self.assertTrue(all(math.isfinite(v) for v in text_bounds(p.text,p.style)))
    def test_math_scripts_fraction_root_and_mixed(self):
        style=dict(font_size=20)
        plain=layout('Area',style);script=layout(r'Area $x_0^2$',style)
        self.assertGreater(script.width,plain.width);self.assertLess(script.top,plain.top)
        frac=layout(r'$\frac{1}{2}$',style);self.assertTrue(frac.rules);self.assertLessEqual(frac.top,-20)
        root=layout(r'$\sqrt{x}+\alpha\times\pi$',style);self.assertTrue(root.rules)
        self.assertTrue(any(t=='α' for t,x,y,size in root.runs))
    def test_math_invalid_and_bounded(self):
        for text in ('$x',r'$\unknown$',r'$\frac{1}$',r'$x^^2$',r'$x^2^3$',r'${x$',r'$x}$','$'+'{'*20+'x'+'}'*20+'$', '$'+'x'*4097+'$'):
            with self.subTest(text=text[:25]),self.assertRaises(ValueError):layout(text,dict(font_size=12))
    def test_math_rotated_clipped_and_visibility(self):
        f,a=azl.subplots();a.set_extent((-5,5,-5,5));t=a.text(0,0,r'$\frac{x_0^2}{\sqrt{y}}$',rotation=35)
        s=f.to_scene();self.assertTrue(any(isinstance(p,Text) and p.text=='x' for p in s.items));self.assertNotIn(r'\frac',f.to_svg())
        out=io.BytesIO();f.savefig(out,format='pdf');self.assertTrue(out.getvalue().startswith(b'%PDF'))
        t.set_visible(False);self.assertFalse(any(isinstance(p,Text) and p.text=='x' for p in f.to_scene().items))
    def test_glyph_implied_points_analytic(self):
        from azimlib.font_outline import glyph_commands
        result=glyph_commands([(0,0,False),(2,2,False),(4,0,True)])
        self.assertEqual(result[0],('M',(4,0)))
        self.assertEqual(result[1],('Q',(0,0),(1,1)))
        self.assertEqual(result[2],('Q',(2,2),(4,0)));self.assertEqual(result[-1],('Z',))
    def test_bundled_glyphs_all_faces_compounds(self):
        from azimlib.font_outline import contours,text_commands
        from azimlib.typography import _metrics
        for weight,slant in (('normal','normal'),('bold','normal'),('normal','italic'),('bold','italic')):
            style=dict(font_weight=weight,font_style=slant);path=font_path(style);metrics=_metrics()[path.stem]
            for char in 'AzimlibSãoPauloçáêñ°αβπ√∞':
                with self.subTest(face=path.stem,char=char):
                    glyph=metrics['chars'][char][0];cs=contours(path,glyph)
                    self.assertTrue(cs);self.assertTrue(all(math.isfinite(v) for ring in cs for p in ring for v in p[:2]))
            commands=list(text_commands(Text(10.25,20.5,'São Paulo',dict(style,font_size=12,rotation=25))))
            self.assertTrue(any(c[0]=='Q' for c in commands))
    def test_pdf_page_physical_size_xref_and_notice(self):
        f,a=azl.subplots(figsize=(4,3),dpi=150);a.set_title('São Paulo')
        out=io.BytesIO();f.savefig(out,format='pdf',dpi=300);data=out.getvalue()
        self.assertIn(b'/MediaBox [0 0 288 216]',data);self.assertIn(b'DejaVu-license.txt',data)
        self.assertIn(b'Bitstream',data);self.assertNotIn(b'/Subtype /Image',data)
        xref=int(data.split(b'startxref\n')[-1].splitlines()[0]);self.assertEqual(data[xref:xref+4],b'xref')
        entries=data[xref:].splitlines()[3:]
        for index,line in enumerate(entries,1):
            if not line.endswith(b' n '):break
            pos=int(line.split()[0]);self.assertTrue(data[pos:].startswith(f'{index} 0 obj'.encode()))
        self.assertFalse(out.closed)
    def test_pdf_rgba_separate_alpha_and_halo(self):
        s=Scene(20,20,None);s.add(Rect(1,1,10,10,dict(fill='#ff000080',stroke='#0000ff40',opacity=.5,fill_opacity=.5)))
        pdf=render_pdf(s);self.assertIn(b'/ca 0.1254902',pdf);self.assertIn(b'/CA 0.1254902',pdf)
        s.add(Text(5,12,'O',dict(fill='red',stroke='white',stroke_width=2)))
        pdf=render_pdf(s);self.assertIn(b'\nS\n',pdf);self.assertIn(b'\nf\n',pdf)
    def test_pdf_rejects_foreign_font_and_preserves_target(self):
        f,a=azl.subplots();a.set_title('Unknown',fontfamily='Unsupported')
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'x.pdf';p.write_bytes(b'existing')
            with self.assertRaises(ValueError):f.savefig(p)
            self.assertEqual(p.read_bytes(),b'existing');self.assertEqual(len(list(Path(tmp).iterdir())),1)
    def test_pdf_determinism_and_empty_scene(self):
        s=Scene(10,20,None);self.assertEqual(render_pdf(s),render_pdf(s))
        for dpi in (0,-1,float('inf')):
            with self.subTest(dpi=dpi),self.assertRaises(ValueError):render_pdf(s,dpi=dpi)
    def test_polygon_anchor_hole_and_concavity(self):
        f,a=azl.subplots(figsize=(5,5));a.set_extent((0,10,0,10));vp=Viewport(a.projection,a._get_extent(),(0,0,500,500))
        g=azl.Geometry('Polygon',[[(0,0),(10,0),(10,10),(0,10),(0,0)],[(4,4),(6,4),(6,6),(4,6),(4,4)]])
        points=interior_anchors(g,vp);self.assertTrue(points)
        from azimlib.render_map import _inside_ring
        for p in points:
            geo=vp.inverse(*p);self.assertTrue(_inside_ring(geo,g.coordinates[0]));self.assertFalse(_inside_ring(geo,g.coordinates[1]))
    def test_interior_anchor_follows_visible_view(self):
        f,a=azl.subplots();a.set_extent((0,2,0,2));vp=Viewport(a.projection,a._get_extent(),(0,0,200,200))
        g=azl.Geometry('Polygon',[[(-10,-10),(10,-10),(10,10),(-10,10),(-10,-10)]])
        points=interior_anchors(g,vp);self.assertTrue(points);self.assertLess(math.dist(points[0],(100,100)),2)
    def test_leader_terminates_on_box(self):
        self.assertEqual(leader_endpoint((100,50),(0,0,20,20)),(20,10+40/9))
        self.assertEqual(leader_endpoint((10,10),(0,0,20,20)),(10,10))
    def test_leaders_avoid_other_text_boxes(self):
        from azimlib.label_layout import BoxIndex
        index=BoxIndex();index.add((10,10,20,20))
        self.assertTrue(index.crosses((0,0),(40,40)))
        self.assertFalse(index.crosses((0,0),(40,5)))
        self.assertTrue(index.crosses((20,20),(40,40)))
        self.assertFalse(index.crosses((20,20),(40,40),allow_origin=True))
    def test_curve_labels_repeat_rotate_and_edit(self):
        f,a=azl.subplots(figsize=(10,4));a.set_extent((0,20,0,8))
        data=collection('LineString',[(i,4+math.sin(i/4)) for i in range(21)],'River')
        l=a.labels(data,placement='curve',repeat=120,fontsize=9)
        s=f.to_scene();glyphs=[p for p in s.items if isinstance(p,Text) and p.text=='R']
        self.assertGreaterEqual(len(glyphs),2);self.assertTrue(any(p.style.get('rotation') for p in glyphs))
        l.set_visible(False);self.assertFalse(any(isinstance(p,Text) and p.text=='R' for p in f.to_scene().items))
    def test_curve_labels_reverse_upright(self):
        from azimlib.curved_text import curve_candidates
        f,a=azl.subplots();a.set_extent((0,10,0,10));vp=Viewport(a.projection,a._get_extent(),(0,0,500,500))
        g=azl.Geometry('LineString',[(9,5),(1,5)])
        poses=next(curve_candidates(g,vp,'River',dict(font_size=12)))
        self.assertTrue(all(abs(p[2])<1e-6 for p in poses));self.assertLess(poses[0][1][0],poses[-1][1][0])
    def test_label_invalid_options_without_mutation(self):
        f,a=azl.subplots();data=collection('Point',(0,0))
        for opts in (dict(placement='curve'),dict(repeat=5),dict(placement='curve',repeat=0),dict(placement='curve',repeat=float('nan'))):
            before=len(a.layers)
            with self.subTest(opts=opts),self.assertRaises(ValueError):a.labels(data,**opts)
            self.assertEqual(len(a.layers),before)
    def test_provenance_and_safe_svg_symbol(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'icon.svg';p.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><path d="M 0 5 L 5 0 L 10 5 L 5 10 Z"/></svg>')
            symbol=azl.read_svg_symbol(p,provenance=PROVENANCE);self.assertEqual(len(symbol.provenance.sha256),64)
            f,a=azl.subplots();a.set_extent((-1,1,-1,1));a.scatter([0],[0],marker=symbol,s=100,rotation=20)
            self.assertIn('<svg',f.to_svg());self.assertTrue(f.to_html());f.savefig(io.BytesIO(),format='pdf')
    def test_svg_rejects_unsafe_or_unimplemented(self):
        for text in ('<!DOCTYPE svg [<!ENTITY x "secret">]><svg/>','<svg><script/></svg>','<svg><image href="https://invalid.test"/></svg>','<svg><path d="m 0 0 l 1 1"/></svg>','<svg><path transform="scale(2)" d="M 0 0 L 1 1"/></svg>','<svg><path d="M 0 0 Q 1"/></svg>'):
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/'x.svg';p.write_text(text)
                with self.subTest(text=text),self.assertRaises(ValueError):azl.read_svg_symbol(p,provenance=PROVENANCE)
    def test_svg_hash_and_missing_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'x.svg';p.write_text('<svg><path d="M 0 0 L 1 1"/></svg>')
            with self.assertRaises(TypeError):azl.read_svg_symbol(p,provenance=None)
            with self.assertRaises(ValueError):azl.read_svg_symbol(p,provenance=azl.Provenance('s','l','c',sha256='0'*64))
        with self.assertRaises(ValueError):azl.Provenance('','BSD-3-Clause','c')
    def test_custom_pattern_clips_holes(self):
        from azimlib.hatches import add_hatches
        pattern=azl.HatchPattern([[(0,.5),(1,.5)]],PROVENANCE)
        rings=[[(0,0),(100,0),(100,100),(0,100),(0,0)],[(30,30),(70,30),(70,70),(30,70),(30,30)]]
        s=Scene(100,100);add_hatches(s,rings,dict(hatch=pattern,hatch_spacing=10))
        self.assertTrue(s.items)
        for item in s.items:
            for line in item.paths:
                p=tuple((a+b)/2 for a,b in zip(line[0],line[-1]))
                self.assertFalse(30<p[0]<70 and 30<p[1]<70)
        self.assertIn('<svg',render_svg(s));self.assertTrue(render_pdf(s))
    def test_pattern_validation_and_integrated_viewer(self):
        for paths in ([],[[(0,0)]],[[(0,0),(2,2)]],[[(0,0),(float('nan'),0)]]):
            with self.subTest(paths=paths),self.assertRaises(ValueError):azl.HatchPattern(paths,PROVENANCE)
        f,a=azl.subplots();a.set_extent((0,2,0,2));pattern=azl.HatchPattern([[(0,0),(.5,.5),(1,0)]],PROVENANCE)
        a.geojson(collection('Polygon',[[(0,0),(2,0),(2,2),(0,2),(0,0)]]),hatch=pattern)
        self.assertIn('azimlib-material-provenance',f.to_svg());self.assertTrue(f.to_html())
        self.assertIn(b'Material-provenance.json',render_pdf(f.to_scene()))
    def test_pdf_numeric_syntax_has_no_exponents(self):
        import re
        s=Scene(20,20,None);s.add(Circle(1e-5,2e-5,3e-5,dict(fill='#258bb0',opacity=1e-7)))
        data=render_pdf(s);content=data.split(b'stream\n',1)[1].split(b'\nendstream',1)[0]
        self.assertIsNone(re.search(rb'[-+]?\d+(?:\.\d+)?[eE][-+]?\d+',content))
        self.assertIn(b'0.00001',content)
    def test_external_svg_bounded_and_finite(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'x.svg'
            for value in ('<svg><path d="M 1e999 0 L 1 1"/></svg>', ' '*1_000_001):
                p.write_text(value)
                with self.subTest(value=value[:60]),self.assertRaises(ValueError):azl.read_svg_symbol(p,provenance=PROVENANCE)
        with self.assertRaises(TypeError):azl.Provenance('s','l','c',license_text=123)
    def test_custom_notices_preserved_in_png_and_scaling(self):
        try:from PIL import Image
        except ImportError:self.skipTest('Pillow optional')
        from azimlib.renderers import render_png
        s=Scene(100,100);s._material_notices=[dict(source='original fixture',license='BSD-3-Clause',copyright='Kernerian',attribution='credit')]
        scaled=s.scaled(2);scaled._material_notices[0]['source']='other'
        self.assertEqual(s._material_notices[0]['source'],'original fixture')
        stream=io.BytesIO();render_png(s,stream);stream.seek(0)
        with Image.open(stream) as image:self.assertIn('original fixture',image.info['Azimlib material provenance'])
    def test_pattern_density_limit(self):
        from azimlib.hatches import add_hatches
        s=Scene(100,100);pattern=azl.HatchPattern([[(0,0),(1,1)]],PROVENANCE)
        rings=[[(0,0),(100,0),(100,100),(0,100),(0,0)]]
        with self.assertRaises(ValueError):add_hatches(s,rings,dict(hatch=pattern,hatch_spacing=1e-200))
    def test_palette_component_and_math_colorbar(self):
        f,a=azl.subplots();a.set_extent((0,2,0,2));m=a.scatter([1],[1],c=[2])
        c=f.colorbar(m,orientation='horizontal',label=r'$\sigma^2$')
        self.assertIn('σ',f.to_svg());c.set_label(r'$\alpha_0$');self.assertIn('α',f.to_svg())
        c.set_visible(False);self.assertNotIn('α',f.to_svg())

if __name__=='__main__':unittest.main()

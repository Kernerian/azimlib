"""Functional scene, geometry, lifecycle and numerical thematic tests."""
import dataclasses,io,math,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
import azimlib as a
from azimlib.colors import Normalize
from azimlib.scene import Path as ScenePath,RasterIcon
from azimlib.picking import inside
from azimlib.thematic_render import symbol_scene
from azimlib.typography import POINT

class Thematic(unittest.TestCase):
    def tearDown(self):a.close('all')
    def axes(self,body=a.EARTH,projection=None):
        f,ax=a.subplots(body=body,**({'projection':projection} if projection else {}));ax.set_extent((-10,10,-10,10));return f,ax
    def square(self,ax,holes=(),**kw):return a.RegionDefinition.polygon([(-4,-4),(4,-4),(4,4),(-4,4)],context=ax.get_context(),holes=holes,**kw)
    def records(self,f,artist):
        s=f.canvas.draw();return s,[i for owner,_,lo,hi in s._pick_records if owner is artist for i in s.items[lo:hi]]
    def viewport(self,f,ax):
        from azimlib.viewport import Viewport
        box=next(m['box'] for m in f.canvas._pick_scene.maps if m['axes_index']==f.axes.index(ax) and not m.get('inset'))
        return Viewport(ax.projection,ax._get_extent(),box,bearing=ax.get_bearing())
    def event(self,f,ax,lon,lat):
        p=self.viewport(f,ax).project(lon,lat);return SimpleNamespace(canvas=f.canvas,x=p[0],y=f.canvas._pick_scene.height-p[1])
    def test_symbols_earth_mars_moon_and_fixed_visual_size(self):
        for body in (a.EARTH,a.MARS,a.MOON):
            f,ax=self.axes(body);s=ax.symbols([(0,0)],'gold',size=18)
            _,items=self.records(f,s);p=items[0];width=max(x for r in p.paths for x,y in r)-min(x for r in p.paths for x,y in r)
            ax.set_extent((-2,2,-2,2));_,items2=self.records(f,s)
            self.assertAlmostEqual(width,max(x for r in items2[0].paths for x,y in r)-min(x for r in items2[0].paths for x,y in r),places=8)
            self.assertIs(s.get_body(),body)
            self.assertIn('cartographic_symbol',f.to_svg())
            output=io.BytesIO();f.savefig(output,format='pdf');self.assertIn(b'%PDF',output.getvalue())
    def test_rotation_offset_anchor_and_aspect(self):
        from azimlib.scene import Scene
        d=a.SymbolDefinition.from_paths('rect',[[(0,0),(2,0),(2,1),(0,1)]],viewbox=(0,0,2,1),source=a.AssetSource('synthetic','BSD','own'))
        scene=Scene(100,100);symbol_scene(d,(50,50),20,{'rotation':90},scene,None,anchor=(0,0),offset=(1,2));points=scene.items[0].paths[0]
        self.assertAlmostEqual(max(x for x,y in points)-min(x for x,y in points),10)
        self.assertAlmostEqual(max(y for x,y in points)-min(y for x,y in points),20)
        self.assertAlmostEqual(points[0][0],50+POINT)
    def test_map_units_scale_with_zoom(self):
        f,ax=self.axes(a.MARS);s=ax.symbols([(0,0)],'city',size=10000,size_unit='m');_,p=self.records(f,s)
        x=lambda i:max(x for r in i.paths for x,y in r)-min(x for r in i.paths for x,y in r)
        old=x(p[0]);oldscale=self.viewport(f,ax).scale;ax.set_extent((-5,5,-5,5));_,p=self.records(f,s);self.assertAlmostEqual(x(p[0])/old,self.viewport(f,ax).scale/oldscale,places=8)
    def test_labels_priority_and_picker(self):
        f,ax=self.axes();s=ax.symbols([(0,0),(0,0)],'city',labels=['first','second'],priorities=[2,1],category='cities');s.set_picker(True)
        scene=f.canvas.draw();self.assertEqual([i for owner,i,_,_ in scene._pick_records if owner is s],[1,0]);self.assertIn('first',f.to_svg())
        hit,info=s.contains(self.event(f,ax,0,0));self.assertTrue(hit);self.assertEqual(set(info['ind']),{0,1})
    def test_symbol_setters_are_validated_and_notify(self):
        f,ax=self.axes();s=ax.symbols([(0,0)]);calls=[];s.add_callback(lambda x:calls.append(x));f.canvas.draw();s.set_size(20);self.assertTrue(f.stale);self.assertEqual(calls,[s])
        for bad in (0,-1,float('nan'),500):
            with self.assertRaises(ValueError):s.set_size(bad)
        self.assertEqual(s._size,20)
        s.set_symbol('rover');s.set_positions([(1,1)]);self.assertEqual(s.data,((1,1),))
    def test_input_budgets_contexts_and_transform_refusals(self):
        f,ax=self.axes(a.MARS)
        with self.assertRaises(ValueError):ax.symbols([(0,0)],context=a.PlanetaryContext.for_body(a.MOON))
        with self.assertRaises(ValueError):ax.symbols([(0,91)])
        with self.assertRaises(ValueError):ax.symbols([(0,0)]*2049)
        with self.assertRaises(ValueError):ax.symbols([(0,0)],size_unit='degree')
        s=ax.symbols([(0,0)])
        with self.assertRaises(a.UnsupportedBodyOperation):s.set_transform(ax.transAxes)
        with self.assertRaises(a.UnsupportedBodyOperation):f.to_html()
    def test_region_hole_is_not_painted_or_picked(self):
        f,ax=self.axes();r=self.square(ax,holes=[[(-1,-1),(-1,1),(1,1),(1,-1)]]);l=ax.region(r,facecolor='red',edgecolor='none');l.set_picker(True);self.records(f,l)
        self.assertFalse(l.contains(self.event(f,ax,0,0))[0]);self.assertTrue(l.contains(self.event(f,ax,3,0))[0])
    def test_multipolygon_components_and_invalid_topology(self):
        f,ax=self.axes(a.MOON);first=self.square(ax);second=a.RegionDefinition.polygon([(6,1),(8,1),(8,3),(6,3)],context=ax.get_context())
        r=a.RegionDefinition(a.Geometry('MultiPolygon',(first.geometry.coordinates,second.geometry.coordinates)),ax.get_context());l=ax.region(r);_,p=self.records(f,l);self.assertEqual(len([x for x in p if isinstance(x,ScenePath)]),2)
        for shell in ([(-1,-1),(1,1),(-1,1),(1,-1)],[(0,0),(1,1),(0,0)]):
            with self.assertRaises(ValueError):a.RegionDefinition.polygon(shell,context=ax.get_context())
        with self.assertRaises(ValueError):self.square(ax,holes=[[(6,6),(7,6),(7,7),(6,7)]])
    def test_mask_and_intersection_area_analytic(self):
        f,ax=self.axes();r=self.square(ax);mask=a.RegionDefinition.polygon([(0,-5),(5,-5),(5,5),(0,5)],context=ax.get_context());m=r.masked(mask)
        from azimlib.overlay import intersection
        self.assertEqual(intersection(m.geometry,m.geometry).area(),32)
        with self.assertRaises(ValueError):r.masked(a.RegionDefinition(mask.geometry,a.PlanetaryContext.for_body(a.MARS)))
    def test_bands_keep_author_semantics_and_atomic_validation(self):
        f,ax=self.axes();r=self.square(ax);g=ax.region_bands([(r,{'facecolor':'red'}),(r,{'facecolor':'blue','alpha':.2})]);self.assertEqual(len(g.get_children()),2)
        count=len(ax.layers)
        with self.assertRaises(ValueError):ax.region_bands([(r,{})],semantics='probability')
        self.assertEqual(len(ax.layers),count)
    def test_linear_gradient_function_and_hole_preservation(self):
        f,ax=self.axes();r=self.square(ax,holes=[[(-1,-1),(-1,1),(1,1),(1,-1)]]);g=a.LinearGradient((-4,0),(4,0),('red','blue'),'decorative',steps=8)
        self.assertEqual(g.fraction((0,0)),.5);self.assertEqual(g.color(.5),'#800080ff');l=ax.region(r,gradient=g);self.assertEqual(len(l.slices),8)
        self.records(f,l);self.assertFalse(l.contains(self.event(f,ax,0,0))[0]);self.assertTrue(l.contains(self.event(f,ax,3,0))[0])
    def test_quantitative_uncertainty_and_decorative_not_conflated(self):
        for semantic in ('quantitative','uncertainty'):
            with self.assertRaises(ValueError):a.LinearGradient((0,0),(1,0),('red','blue'),semantic)
            g=a.LinearGradient((0,0),(1,0),('red','blue'),semantic,values=(0,5),unit='m',meaning='Author supplied standard deviation' if semantic=='uncertainty' else 'Author field')
            self.assertEqual(g.values,(0,5))
        with self.assertRaises(ValueError):a.LinearGradient((0,0),(1,0),('red','blue'),'decorative',values=(0,1))
    def test_antimeridian_and_horizon_not_bridged(self):
        f,ax=self.axes(a.MARS);ax.set_extent((-180,180,-60,60));r=a.RegionDefinition.polygon([(170,-10),(-170,-10),(-170,10),(170,10)],context=ax.get_context());l=ax.region(r,facecolor='red');_,p=self.records(f,l)
        self.assertGreaterEqual(len(p),2)
        for item in p:self.assertLess(max(x for ring in item.paths for x,y in ring)-min(x for ring in item.paths for x,y in ring),self.viewport(f,ax).box[2]/2)
        f2,b=self.axes(a.MOON,'orthographic');b.set_extent((-180,180,-90,90));s=b.symbols([(180,0),(0,0)]);scene,_=self.records(f2,s);self.assertEqual(len([r for r in scene._pick_records if r[0] is s]),1)
    def test_poles_ambiguous_interiors_and_interrupted_projection_refuse(self):
        f,ax=self.axes(a.MARS)
        with self.assertRaises(a.UnsupportedBodyOperation):a.RegionDefinition.polygon([(-20,80),(20,80),(20,90),(-20,90)],context=ax.get_context())
        with self.assertRaises(a.UnsupportedBodyOperation):ax.set_projection('interrupted')
        r=a.RegionDefinition.polygon([(-10,78),(10,78),(10,85),(-10,85)],context=ax.get_context());ax.set_extent((-15,15,75,86));ax.region(r);self.assertTrue(f.to_svg())
    def test_bezier_analytic_midpoint_and_endpoints(self):
        _,ax=self.axes();c=[(0,0),(0,3),(4,3),(4,0)];p=a.CartographicPath.bezier(c,context=ax.get_context(),samples=97)
        self.assertEqual(p.points[0],c[0]);self.assertEqual(p.points[-1],c[-1]);self.assertAlmostEqual(p.points[48][0],2,places=10);self.assertAlmostEqual(p.points[48][1],2.25,places=10)
        with self.assertRaises(a.UnsupportedBodyOperation):p.surface_length()
    def test_spline_interpolates_waypoints_and_is_c1(self):
        _,ax=self.axes();controls=[(0,0),(2,3),(5,2),(7,4)];p=a.CartographicPath.spline(controls,context=ax.get_context(),samples_per_segment=101)
        for i,c in enumerate(controls):self.assertEqual(p.points[i*100],c)
        left=tuple(p.points[100][i]-p.points[99][i] for i in (0,1));right=tuple(p.points[101][i]-p.points[100][i] for i in (0,1));self.assertLess(math.dist(left,right),.002)
    def test_surface_geodesic_independent_of_editorial_and_projection(self):
        f,ax=self.axes(a.MARS);p=a.CartographicPath.geodesic([(0,0),(3,0)],context=ax.get_context());expected=a.MARS.axes[0]*math.radians(3)
        self.assertAlmostEqual(p.surface_length(),expected,places=4);l=ax.cartographic_path(p,color='red',arrow='end');old=l.get_length();ax.set_projection('mercator');self.assertEqual(l.get_length(),old)
        self.assertGreater(l.get_length(space='visual'),0)
        with self.assertRaises(ValueError):a.CartographicPath(((0,0),(1,1)),ax.get_context(),kind='geodesic',physical_length_m=3)
    def test_path_unwrap_and_marker_direction_spacing(self):
        f,ax=self.axes();ax.set_extent((-180,180,-30,30));p=a.CartographicPath.bezier([(170,0),(175,4),(-175,4),(-170,0)],context=ax.get_context());self.assertLess(max(x for x,y in p.points)-min(x for x,y in p.points),30)
        l=ax.cartographic_path(p,path_symbol='arrow',spacing=20,color='red');scene,items=self.records(f,l)
        self.assertTrue(any(isinstance(i,ScenePath) and i.closed for i in items))
        self.assertEqual(p.points,l.definition.points)
    def test_nested_groups_clipping_styles_and_legend_inclusion(self):
        f,ax=self.axes();root=ax.group(style={'alpha':.5,'color':'red'},zorder=5);child=ax.group(parent=root,style={'alpha':.8});s=child.add(ax.symbols([(0,0),(6,0)],category='cities'));s.set_picker(True)
        root.set_clip_box((0,0,.5,1));scene,items=self.records(f,s);self.assertTrue(all(i.clip[2]<=self.viewport(f,ax).box[2]/2+1e-8 for i in items));self.assertEqual(s.get_alpha(),.8)
        self.assertTrue(s.get_legend_entries());root.set_legend_visible(False);self.assertEqual(s.get_legend_entries(),[])
        child.set_visible(False);scene=f.to_scene();self.assertFalse(any(o is s for o,_,_,_ in scene._pick_records));child.set_visible(True)
        with self.assertRaises(ValueError):child.add(root)
    def test_group_clone_is_independent_and_keeps_local_state(self):
        f,ax=self.axes(a.MARS);g=ax.group(name='science',style={'color':'red'});s=g.add(ax.symbols([(0,0)],'rover',labels=['local']));s.set_visible(False)
        g.add(ax.region(self.square(ax)));g.add(ax.cartographic_path(a.CartographicPath.polyline([(-1,0),(1,0)],context=ax.get_context())));g.set_clip_box((.1,.1,.8,.8));calls=[];s.add_callback(calls.append)
        _,other=self.axes(a.MARS);clone=g.instantiate(other);cs=clone.get_children()[0];self.assertIsNot(cs,s);self.assertIs(cs.symbol,s.symbol);self.assertFalse(cs.get_local_visible());cs.set_visible(True);self.assertFalse(s.get_visible());self.assertEqual(calls,[])
        g.remove();self.assertIsNone(s.axes);self.assertIsNotNone(cs.axes)
        _,earth=self.axes()
        with self.assertRaises(ValueError):clone.instantiate(earth)
    def test_removal_invalidation_callbacks_and_context_ownership(self):
        f,ax=self.axes();s=ax.symbols([(0,0)]);g=ax.group();g.add(s);calls=[];s.add_callback(lambda x:calls.append(x));f.canvas.draw();g.set_style(alpha=.4);self.assertTrue(f.stale);self.assertEqual(calls,[s])
        _,other=self.axes()
        with self.assertRaises(ValueError):other.add_collection(s)
        s.remove();self.assertEqual(g.get_children(),[]);self.assertIsNone(s.axes)
    def test_exports_vector_paths_and_embedded_png_alpha(self):
        try:from PIL import Image
        except ImportError:self.skipTest('Optional PNG loader requires Pillow')
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'own.png'
            with Image.new('RGBA',(8,4),(240,20,40,128)) as im:im.save(path)
            icon=a.SymbolDefinition.from_png(path,source=a.AssetSource('synthetic:own','BSD-3-Clause','Own fixture'))
            f,ax=self.axes();s=ax.symbols([(0,0)],icon,size=24,rotation=35);ax.cartographic_path(a.CartographicPath.polyline([(-5,-5),(5,5)],context=ax.get_context()),color='blue')
            svg=f.to_svg();self.assertIn('<image ',svg);self.assertIn('data:image/png;base64,',svg);self.assertIn('<path ',svg)
            pdf=io.BytesIO();f.savefig(pdf,format='pdf');self.assertIn(b'/Subtype /Image',pdf.getvalue());self.assertIn(b'/SMask',pdf.getvalue());self.assertIn(b' m',pdf.getvalue())
            png=io.BytesIO();f.savefig(png,format='png');self.assertTrue(png.getvalue().startswith(b'\x89PNG'))
            scene=f.to_scene();sprite=next(i for i in scene.items if isinstance(i,RasterIcon));self.assertTrue(any(0<v<255 for v in sprite.rgba[3::4]))
            self.assertEqual(f.to_svg(),svg)
    def test_png_frame_cache_key_includes_pixel_content(self):
        from azimlib.backends._raster_cache import scene_key
        from azimlib.scene import Scene
        one=Scene(30,30);two=Scene(30,30);one.add(RasterIcon(0,0,10,10,1,1,b'\xff\x00\x00\xff'));two.add(RasterIcon(0,0,10,10,1,1,b'\x00\xff\x00\xff'));self.assertNotEqual(scene_key(one),scene_key(two))
    def test_network_adapter_preserves_existing_router_metrics(self):
        import hashlib
        from azimlib._pbf_decode import OSMRecord
        source=a.RoutingSource('own-test','1','BSD-3-Clause','Kernerian','Synthetic road','urn:azimlib:test',hashlib.sha256(b'own').hexdigest(),('Own BSD fixture',))
        records=[OSMRecord('node',1,{},(0,0)),OSMRecord('node',2,{},(.01,0)),OSMRecord('way',10,{'highway':'residential'},refs=(1,2))]
        route=a.RoadGraph.from_records(records,source=source).route(1,2)
        _,ax=self.axes();path=a.CartographicPath.network(route,context=ax.get_context());self.assertEqual(path.surface_length(),route.distance_m);self.assertEqual(path.points,route.geometry.coordinates)
        _,mars=self.axes(a.MARS)
        with self.assertRaises(a.UnsupportedBodyOperation):a.CartographicPath.network(route,context=mars.get_context())
    def test_own_asset_provenance_in_all_exports(self):
        f,ax=self.axes();ax.symbols([(0,0)],'gold',category='gold');self.assertIn('azimlib:programmatic-catalog',f.to_svg())
        pdf=io.BytesIO();f.savefig(pdf,format='pdf');self.assertIn(b'cartographic_symbol',pdf.getvalue())
        try:from PIL import Image
        except ImportError:return
        png=io.BytesIO();f.savefig(png,format='png');png.seek(0)
        with Image.open(png) as im:self.assertIn('cartographic_symbol',im.info['Azimlib material provenance'])
    def test_explicit_legend_handles_keep_real_symbol(self):
        f,ax=self.axes();s=ax.symbols([(0,0)],'rover');ax.legend(handles=[s],labels=['Rover'])
        svg=f.to_svg();self.assertIn('Rover',svg);self.assertIn('programmatic-catalog',svg)
    def test_no_ignored_scalar_mapping(self):
        f,ax=self.axes();s=ax.symbols([(0,0)])
        for fun in (lambda:s.set_array([1]),lambda:s.set_cmap('viridis'),lambda:s.set(norm=Normalize()),lambda:s.set_clim(0,1)):
            with self.assertRaises(TypeError):fun()

    def test_legacy_spherical_region_and_default_earth_unchanged(self):
        f,ax=self.axes();ax.map('world',fit=False);self.assertIs(ax.get_body(),a.EARTH);self.assertEqual(a.__version__,'0.5.0.dev0');self.assertIn('<svg',f.to_svg())
    def test_png_transparent_corner_not_pickable(self):
        from azimlib.picking import primitive_hit
        icon=RasterIcon(0,0,2,1,2,1,b'\x00\x00\x00\x00\xff\x00\x00\xff');self.assertFalse(primitive_hit(icon,(.25,.5),0));self.assertTrue(primitive_hit(icon,(1.5,.5),0))

if __name__=='__main__':unittest.main()

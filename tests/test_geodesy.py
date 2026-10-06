"""Independent core contracts, black-box numerical evidence and seam navigation."""
import io,json,math,shutil,subprocess,tempfile,unittest
from pathlib import Path
from dataclasses import FrozenInstanceError
import azimlib as az
from azimlib.crs import transform_coordinates
from azimlib.geometry import wrap_longitude
from azimlib.navigation import Navigation,drag_extent,zoom_extent,viewport_from_metadata
from azimlib.transverse import tm_forward,tm_inverse

ROOT=Path(__file__).resolve().parents[1]
REFERENCE=json.loads((ROOT/'docs/geodesy-reference-0.3.json').read_text())


class GeodesyTests(unittest.TestCase):
    def test_models_units_datum_and_immutability(self):
        self.assertEqual(az.CRS(4326).datum,az.WGS84_DATUM)
        self.assertEqual(az.CRS(32723).ellipsoid,az.WGS84)
        self.assertEqual(az.CRS(32723).axis_order,('easting','northing'))
        self.assertAlmostEqual(az.WGS84.semi_minor_axis,6356752.314245179,places=7)
        self.assertAlmostEqual(az.WGS84.eccentricity_squared,.0066943799901413165,places=16)
        self.assertEqual(az.KILOMETRE.convert(2,az.METRE),2000)
        self.assertAlmostEqual(az.DEGREE.convert(180,az.RADIAN),math.pi)
        with self.assertRaises(ValueError):az.METRE.convert(1,az.RADIAN)
        with self.assertRaises(FrozenInstanceError):az.WGS84.name='other'
        for kw in ({'semi_major_axis':0},{'inverse_flattening':-1},{'inverse_flattening':100},{'semi_major_axis':True}):
            with self.subTest(kw=kw),self.assertRaises(ValueError):az.Ellipsoid(**kw)
        with self.assertRaises(ValueError):az.Datum(ellipsoid='WGS84')
        with self.assertRaises(ValueError):az.Unit('bad','x',0)

    def test_inverse_reference_global_polar_and_nearly_antipodal(self):
        solver=az.Geodesic();methods=set()
        for row in REFERENCE['inverse']:
            c=row['input']
            with self.subTest(coordinates=c):
                result=solver.inverse(*c);methods.add(result.method)
                self.assertLessEqual(abs(result.distance-row['distance']),.001)
                # Azimuth is nonunique for coincident/exact antipodes and poles.
                ambiguous=result.distance==0 or abs(c[1])==90 or abs(c[3])==90 or abs(abs(wrap_longitude(c[2]-c[0]))-180)<1e-10 and abs(c[1]+c[3])<1e-10
                if not ambiguous:
                    self.assertLessEqual(abs(wrap_longitude(result.azimuth1-row['azimuth1'])),1e-7)
                    self.assertLessEqual(abs(wrap_longitude(result.azimuth2-row['azimuth2'])),1e-7)
                endpoint=solver.direct(c[0],c[1],result.azimuth1,result.distance)
                self.assertLessEqual(az.haversine((endpoint.longitude,endpoint.latitude),(c[2],c[3])),.001)
        self.assertIn('shooting',methods);self.assertIn('vincenty',methods)

    def test_direct_reference_and_forward_endpoint_azimuth(self):
        solver=az.Geodesic()
        for row in REFERENCE['direct']:
            with self.subTest(coordinates=row['input']):
                result=solver.direct(*row['input'])
                self.assertLessEqual(abs(wrap_longitude(result.longitude-row['longitude'])),2e-8)
                self.assertLessEqual(abs(result.latitude-row['latitude']),2e-8)
                self.assertLessEqual(abs(wrap_longitude(result.azimuth2-row['azimuth2'])),1e-7)

    def test_sphere_grs80_and_distinct_spherical_legacy(self):
        sphere=az.Geodesic(az.Ellipsoid(6371008.8,0,'sphere'))
        self.assertAlmostEqual(sphere.inverse(0,0,90,0).distance,math.pi/2*6371008.8,places=7)
        self.assertAlmostEqual(sphere.inverse(0,0,180,0).distance,math.pi*6371008.8,places=5)
        wgs=az.Geodesic().inverse(-46,-23,-43,-22).distance
        grs=az.Geodesic(az.GRS80).inverse(-46,-23,-43,-22).distance
        self.assertLess(abs(wgs-grs),.001)
        self.assertGreater(abs(wgs-az.haversine((-46,-23),(-43,-22))),100)

    def test_geodesic_line_endpoints_zero_and_errors_without_mutation(self):
        solver=az.Geodesic();points=solver.line((175,0),(-175,5),steps=10)
        self.assertEqual(len(points),11);self.assertEqual(points[0],(175,0));self.assertEqual(points[-1],(-175,5))
        self.assertEqual(solver.direct(12,90,34,0).latitude,90)
        self.assertEqual(solver.inverse(10,90,20,90).distance,0)
        for c in ((181,0,0,1),(0,91,0,1),(0,0,0,-1),(0,0,True,1)):
            with self.subTest(c=c),self.assertRaises(ValueError):solver.direct(*c)
        for steps in (0,True,1.5):
            with self.assertRaises(ValueError):solver.line((0,0),(1,1),steps=steps)
        fig,ax=az.subplots();before=(ax.get_extent(),len(ax.layers))
        with self.assertRaises(ValueError):ax.route([(0,0),(181,1)],ellipsoid=az.WGS84)
        self.assertEqual(before,(ax.get_extent(),len(ax.layers)))
        layer=ax.route([(0,0),(1,1)],ellipsoid=az.WGS84,steps=5)
        self.assertEqual(len(layer.data[0].geometry.coordinates),6);az.close(fig)


class ProjectionCRSTests(unittest.TestCase):
    def test_all_utm_zones_hemispheres_against_reference(self):
        for row in REFERENCE['utm']:
            c=row['input'];crs=az.CRS(row['crs'])
            with self.subTest(crs=crs.code):
                xy=az.transform(*c,4326,crs)
                for actual,expected in zip(xy,row['output']):self.assertLessEqual(abs(actual-expected),.002)
                for actual,expected in zip(az.transform(*xy,crs,4326),c):self.assertAlmostEqual(actual,expected,delta=1e-8)
                self.assertEqual(az.transform(*xy,crs,crs),xy)
                self.assertEqual(crs.zone,row['crs']%100)

    def test_tm_edges_inverse_and_origin_parameters(self):
        for row in REFERENCE['transverse']:
            with self.subTest(coordinates=row['input']):
                xy=tm_forward(*row['input'])
                for a,b in zip(xy,row['output']):self.assertLessEqual(abs(a-b),.02)
                for a,b in zip(tm_inverse(*xy),row['input']):self.assertAlmostEqual(a,b,delta=1e-8)
        p=az.TransverseMercator(central_longitude=-45,central_latitude=-20,false_easting=500000,false_northing=10000000)
        self.assertEqual(p.forward(-45,-20),(500000,10000000))
        self.assertIsNone(p.forward(-30,-20));self.assertIsNone(p.inverse(1e9,1e9))
        self.assertIsNone(p.forward(-45,85))
        for params in ({'scale_factor':0},{'ellipsoid':'WGS84'},{'central_latitude':90}):
            with self.subTest(params=params),self.assertRaises((ValueError,TypeError)):az.TransverseMercator(**params)

    def test_spherical_projection_reference_matrix(self):
        for row in REFERENCE['projections']:
            with self.subTest(name=row['name'],coordinates=row['input']):
                p=az.get_projection(row['name'],central_longitude=-45,central_latitude=-20);xy=p.forward(*row['input'])
                for a,b in zip(xy,row['output']):self.assertAlmostEqual(a,b,delta=1e-5)
                for a,b in zip(p.inverse(*xy),row['input']):self.assertAlmostEqual(a,b,delta=1e-8)

    def test_azimuthal_centre_poles_distance_and_singularities(self):
        for cls in (az.Stereographic,az.AzimuthalEquidistant):
            for lat0 in (-90,-20,0,90):
                p=cls(central_longitude=30,central_latitude=lat0)
                self.assertLess(math.hypot(*p.forward(30,lat0)),1e-7)
                self.assertEqual(p.inverse(0,0),(30,lat0))
                self.assertIsNone(p.forward(-150,-lat0))
                with self.assertRaises(ValueError):p.forward(0,float('nan'))
        p=az.AzimuthalEquidistant();xy=p.forward(20,30)
        self.assertAlmostEqual(math.hypot(*xy),az.haversine((0,0),(20,30)),places=7)
        self.assertIsNone(p.inverse(math.pi*p.radius,0))

    def test_zone_rules_seam_and_explicit_hemisphere_validation(self):
        for lon,lat,zone in ((180,0,60),(-180,0,1),(6,60,32),(8,75,31),(10,75,33),(22,75,35),(34,75,37)):
            self.assertEqual(az.utm_zone(lon,lat),zone)
        self.assertEqual(az.utm_crs(-46.63,-23.55),az.CRS(32723))
        for lon,lat in ((181,0),(0,85),(0,-81)):
            with self.assertRaises(ValueError):az.utm_zone(lon,lat)
        for code in (32600,32661,32700,32761,26923):
            with self.assertRaises(ValueError):az.CRS(code)
        for c,code in (((-45,-20),32623),((-45,20),32723),((-30,-20),32723)):
            with self.assertRaises(ValueError):az.transform(*c,4326,code)
        with self.assertRaises(ValueError):az.transform(-1,0,32623,4326)

    def test_explicit_vector_input_and_elevation_preservation(self):
        xy=az.transform(-46.63,-23.55,4326,32723)
        c=transform_coordinates([(*xy,120)],32723,4326)[0]
        self.assertAlmostEqual(c[0],-46.63,places=8);self.assertEqual(c[2],120)
        data={'type':'Point','coordinates':[*xy,120]}
        feature=az.read_geojson(data,crs=32723)[0]
        self.assertAlmostEqual(feature.geometry.coordinates[1],-23.55,places=8)
        csv=az.read_csv(io.StringIO('x,y\n'+str(xy[0])+','+str(xy[1])),longitude='x',latitude='y',crs=32723)
        self.assertAlmostEqual(csv[0].geometry.coordinates[0],-46.63,places=8)
        raster=az.GeoRaster([[1]],(1,0,xy[0],0,-1,xy[1]),crs=32723)
        with self.assertRaisesRegex(ValueError,'curvilinear'):raster.geographic_mesh()


class TopologyTests(unittest.TestCase):
    def test_intersection_cross_endpoint_overlap_disjoint_zero_length(self):
        cases=[(((0,0),(2,2),(0,2),(2,0)),'point',((1.,1.),)),(((0,0),(2,0),(1,0),(3,0)),'overlap',((1.,0.),(2.,0.))),(((0,0),(1,0),(1,0),(2,1)),'point',((1.,0.),)),(((0,0),(1,0),(2,0),(3,0)),'none',()),(((1,0),(1,0),(0,0),(2,0)),'point',((1.,0.),))]
        for points,kind,expected in cases:
            for args in (points,points[2:]+points[:2]):
                hit=az.segment_intersection(*args);self.assertEqual((hit.kind,hit.points),(kind,expected))
        self.assertEqual(az.orientation((0,0),(1,1),(2,2)),0)
        self.assertEqual(az.orientation((0,0),(1,1),(2,2+1e-15)),1)

    def test_ring_closure_winding_bowtie_degenerate_and_seam(self):
        ring=((170,0),(-170,0),(-170,10),(170,10),(170,0))
        self.assertEqual(az.ring_orientation(ring),'counterclockwise')
        self.assertTrue(az.validate_ring(ring).valid)
        self.assertFalse(az.validate_ring(ring,winding='clockwise').valid)
        report=az.validate_ring(((0,0),(2,2),(0,2),(2,0),(0,0)))
        self.assertIn('self_intersection',{i.code for i in report.issues})
        for ring in (((0,0),(1,0),(2,0),(0,0)),((0,0),(1,0),(1,1)),((0,0),(0,0),(1,1),(0,0))):
            self.assertFalse(az.validate_ring(ring).valid)
        with self.assertRaises(ValueError):report.raise_if_invalid()

    def test_holes_and_multipolygon_overlap_opt_in_not_repair(self):
        shell=((0,0),(4,0),(4,4),(0,4),(0,0));hole=((1,1),(1,2),(2,2),(2,1),(1,1))
        good=az.Geometry('Polygon',(shell,hole));self.assertTrue(az.validate_geometry(good,require_winding=True).valid)
        outside=((5,5),(5,6),(6,6),(6,5),(5,5))
        self.assertFalse(az.validate_geometry(az.Geometry('Polygon',(shell,outside))).valid)
        self.assertFalse(az.validate_geometry(az.Geometry('Polygon',(shell,hole,hole))).valid)
        self.assertFalse(az.validate_geometry(az.Geometry('MultiPolygon',((shell,),(shell,)))).valid)
        self.assertTrue(az.validate_geometry(az.Geometry('MultiPolygon',((shell,hole),(((1.2,1.2),(1.8,1.2),(1.8,1.8),(1.2,1.8),(1.2,1.2)),)))).valid)
        self.assertTrue(az.validate_geometry(az.Geometry('GeometryCollection',geometries=(good,))).valid)
        self.assertEqual(good.coordinates,(shell,hole))


class SeamClippingTests(unittest.TestCase):
    def tearDown(self):az.close('all')

    def test_longitude_labels_wrap_without_changing_scalar_ticks(self):
        formatter=az.ticker.LongitudeFormatter()
        for value,label in ((185,'175°W'),(175,'175°E'),(180,'180°'),(540,'180°'),(-185,'175°E')):
            self.assertEqual(formatter(value),label)

    def test_fit_and_pan_zoom_cursor_across_seam(self):
        fig,ax=az.subplots();ax.line([(175,0),(-175,5)]);ax.fit_extent(margin=0)
        self.assertEqual(ax.get_extent(),(175,185,0,5))
        ax.pan(2,0);self.assertEqual(ax.get_xlim(),(177,187))
        expected=zoom_extent(ax,2,(-175,2));self.assertEqual(expected,(181.,186.,1.,3.5))
        ax.zoom(2,(-175,2));self.assertEqual(ax.get_extent(),(182.5,187.5,.75,3.25))
        meta=fig.to_scene().maps[0];self.assertTrue(meta['longitude_wrap'])
        vp=viewport_from_metadata(ax.projection,meta);x,y,w,h=vp.box
        extent=drag_extent(ax,vp,(x+w/2,y+h/2),(x+w*.6,y+h/2))
        self.assertLess(extent[1]-extent[0],10);self.assertGreater(extent[0],170)
        self.assertLess(abs(wrap_longitude(vp.inverse(*vp.project(-175,2))[0]+175)),1e-8)

    def test_history_restores_projection_branch_and_shared_limits(self):
        fig,axes=az.subplots(1,2,sharex=True);axes[0].set_extent((-60,-40,-30,-10));nav=Navigation(fig)
        axes[0].set_extent((170,-170,-10,10));nav.push()
        self.assertEqual(axes[1].get_xlim(),(170,190));self.assertTrue(axes[1]._longitude_wrap)
        axes[0].pan(2,0);nav.push();self.assertEqual(axes[1].get_xlim(),(172,192))
        nav.home();self.assertFalse(axes[0]._longitude_wrap);self.assertEqual(axes[0].projection.central_longitude,0)
        nav.back();self.assertEqual(axes[0].get_xlim(),(172,192));self.assertTrue(axes[0]._longitude_wrap)

    def test_bad_extent_is_atomic_and_non_cylindrical_cut_is_explicit(self):
        fig,ax=az.subplots();before=(ax.get_extent(),ax.projection,ax._longitude_wrap)
        for extent in ((180,-180,0,1),(170,-170,10,0),(170,-170,0,100),(0,400,0,1)):
            with self.subTest(extent=extent),self.assertRaises(ValueError):ax.set_extent(extent)
            self.assertEqual((ax.get_extent(),ax.projection,ax._longitude_wrap),before)
        other=fig.add_axes((.1,.1,.2,.2),projection='orthographic')
        with self.assertRaises(ValueError):other.set_extent((170,-170,-10,10))

    def test_static_export_continuous_lines_polygons_and_holes(self):
        fig,ax=az.subplots();ax.set_extent((170,-170,-10,10))
        ax.line([(175,0),(-175,0)],color='red');ax.polygon([(172,-6),(-172,-6),(-172,6),(172,6)],holes=[[(177,-2),(177,2),(-177,2),(-177,-2)]])
        with tempfile.TemporaryDirectory() as directory:
            png=Path(directory)/'seam.png';svg=Path(directory)/'seam.svg';fig.savefig(png);fig.savefig(svg)
            self.assertGreater(png.stat().st_size,1000);self.assertIn('fill-rule="evenodd"',svg.read_text())
        self.assertIn('longitude_wrap',fig.to_html());self.assertNotIn('<script',fig.to_svg())

    def test_horizon_crossing_hidden_hidden_tangent_and_degenerate_lines(self):
        p=az.Orthographic()
        parts=az.clip_orthographic_line(((80,0),(100,0)),p)
        self.assertEqual(len(parts),1);self.assertAlmostEqual(math.hypot(*parts[0][-1]),p.radius,delta=1e-7)
        self.assertEqual(az.clip_orthographic_line(((120,0),(130,0)),p),())
        self.assertEqual(az.clip_orthographic_line(((0,0),(0,0)),p),())
        parts=az.clip_orthographic_line(((-100,0),(100,0)),p)
        self.assertEqual(parts,()) # shortest longitude branch crosses the hidden side.
        for step in (0,11):
            with self.assertRaises(ValueError):az.clip_orthographic_line(((0,0),(1,0)),p,step=step)

    def test_polygon_horizon_holes_and_winding_symmetry(self):
        p=az.Orthographic();shell=((70,-20),(110,-20),(110,20),(70,20),(70,-20))
        result=az.clip_orthographic_polygon((shell,),p)
        self.assertTrue(result)
        for poly in result:
            for ring in poly:
                self.assertEqual(ring[0],ring[-1])
                self.assertTrue(all(math.hypot(*point)<=p.radius*(1+1e-10) for point in ring))
        reverse=az.clip_orthographic_polygon((tuple(reversed(shell)),),p)
        self.assertEqual(len(reverse),len(result))
        degenerate=((0,0),(1,0),(2,0),(0,0));self.assertEqual(az.clip_orthographic_polygon((degenerate,),p),())

    @unittest.skipUnless(shutil.which('node'),'Node is optional for portable integration')
    def test_portable_seam_pan_zoom_history_and_shared_model(self):
        fig,axes=az.subplots(1,2,sharex=True);axes[0].set_extent((170,-170,-10,10))
        script=r"""const fs=require('fs'),assert=require('assert');const {Navigation}=require(process.argv[1]);const meta=JSON.parse(fs.readFileSync(0,'utf8'));const n=new Navigation(meta);assert(n.portable(0));assert.deepStrictEqual(n.extent(0).map(Math.round),[170,190,-10,10]);n.pan(0,-20,0);n.commit();const next=n.extent(0);assert(next[0]>170&&next[1]>180);assert(Math.abs(n.extent(1)[0]-next[0])<1e-8);n.zoom(0,2);n.commit();assert(n.extent(0)[1]-n.extent(0)[0]<11);n.home();assert.deepStrictEqual(n.extent(0).map(Math.round),[170,190,-10,10]);n.navigate(-1);assert(n.extent(0)[1]-n.extent(0)[0]<11);n.setExtent(0,[175,-175,-5,5]);assert.deepStrictEqual(n.extent(0).map(Math.round),[175,185,-5,5]);"""
        result=subprocess.run(['node','-e',script,str(ROOT/'src/azimlib/assets/navigation.js')],input=json.dumps(fig.to_scene().maps),text=True,capture_output=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

if __name__=='__main__':unittest.main()

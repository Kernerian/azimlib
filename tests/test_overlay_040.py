"""Analytic set identities, exact constructions and global spherical cases."""
import io,json,math,random,unittest
from dataclasses import FrozenInstanceError
from fractions import Fraction

import azimlib as az
from azimlib import _overlay_planar as plane
from azimlib import _overlay_sphere as sphere


def rectangle(x0,y0,x1,y1):return az.Geometry('Polygon',(((x0,y0),(x1,y0),(x1,y1),(x0,y1),(x0,y0)),))
def ring(x0,y0,x1,y1):return rectangle(x0,y0,x1,y1).coordinates[0]


class PlanarOverlayTests(unittest.TestCase):
    def test_analytic_rectangle_boolean_areas(self):
        a,b=rectangle(0,0,3,3),rectangle(1,1,4,4)
        for op,area in (('intersection',4),('union',14),('difference',5),('symmetric_difference',10)):
            with self.subTest(operation=op):
                result=az.overlay(a,b,op)
                self.assertEqual(result.area(),area)
                self.assertTrue(az.validate_topology(result.geometry).valid)
                self.assertTrue(result.topology.nodes);self.assertGreater(result.topology.candidate_pairs,0)
        self.assertEqual(a,rectangle(0,0,3,3))

    def test_holes_nesting_and_difference(self):
        shell,inner=rectangle(0,0,8,8),rectangle(2,2,6,6)
        result=az.difference(shell,inner)
        self.assertEqual(result.area(),48);self.assertEqual(len(result.geometry.coordinates),2)
        self.assertGreater(plane.signed_area(result.geometry.coordinates[0]),0)
        self.assertLess(plane.signed_area(result.geometry.coordinates[1]),0)
        self.assertEqual(az.union(result.geometry,inner).area(),64)
        self.assertTrue(az.intersection(result.geometry,rectangle(3,3,5,5)).is_empty)

    def test_contact_line_and_point_not_fabricated_area(self):
        a=rectangle(0,0,1,1)
        line=az.intersection(a,rectangle(1,0,2,1))
        point=az.intersection(a,rectangle(1,1,2,2))
        self.assertEqual(line.geometry.type,'LineString');self.assertEqual(line.area(),0)
        self.assertEqual(point.geometry.type,'Point');self.assertEqual(point.geometry.coordinates,(1,1))
        self.assertEqual(az.union(a,rectangle(1,1,2,2)).area(),2)

    def test_coincident_dissolve_and_edge_lineage(self):
        a,b=rectangle(0,0,2,2),rectangle(2,0,4,2)
        result=az.union(a,b);self.assertEqual(result.area(),8)
        self.assertEqual(len(result.topology.shared_edges),1)
        self.assertEqual(result.shared_boundaries().coordinates,(((2.,0.),(2.,2.)),))
        edge=result.topology.shared_edges[0]
        self.assertEqual({s[0] for s in edge.sources},{0,1})
        with self.assertRaises(FrozenInstanceError):edge.start=4
        identical=az.intersection(a,a)
        self.assertEqual(identical.area(),4);self.assertEqual(len(identical.topology.shared_edges),4)
        self.assertTrue(az.difference(a,a).is_empty)

    def test_exact_rational_noding_and_lines(self):
        a=az.Geometry('LineString',((0,0),(1,1)))
        b=az.Geometry('LineString',((0,1),(2,0)))
        result=az.intersection(a,b)
        self.assertEqual(result.geometry.type,'Point')
        self.assertIn((Fraction(2,3),Fraction(2,3)),result.topology.nodes)
        overlap=az.intersection(az.Geometry('LineString',((0,0),(4,0))),az.Geometry('LineString',((2,0),(6,0))))
        self.assertEqual(overlap.geometry.coordinates,((2,0),(4,0)))
        line=az.Geometry('LineString',((-1,1),(5,1)))
        clipped=az.intersection(line,rectangle(0,0,4,2));self.assertEqual(clipped.geometry.coordinates,((0,1),(4,1)))
        outside=az.difference(line,rectangle(0,0,4,2));self.assertEqual(outside.geometry.type,'MultiLineString')
        self.assertEqual(az.difference(rectangle(0,0,4,2),line).area(),8)

    def test_isolated_points_and_multipart(self):
        p=az.Geometry('MultiPoint',((.5,.5),(5,5)))
        result=az.intersection(p,rectangle(0,0,1,1))
        self.assertEqual(result.geometry.coordinates,(.5,.5))
        result=az.union(p,rectangle(0,0,1,1));self.assertEqual(result.geometry.type,'GeometryCollection')
        multi=az.Geometry('MultiPolygon',(rectangle(0,0,1,1).coordinates,rectangle(2,2,3,3).coordinates))
        self.assertEqual(az.intersection(multi,rectangle(-1,-1,4,4)).area(),2)

    def test_no_implicit_longitude_unwrap_or_repair(self):
        seam=rectangle(-175,-10,175,10)
        self.assertEqual(az.intersection(seam,rectangle(-1,-1,1,1)).area(),4)
        bow=az.Geometry('Polygon',(((0,0),(2,2),(0,2),(2,0),(0,0)),))
        self.assertFalse(az.validate_topology(bow).valid)
        with self.assertRaises(az.TopologyError):az.union(bow,rectangle(3,3,4,4))
        repaired=az.repair_geometry(bow,method='even_odd')
        self.assertFalse(repaired.before.valid);self.assertTrue(repaired.after.valid)
        self.assertEqual(az.union(repaired.geometry,az.Geometry('Polygon')).area(),2)
        self.assertTrue(repaired.changes)
        self.assertEqual(bow.coordinates[0][1],(2,2))

    def test_repair_normalize_is_opt_in_and_reports(self):
        bad=az.Geometry('Polygon',(((0,0),(0,2),(0,2),(2,2),(2,0),(0,0)),))
        repaired=az.repair_geometry(bad)
        self.assertEqual(len(repaired.geometry.coordinates[0]),5);self.assertEqual(len(repaired.changes),2)
        self.assertEqual(len(bad.coordinates[0]),6)
        outside=az.Geometry('Polygon',(ring(0,0,2,2),ring(4,4,5,5)))
        with self.assertRaises(az.TopologyError):az.repair_geometry(outside)
        fixed=az.repair_geometry(outside,method='even_odd')
        self.assertEqual(az.union(fixed.geometry,az.Geometry('Polygon')).area(),4)

    def test_validation_holes_crossings_dimensions_and_budgets(self):
        cases=[az.Geometry('Polygon',(ring(0,0,3,3),ring(2,2,4,4))),
               az.Geometry('Polygon',(ring(0,0,8,8),ring(1,1,6,6),ring(2,2,3,3))),
               az.Geometry('MultiPolygon',(rectangle(0,0,3,3).coordinates,rectangle(1,1,4,4).coordinates)),
               az.Geometry('LineString',((0,0),(0,0))),
               az.Geometry('LineString',((0,0,1),(1,1,1)))]
        for geom in cases:
            with self.subTest(geometry=geom),self.assertRaises(az.TopologyError):az.union(geom,az.Geometry('Polygon'))
        a,b=rectangle(0,0,3,3),rectangle(1,1,4,4)
        for kwargs in ({'max_segments':2},{'max_pairs':1},{'max_edges':1},{'max_pairs':True},{'domain':'unknown'}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):az.intersection(a,b,**kwargs)
        self.assertEqual(az.union(az.Geometry('GeometryCollection',geometries=(a,)),b).area(),14)

    def test_deterministic_random_rectangles_analytic_oracle(self):
        rng=random.Random(4004)
        for i in range(80):
            x,y,u,v=[rng.randint(-20,20) for _ in range(4)];w,h,p,q=[rng.randint(1,12) for _ in range(4)]
            a,b=rectangle(x,y,x+w,y+h),rectangle(u,v,u+p,v+q)
            area=max(0,min(x+w,u+p)-max(x,u))*max(0,min(y+h,v+q)-max(y,v))
            for op,expected in (('intersection',area),('union',w*h+p*q-area),('difference',w*h-area),('symmetric_difference',w*h+p*q-2*area)):
                with self.subTest(i=i,operation=op):self.assertEqual(az.overlay(a,b,op).area(),expected)

    def test_exact_predicates_near_parallel_and_large_translation(self):
        a=(Fraction(0),Fraction(0));b=(Fraction(10**12),Fraction(1));c=(Fraction(0),Fraction(1,10**12));d=(Fraction(10**12),Fraction(0))
        hit,=plane.hits(a,b,c,d)
        self.assertTrue(plane.on(hit,a,b));self.assertTrue(plane.on(hit,c,d))
        for offset in (0,10**12):
            self.assertEqual(az.intersection(rectangle(offset,0,offset+3,3),rectangle(offset+1,1,offset+4,4)).area(),4)


class SphericalOverlayTests(unittest.TestCase):
    def test_hemisphere_lune_octant_analytic_areas(self):
        north=az.SphericalRegion.hemisphere(0,90);east=az.SphericalRegion.hemisphere(0,0)
        quarter=az.intersection(north,east,domain='spherical')
        self.assertAlmostEqual(north.area(radius=1),2*math.pi,places=12)
        self.assertAlmostEqual(quarter.area(radius=1),math.pi,places=12)
        octant=az.intersection(quarter.geometry,az.SphericalRegion.hemisphere(90,0),domain='spherical')
        self.assertAlmostEqual(octant.area(radius=1),math.pi/2,places=12)
        self.assertTrue(octant.geometry.covers(45,45));self.assertFalse(octant.geometry.covers(-45,45))
        for delta in (10,35,80,120,170):
            other=az.SphericalRegion.hemisphere(delta,0)
            with self.subTest(delta=delta):
                self.assertAlmostEqual(az.intersection(east,other,domain='spherical').area(radius=1),2*(math.pi-math.radians(delta)),places=10)

    def test_poles_antimeridian_and_large_complements(self):
        cap=az.SphericalRegion.from_geometry(az.Geometry('Polygon',(((-135,60),(-45,60),(45,60),(135,60),(-135,60)),)))
        self.assertTrue(cap.covers(0,90));self.assertTrue(cap.covers(170,80));self.assertFalse(cap.covers(0,0))
        seam=az.SphericalRegion.from_geometry(az.Geometry('Polygon',(((170,-10),(-170,-10),(-170,10),(170,10),(170,-10)),)))
        self.assertTrue(seam.covers(180,0));self.assertTrue(seam.covers(-180,0));self.assertFalse(seam.covers(0,0))
        large=seam.complement();self.assertGreater(large.area(radius=1),2*math.pi)
        self.assertAlmostEqual(large.area(radius=1)+seam.area(radius=1),4*math.pi,places=12)
        north=az.SphericalRegion.hemisphere(0,90)
        self.assertTrue(az.intersection(large,north,domain='spherical').geometry.covers(0,80))
        self.assertFalse(az.intersection(large,north,domain='spherical').geometry.covers(180,5))

    def test_sphere_boolean_identities_full_empty_and_serialization(self):
        a=az.SphericalRegion.from_geometry(rectangle(-20,-10,20,10))
        full=az.union(a,a.complement(),domain='spherical').geometry
        self.assertTrue(full.is_full);self.assertAlmostEqual(full.area(radius=1),4*math.pi)
        self.assertTrue(az.intersection(a,a.complement(),domain='spherical').is_empty)
        self.assertTrue(az.difference(a,a,domain='spherical').is_empty)
        self.assertTrue(az.symmetric_difference(a,a,domain='spherical').is_empty)
        self.assertAlmostEqual(az.intersection(full,a,domain='spherical').area(radius=1),a.area(radius=1))
        for item in (a,a.complement(),full,full.complement()):
            restored=az.SphericalRegion.from_dict(json.loads(json.dumps(item.to_dict())))
            self.assertAlmostEqual(item.area(radius=1),restored.area(radius=1),places=11)
            for x,y in ((0,0),(180,0),(0,90),(-175,-80),(19,0)):
                with self.subTest(point=(x,y)):self.assertEqual(item.location(x,y),restored.location(x,y))

    def test_general_overlapping_regions_and_set_area_identity(self):
        a,b=(az.SphericalRegion.from_geometry(g) for g in (rectangle(-25,-20,10,20),rectangle(-10,-10,30,30)))
        intersection=az.intersection(a,b,domain='spherical');union=az.union(a,b,domain='spherical')
        diff=az.difference(a,b,domain='spherical');xor=az.symmetric_difference(a,b,domain='spherical')
        self.assertAlmostEqual(a.area(radius=1)+b.area(radius=1),intersection.area(radius=1)+union.area(radius=1),places=11)
        self.assertAlmostEqual(a.area(radius=1),intersection.area(radius=1)+diff.area(radius=1),places=11)
        self.assertAlmostEqual(xor.area(radius=1),union.area(radius=1)-intersection.area(radius=1),places=11)
        restored=az.SphericalRegion.from_dict(xor.geometry.to_dict())
        self.assertAlmostEqual(restored.area(radius=1),xor.area(radius=1),places=11)
        for x in range(-35,40,7):
            for y in range(-35,40,7):
                la,lb=a.covers(x,y),b.covers(x,y)
                for op,result in (('union',union),('intersection',intersection),('difference',diff),('symmetric_difference',xor)):
                    with self.subTest(point=(x,y),op=op):self.assertEqual(result.geometry.covers(x,y),plane.boolean(op,la,lb))

    def test_hole_and_left_interior_explicit(self):
        geom=az.Geometry('Polygon',(ring(-30,-30,30,30),ring(-10,-10,10,10)))
        donut=az.SphericalRegion.from_geometry(geom)
        self.assertFalse(donut.covers(0,0));self.assertTrue(donut.covers(20,0))
        small=az.SphericalRegion.from_geometry(rectangle(-10,-10,10,10))
        reverse=az.Geometry('Polygon',(rectangle(-10,-10,10,10).coordinates[0][::-1],))
        left=az.SphericalRegion.from_geometry(reverse,interior='left')
        self.assertGreater(left.area(radius=1),2*math.pi);self.assertFalse(left.covers(0,0));self.assertTrue(left.covers(120,0))
        self.assertAlmostEqual(az.union(donut,small,domain='spherical').area(radius=1),az.SphericalRegion.from_geometry(rectangle(-30,-30,30,30)).area(radius=1),places=11)

    def test_coincident_arcs_and_sphere_budgets(self):
        a=az.SphericalRegion.from_geometry(rectangle(-20,-10,20,10))
        result=az.intersection(a,a,domain='spherical')
        self.assertEqual(len(result.topology.shared_edges),4);self.assertEqual(len(result.shared_boundaries().coordinates),4)
        self.assertAlmostEqual(result.area(radius=1),a.area(radius=1),places=12)
        for kwargs in ({'max_segments':2},{'max_pairs':1},{'max_edges':1}):
            with self.subTest(kwargs=kwargs),self.assertRaises(az.TopologyError):az.union(a,a,domain='spherical',**kwargs)
        with self.assertRaises(TypeError):az.union(rectangle(0,0,1,1),rectangle(1,1,2,2),domain='spherical')

    def test_spherical_invalid_and_ambiguous_fail_explicitly(self):
        for geom in (az.Geometry('Polygon',(((0,0),(180,0),(90,30),(0,0)),)),
                     az.Geometry('Polygon',(((0,0),(20,20),(0,20),(20,0),(0,0)),)),
                     az.Geometry('Polygon',(((0,0),(1e-12,0),(1,1),(0,0)),))):
            with self.subTest(geometry=geom),self.assertRaises(az.TopologyError):az.SphericalRegion.from_geometry(geom)
        with self.assertRaises(ValueError):az.SphericalRegion(tolerance=0)
        with self.assertRaises(ValueError):az.SphericalRegion.from_dict({})
        with self.assertRaises(az.TopologyError):az.SphericalRegion((ring(-10,-10,10,10),),reference=(0,0),reference_inside=False)

    def test_global_random_hemisphere_oracles_and_demorgan(self):
        rng=random.Random(404040)
        for i in range(24):
            a=az.SphericalRegion.hemisphere(rng.uniform(-180,180),rng.uniform(-85,85))
            b=az.SphericalRegion.hemisphere(rng.uniform(-180,180),rng.uniform(-85,85))
            # Independent analytic lune: intersection area = 2*(pi-theta),
            # where theta is the angle between the two hemisphere normals.
            theta=math.acos(max(-1,min(1,sum(x*y for x,y in zip(a.reference,b.reference)))))
            both=az.intersection(a,b,domain='spherical')
            either=az.union(a,b,domain='spherical')
            demorgan=az.intersection(a.complement(),b.complement(),domain='spherical')
            with self.subTest(i=i):
                self.assertAlmostEqual(both.area(radius=1),2*(math.pi-theta),places=10)
                self.assertAlmostEqual(either.area(radius=1)+demorgan.area(radius=1),4*math.pi,places=10)
                for lon,lat in ((0,0),(170,80),(-175,-80),(95,-5)):
                    self.assertEqual(both.geometry.covers(lon,lat),a.covers(lon,lat) and b.covers(lon,lat))

    def test_disconnected_large_regions_and_multiple_holes(self):
        a=az.SphericalRegion.from_geometry(rectangle(-80,-10,-60,10))
        b=az.SphericalRegion.from_geometry(rectangle(60,-10,80,10))
        islands=az.union(a,b,domain='spherical').geometry
        self.assertEqual(len(islands.rings),2)
        self.assertAlmostEqual(islands.area(radius=1),a.area(radius=1)+b.area(radius=1),places=11)
        complement=islands.complement()
        self.assertGreater(complement.area(radius=1),2*math.pi)
        restored=az.SphericalRegion.from_dict(complement.to_dict())
        for lon,lat in ((0,0),(-70,0),(70,0),(0,90),(180,-90)):
            with self.subTest(point=(lon,lat)):self.assertEqual(restored.covers(lon,lat),not islands.covers(lon,lat))
        self.assertAlmostEqual(az.intersection(a.complement(),b.complement(),domain='spherical').area(radius=1),complement.area(radius=1),places=11)


class OverlayIntegrationTests(unittest.TestCase):
    def tearDown(self):az.close('all')

    def test_reader_clip_select_properties_and_editable_layer(self):
        source=az.read_geojson({'type':'FeatureCollection','features':[
            az.Feature(rectangle(0,0,3,3),{'name':'block','building':'yes'},'way/1').to_geojson(),
            az.Feature(az.Geometry('LineString',((-1,1),(5,1))),{'highway':'residential'},'way/2').to_geojson()]})
        selected=source.spatial_select(rectangle(1,1,2,2));self.assertIs(selected[0],source[0])
        clipped=source.clip(rectangle(1,1,2,2));self.assertEqual([f.id for f in clipped],['way/1','way/2'])
        self.assertEqual(clipped[0].properties,source[0].properties)
        combined=az.overlay_features(source[0],az.Feature(rectangle(1,1,2,2),{'name':'area'},'region'))
        self.assertEqual(combined.properties['left']['properties']['name'],'block')
        self.assertEqual(combined.properties['right']['properties']['name'],'area')
        fig,ax=az.subplots(figsize=(3,3));layer=ax.geojson(clipped)
        layer.set_visible(False);self.assertFalse(layer.get_visible());layer.set_visible(True)
        for format in ('svg','png'):
            output=io.StringIO() if format=='svg' else io.BytesIO();fig.savefig(output,format=format);self.assertGreater(len(output.getvalue()),100)

    def test_scalar_rgba_projected_masks_preserve_nodata_and_height(self):
        frame=az.CoordinateFrame('height','geographic')
        raster=az.GeoRaster(((1,None),(3,4)),(1,0,0,0,1,0),height_frame=frame)
        mask=raster.mask_region(rectangle(0,0,1,2))
        self.assertEqual(mask.values,((1,None),(3,None)));self.assertEqual(mask.height_frame,frame)
        self.assertEqual(raster.mask_region(rectangle(0,0,1,2),invert=True).values,((None,None),(None,4)))
        rgba=az.GeoRaster((((255,0,0,255),(0,255,0,255)),),(1,0,0,0,1,0),color_mode='rgba')
        self.assertEqual(rgba.mask_region(rectangle(0,0,1,2)).values[0][1],(0,0,0,0))
        projected=az.GeoRaster(((1,2),),(1000,0,0,0,1000,0),3857)
        self.assertEqual(projected.mask_region(rectangle(0,0,.009,1)).values,((1,None),))
        hemi=az.SphericalRegion.hemisphere(0,90)
        self.assertEqual(raster.mask_region(hemi,domain='spherical').values,raster.values)

    def test_global_region_optional_artists_and_export(self):
        fig,ax=az.subplots(projection='orthographic',projection_kw={'central_latitude':35})
        before=len(ax.layers);region=az.SphericalRegion.hemisphere(20,30)
        artists=ax.region(region,fill_step=15,boundary_step=5)
        self.assertEqual(len(ax.layers),before+2)
        for artist in artists:artist.set_visible(False);self.assertFalse(artist.get_visible());artist.set_visible(True)
        for format in ('png','svg'):
            output=io.StringIO() if format=='svg' else io.BytesIO();fig.savefig(output,format=format);self.assertGreater(len(output.getvalue()),100)
        with self.assertRaises(az.TopologyError):ax.region(region,fill_step=.1,max_cells=10)


if __name__=='__main__':unittest.main()

"""Independent analytic fixtures and published numeric facts; no GIS oracle."""
from dataclasses import FrozenInstanceError
import io
import json
import math
from pathlib import Path
import shutil
import subprocess
import unittest

import azimlib as azl
from azimlib.crs import transform_coordinates, transform_geojson


class CatalogTests(unittest.TestCase):
    def test_catalog_coverage_and_immutable_definitions(self):
        self.assertEqual(len(azl.crs_catalog.codes()), 124)
        self.assertEqual(len(azl.crs_catalog.codes(kind='projected')), 121)
        for code in azl.crs_catalog.codes():
            with self.subTest(code=code):
                crs = azl.CRS(code)
                self.assertEqual(crs.definition.catalog_version, azl.crs_catalog.version)
                self.assertEqual(len(crs.axis_order), crs.dimensions)
                self.assertEqual(len(crs.axis_units), crs.dimensions)
                self.assertEqual(crs.definition.definition_license, 'BSD-3-Clause')
                self.assertTrue(crs.definition.sources)
                self.assertEqual(azl.CRS.from_user_input(json.loads(json.dumps(crs.to_dict()))), crs)
        with self.assertRaises(FrozenInstanceError):
            azl.crs_catalog.get(4326).dimensions = 4
        with self.assertRaises(ValueError):
            azl.crs_catalog.codes(kind='unknown')

    def test_axis_authority_distinction_and_utm_metadata(self):
        self.assertEqual(azl.CRS(4979).axis_order, ('longitude', 'latitude', 'height'))
        self.assertEqual(azl.CRS(4979).authority_axis_order, ('latitude', 'longitude', 'height'))
        self.assertEqual(azl.CRS(4978).axis_units, ('metres',)*3)
        self.assertEqual(azl.CRS(32723).area_of_use, (-48, -80, -42, 0))
        self.assertEqual(azl.CRS('OGC:CRS84'), azl.CRS(4326))

    def test_profiles_reject_stale_conflicting_or_partial_identity(self):
        for update in ({'version': 2}, {'catalog_version': 'other'}, {'axes': ['latitude','longitude']},
                       {'datum': 'NAD83'}, {'extra': 'ignored?'}):
            profile = azl.CRS(4326).to_dict(); profile.update(update)
            with self.subTest(update=update), self.assertRaises(ValueError):
                azl.CRS.from_dict(profile)
        for value in ({'code': 'EPSG:4326'}, {}, 'GEOGCRS["WGS84",ID["EPSG",4326]]',
                      '+proj=longlat +datum=WGS84', 'EPSG:999999', 'EPSG:4269'):
            with self.assertRaises(ValueError):
                azl.CRS.from_user_input(value)


class ConversionTests(unittest.TestCase):
    def tearDown(self):
        azl.close('all')

    def test_geocentric_cardinal_analytic_values(self):
        forward = azl.Transformer(4979, 4978)
        a, b = azl.WGS84.semi_major_axis, azl.WGS84.semi_minor_axis
        for point, expected in (((0,0,0),(a,0,0)), ((90,0,100),(0,a+100,0)),
                                ((0,90,0),(0,0,b)), ((-90,0,-100),(0,-a+100,0))):
            with self.subTest(point=point):
                for actual, wanted in zip(forward.transform(*point), expected):
                    self.assertAlmostEqual(actual, wanted, delta=1e-8)

    def test_global_3d_roundtrips_including_shallow_height_and_poles(self):
        transform = azl.Transformer(4979, 4978)
        for lon in (-180,-120,-45,0,45,120,180):
            for lat in (-90,-89.999,-60,0,60,89.999,90):
                for height in (-10000,0,1000,35_786_000):
                    with self.subTest(lon=lon, lat=lat, height=height):
                        back = transform.inverse().transform(*transform.transform(lon,lat,height))
                        if abs(lat) != 90:
                            self.assertAlmostEqual(back[0],lon,delta=1e-10)
                        self.assertAlmostEqual(back[1],lat,delta=1e-10)
                        self.assertAlmostEqual(back[2],height,delta=1e-7)

    def test_3d_input_validation_identity_and_legacy_height(self):
        for xyz in ((0,0,0),(1,2,3),(math.nan,1,2)):
            with self.assertRaises(ValueError):
                azl.Transformer(4978,4979).transform(*xyz)
        for point in ((181,0,0),(0,91,0),(0,0,-10001),(0,0,math.inf)):
            with self.assertRaises(ValueError):
                azl.Transformer(4979,4979).transform(*point)
        with self.assertRaises(ValueError):
            azl.transform(0,0,4979,4978)
        with self.assertRaises(ValueError):
            azl.Transformer(4326,4978).transform(0,0)
        self.assertEqual(azl.Transformer(4979,4979).transform(1,2,3),(1,2,3))
        self.assertEqual(transform_coordinates([(0,0,12)],4326,4326),((0,0,12),))
        with self.assertRaises(ValueError):
            transform_coordinates([(0,0,0,0)])

    def test_projected_xyz_3d_and_geojson_reader_artist_export(self):
        lon, lat, height = -46.63,-23.55,760
        xy = azl.transform(lon,lat,4326,32723)
        transform = azl.Transformer(32723,4978)
        xyz = transform.transform(*xy,height)
        for actual, expected in zip(transform.inverse().transform(*xyz),(*xy,height)):
            self.assertAlmostEqual(actual,expected,delta=1e-6)
        raw = {'type':'Feature','id':'xyz','properties':{'value':5},'bbox':[0,0,1,1],
               'geometry':{'type':'Point','coordinates':xyz}}
        original = json.dumps(raw)
        converted = transform_geojson(raw,4978,4326)
        self.assertNotIn('bbox',converted)
        self.assertEqual(json.dumps(raw),original)
        data = azl.read_geojson(raw,crs=4978)
        for actual, expected in zip(data[0].geometry.coordinates,(lon,lat,height)):
            self.assertAlmostEqual(actual,expected,delta=1e-8)
        fig,ax = azl.subplots(figsize=(3,2));ax.geojson(data);ax.set_extent((-48,-45,-25,-22))
        svg = io.StringIO();fig.savefig(svg,format='svg');self.assertIn('<svg',svg.getvalue())
        png = io.BytesIO();fig.savefig(png,format='png');self.assertTrue(png.getvalue().startswith(b'\x89PNG'))

    def test_crs_pipeline_composition_and_inversion(self):
        pipeline = azl.CoordinatePipeline((azl.Transformer(4326,32723),azl.Transformer(32723,4978)))
        point = (-46,-23,12)
        result = pipeline.transform(*point)
        for actual,expected in zip(pipeline.inverse().transform(*result),point):
            self.assertAlmostEqual(actual,expected,delta=1e-8)
        self.assertEqual(pipeline.source,azl.CRS(4326))
        for steps in ((),(object(),),(azl.Transformer(4326,3857),azl.Transformer(32723,4326))):
            with self.assertRaises((ValueError,TypeError)):
                azl.CoordinatePipeline(steps)
        self.assertEqual(azl.CoordinatePipeline((azl.Transformer(4326,32723),)).then(
            azl.Transformer(32723,4978)),pipeline)

    def test_raster_rejects_missing_third_axis_and_preserves_2d(self):
        for code in (4978,4979):
            with self.assertRaisesRegex(ValueError,'2D CRS'):
                azl.GeoRaster([[1]],(1,0,0,0,-1,1),crs=code)
        raster = azl.GeoRaster([[1,2],[3,4]],(1,0,0,0,-1,2))
        x,y,rows=raster.geographic_mesh()
        self.assertEqual(x,(0,1,2));self.assertEqual(y,(0,1,2))
        self.assertEqual(rows,((3,4),(1,2)))

    def test_laea_cardinal_values_and_area_jacobian(self):
        projection = azl.get_projection('laea',radius=1)
        self.assertIsInstance(projection,azl.LambertAzimuthalEqualArea)
        for point,expected in (((0,0),(0,0)),((90,0),(math.sqrt(2),0)),
                               ((0,90),(0,math.sqrt(2))),((-90,0),(-math.sqrt(2),0))):
            for actual,wanted in zip(projection.forward(*point),expected):
                self.assertAlmostEqual(actual,wanted,delta=1e-14)
        for lon,lat in ((30,20),(-45,-60),(120,40)):
            h=1e-4;d=math.radians(h)
            left,right=projection.forward(lon-h,lat),projection.forward(lon+h,lat)
            down,up=projection.forward(lon,lat-h),projection.forward(lon,lat+h)
            u=[(b-a)/(2*d) for a,b in zip(left,right)]
            v=[(b-a)/(2*d) for a,b in zip(down,up)]
            self.assertAlmostEqual(abs(u[0]*v[1]-u[1]*v[0]),math.cos(math.radians(lat)),delta=1e-9)

    def test_laea_origins_roundtrips_singularities_and_export(self):
        for origin in ((0,0),(-45,-20),(30,90),(30,-90)):
            projection=azl.LambertAzimuthalEqualArea(central_longitude=origin[0],central_latitude=origin[1])
            self.assertEqual(projection.inverse(0,0),origin)
            self.assertIsNone(projection.forward(origin[0]+180,-origin[1]))
            self.assertIsNone(projection.inverse(2*projection.radius,0))
            for lon,lat in ((0,0),(10,20),(-100,-50),(160,65)):
                xy=projection.forward(lon,lat)
                if xy is not None:
                    for actual,wanted in zip(projection.inverse(*xy),(lon,lat)):
                        self.assertAlmostEqual(actual,wanted,delta=1e-8)
            with self.assertRaises(ValueError):projection.forward(0,math.nan)
        fig,ax=azl.subplots(projection=azl.LambertAzimuthalEqualArea(central_longitude=-45,central_latitude=-20))
        ax.map('brazil');ax.set_extent((-76,-33,-35,7));ax.grid()
        self.assertIn('<svg',fig.to_svg())
        self.assertIn('lambert_azimuthal_equal_area',fig.to_html())

    @unittest.skipUnless(shutil.which('node'),'Node optional for portable cursor integration')
    def test_portable_laea_cursor_matches_python_inverse(self):
        root=Path(__file__).resolve().parents[1]
        projection=azl.LambertAzimuthalEqualArea(central_longitude=-45,central_latitude=-20)
        cases=[]
        for lon,lat in ((-45,-20),(-76,-30),(-33,8),(110,40)):
            x,y=projection.forward(lon,lat)
            cases.append(dict(point=dict(x=x,y=-y),expected=projection.inverse(x,y)))
        cases.append(dict(point=dict(x=2*projection.radius,y=0),expected=None))
        script="""
const fs=require('fs'),vm=require('vm');
const source=fs.readFileSync(process.argv[1],'utf8'),input=JSON.parse(fs.readFileSync(0,'utf8'));
const begin=source.indexOf('function coordinate('),end=source.indexOf('function showCoordinate(',begin);
if(begin<0||end<0)throw Error('Missing viewer coordinate implementation');
const context={Math,Number};vm.createContext(context);vm.runInContext(source.slice(begin,end),context);
const state={k:1,tx:0,ty:0,meta:{ox:0,oy:0,scale:1,projection:input.projection}};
console.log(JSON.stringify(input.cases.map(row=>context.coordinate(state,row.point))));
"""
        params=dict(name=projection.name,radius=projection.radius,central_longitude=-45,central_latitude=-20)
        result=subprocess.run(['node','-e',script,str(root/'src/azimlib/assets/viewer.js')],
                              input=json.dumps(dict(projection=params,cases=cases)),
                              text=True,capture_output=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr)
        for actual,row in zip(json.loads(result.stdout),cases):
            if row['expected'] is None:self.assertIsNone(actual)
            else:
                for value,wanted in zip(actual,row['expected']):
                    self.assertAlmostEqual(value,wanted,delta=1e-8)


class DatumOperationsTests(unittest.TestCase):
    def setUp(self):
        self.a = azl.CoordinateFrame('source-realization','geocentric')
        self.b = azl.CoordinateFrame('target-realization','geocentric')

    def test_published_helmert_numeric_example(self):
        # Numeric facts, IOGP GN7-2 September 2019 printed p108. No prose/code copied.
        # https://www.iogp.org/wp-content/uploads/2019/09/373-07-02.pdf
        operation = azl.Helmert(self.a,self.b,(0,0,4.5,0,0,.554,.219),'position_vector')
        point = (3657660.66,255768.55,5201382.11)
        result = operation.transform(*point)
        for actual,expected in zip(result,(3657660.78,255778.43,5201387.75)):
            self.assertAlmostEqual(actual,expected,delta=.01)
        for actual,expected in zip(operation.inverse().transform(*result),point):
            self.assertAlmostEqual(actual,expected,delta=1e-8)
        self.assertIs(operation.inverse().inverse(),operation)

    def test_sign_convention_translation_scale_and_exact_inverse(self):
        pv = azl.Helmert(self.a,self.b,(1,2,3,4,5,6,7),'position_vector')
        cf = azl.Helmert(self.a,self.b,(1,2,3,-4,-5,-6,7),'coordinate_frame')
        self.assertEqual(pv.transform(1,2,3),cf.transform(1,2,3))
        scale = azl.Helmert(self.a,self.b,(1,2,3,0,0,0,1000),'position_vector')
        for actual,expected in zip(scale.transform(1000,2000,3000),(1002,2004,3006)):
            self.assertAlmostEqual(actual,expected,delta=1e-10)
        for point in ((1,2,3),(6378137,0,0),(-4e6,3e6,-5e6)):
            for actual,expected in zip(pv.inverse().transform(*pv.transform(*point)),point):
                self.assertAlmostEqual(actual,expected,delta=1e-8)

    def test_dynamic_rates_epoch_and_validity(self):
        operation = azl.Helmert(self.a,self.b,(1,2,3,0,0,0,0),'position_vector',
                                rates=(.1,.2,.3,0,0,0,0),reference_epoch=2000,
                                valid_epochs=(1990,2010))
        self.assertEqual(operation.transform(0,0,0,epoch=2010),(2,4,6))
        self.assertEqual(operation.inverse().transform(2,4,6,epoch=2010),(0,0,0))
        for epoch in (None,1989,2011,math.nan,True):
            with self.assertRaises(ValueError):
                operation.transform(0,0,0,epoch=epoch)

    def test_invalid_parameters_frames_and_unavailable_operations(self):
        base = dict(source=self.a,target=self.b,parameters=(0,)*7,convention='position_vector')
        for update in ({'convention':'unknown'},{'parameters':(0,)*6},{'parameters':(0,)*6+(math.nan,)},
                       {'target':self.a},{'rates':(0,)*7},{'reference_epoch':2000},
                       {'valid_epochs':(2010,2000)},{'area_of_use':(-190,0,0,10)},
                       {'parameters':(0,0,0,3601,0,0,0)},
                       {'source':azl.CoordinateFrame('geo','geographic')}):
            with self.subTest(update=update),self.assertRaises((ValueError,TypeError)):
                azl.Helmert(**dict(base,**update))
        with self.assertRaises(ValueError):
            azl.GeodeticConversion(self.a,self.b)

    def test_area_dateline_and_inverse_checks_source_area(self):
        operation = azl.Helmert(self.a,self.b,(1,2,3,0,0,0,0),'position_vector',
                                area_of_use=(170,-10,-170,10))
        forward = azl.Transformer(4979,4978)
        for lon in (-175,175):
            xyz = forward.transform(lon,0,0)
            for actual,expected in zip(operation.inverse().transform(*operation.transform(*xyz)),xyz):
                self.assertAlmostEqual(actual,expected,delta=1e-8)
        for lon,lat in ((0,0),(175,20)):
            xyz = forward.transform(lon,lat,0)
            with self.assertRaises(ValueError):
                operation.transform(*xyz)
            with self.assertRaises(ValueError):
                operation.inverse().transform(*(v+t for v,t in zip(xyz,(1,2,3))))

    def test_geodetic_pipeline_prime_meridian_and_datum_identity(self):
        datum = azl.Datum('synthetic local',azl.GRS80,2)
        geo = azl.CoordinateFrame('local-realization','geographic',datum)
        xyz = azl.CoordinateFrame('local-realization','geocentric',datum)
        target_geo = azl.CoordinateFrame('target-realization','geographic')
        shift = azl.Helmert(xyz,self.b,(0,0,0,0,0,0,0),'position_vector')
        pipeline = azl.CoordinatePipeline((azl.GeodeticConversion(geo,xyz),shift,
                                           azl.GeodeticConversion(self.b,target_geo)))
        result = pipeline.transform(-2,0,100)
        for actual,expected in zip(result,(0,0,100)):
            self.assertAlmostEqual(actual,expected,delta=1e-8)
        for actual,expected in zip(pipeline.inverse().transform(*result),(-2,0,100)):
            self.assertAlmostEqual(actual,expected,delta=1e-8)
        with self.assertRaises(ValueError):
            azl.GeodeticConversion(geo,self.b)
        with self.assertRaises(ValueError):
            azl.GeodeticConversion(geo,azl.CoordinateFrame('another-realization','geocentric',datum))
        with self.assertRaises(ValueError):
            azl.GeodeticConversion(geo,xyz).transform(181,0,0)

    def test_dynamic_pipeline_passes_same_epoch_to_every_step(self):
        c = azl.CoordinateFrame('third-realization','geocentric')
        first = azl.Helmert(self.a,self.b,(0,)*7,'position_vector',rates=(1,0,0,0,0,0,0),
                            reference_epoch=2000,valid_epochs=(2000,2001))
        second = azl.Helmert(self.b,c,(0,)*7,'position_vector',rates=(0,1,0,0,0,0,0),
                             reference_epoch=2000,valid_epochs=(2000,2001))
        pipeline = azl.CoordinatePipeline((first,second))
        self.assertEqual(pipeline.transform(0,0,0,epoch=2001),(1,1,0))
        self.assertEqual(pipeline.inverse().transform(1,1,0,epoch=2001),(0,0,0))
        with self.assertRaises(ValueError):
            pipeline.transform(0,0,0)


if __name__ == '__main__':
    unittest.main()

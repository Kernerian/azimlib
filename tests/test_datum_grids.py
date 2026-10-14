"""Independent synthetic format fixtures and explicit datum-grid contracts."""
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import azimlib as azl

ROOT = Path(__file__).resolve().parents[1]


def gtx(values=((0.,2.),(4.,8.)), origin=(0.,0.), step=(1.,1.)):
    rows,cols = len(values),len(values[0])
    return struct.pack('>4d2i',origin[1],origin[0],step[1],step[0],rows,cols)+struct.pack('>'+'f'*(rows*cols),*(v for row in values for v in row))


def ntv2(tiles=None, endian='<'):
    # Entirely synthetic values and geometry; no external grid data vendored.
    if tiles is None: tiles = [('ROOT','NONE',0.,0.,1.,2,2,[(36.,-72.,.1,.2)]*4)]
    def record(key,value):
        packed = struct.pack(endian+'i',value)+b'\0'*4 if isinstance(value,int) else struct.pack(endian+'d',value) if isinstance(value,float) else value.encode().ljust(8)
        return key.encode().ljust(8)+packed
    pairs = [('NUM_OREC',11),('NUM_SREC',11),('NUM_FILE',len(tiles)),('GS_TYPE','SECONDS'),('VERSION','SYNTH'),('SYSTEM_F','SOURCE'),('SYSTEM_T','TARGET'),('MAJOR_F',6378137.),('MINOR_F',azl.WGS84.semi_minor_axis),('MAJOR_T',6378137.),('MINOR_T',azl.WGS84.semi_minor_axis)]
    result = b''.join(record(*p) for p in pairs)
    for name,parent,west,south,step,rows,cols,values in tiles:
        pairs = [('SUB_NAME',name),('PARENT',parent),('CREATED','20260101'),('UPDATED','20260101'),('S_LAT',south*3600),('N_LAT',(south+(rows-1)*step)*3600),('E_LONG',-(west+(cols-1)*step)*3600),('W_LONG',-west*3600),('LAT_INC',step*3600),('LONG_INC',step*3600),('GS_COUNT',rows*cols)]
        result += b''.join(record(*p) for p in pairs)
        result += b''.join(struct.pack(endian+'4f',*node) for node in values)
    return result+record('END',0.)


def frames():
    return azl.CoordinateFrame('source','geographic'), azl.CoordinateFrame('target','geographic')


def vertical(values=((10.,20.),(30.,40.)), **kwargs):
    a = azl.CoordinateFrame('horizontal','geographic')
    b = replace(a,height_reference='synthetic gravity-related')
    return azl.GridOperation(a,b,azl.read_gtx(gtx(values)), 'vertical',factor=-1,**kwargs)


class GridReaderTests(unittest.TestCase):
    def test_path_read_does_not_allocate_configured_byte_ceiling(self):
        import tracemalloc
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/'small.gtx';file.write_bytes(gtx())
            tracemalloc.start()
            try:
                grid=azl.read_gtx(file,max_bytes=128*1024*1024)
                self.assertLess(tracemalloc.get_traced_memory()[1],4*1024*1024)
            finally:tracemalloc.stop()
            self.assertEqual(grid.sample(.5,.5),(3.5,))
        with self.assertRaises(ValueError):azl.read_gtx(gtx(),nodata=(1e100,))

    def test_gtx_analytic_nodes_bilinear_edges(self):
        grid = azl.read_gtx(gtx())
        for x,y,expected in [(0,0,0),(1,0,2),(0,1,4),(1,1,8),(.5,.5,3.5),(1,.5,5),(.25,.75,3.875)]:
            with self.subTest(x=x,y=y): self.assertEqual(grid.sample(x,y),(expected,))
        self.assertEqual(grid.units,'metres')
        self.assertEqual(grid.sha256,hashlib.sha256(gtx()).hexdigest())
        with self.assertRaises(ValueError): grid.accuracy(0,0)

    def test_gtx_primary_noaa_format_numeric_facts_and_sentinel(self):
        # NOAA's published example: origin 42.25N,276.75E; 0.05/0.025 deg;
        # first node 0.88880 m, next node -88.88880 (missing).
        # Numeric facts only, https://www.vdatum.noaa.gov/docs/gtx_info.html
        grid = azl.read_gtx(gtx(((.8888,-88.8888),(1.,2.)),(276.75,42.25),(.025,.05)))
        self.assertAlmostEqual(grid.sample(-83.25,42.25)[0],.8888,places=7)
        for x,y in [(-83.225,42.25),(-83.24,42.26)]:
            with self.assertRaises(azl.GridNoDataError): grid.sample(x,y)

    def test_gtx_nodata_positive_weights_and_nonfinite(self):
        for invalid in (-9999.,float('nan'),float('inf')):
            grid = azl.read_gtx(gtx(((1.,invalid),(3.,5.))),nodata=(-9999.,))
            self.assertEqual(grid.sample(0,0),(1.,))
            self.assertEqual(grid.sample(0,.5),(2.,))
            with self.assertRaises(azl.GridNoDataError): grid.sample(.5,.5)
        grid = azl.read_gtx(gtx(((-88.8888,2.),(3.,4.))),nodata=())
        self.assertLess(grid.sample(0,0)[0],-88)

    def test_gtx_invalid_sizes_geometry_and_budgets(self):
        raw = gtx()
        for broken in (raw[:39],raw[:-1],raw+b'x',struct.pack('>4d2i',0,0,0,1,2,2)+raw[40:],struct.pack('>4d2i',float('nan'),0,1,1,2,2)+raw[40:],struct.pack('>4d2i',90,0,1,1,2,2)+raw[40:],struct.pack('<4d2i',0,0,1,1,2,2)+raw[40:]):
            with self.subTest(broken=broken[:8]), self.assertRaises(ValueError): azl.read_gtx(broken)
        for kwargs in ({'max_bytes':len(raw)-1},{'max_nodes':3},{'max_bytes':True},{'max_nodes':0}):
            with self.assertRaises(ValueError): azl.read_gtx(raw,**kwargs)

    def test_canonical_domains_seam_and_no_extrapolation(self):
        grid = azl.read_gtx(gtx(origin=(179.,0.)))
        self.assertEqual(grid.sample(-180,1),(8.,))
        for x,y in [(181,0),(178.999,0),(179,-.001),(179,1.001),(179,91),(float('nan'),0),(True,0)]:
            with self.subTest(x=x,y=y),self.assertRaises(ValueError): grid.sample(x,y)

    def test_ntv2_either_endian_sign_precision_accuracy(self):
        for endian in ('<','>'):
            with self.subTest(endian=endian):
                grid = azl.read_ntv2(ntv2(endian=endian))
                self.assertEqual(grid.sample(.5,.5),(72.,36.))
                self.assertEqual(grid.units,'arcseconds')
                self.assertAlmostEqual(grid.accuracy(.2,.8)[0],.2,places=7)
                self.assertAlmostEqual(grid.accuracy(.2,.8)[1],.1,places=7)
                with self.assertRaises(TypeError): grid.metadata['VERSION']='changed'
                with self.assertRaises(Exception): grid.tiles[0].rows=99

    def test_ntv2_reversed_longitude_node_order(self):
        tile = ('ROOT','NONE',0.,0.,1.,2,2,[(0.,-2.,0.,0.),(0.,-4.,0.,0.),(0.,-6.,0.,0.),(0.,-8.,0.,0.)])
        grid = azl.read_ntv2(ntv2([tile]))
        self.assertEqual(grid.sample(1,0),(2.,0.))
        self.assertEqual(grid.sample(0,1),(8.,0.))
        self.assertEqual(grid.sample(.5,.5),(5.,0.))

    def test_ntv2_nested_finest_no_parent_fallback_and_edges(self):
        root = ('ROOT','NONE',0.,0.,1.,3,3,[(1.,1.,.1,.1)]*9)
        child = ('CHILD','ROOT',.5,.5,.5,2,2,[(2.,2.,.2,.2)]*4)
        for tiles in ([root,child],[child,root]):
            grid = azl.read_ntv2(ntv2(tiles))
            self.assertEqual(grid.sample(.75,.75),(-2.,2.))
            self.assertEqual(grid.sample(.25,.25),(-1.,1.))
            self.assertEqual(grid.sample(1,1),(-2.,2.))
        missing = (*child[:-1],[(float('nan'),2.,.2,.2)]*4)
        with self.assertRaises(azl.GridNoDataError): azl.read_ntv2(ntv2([root,missing])).sample(.75,.75)
        self.assertEqual(azl.read_ntv2(ntv2([root,child])).sample(1.00001,1.00001),(-1.,1.))

    def test_ntv2_invalid_hierarchy_and_overlap(self):
        root = ('ROOT','NONE',0.,0.,1.,3,3,[(1.,1.,.1,.1)]*9)
        children = [('CHILD','MISSING',.5,.5,.5,2,2,[(2.,2.,.2,.2)]*4),('ROOT','ROOT',.5,.5,.5,2,2,[(2.,2.,.2,.2)]*4),('CHILD','ROOT',2.,2.,.5,2,2,[(2.,2.,.2,.2)]*4)]
        for child in children:
            with self.assertRaises(ValueError): azl.read_ntv2(ntv2([root,child]))
        child = ('CHILD','ROOT',.5,.5,.5,2,2,[(2.,2.,.2,.2)]*4)
        with self.assertRaises(ValueError): azl.read_ntv2(ntv2([root,child,('OTHER',*child[1:])]))
        with self.assertRaises(ValueError): azl.read_ntv2(ntv2([root,('SIBLING','NONE',1.,1.,1.,2,2,[(1.,1.,0.,0.)]*4)]))
        cycle = [('A','B',0.,0.,1.,2,2,[(1.,1.,0.,0.)]*4),('B','A',0.,0.,1.,2,2,[(1.,1.,0.,0.)]*4)]
        with self.assertRaises(ValueError): azl.read_ntv2(ntv2(cycle))

    def test_ntv2_malformed_headers_records_and_limits(self):
        raw = ntv2()
        for broken in (raw[:175],raw[:-17],raw+b'x',raw.replace(b'SECONDS ',b'DEGREES '),raw.replace(b'NUM_SREC',b'BAD_KEY '),raw[:12]+b'xx\0\0'+raw[16:]):
            with self.assertRaises(ValueError): azl.read_ntv2(broken)
        for kwargs in ({'max_nodes':3},{'max_bytes':10},{'max_tiles':0}):
            with self.assertRaises(ValueError): azl.read_ntv2(raw,**kwargs)
        # END's value is unused padding; real publisher files need not zero it.
        self.assertEqual(azl.read_ntv2(raw[:-8]+b'12345678').sample(0,0),(72.,36.))

    def test_sibling_edge_discontinuity_is_deterministic(self):
        tiles=[('Z','NONE',0.,0.,1.,2,2,[(1.,1.,0.,0.)]*4),
               ('A','NONE',1.,0.,1.,2,2,[(2.,2.,0.,0.)]*4)]
        for order in (tiles,tiles[::-1]):
            grid=azl.read_ntv2(ntv2(order))
            self.assertEqual(grid.sample(1,.5),(-2.,2.))
            self.assertEqual(grid.sample(.99999,.5),(-1.,1.))

    def test_nonintegral_or_overflowing_grid_geometry_fails(self):
        raw=ntv2()
        for increment in (3601.,1e-300,float('inf')):
            broken=raw.replace(b'LAT_INC '+struct.pack('<d',3600.),b'LAT_INC '+struct.pack('<d',increment))
            with self.assertRaises(ValueError):azl.read_ntv2(broken)


class GridOperationTests(unittest.TestCase):
    def test_inverse_ambiguity_nodata_and_divergence_fail_closed(self):
        tiles=[('A','NONE',0.,0.,1.,2,2,[(0.,0.,0.,0.)]*4),
               ('B','NONE',2.,0.,1.,2,2,[(0.,7200.,0.,0.)]*4)]
        op=azl.GridOperation(*frames(),azl.read_ntv2(ntv2(tiles)),'horizontal')
        with self.assertRaisesRegex(ValueError,'Ambiguous'):op.inverse().transform(.5,.5,0)
        tiles=[('A','NONE',0.,0.,1.,2,2,[(float('nan'),0.,0.,0.)]*4)]
        op=azl.GridOperation(*frames(),azl.read_ntv2(ntv2(tiles)),'horizontal')
        with self.assertRaises(azl.GridNoDataError):op.inverse().transform(.5,.5,0)
        # dlon = 2*x degrees produces divergent fixed-point iterations. It must
        # report non-convergence, never return the last iterate as a coordinate.
        nodes=[(0.,-7200.,0.,0.),(0.,0.,0.,0.)]*2
        op=azl.GridOperation(*frames(),azl.read_ntv2(ntv2([('A','NONE',0.,0.,1.,2,2,nodes)])),'horizontal')
        with self.assertRaises(azl.GridCoverageError):op.inverse().transform(.5,.5,0)

    def test_selection_coverage_and_missing_never_falls_back(self):
        first=vertical();other=replace(first,grid=azl.read_gtx(gtx(((1.,1.),(1.,1.)),origin=(2.,0.))))
        selected=azl.OperationSet({'west':first,'east':other}).select(first.source,first.target,.5,.5,100)
        self.assertEqual(selected.transform(.5,.5,100)[2],75)
        missing=replace(first,grid=azl.read_gtx(gtx(((float('nan'),1.),(1.,1.)))))
        with self.assertRaises(ValueError):azl.OperationSet({'missing':missing,'valid':first}).select(first.source,first.target,.5,.5,100)
        with self.assertRaises(ValueError):azl.OperationSet([('duplicate',first),('duplicate',other)])

    def test_horizontal_forward_inverse_shifted_boundaries(self):
        op = azl.GridOperation(*frames(),azl.read_ntv2(ntv2()),'horizontal')
        for point in [(0,0,15),(1,1,-3),(.5,.5,0),(1,0,1),(0,1,1)]:
            with self.subTest(point=point):
                shifted = op.transform(*point)
                self.assertAlmostEqual(shifted[0],point[0]+.02,places=12)
                self.assertAlmostEqual(shifted[1],point[1]+.01,places=12)
                for x,y in zip(op.inverse().transform(*shifted),point): self.assertAlmostEqual(x,y,places=10)
        self.assertIs(op.inverse().inverse(),op)
        with self.assertRaises(azl.GridCoverageError): op.inverse().transform(20,20,0)

    def test_nonconstant_horizontal_inverse_and_pipeline(self):
        nodes = [(10.,-8.,0.,0.),(12.,-4.,0.,0.),(14.,-6.,0.,0.),(16.,-2.,0.,0.)]
        raw = ntv2([('ROOT','NONE',0.,0.,1.,2,2,nodes)])
        op = azl.GridOperation(*frames(),azl.read_ntv2(raw),'horizontal')
        for i in range(1,10):
            point = i/10,(10-i)/10,123
            back = azl.CoordinatePipeline((op,op.inverse())).transform(*point,epoch=2000)
            for a,b in zip(point,back): self.assertAlmostEqual(a,b,places=10)

    def test_vertical_height_references_geocentric_guard(self):
        op = vertical()
        self.assertEqual(op.transform(.5,.5,100),(.5,.5,75))
        self.assertEqual(op.inverse().transform(.5,.5,75),(.5,.5,100))
        with self.assertRaises(ValueError): azl.GeodeticConversion(op.target,replace(op.source,kind='geocentric'))
        with self.assertRaises(ValueError): replace(op.target,kind='geocentric')
        with self.assertRaises(ValueError): replace(op,target=replace(op.target,name='other horizontal'))
        with self.assertRaises(ValueError): replace(op,factor=.5)

    def test_models_epochs_and_exact_identity_selection(self):
        op = vertical(valid_epochs=(2000,2030))
        for epoch in (None,1999,2031,True,float('nan')):
            with self.assertRaises(ValueError): op.transform(.5,.5,100,epoch=epoch)
            with self.assertRaises(ValueError): op.inverse().transform(.5,.5,100,epoch=epoch)
        choices = azl.OperationSet({'reviewed':op,'alternative':replace(op,factor=1)})
        for kwargs in ({},{'epoch':2000},{'epoch':2000,'name':'missing'}):
            with self.assertRaises((ValueError,KeyError)): choices.select(op.source,op.target,.5,.5,100,**kwargs)
        selected = choices.select(op.source,op.target,.5,.5,100,epoch=2000,name='reviewed')
        self.assertEqual(selected.transform(.5,.5,100,epoch=2000)[2],75)
        with self.assertRaises(ValueError): choices.select(replace(op.source,name='other'),op.target,.5,.5,100,epoch=2000,name='reviewed')

    def test_epoch_dependent_chain_with_vertical_model(self):
        vertical_op = vertical(valid_epochs=(2000,2030))
        source_fixed = replace(vertical_op.source,kind='geocentric')
        earlier_fixed = replace(source_fixed,name='earlier realization')
        helmert = azl.Helmert(earlier_fixed,source_fixed,(0,0,0,0,0,0,0),'position_vector',rates=(0,0,.01,0,0,0,0),reference_epoch=2000,valid_epochs=(2000,2030))
        pipeline = azl.CoordinatePipeline((helmert,azl.GeodeticConversion(source_fixed,vertical_op.source),vertical_op))
        xyz = azl.GeodeticConversion(vertical_op.source,source_fixed).transform(.5,.5,100)
        shifted = pipeline.transform(*xyz,epoch=2020)
        restored = pipeline.inverse().transform(*shifted,epoch=2020)
        for a,b in zip(xyz,restored): self.assertAlmostEqual(a,b,places=7)
        with self.assertRaises(ValueError): pipeline.transform(*xyz)
        with self.assertRaises(ValueError): pipeline.transform(*xyz,epoch=2031)

    def test_raster_explicit_height_frame_mask_and_resampling(self):
        op = vertical()
        raster = azl.GeoRaster(((100,None),(200,300)),(.5,0,0,0,.5,0),height_frame=op.source)
        result = op.transform_raster(raster)
        self.assertEqual(result.height_frame,op.target)
        self.assertEqual(result.values,((82.5,None),(172.5,267.5)))
        self.assertEqual(op.inverse().transform_raster(result).values,raster.values)
        self.assertEqual(result.resample((4,4)).height_frame,op.target)
        with self.assertRaises(ValueError): result.resample((4,4),crs=3857,extent=(0,10,0,10))
        with self.assertRaises(ValueError): op.transform_raster(replace(raster,height_frame=None))
        with self.assertRaises(ValueError): op.transform_raster(replace(raster,affine=(.5,0,10,0,.5,10)))
        with self.assertRaises(ValueError): replace(raster,crs=3857)
        with self.assertRaises(ValueError): replace(raster,height_frame=replace(op.source,datum=azl.Datum('other datum',azl.GRS80)))

    def test_raster_viewport_and_exports(self):
        op = vertical();raster = azl.GeoRaster(((100,110),(120,130)),(.5,0,0,0,.5,0),height_frame=op.source)
        fig,ax=azl.subplots(figsize=(3,3),projection='mercator')
        try:
            mesh = ax.raster(op.transform_raster(raster),cmap='viridis')
            ax.set_extent((0,1,0,1));ax.set_title('Synthetic vertical correction')
            fig.colorbar(mesh,ax=ax,label='Height (m)')
            output=io.StringIO();fig.savefig(output,format='svg');self.assertIn('<svg',output.getvalue())
            image=io.BytesIO();fig.savefig(image,format='png');self.assertTrue(image.getvalue().startswith(b'\x89PNG'))
            self.assertEqual(op.transform_raster(raster).height_frame,op.target)
        finally: azl.close(fig)


class GridCatalogTests(unittest.TestCase):
    def catalog(self, folder):
        folder=Path(folder);op=vertical()
        source=dict(name=op.source.name,datum=op.source.datum.name,ellipsoid=dict(name='WGS84',semi_major_axis=6378137.,inverse_flattening=298.257223563),height_reference='ellipsoidal')
        target=dict(source,height_reference=op.target.height_reference)
        raw=gtx(((10.,20.),(30.,40.)));notice=b'Synthetic data, original Azimlib test fixture. BSD-3-Clause.\n'
        (folder/'data.gtx').write_bytes(raw);(folder/'LICENSE.txt').write_bytes(notice)
        entry=dict(id='test',version='1',format='gtx',file='data.gtx',crs=source['name'],license='BSD-3-Clause',copyright='Kernerian',source='synthetic',attribution='Original test fixture',license_file='LICENSE.txt',files={'data.gtx':hashlib.sha256(raw).hexdigest(),'LICENSE.txt':hashlib.sha256(notice).hexdigest()},operation=dict(kind='vertical',source=source,target=target,factor=-1,registration='source-horizontal',units='metres',interpolation='bilinear',accuracy='Synthetic affine surface, exact numeric expectation',reference='Synthetic analytic fixture'))
        (folder/'catalog.json').write_text(json.dumps(dict(schema_version=1,datasets=[entry])),encoding='utf8')
        return folder/'catalog.json',entry

    def test_grid_catalog_integrity_notices_metadata_and_detachment(self):
        with tempfile.TemporaryDirectory() as folder:
            path,entry=self.catalog(folder);catalog=azl.DatasetCatalog(path)
            self.assertEqual(catalog.grid_operation('test').transform(.5,.5,100)[2],75)
            self.assertEqual(catalog.verify()['files_verified'],2)
            catalog.available()[0]['operation']['factor']=1
            self.assertEqual(catalog.grid_operation('test').factor,-1)
            (path.parent/'LICENSE.txt').write_text('changed')
            with self.assertRaises(ValueError): catalog.grid_operation('test')

    def test_catalog_missing_data_or_model_never_approximates(self):
        with tempfile.TemporaryDirectory() as folder:
            path,entry=self.catalog(folder)
            for key,value in [('units','feet'),('registration','target-horizontal'),('interpolation','nearest'),('accuracy','')]:
                broken=json.loads(json.dumps(entry));broken['operation'][key]=value
                path.write_text(json.dumps(dict(schema_version=1,datasets=[broken])))
                with self.assertRaises(ValueError): azl.DatasetCatalog(path).grid_operation('test')
            path.write_text(json.dumps(dict(schema_version=1,datasets=[entry])))
            (path.parent/'data.gtx').unlink()
            with self.assertRaises(FileNotFoundError): azl.DatasetCatalog(path).grid_operation('test')

    def test_pinned_official_models_and_licenses(self):
        presets=json.loads((ROOT/'src/azimlib/data/optional-grids.json').read_text('utf8'))
        self.assertEqual(presets,json.loads((ROOT/'docs/grid-models-0.4.json').read_text('utf8')))
        self.assertEqual(presets['upstream_version'],'20200110')
        for entry in presets['datasets']:
            self.assertEqual(entry['license'],'CC-BY-4.0')
            self.assertEqual(hashlib.sha256((ROOT/'licenses/CC-BY-4.0.txt').read_bytes()).hexdigest(),entry['files']['CC-BY-4.0.txt'])
            self.assertIn(entry['upstream_commit'],entry['source'])
            self.assertIn('Land Information New Zealand',entry['attribution'])
            self.assertFalse((ROOT/'src/azimlib/data'/entry['file']).exists())

    def test_acquisition_budgets_and_no_clobber(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('acquire_datum_grid',ROOT/'tools/acquire_datum_grid.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as folder:
            for kwargs in ({'max_bytes':1},{'max_storage_bytes':1},{'reserve_free_bytes':True}):
                with self.assertRaises(ValueError): module.acquire('linz-nzgeoid2016',Path(folder)/'new',**kwargs)
                self.assertFalse((Path(folder)/'new').exists())
            with self.assertRaises(ValueError): module.acquire('linz-nzgeoid2016',folder)
            with patch.object(module,'urlopen',side_effect=RuntimeError('synthetic network failure')):
                with self.assertRaises(RuntimeError): module.acquire('linz-nzgd1949-nzgd2000',Path(folder)/'new',reserve_free_bytes=0)
            self.assertEqual(list(Path(folder).iterdir()),[])


if __name__ == '__main__': unittest.main()

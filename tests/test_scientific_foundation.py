"""Own analytical fixtures for scientific 2D kernels and linked Artists."""
import io
import math
import random
import unittest
import azimlib as azl
from azimlib.colors import Normalize,BoundaryNorm,ListedColormap
from azimlib.scientific import area,histogram
from azimlib.legend_handler import HandlerSymbol
from azimlib.transforms import Affine2D


class ScientificFoundationTests(unittest.TestCase):
    def tearDown(self):azl.close('all');azl.ioff()
    def axes(self):return azl.subplots(figsize=(5,4))

    def test_symbol_fits_handle_uniformly_and_centers_nonunit_path(self):
        symbol=azl.Symbol(azl.Path([(2,3),(3,5),(4,3),(2,3)], [1,2,2,79]))
        for dpi in (72,100,200):
            for width,height in ((30,10),(8,24),(12,12)):
                with self.subTest(dpi=dpi,size=(width,height)):
                    patch=HandlerSymbol().create_artists(None,symbol,2,3,width,height,10,Affine2D().scale(dpi/100)) [0]
                    points=patch.get_transform().transform(symbol.path.vertices)
                    ratio=(points[2][0]-points[0][0])/(points[1][1]-points[0][1])
                    self.assertAlmostEqual(ratio,1)
                    self.assertAlmostEqual((min(p[0] for p in points)+max(p[0] for p in points))/2,(-2+width/2)*dpi/100)
                    self.assertAlmostEqual((min(p[1] for p in points)+max(p[1] for p in points))/2,(-3+height/2)*dpi/100)
                    self.assertIsNone(patch.axes)
        self.assertEqual(symbol.path.vertices[0],(2.,3.))
        with self.assertRaises(ValueError):HandlerSymbol().create_artists(None,azl.Symbol(azl.Path([])),0,0,10,10,10,Affine2D())

    def test_color_image_origin_editing_and_no_scalar_colorbar(self):
        fig,ax=self.axes();pixels=[[(255,0,0),(0,255,0)],[(0,0,255),(0,0,0)]]
        image=ax.imshow(pixels,extent=(0,2,0,2),origin='upper')
        self.assertIsInstance(image,azl.ColorImage);self.assertEqual(image.get_data()[0][0],(1.,0.,0.,1.))
        self.assertEqual(image.get_extent(),(0.,2.,0.,2.));before=ax.get_extent()
        image.set(data=[[(1.,.5,0.,.25)]],extent=(0,4,0,1),alpha=.6)
        self.assertEqual(image.get_data(),[[(1.,.5,0.,.25)]]);self.assertEqual(ax.get_extent(),before)
        svg=fig.to_svg();self.assertIn('#ff800040',svg)
        with self.assertRaises(ValueError):fig.colorbar(image)
        with self.assertRaises(ValueError):image.set_norm(Normalize(0,1))

    def test_bad_color_image_edits_are_atomic(self):
        fig,ax=self.axes();image=ax.imshow([[(1.,0.,0.)]],extent=(0,1,0,1))
        before=(image.get_data(),image.get_extent(),dict(image.style))
        for edit in (dict(data=[]),dict(data=[[(300,0,0)]]),dict(data=[[(2.,0.,0.)]]),dict(data=[[(1,2)]]),dict(data=[[(1.,0.,0.)]],linewidth=-1),dict(extent=(2,1,0,1)),dict(norm=Normalize())):
            with self.subTest(edit=edit):
                with self.assertRaises((ValueError,TypeError)):image.set(**edit)
                self.assertEqual((image.get_data(),image.get_extent(),dict(image.style)),before)
        count=len(ax.layers)
        with self.assertRaises(ValueError):ax.imshow([[(255,0,0)]],extent=(0,1,0,1),norm=Normalize())
        self.assertEqual(len(ax.layers),count)

    def test_raster_scalar_mask_and_rgba_mask_are_immutable(self):
        scalar=azl.GeoRaster([[1,2],[3,-999]],(1,0,0,0,1,0),nodata=-999,mask=[[0,1],[0,0]])
        self.assertEqual(scalar.values,((1.,None),(3.,None)));self.assertEqual(scalar.mask,((False,True),(False,True)))
        color=azl.GeoRaster([[(255,0,0,255),None]],(1,0,0,0,1,0),color_mode='rgba')
        self.assertEqual(color.mask,((False,True),));self.assertEqual(color.sample(1.5,.5),(0.,0.,0.,0.))
        with self.assertRaises(ValueError):azl.GeoRaster([[(255,0,0)]],(1,0,0,0,1,0),nodata=0)
        with self.assertRaises(ValueError):azl.GeoRaster([[1]],(1,0,0,0,1,0),mask=[[0,1]])

    def test_nearest_identity_and_inverse_rotated_affine(self):
        for affine in ((2,0,10,0,-3,20),(2,.2,10,.5,3,20)):
            r=azl.GeoRaster([[1,2],[3,4]],affine)
            for method in ('nearest','bilinear'):
                for row,expected in zip(r.resample((2,2),method=method).values,r.values):
                    for actual,value in zip(row,expected):self.assertAlmostEqual(actual,value)
            for j in range(2):
                for i in range(2):self.assertEqual(r.sample(*r.coordinate(i,j,center=True)),r.values[j][i])
        for shape in ((0,2),(2,False),(1,),(10000,10000)):
            with self.assertRaises(ValueError):r.resample(shape)

    def test_bilinear_exact_affine_field_interior_and_coverage(self):
        r=azl.GeoRaster([[1,3,5],[4,6,8],[7,9,11]],(1,0,0,0,1,0))
        for x in (.5,.8,1.,1.5,2.5):
            for y in (.5,1.2,1.5,2.,2.5):self.assertAlmostEqual(r.sample(x,y,method='bilinear'),2*x+3*y-1.5)
        self.assertIsNone(r.sample(-.01,.5));self.assertIsNone(r.sample(3,.5))
        output=r.resample((2,2),extent=(4,6,0,2))
        self.assertTrue(all(all(row) for row in output.mask))
        with self.assertRaises(ValueError):r.resample((2,2),crs=3857)
        with self.assertRaises(ValueError):r.sample(.5,.5,method='cubic')

    def test_bilinear_nodata_strict_and_renormalized(self):
        r=azl.GeoRaster([[2,None],[6,10]],(1,0,0,0,1,0))
        self.assertIsNone(r.sample(1,1,method='bilinear'))
        self.assertEqual(r.sample(1,1,method='bilinear',missing='renormalize'),6)
        self.assertEqual(r.sample(.5,.5,method='bilinear'),2)
        self.assertIsNone(r.sample(-1,1,method='bilinear',missing='renormalize'))

    def test_premultiplied_color_interpolation_has_no_invisible_red_bleed(self):
        r=azl.GeoRaster([[(255,0,0,0),(0,0,255,255)]],(1,0,0,0,1,0))
        self.assertEqual(r.sample(1,.5,method='bilinear'),(0.,0.,1.,.5))
        self.assertEqual(r.resample((1,3),method='bilinear').values[0][1],(0.,0.,1.,.5))

    def test_explicit_crs_destination_sample_matches_own_transform(self):
        r=azl.GeoRaster([[1,2],[3,4]],(1,0,-2,0,1,-2))
        x,y=azl.transform(-1.5,-1.5,4326,3857)
        self.assertEqual(r.sample(x,y,crs=3857),1)
        w,s=azl.transform(-2,-2,4326,3857);e,n=azl.transform(0,0,4326,3857)
        out=r.resample((2,2),extent=(w,e,s,n),crs=3857)
        self.assertEqual(out.values,((3.,4.),(1.,2.)))

    def test_rgb_png_and_geotiff_codecs_keep_alpha(self):
        try:from PIL import Image,TiffImagePlugin
        except ImportError:self.skipTest('Pillow optional')
        stream=io.BytesIO();Image.new('RGBA',(2,1),(20,80,160,128)).save(stream,format='PNG')
        r=azl.read_raster(stream.getvalue(),crs=4326,extent=(0,2,0,1))
        self.assertEqual(r.values[0][0],(20/255,80/255,160/255,128/255))
        info=TiffImagePlugin.ImageFileDirectory_v2();info[34264]=(1.,0.,0.,0.,0.,-1.,0.,1.,0.,0.,1.,0.,0.,0.,0.,1.);info.tagtype[34264]=12
        stream=io.BytesIO();Image.new('RGBA',(2,1),(20,80,160,128)).save(stream,format='TIFF',tiffinfo=info)
        geo=azl.read_geotiff(stream.getvalue(),crs=4326)
        self.assertEqual(geo.values,r.values)
        fig,ax=self.axes();image=ax.raster(geo);self.assertIsInstance(image,azl.ColorImage)

    def test_scalar_bad_color_is_rendered_and_default_missing_is_omitted(self):
        fig,ax=self.axes();mesh=ax.pcolormesh([0,1,2],[0,1],[[None,1]])
        self.assertNotIn('#ff00ff',fig.to_svg());cmap=azl.colors.get_cmap('viridis');cmap.set_bad('#ff00ff');mesh.set_cmap(cmap)
        self.assertIn('#ff00ff',fig.to_svg())

    def test_contourf_analytic_linear_bands_partition_area(self):
        fig,ax=self.axes();bands=ax.contourf([0,1,2],[0,1,2],[[0,1,2]]*3,levels=[0,1,2])
        self.assertIsInstance(bands,azl.FilledContourSet);self.assertEqual(bands.cvalues,[.5,1.5])
        totals=[0,0]
        for feature in bands.data:totals[feature.properties['band']]+=sum(area(list(r)) for r in feature.geometry.coordinates)
        self.assertEqual(totals,[2.,2.]);bar=fig.colorbar(bands);self.assertEqual(bar.boundaries,(0.,1.,2.))
        self.assertEqual(list(bar.get_ticks()),[0,1,2]);self.assertIn('<svg',fig.to_svg())

    def test_contourf_nodata_is_actual_inner_ring(self):
        fig,ax=self.axes();z=[[1]*5 for _ in range(5)];z[2][2]=None
        bands=ax.contourf(range(5),range(5),z,levels=[0,2])
        self.assertEqual(len(bands.data),1);rings=bands.data[0].geometry.coordinates
        self.assertEqual(len(rings),2);self.assertGreater(area(list(rings[0])),0);self.assertLess(area(list(rings[1])),0)
        self.assertEqual(sum(area(list(r)) for r in rings),12)

    def test_contourf_islands_plateaus_and_upper_endpoint(self):
        fig,ax=self.axes();bands=ax.contourf([0,1,2],[0,1],[[2,2,2]]*2,levels=[0,1,2])
        self.assertTrue(all(f.properties['band']==1 for f in bands.data));self.assertEqual(sum(area(list(f.geometry.coordinates[0])) for f in bands.data),2)
        constant=ax.contourf([0,1],[0,1],[[1,1],[1,1]],levels=3)
        self.assertTrue(constant.data)

    def test_filled_explicit_colors_and_linked_legend_recolor(self):
        fig,ax=self.axes();bands=ax.contourf([0,1,2],[0,1],[[0,1,2]]*2,levels=[0,1,2],colors=['red','blue'])
        legend=ax.legend();bar=fig.colorbar(bands,orientation='horizontal');svg=fig.to_svg()
        self.assertIn('red',svg);self.assertIn('blue',svg);self.assertEqual(bar.values,(0.,1.))
        bands.set_cmap(ListedColormap(['#ff00ff','#00ffff']))
        self.assertEqual(bands.get_legend_entries()[0][1]['facecolor'],'#ff00ff');self.assertIn('#00ffff',fig.to_svg())
        with self.assertRaises(ValueError):bands.set_levels([0,.5,1,2])

    def test_filled_level_edits_update_geometry_boundaries_without_invalid_mutation(self):
        fig,ax=self.axes();bands=ax.contourf([0,1,2],[0,1],[[0,1,2]]*2,levels=[0,1,2]);bar=fig.colorbar(bands)
        bands.set_levels([0,.5,1,2]);self.assertEqual(bar.boundaries,(0.,.5,1.,2.));self.assertEqual(len(bands.cvalues),3)
        before=(bands.levels,bands.data,bands.cvalues)
        for bad in ([0,0,1],[1],[],[0,float('inf')]):
            with self.assertRaises(ValueError):bands.set_levels(bad)
            self.assertEqual((bands.levels,bands.data,bands.cvalues),before)
        with self.assertRaises(ValueError):bands.set_array([1])
        bands.set_visible(False);self.assertFalse(bands.get_visible());bands.remove();self.assertNotIn(bands,ax.layers)

    def test_delaunay_analytic_plane_hull_and_determinism(self):
        x=[0,2,2,0,.7];y=[0,0,2,2,.9];z=[2*a+3*b+1 for a,b in zip(x,y)]
        tri=azl.Triangulation(x,y);self.assertEqual(tri.triangles,azl.Triangulation(x,y).triangles)
        total=sum(area([(tri.x[i],tri.y[i]) for i in t]) for t in tri.triangles);self.assertAlmostEqual(total,4)
        interp=azl.LinearTriInterpolator(tri,z)
        for a,b in ((0,0),(.2,.1),(.8,.9),(1.5,1.8),(2,2)):self.assertAlmostEqual(interp(a,b),2*a+3*b+1)
        self.assertIsNone(interp(3,1));self.assertEqual(interp([0,3],[0,1]),[1.,None])

    def test_delaunay_circumcircles_random_cloud(self):
        from azimlib.tri import _incircle
        rng=random.Random(507);x=[rng.uniform(-2,2) for _ in range(30)];y=[rng.uniform(-2,2) for _ in x]
        tri=azl.Triangulation(x,y)
        for t in tri.triangles:
            for i in range(len(x)):
                if i not in t:
                    with self.subTest(triangle=t,node=i):self.assertLessEqual(_incircle(*[(x[k],y[k]) for k in t],(x[i],y[i])),1e-9)

    def test_triangulation_degeneracy_mask_and_irregular_artists(self):
        for x,y in (([0,0,1],[0,0,1]),([0,1,2],[0,0,0]),([0,1,2],[0,math.nan,1]),([-170,170,0],[0,0,2])):
            with self.assertRaises(ValueError):azl.Triangulation(x,y)
        tri=azl.Triangulation([0,1,0],[0,0,1]);interp=azl.LinearTriInterpolator(tri,[0,1,1]);tri.set_mask([True]);self.assertIsNone(interp(.2,.2))
        before=tri.mask
        with self.assertRaises(ValueError):tri.set_mask([True,False])
        self.assertEqual(tri.mask,before);tri.set_mask(None)
        fig,ax=self.axes();a=ax.tripcolor(tri,[0,1,1]);b=ax.tricontourf(tri,[0,1,1],levels=[0,.5,1])
        self.assertAlmostEqual(a.get_array()[0],2/3);self.assertTrue(b.data);self.assertIn('<svg',fig.to_svg())
        self.assertEqual(tri.field([0,None,1]),[])

    def test_histogram_weighted_mass_smoothing_and_normalizations(self):
        for sigma in (0,.5,2,5):
            for normalization in ('count','probability','density'):
                x,y,z=histogram([0,.5,1,3],[0,.5,1,3],weights=[1,2,4,100],bins=(3,4),extent=(0,1,0,1),smoothing=sigma,normalization=normalization)
                mass=sum(map(sum,z));self.assertAlmostEqual(mass*(1/12 if normalization=='density' else 1),7 if normalization=='count' else 1)
        for options in (dict(weights=[-1]),dict(weights=[math.nan]),dict(bins=(1,2)),dict(normalization='km2'),dict(weights=[0],normalization='probability')):
            with self.assertRaises(ValueError):histogram([0],[0],**options)

    def test_heatmap_density_hist2d_return_editable_mappables(self):
        fig,ax=self.axes();h,x,y,m=ax.hist2d([0,.5,1],[0,.5,1],weights=[1,2,3],bins=(2,3),extent=(0,1,0,1))
        self.assertEqual(sum(map(sum,h)),6);self.assertEqual(len(x),3);self.assertEqual(len(y),4)
        density=ax.density([0,1],[0,1],weights=[1,2],bins=(2,3),smoothing=1,normalization='probability')
        self.assertAlmostEqual(sum(density.get_array()),1);bar=fig.colorbar(density);density.set_clim(0,1);self.assertEqual(bar.norm.vmax,1)
        heat=ax.heatmap([[1,None]],extent=(0,1,0,1));self.assertIsInstance(heat,azl.ScalarImage)

    def test_flow_geodesic_mapping_legend_and_atomic_edits(self):
        fig,ax=self.axes();flow=ax.flow([(-60,-5),(-48,-20)],[(-40,-20),(-50,-30)],[10,100],ellipsoid=azl.WGS84,minwidth=.5,maxwidth=4,steps=8)
        self.assertEqual(len(flow.data[0].geometry.coordinates),9);self.assertEqual(flow._feature_style(0,flow.data[0])['linewidth'],.5)
        self.assertEqual(flow._feature_style(1,flow.data[1])['linewidth'],4)
        legend=ax.legend();bar=fig.colorbar(flow);flow.set_array([100,10]);self.assertEqual(flow._feature_style(0,flow.data[0])['linewidth'],4)
        flow.set_clim(0,200);self.assertEqual(flow.get_legend_entries()[-1][0],'200');self.assertEqual(bar.norm.vmax,200)
        before=flow.get_array()
        with self.assertRaises(ValueError):flow.set_array([-1,10])
        self.assertEqual(flow.get_array(),before);self.assertIn('<svg',fig.to_svg())

    def test_flow_invalid_inputs_do_not_attach(self):
        fig,ax=self.axes()
        for args in (([],[],[]),([(0,0)],[(1,1)],[-1]),([(0,0)],[(1,1)],[None])):
            with self.assertRaises(ValueError):ax.flow(*args)
            self.assertFalse(ax.layers)
        with self.assertRaises(ValueError):ax.flow([(0,0)],[(1,1)],[1],minwidth=4,maxwidth=1)

    def test_geographic_vectors_have_thematic_legend_elements(self):
        fig,ax=self.axes();v=ax.quiver([0,1],[0,1],[1,2],[0,0],[10,20],scale=10)
        handles,labels=v.legend_elements();self.assertEqual(labels,['1','1.5','2']);self.assertEqual(len(handles),3)
        ax.legend(handles,labels);self.assertIn('<svg',fig.to_svg())

    def test_hillshade_flat_plane_mask_and_terrain_composition(self):
        from azimlib.fields import hillshade
        flat=hillshade([[1,1],[1,1]],altdeg=30);self.assertAlmostEqual(flat[0][0],.5)
        plane=hillshade([[0,1],[0,1]],dx=1,dy=1,azdeg=270,altdeg=45);self.assertAlmostEqual(plane[0][0],1)
        masked=hillshade([[1,1,1],[1,None,1],[1,1,1]]);self.assertIsNone(masked[1][1])
        fig,ax=self.axes();image,elevation=ax.terrain([[0,1],[2,3]],extent=(0,2,0,2),dx=100,dy=100)
        self.assertIsInstance(image,azl.ColorImage);self.assertEqual(elevation.get_clim(),(0.,3.));fig.colorbar(elevation,label='Elevation')
        ax.contour([.5,1.5],[.5,1.5],[[0,1],[2,3]],levels=[1,2],colors='#444444');ax.line([(0,0),(1,1)],color='#227fa6')
        self.assertIn('Elevation',fig.to_svg());shade=ax.hillshade([[0,1],[2,3]],extent=(0,2,0,2),dx=100,dy=100)
        self.assertEqual(shade.get_clim(),(0.,1.))

    def test_rgba_mapping_masks_bytes_and_shared_norm(self):
        m=azl.cm.ScalarMappable(Normalize(0,2),'gray')
        self.assertEqual(m.to_rgba([0,1,2,None],bytes=True),[(0,0,0,255),(128,128,128,255),(255,255,255,255),(0,0,0,0)])
        self.assertEqual(m.to_rgba([[(255,0,0,128)]],bytes=True),[[(255,0,0,128)]])
        self.assertEqual(m.to_rgba([[0,2],[None,1]])[1][0][-1],0)
        self.assertEqual(m.to_rgba(1,alpha=.3)[-1],.3)
        m.cmap.set_bad('#ff000080');self.assertEqual(m.to_rgba(None)[-1],128/255)

    def test_numpy_masked_scalars_pixels_and_contourf(self):
        try:import numpy as np
        except ImportError:self.skipTest('NumPy optional')
        fig,ax=self.axes();matrix=np.ma.array([[1,2],[3,4]],mask=[[0,1],[0,0]])
        image=ax.imshow(matrix,extent=(0,2,0,2));self.assertIsNone(image.get_data()[0][1])
        r=azl.GeoRaster(matrix,(1,0,0,0,1,0));self.assertIsNone(r.values[0][1])
        pixels=np.ma.array(np.ones((2,2,4)),mask=False);pixels.mask[0,0,0]=True
        color=ax.imshow(pixels,extent=(0,2,0,2));self.assertEqual(color.get_data()[0][0],(0.,0.,0.,0.))
        self.assertEqual(azl.cm.ScalarMappable(Normalize(0,4)).to_rgba(matrix)[0][1][-1],0)

    def test_choropleth_class_color_and_mask_updates_refresh_legend(self):
        collection=azl.FeatureCollection([azl.Feature(azl.Geometry('Polygon',[[[i,0],[i+1,0],[i+1,1],[i,1],[i,0]]])) for i in range(3)])
        fig,ax=self.axes();layer=ax.choropleth(collection,[0,5,10],bins=2);bar=fig.colorbar(layer);ax.legend()
        layer.set_clim(0,20);self.assertTrue(layer.legend_entries[-1][0].endswith('20'))
        layer.set_cmap('sunset');self.assertEqual(layer.legend_entries[0][1]['facecolor'],layer.cmap(.25))
        layer.set_array([None,5,10]);self.assertEqual(layer.legend_entries[-1][0],'Sem dados')
        layer.set_classes(3);self.assertEqual(len(layer.legend_entries),4);self.assertEqual(bar.norm.vmax,20)
        before=dict(layer.options)
        with self.assertRaises(ValueError):layer.set_classes(0)
        self.assertEqual(layer.options,before)
        self.assertIn('Sem dados',fig.to_svg())

    def test_quantile_reclassification_and_boundary_norm_colorbar(self):
        collection=azl.FeatureCollection([azl.Feature(azl.Geometry('Polygon',[[[i,0],[i+1,0],[i+1,1],[i,1],[i,0]]])) for i in range(4)])
        fig,ax=self.axes();layer=ax.choropleth(collection,[1,2,3,100],bins=2,scheme='quantile');bar=fig.colorbar(layer)
        layer.set_array([0,5,50,100]);self.assertEqual(layer.options['color_scale']['edges'],[1.,50.,100.])
        layer.set_norm(BoundaryNorm([0,20,100],2));self.assertEqual(bar.boundaries,(0.,20.,100.))
        with self.assertRaises(ValueError):layer.set_classes(3)
        self.assertIn('<svg',fig.to_svg())

    def test_rgba_export_pixels_match_both_origins_and_alpha(self):
        try:from PIL import Image
        except ImportError:self.skipTest('Pillow optional')
        for origin in ('lower','upper'):
            fig=azl.figure(figsize=(2,2),dpi=100);ax=fig.add_axes((0,0,1,1));ax.set_axis_off()
            ax.imshow([[(255,0,0,255)],[(0,0,255,128)]],extent=(0,1,0,2),origin=origin)
            output=io.BytesIO();fig.savefig(output,format='png')
            with Image.open(output) as image:
                top=image.convert('RGB').getpixel((100,50));bottom=image.convert('RGB').getpixel((100,150))
                expected_top=(255,0,0) if origin=='upper' else (127,127,255)
                expected_bottom=(127,127,255) if origin=='upper' else (255,0,0)
                for actual,expected in ((top,expected_top),(bottom,expected_bottom)):
                    self.assertTrue(all(abs(a-b)<=1 for a,b in zip(actual,expected)),(origin,actual,expected))

    def test_origin_upper_terrain_and_hillshade_keep_geographic_light(self):
        fig,ax=self.axes()
        south_to_north=[[0,0],[1,1]]
        lower=ax.hillshade(south_to_north,extent=(0,2,0,2),dx=1,dy=1,azdeg=180)
        upper=ax.hillshade(south_to_north[::-1],extent=(0,2,0,2),dx=1,dy=1,azdeg=180,origin='upper')
        self.assertEqual(upper.get_data()[::-1],lower.get_data())
        low,m=ax.terrain(south_to_north,extent=(0,2,0,2),dx=1,dy=1,azdeg=180)
        up,n=ax.terrain(south_to_north[::-1],extent=(0,2,0,2),dx=1,dy=1,azdeg=180,origin='upper')
        self.assertEqual(up.get_data()[::-1],low.get_data())

    def test_scalar_image_and_mesh_masked_edits_use_nodata(self):
        try:import numpy as np
        except ImportError:self.skipTest('NumPy optional')
        fig,ax=self.axes();mesh=ax.pcolormesh([0,1,2],[0,1],[[1,2]])
        mesh.set_array(np.ma.array([3,4],mask=[0,1]));self.assertEqual(mesh.get_array(),[3.,None])
        mapper=azl.cm.ScalarMappable();mapper.set_array(np.ma.array([3,4],mask=[0,1]));self.assertEqual(mapper.get_array(),[3.,None])

    def test_filled_union_partition_random_nodes_and_saddle_boundaries(self):
        rng=random.Random(533)
        fig,ax=self.axes()
        for case in range(12):
            z=[[rng.uniform(-2,2) for _ in range(4)] for _ in range(4)]
            bands=ax.contourf(range(4),range(4),z,levels=[-3,-1,0,1,3])
            total=sum(sum(area(list(r)) for r in f.geometry.coordinates) for f in bands.data)
            self.assertAlmostEqual(total,9,places=9);bands.remove()
        plateau=ax.contourf(range(3),range(3),[[0,1,0],[1,1,1],[0,1,0]],levels=[0,1,2])
        self.assertAlmostEqual(sum(sum(area(list(r)) for r in f.geometry.coordinates) for f in plateau.data),4)

    def test_pyplot_scientific_delegates_and_optional_components(self):
        import azimlib.pyplot as plt
        fig,ax=plt.subplots();b=plt.contourf([0,1],[0,1],[[0,1],[0,1]],levels=[0,.5,1])
        self.assertIs(b.axes,ax);self.assertIsNone(ax._legend);self.assertIsNone(ax._colorbar)
        self.assertIsNone(ax._north);self.assertIsNone(ax._compass);self.assertIsNone(ax._grid_config)
        self.assertIn('<svg',fig.to_svg())

    def test_field_creation_errors_preserve_axes_limits_and_layers(self):
        fig,ax=self.axes();ax.set_extent((0,2,0,2));before=ax.get_extent()
        attempts=(lambda:ax.contourf([0,1],[0,1],[[None,None]]*2),
                  lambda:ax.contourf([0,1],[0,1],[[0,1]]*2,levels=[0,1,0]),
                  lambda:ax.contourf([0,1],[0,1],[[0,1]]*2,linewidth=-1),
                  lambda:ax.terrain([[0,1],[2,3]],extent=(0,1,0,1),dx=0,dy=1),
                  lambda:ax.density([0],[0],weights=[-1]),
                  lambda:ax.hist2d([0],[0],weights=[0],density=True))
        for attempt in attempts:
            with self.assertRaises(ValueError):attempt()
            self.assertEqual(ax.get_extent(),before);self.assertFalse(ax.layers)

    def test_rgba_index_dtype_no_norm_and_norm_false(self):
        palette=ListedColormap(['#ff0000','#00ff00','#0000ff'])
        m=azl.cm.ScalarMappable(azl.colors.NoNorm(0,2),palette)
        self.assertEqual(m.to_rgba([0,1,2],bytes=True),[(255,0,0,255),(0,255,0,255),(0,0,255,255)])
        self.assertEqual(m.to_rgba([0.,.5,1.],norm=False,bytes=True),[(255,0,0,255),(0,255,0,255),(0,0,255,255)])

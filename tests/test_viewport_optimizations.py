"""Viewport optimizations preserve visible geography and editable data."""
import io
import unittest
from dataclasses import replace
from unittest.mock import patch
import azimlib as azl
from azimlib.geometry import Geometry,Feature,FeatureCollection
from azimlib.projections import (Projection,Equirectangular,Mercator,EqualEarth,
                                Orthographic,LambertConformalConic,AlbersEqualArea)
from azimlib.viewport import Viewport,_cached_bounds,_projected_bounds
from azimlib.renderers import render_png
from azimlib.scene import Path
from azimlib.navigation import Navigation


def png(scene):
    stream=io.BytesIO();render_png(scene,stream);return stream.getvalue()


def square(x,y,size=2):
    return Geometry('Polygon',[[(x,y),(x+size,y),(x+size,y+size),(x,y+size),(x,y)]])


class ViewportOptimizationTests(unittest.TestCase):
    def tearDown(self):
        azl.close('all');_cached_bounds.cache_clear()

    def test_builtin_bounds_remain_exact_across_resize_parameters_and_cache_eviction(self):
        projections=(Equirectangular(standard_parallel=25),Mercator(central_longitude=-60),
                     EqualEarth(),Orthographic(central_longitude=-50),
                     LambertConformalConic(central_longitude=-50),AlbersEqualArea(central_longitude=-50))
        extent=(-65,-30,-35,5)
        _cached_bounds.cache_clear()
        for projection in projections:
            with self.subTest(projection=projection.name):
                expected=_projected_bounds(projection,extent)
                a=Viewport(projection,extent,(0,0,400,300))
                b=Viewport(projection,list(extent),(10,20,800,600))
                self.assertEqual(a.projected_bounds,expected);self.assertEqual(b.projected_bounds,expected)
                point=a.project(-50,-15);larger=b.project(-50,-15)
                self.assertAlmostEqual(larger[0],10+2*point[0]);self.assertAlmostEqual(larger[1],20+2*point[1])
                self.assertAlmostEqual(b.inverse(*larger)[0],-50,places=7)
        self.assertEqual(_cached_bounds.cache_info().hits,6)
        for i in range(140):Viewport(Equirectangular(),(-20+i*.01,-5,20,5),(0,0,400,300))
        self.assertLessEqual(_cached_bounds.cache_info().currsize,128)
        self.assertEqual(Viewport(projections[0],extent,(0,0,400,300)).projected_bounds,
                         _projected_bounds(projections[0],extent))

    def test_custom_projection_is_not_implicitly_cached_or_culled(self):
        class Moving(Equirectangular):
            displacement=0
            def forward(self,lon,lat):
                x,y=super().forward(lon,lat);return x+self.displacement,y
        projection=Moving();extent=(-10,-10,10,10)
        first=Viewport(projection,extent,(0,0,200,200))
        projection.displacement=1000
        second=Viewport(projection,extent,(0,0,200,200))
        self.assertEqual(second.projected_bounds[0]-first.projected_bounds[0],1000)
        self.assertTrue(second.may_intersect((100,50,110,60)))

    def test_immutable_bounds_survive_replacement_and_serialization(self):
        geometry=square(0,0);payload=geometry.to_geojson();bounds=geometry.bounds
        self.assertIs(geometry.bounds,bounds);self.assertEqual(geometry.to_geojson(),payload)
        moved=replace(geometry,coordinates=square(20,30).coordinates)
        collection=FeatureCollection([Feature(geometry),Feature(None),Feature(moved),Feature(Geometry('Point'))])
        self.assertEqual(geometry.bounds,(0,0,2,2));self.assertEqual(moved.bounds,(20,30,22,32))
        self.assertEqual(collection.bounds,(0,0,22,32));self.assertIs(collection.bounds,collection.bounds)

    def scene_pair(self,projection='equirectangular',extent=(-10,10,-10,10),dpi=100):
        fig,ax=azl.subplots(figsize=(3.2,3.2),projection=projection);fig.dpi=dpi
        data=FeatureCollection([Feature(square(40,40)),Feature(square(-3,-3)),
                                Feature(Geometry('LineString',[(-30,0),(30,0)])),
                                Feature(Geometry('Polygon',[[(-30,-30),(30,-30),(30,30),(-30,30),(-30,-30)],
                                                            [(-5,-5),(-5,5),(5,5),(5,-5),(-5,-5)]]))])
        ax.geojson(data,fit=False,facecolor='#dce8ea',edgecolor='#333333',linewidth=.7,hatch='/')
        ax.set_extent(extent)
        return fig,ax,fig.to_scene(cull=False),fig.to_scene(cull=True)

    def test_crossings_enclosing_polygon_holes_and_hatches_keep_identical_png(self):
        for projection in ('equirectangular','mercator'):
            for dpi in (35,100,200):
                with self.subTest(projection=projection,dpi=dpi):
                    fig,_,full,culled=self.scene_pair(projection,dpi=dpi)
                    self.assertLess(len(culled.items),len(full.items))
                    self.assertEqual(png(full),png(culled));azl.close(fig)

    def test_stroke_overscan_and_display_sized_symbols_are_preserved(self):
        fig,ax=azl.subplots(figsize=(3.2,3.2));ax.set_extent((-10,10,-10,10))
        ax.line([(10.1,-5),(10.1,5)],fit=False,linewidth=12,linejoin='miter',linecap='square')
        ax.line([(13,-5),(13,5)],fit=False,linewidth=1,marker='D',markersize=60)
        ax.line([(15,-5),(15,5)],fit=False,arrow=True,arrowsize=80)
        ax.line([(15,-5),(15,5)],fit=False,curved=3)
        ax.scatter([10.1],[0],s=900)
        self.assertEqual(png(fig.to_scene()),png(fig.to_scene(cull=True)))

    def test_seams_unwrapped_longitude_and_other_projections_fall_back_safely(self):
        for projection,extent in ((Equirectangular(),(-180,180,-40,40)),
                                  (Mercator(central_longitude=180),(140,180,-30,30)),
                                  (Equirectangular(),(-10,10,-10,10)),
                                  (Orthographic(),(-90,90,-70,70)),(EqualEarth(),(-90,90,-70,70)),
                                  (LambertConformalConic(),(-60,60,0,60)),(AlbersEqualArea(),(-60,60,0,60))):
            with self.subTest(projection=projection.name,extent=extent):
                fig,ax=azl.subplots(figsize=(3.2,3.2),projection=projection)
                ax.line([(170,-15),(-170,15)],fit=False,linewidth=1)
                ax.polygon([(350,-5),(370,-5),(370,5),(350,5)],fit=False,facecolor='red')
                ax.set_extent(extent)
                self.assertEqual(png(fig.to_scene()),png(fig.to_scene(cull=True)));azl.close(fig)

    def test_callbacks_original_scalar_indices_editing_and_history(self):
        fig,ax=azl.subplots(figsize=(3.2,3.2));calls=[]
        data=FeatureCollection([Feature(square(40,40),{'index':0}),Feature(square(-2,-2),{'index':1})])
        layer=ax.choropleth(data,[0,100],bins=None,cmap='viridis')
        layer.options['feature_style']=lambda feature:(calls.append(feature.properties['index']) or {})
        ax.set_extent((-10,10,-10,10));nav=Navigation(fig)
        full=fig.to_scene();calls.clear();culled=fig.to_scene(cull=True)
        self.assertEqual(calls,[0,1]);self.assertEqual(png(full),png(culled))
        ax.set_extent((35,50,35,50));nav.push()
        self.assertEqual(png(fig.to_scene()),png(fig.to_scene(cull=True)))
        nav.home();self.assertEqual(ax.get_extent(),(-10.,10.,-10.,10.))
        line=ax.line([(40,40),(42,42)],fit=False,color='red');fig.to_scene(cull=True)
        line.set_data([-5,5],[-5,5])
        self.assertEqual(png(fig.to_scene()),png(fig.to_scene(cull=True)))
        self.assertEqual(line.data.bounds,(-5,-5,5,5))

    def test_compound_geometry_and_mercator_polar_clipping_keep_visible_parts(self):
        fig,ax=azl.subplots(figsize=(3.2,3.2),projection='mercator')
        collection=Geometry('GeometryCollection',geometries=[square(40,40),square(-3,-3)])
        lines=Geometry('MultiLineString',[[(-30,0),(30,0)],[(40,40),(45,45)]])
        polygons=Geometry('MultiPolygon',[square(40,40).coordinates,square(1,1).coordinates])
        polar=Geometry('Polygon',[[(-5,80),(5,80),(5,90),(-5,90),(-5,80)]])
        ax.geojson(FeatureCollection([Feature(g) for g in (collection,lines,polygons,polar)]),
                   fit=False,facecolor='#b7d2d8',linewidth=.6)
        for extent in ((-10,10,-10,10),(-10,10,75,89)):
            with self.subTest(extent=extent):
                ax.set_extent(extent)
                self.assertEqual(png(fig.to_scene()),png(fig.to_scene(cull=True)))

    def test_portable_html_retains_navigation_geometry_and_insets_recompose(self):
        fig,ax,full,culled=self.scene_pair();inset=ax.inset((.6,.6,.35,.35))
        inset.geojson(FeatureCollection([Feature(square(40,40)),Feature(square(0,0))]),fit=False)
        inset.set_extent((-10,10,-10,10));ax.overview(extent=(-60,60,-60,60),width=70)
        self.assertEqual(png(fig.to_scene()),png(fig.to_scene(cull=True)))
        with patch('azimlib.viewer.render_html',side_effect=lambda scene,**kw:scene) as render:
            html_scene=fig.to_html()
        self.assertGreater(len(html_scene.items),len(fig.to_scene(cull=True).items))
        self.assertEqual(html_scene.items,fig.to_scene(cull=False).items)
        with patch.object(fig,'to_scene',wraps=fig.to_scene) as compose:
            fig.savefig(io.StringIO(),format='svg');self.assertTrue(compose.call_args.kwargs['cull'])
            fig.savefig(io.BytesIO(),format='png',dpi=50);self.assertFalse(compose.call_args.kwargs['cull'])


if __name__=='__main__':unittest.main()

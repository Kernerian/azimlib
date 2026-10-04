"""Projected reuse preserves geometry/style and releases replaced source data."""
from dataclasses import replace
import gc
import io
import unittest
import weakref
from unittest.mock import patch
import azimlib as azl
from azimlib import render_map
from azimlib.geometry import Geometry,Feature,FeatureCollection
from azimlib.projected_paths import _paths,_ProjectedPathCache
from azimlib.projections import (Equirectangular,Mercator,EqualEarth,Orthographic,
                                AlbersEqualArea,LambertConformalConic)
from azimlib.renderers import render_png,render_svg
from azimlib.scene import Scene
from azimlib.viewport import Viewport


def polygon(x=-8,y=-8):
    return Geometry('Polygon',[[[x,y],[x+16,y],[x+16,y+16],[x,y+16],[x,y]],
        [[x+4,y+4],[x+4,y+12],[x+12,y+12],[x+12,y+4],[x+4,y+4]]])


def png(scene):
    stream=io.BytesIO();render_png(scene,stream);return stream.getvalue()


class ProjectedPathTests(unittest.TestCase):
    def setUp(self):_paths.clear()
    def tearDown(self):azl.close('all');_paths.clear()

    def compare_geometry(self,geometry,projection,extent=(-20,-20,20,20),style=None,pixels=False):
        vp=Viewport(projection,extent,(10,10,200,200))
        style=style or dict(facecolor='#cbd8df',edgecolor='#445566',linewidth=.7)
        def draw():
            scene=Scene(220,220);render_map._geometry(geometry,style,vp,scene);return scene
        with patch.object(_paths,'get',return_value=None):expected=draw()
        first=draw();warm=draw()
        self.assertEqual(expected.items,first.items);self.assertEqual(expected.items,warm.items)
        self.assertEqual(render_svg(expected),render_svg(warm))
        if pixels:self.assertEqual(png(expected),png(warm))
        return warm

    def test_all_builtin_projections_and_geometry_forms_keep_exact_scene(self):
        line=Geometry('LineString',[[-15,-12,20],[0,5,30],[14,12,40]])
        area=polygon()
        forms=(line,Geometry('MultiLineString',[line.coordinates,[],line.coordinates[::-1]]),
               area,Geometry('MultiPolygon',[area.coordinates,polygon(10,10).coordinates]),
               Geometry('GeometryCollection',geometries=(line,area)),
               Geometry('MultiPolygon'),Geometry('LineString'))
        for projection in (Equirectangular(standard_parallel=20),Mercator(),EqualEarth(),
                           Orthographic(),AlbersEqualArea(),LambertConformalConic()):
            for geometry in forms:
                with self.subTest(projection=projection.name,kind=geometry.type):
                    self.compare_geometry(geometry,projection)

    def test_antimeridian_polar_clipping_and_globe_horizon_preserve_pixels(self):
        seam=Geometry('Polygon',[[[170,70],[-170,70],[-170,89],[170,89],[170,70]]])
        horizon=Geometry('Polygon',[[[70,-20],[110,-20],[110,20],[70,20],[70,-20]]])
        cases=((seam,Mercator(),(-180,65,180,89)),
               (Geometry('LineString',[[170,-20],[-170,20]]),Equirectangular(),(-180,-30,180,30)),
               (Geometry('LineString',[[0,84],[0,89],[10,84]]),Mercator(),(-20,75,20,89)),
               (horizon,Orthographic(),(-90,-80,90,80)),
               (polygon(350,-8),Equirectangular(),(-20,-20,20,20)))
        for geometry,projection,extent in cases:
            with self.subTest(projection=projection.name,kind=geometry.type):
                self.compare_geometry(geometry,projection,extent,dict(facecolor='#dddddd',linewidth=.5,hatch='/',hatch_linewidth=.4),pixels=True)

    def test_warm_paths_do_not_reproject_vertices_and_display_transform_stays_fresh(self):
        geometry=polygon();projection=Mercator()
        vp=Viewport(projection,(-20,-20,20,20),(0,0,200,200))
        style=dict(facecolor='white',linewidth=.5)
        first=Scene(200,200);render_map._geometry(geometry,style,vp,first)
        bigger=Viewport(projection,(-10,-10,10,10),(30,40,400,400))
        with patch.object(Mercator,'forward',side_effect=AssertionError('warm geometry must not reproject')):
            warm=Scene(500,500);render_map._geometry(geometry,style,bigger,warm)
        with patch.object(_paths,'get',return_value=None):
            expected=Scene(500,500);render_map._geometry(geometry,style,bigger,expected)
        self.assertEqual(warm.items,expected.items);self.assertNotEqual(first.items,warm.items)

    def test_style_changes_curves_arrows_markers_hatches_and_callbacks_remain_live(self):
        fig,ax=azl.subplots(figsize=(3,3));ax.set_extent((-20,20,-20,20))
        line=ax.line([[-15,-5],[0,10],[15,-5]],color='red',arrow='both',marker='^')
        data=FeatureCollection([Feature(polygon(),{'value':2})])
        layer=ax.geojson(data,fit=False,facecolor='#dddddd',hatch='/')
        calls=[]
        layer.options['feature_style']=lambda f:(calls.append(f.properties['value']) or {'edgecolor':'blue'})
        fig.to_scene();calls.clear()
        line.style.update(color='green',curved=.3,arrowsize=12,markersize=5,linestyle='--')
        layer.style.update(facecolor='#c4d7e0',hatch='xx',hatch_linewidth=.6)
        with patch.object(_paths,'get',return_value=None):expected=fig.to_scene()
        cached=fig.to_scene();self.assertEqual(calls,[2,2]);self.assertEqual(expected.items,cached.items)
        self.assertEqual(png(expected),png(cached))
        line.set_data([-10,0,10],[10,-10,10])
        with patch.object(_paths,'get',return_value=None):expected=fig.to_scene()
        self.assertEqual(expected.items,fig.to_scene().items)

    def test_replacements_and_projection_parameters_receive_distinct_paths(self):
        cache=_ProjectedPathCache();geometry=polygon();projection=Mercator()
        first=cache.get(geometry,projection)
        self.assertIs(first,cache.get(geometry,Mercator()))
        moved=replace(geometry,coordinates=polygon(10,10).coordinates)
        self.assertNotEqual(first,cache.get(moved,projection))
        self.assertNotEqual(first,cache.get(geometry,Mercator(central_longitude=30)))
        self.assertEqual(cache.info().entries,3)
        self.assertEqual(geometry.to_geojson()['coordinates'][0][0],[-8.,-8.])

    def test_budget_lru_oversized_sources_and_weak_release(self):
        geometry=polygon();projection=Mercator();cache=_ProjectedPathCache(max_entries=2)
        original=cache.get(geometry,projection)
        cache.get(geometry,Mercator(central_longitude=10))
        self.assertIs(original,cache.get(geometry,projection))
        cache.get(geometry,Mercator(central_longitude=20))
        misses=cache.info().misses;cache.get(geometry,Mercator(central_longitude=10))
        self.assertEqual(cache.info().misses,misses+1);self.assertEqual(cache.info().entries,2)
        budget=_ProjectedPathCache(max_bytes=cache.info().payload_bytes//2,max_entries=10)
        areas=[polygon(i*5,i*5) for i in range(5)]
        for area in areas:
            budget.get(area,projection);self.assertLessEqual(budget.info().payload_bytes,budget.max_bytes)
        tiny=_ProjectedPathCache(max_bytes=1)
        self.assertEqual(tiny.get(geometry,projection),original);self.assertEqual(tiny.info().entries,0)
        self.assertIsNone(_ProjectedPathCache(max_bytes=0).get(geometry,projection))
        reference=weakref.ref(geometry);del geometry;gc.collect()
        self.assertIsNone(reference());self.assertEqual(cache.info().entries,0)
        self.assertEqual(cache.info().payload_bytes,0)

    def test_custom_projection_and_geometry_subclasses_are_never_cached(self):
        class Moving(Equirectangular):
            displacement=0
            def forward(self,lon,lat):
                x,y=super().forward(lon,lat);return x+self.displacement,y
        class Extended(Geometry):pass
        geometry=polygon();projection=Moving();cache=_ProjectedPathCache()
        self.assertIsNone(cache.get(geometry,projection))
        self.assertIsNone(cache.get(Extended('Polygon',geometry.coordinates),Equirectangular()))
        vp=Viewport(projection,(-20,-20,20,20),(0,0,200,200))
        first=Scene(200,200);render_map._geometry(geometry,{},vp,first)
        projection.displacement=1000
        second=Scene(200,200);render_map._geometry(geometry,{},vp,second)
        self.assertNotEqual(first.items,second.items);self.assertEqual(cache.info().entries,0)

    def test_navigation_insets_overview_culling_and_html_keep_full_composition(self):
        fig,ax=azl.subplots(figsize=(4,3),layout='constrained')
        data=FeatureCollection([Feature(polygon())]);ax.geojson(data,fit=False,facecolor='#dde5e8')
        ax.set_extent((-20,20,-20,20));ax.scale_bar();ax.north_arrow()
        inset=ax.inset((.6,.6,.3,.3));inset.geojson(data,fit=False)
        inset.set_extent((-15,15,-15,15));ax.overview(extent=(-30,30,-30,30),width=60)
        for extent,dpi in (((-20,20,-20,20),100),((-10,10,-10,10),50),((0,25,0,25),200)):
            ax.set_extent(extent);fig.dpi=dpi
            with self.subTest(extent=extent,dpi=dpi):
                with patch.object(_paths,'get',return_value=None):expected=fig.to_scene(cull=True)
                cached=fig.to_scene(cull=True)
                self.assertEqual(expected.items,cached.items);self.assertEqual(expected.maps,cached.maps)
                self.assertEqual(png(expected),png(cached))
        with patch.object(_paths,'get',return_value=None):html=fig.to_html()
        self.assertEqual(html,fig.to_html())

    def test_cache_payload_cannot_be_changed_through_scene_and_errors_are_not_retained(self):
        geometry=polygon();vp=Viewport(Equirectangular(),(-20,-20,20,20),(0,0,200,200))
        scene=Scene(200,200);render_map._geometry(geometry,{},vp,scene)
        original=scene.items[0].paths[0][0];scene.items[0].paths[0][0]=(999,999)
        redraw=Scene(200,200);render_map._geometry(geometry,{},vp,redraw)
        self.assertEqual(redraw.items[0].paths[0][0],original)
        invalid=Geometry('Polygon',[[[-20,-90],[20,-90],[20,-70],[-20,-70],[-20,-90]]])
        cache=_ProjectedPathCache()
        with self.assertRaises(ValueError):cache.get(invalid,LambertConformalConic())
        self.assertEqual(cache.info().entries,0)
        for limits in ({'max_bytes':-1},{'max_entries':False},{'max_bytes':1.5}):
            with self.assertRaises(ValueError):_ProjectedPathCache(**limits)


if __name__=='__main__':unittest.main()

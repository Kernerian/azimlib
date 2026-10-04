"""Spatial queries and indexed map composition versus independent full scans."""
from dataclasses import FrozenInstanceError
import io
import math
import random
import unittest
from unittest.mock import patch
import azimlib as azl
from azimlib.geometry import Geometry,Feature,FeatureCollection
from azimlib.projections import Equirectangular,Mercator,EqualEarth
from azimlib.renderers import render_png
from azimlib.spatial import BoundsIndex
from azimlib import render_map


def png(scene):
    buffer=io.BytesIO();render_png(scene,buffer);return buffer.getvalue()


def collection():
    features=[]
    for y in range(-40,41,5):
        for x in range(-90,91,5):
            ring=[(x,y),(x+2,y),(x+2,y+2),(x,y+2),(x,y)]
            features.append(Feature(Geometry('Polygon',[ring]),{'i':len(features)}))
    return FeatureCollection(features)


class BoundsIndexTests(unittest.TestCase):
    def test_clustered_thin_and_extreme_boxes_preserve_exact_closed_queries(self):
        tiny=math.nextafter(1.,2.)
        entries=[(-10**60,(-1e308,-1e308,1e308,1e308)),
                 (10**60,(tiny,-0.,tiny,0.)),(7000,(1.,0.,1.,0.))]
        entries.extend((i,(i*.001,-10.,i*.001,10.)) for i in range(250))
        entries.extend((i+1000,(-.1,-.1,.1,.1)) for i in range(250))
        for leaf_size in (1,2,12,31,1000,10**400):
            index=BoundsIndex(reversed(entries),leaf_size=leaf_size)
            for query in ((1.,0.,1.,0.),(tiny,0.,tiny,0.),(-0.,-0.,0.,0.),
                          (-1e308,-1e308,1e308,1e308),(.12,-5.,.2,5.),(2.,2.,3.,3.)):
                expected=tuple(sorted(key for key,(w,s,e,n) in entries
                    if w<=query[2] and e>=query[0] and s<=query[3] and n>=query[1]))
                with self.subTest(leaf_size=leaf_size,query=query):
                    self.assertEqual(index.query(query),expected)

    def test_random_rectangles_match_independent_brute_force(self):
        rng=random.Random(903);entries=[]
        for i in range(1500):
            x,y=rng.uniform(-100,100),rng.uniform(-100,100)
            entries.append((i,(x,y,x+rng.uniform(0,60),y+rng.uniform(0,60))))
        index=BoundsIndex(reversed(entries));self.assertEqual(index.size,1500)
        for trial in range(120):
            x,y=rng.uniform(-120,120),rng.uniform(-120,120)
            query=(x,y,x+rng.uniform(0,40),y+rng.uniform(0,40))
            expected=tuple(i for i,(w,s,e,n) in entries if w<=query[2] and e>=query[0] and s<=query[3] and n>=query[1])
            with self.subTest(trial=trial):self.assertEqual(index.query(query),expected)

    def test_touching_zero_area_enclosing_duplicate_boxes_and_owned_input(self):
        boxes=[[0,0,1,1],[1,1,1,1],[-10,-10,10,10],[0,0,1,1]]
        index=BoundsIndex([(9,boxes[0]),(2,boxes[1]),(5,boxes[2]),(7,boxes[3])],leaf_size=1)
        boxes[0][:]=[100,100,101,101]
        self.assertEqual(index.query((1,1,1,1)),(2,5,7,9))
        self.assertEqual(index.query((2,2,3,3)),(5,))
        self.assertEqual(index.query((100,100,101,101)),())
        self.assertEqual(index.bounds,(-10,-10,10,10))
        self.assertEqual(BoundsIndex().query((0,0,0,0)),());self.assertIsNone(BoundsIndex().bounds)
        with self.assertRaises(FrozenInstanceError):index.size=0

    def test_invalid_entries_and_queries_are_rejected(self):
        for entries in ([(0,(0,0,1,float('nan')))],[(True,(0,0,1,1))],[(0,(0,0,1,1)),(0,(1,1,2,2))],
                        [(0,(1,0,0,1))],[(0,(0,False,1,1))],[(0,(0,0,1))]):
            with self.subTest(entries=entries):
                with self.assertRaises(ValueError):BoundsIndex(entries)
        for leaf in (0,False,1.5):
            with self.assertRaises(ValueError):BoundsIndex(leaf_size=leaf)
        for box in ((2,0,1,1),(0,0,1,float('inf'))):
            with self.assertRaises(ValueError):BoundsIndex().query(box)


class IndexedCompositionTests(unittest.TestCase):
    def tearDown(self):azl.close('all')

    def compare(self,fig,*,pixels=True):
        with patch.object(render_map,'_geometry_candidates',return_value=None):full=fig.to_scene(cull=True)
        indexed=fig.to_scene(cull=True)
        self.assertEqual(full.items,indexed.items)
        self.assertEqual(full.maps,indexed.maps)
        if pixels:self.assertEqual(png(full),png(indexed))
        return indexed

    def test_dense_layer_queries_only_candidates_and_preserves_scene_across_pan_zoom_dpi(self):
        data=collection();fig,ax=azl.subplots(figsize=(3.2,3.2),projection='mercator')
        layer=ax.geojson(data,fit=False,facecolor='#b7d2d8',linewidth=.5)
        for extent,dpi in (((-10,10,-10,10),100),((40,60,10,25),35),((-8,8,-6,6),200)):
            with self.subTest(extent=extent,dpi=dpi):
                ax.set_extent(extent);fig.dpi=dpi
                with patch.object(render_map,'_geometry',wraps=render_map._geometry) as draw:
                    fig.to_scene(cull=True)
                    self.assertLess(draw.call_count,len(data)//4)
                self.compare(fig)
        self.assertEqual(ax.layers[0].data,data)
        self.assertEqual(len(data),629)

    def test_per_feature_width_symbols_and_direct_style_edits_keep_original_indices(self):
        data=collection();fig,ax=azl.subplots(figsize=(3.2,3.2))
        layer=ax.choropleth(data,list(range(len(data))),bins=None,cmap='viridis')
        ax.set_extent((-10,10,-10,10))
        layer.options['feature_styles'][0].update(marker='s',markersize=8)
        near=next(i for i,f in enumerate(data) if f.bounds==(10.,0.,12.,2.))
        layer.options['feature_styles'][near]['linewidth']=18
        self.compare(fig)
        layer.options['feature_styles'][near]['linewidth']=.2
        layer.options['feature_styles'][0].update(curved=1)
        layer.set_array(list(reversed(range(len(data)))))
        self.compare(fig)
        layer.set(linewidth=25);self.compare(fig)

    def test_callback_layers_keep_full_order_and_no_implicit_index(self):
        data=collection();fig,ax=azl.subplots(figsize=(3.2,3.2));calls=[]
        layer=ax.geojson(data,fit=False);ax.set_extent((-10,10,-10,10))
        layer.options['feature_style']=lambda feature:(calls.append(feature.properties['i']) or {})
        fig.to_scene(cull=True)
        self.assertEqual(calls,list(range(len(data))))
        self.assertNotIn('_viewport_indexes',data.__dict__)
        calls.clear();self.compare(fig,pixels=False)
        self.assertEqual(calls,list(range(len(data)))*2)

    def test_thick_hatch_strokes_outside_the_view_are_included_in_overscan(self):
        data=collection();fig,ax=azl.subplots(figsize=(3.2,3.2))
        layer=ax.geojson(data,fit=False,facecolor='none',linewidth=.2)
        layer.options['feature_styles']=[{} for _ in data]
        near=next(i for i,f in enumerate(data) if f.bounds==(15.,0.,17.,2.))
        layer.options['feature_styles'][near].update(hatch='-',hatch_linewidth=60,hatch_color='red')
        ax.set_extent((-10,10,-10,10))
        self.assertEqual(png(fig.to_scene(cull=False)),png(self.compare(fig)))
        layer.options['feature_styles'][near]['hatch_linewidth']=.1
        self.compare(fig)

    def test_seams_enclosing_crossings_points_collections_and_poles_are_retained(self):
        extra=[Geometry('LineString',[(-80,0),(80,0)]),
               Geometry('Polygon',[[(-30,-30),(30,-30),(30,30),(-30,30),(-30,-30)]]),
               Geometry('LineString',[(170,-5),(-170,5)]),
               Geometry('Polygon',[[(350,-5),(370,-5),(370,5),(350,5),(350,-5)]]),
               Geometry('Point',(10.1,0)),Geometry('MultiPoint',[(0,0),(40,40)]),
               Geometry('GeometryCollection',geometries=(Geometry('LineString',[(-20,-5),(20,5)]),)),
               Geometry('LineString',[(0,86),(5,89)])]
        data=FeatureCollection([*collection(),*[Feature(g) for g in extra],Feature(None)])
        for projection,extent in ((Mercator(),(-10,10,-10,10)),
                                  (Mercator(central_longitude=180),(140,180,-30,30)),
                                  (Equirectangular(central_longitude=30),(-20,20,-20,20)),
                                  (Mercator(),(-10,10,75,89))):
            with self.subTest(projection=projection,extent=extent):
                fig,ax=azl.subplots(figsize=(3.2,3.2),projection=projection)
                ax.geojson(data,fit=False,facecolor='#eeeeee',hatch='/');ax.set_extent(extent)
                self.compare(fig);azl.close(fig)

    def test_collection_replacement_projection_cache_eviction_insets_and_html(self):
        data=collection();fig,ax=azl.subplots(figsize=(3.2,3.2));layer=ax.geojson(data,fit=False)
        ax.set_extent((-10,10,-10,10));first=None
        for central in range(0,100,15):
            ax.projection=Equirectangular(central_longitude=central)
            self.compare(fig,pixels=False)
            if central==0:first=data._viewport_indexes.get(data,ax.projection)
        self.assertLessEqual(len(data._viewport_indexes._entries),4)
        ax.projection=Equirectangular()
        self.assertIsNot(data._viewport_indexes.get(data,ax.projection),first)
        layer.data=FeatureCollection([Feature(Geometry('LineString',[(-5,-5),(5,5)])) for _ in range(70)])
        self.compare(fig,pixels=False)
        self.assertIsNot(layer.data._viewport_indexes,data._viewport_indexes)
        inset=ax.inset((.6,.6,.35,.35));inset.geojson(data,fit=False);inset.set_extent((-10,10,-10,10))
        ax.overview(extent=(-60,60,-50,50),width=70);self.compare(fig)
        with patch.object(render_map,'_geometry_candidates',side_effect=AssertionError('HTML must stay complete')):
            fig.to_html()
        ax.projection=EqualEarth();self.compare(fig,pixels=False)


if __name__=='__main__':unittest.main()

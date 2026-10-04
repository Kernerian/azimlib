"""Exact keys, caller ownership, bounded retention and fail-fast scene checks."""
import unittest
from unittest.mock import patch
from azimlib.backends._raster_cache import RasterCache,scene_key
from azimlib.scene import Scene,Rect,Text,Path,Circle

class RasterCacheTests(unittest.TestCase):
    def setUp(self):
        try:from PIL import Image
        except ImportError:self.skipTest('Pillow optional raster extra')
        self.Image=Image;self.scene=Scene(10,10);self.scene.add(Rect(1,1,3,3,{'fill':'red'}))
        self.cache=RasterCache(max_entries=2,max_bytes=800)
    def tearDown(self):
        if hasattr(self,'cache'):self.cache.clear()
    def test_hit_owns_copy_and_source_or_previous_hit_mutation_cannot_poison_cache(self):
        key,miss=self.cache.lookup(self.scene);self.assertIsNone(miss)
        with self.Image.new('RGBA',(10,10),'red') as image:
            self.cache.store(key,image);image.putpixel((0,0),(0,0,0,0))
        _,hit=self.cache.lookup(self.scene);self.assertEqual(hit.getpixel((0,0)),(255,0,0,255))
        hit.putpixel((0,0),(0,0,0,0));hit.close()
        _,hit=self.cache.lookup(self.scene);self.assertEqual(hit.getpixel((0,0)),(255,0,0,255));hit.close()
        self.assertEqual((self.cache.hits,self.cache.misses,self.cache.bytes),(2,1,400))
    def test_lru_eviction_closes_image_and_respects_limits(self):
        with self.Image.new('RGBA',(10,10),'red') as image:
            for key in (b'a',b'b'):self.cache.store(key,image)
            evicted=self.cache._images[b'a'];self.cache.store(b'c',image)
        self.assertEqual(list(self.cache._images),[b'b',b'c'])
        with self.assertRaises(ValueError):evicted.getpixel((0,0))
        self.assertEqual(self.cache.bytes,800)
        self.cache.clear();self.assertEqual(self.cache.bytes,0)
    def test_oversized_or_disabled_cache_does_not_retain_pixels(self):
        for limits in (dict(max_entries=0),dict(max_bytes=0),dict(max_bytes=399)):
            with self.subTest(limits=limits):
                cache=RasterCache(**limits)
                with self.Image.new('RGBA',(10,10)) as image:cache.store(b'a',image)
                self.assertEqual(cache.bytes,0);self.assertFalse(cache._images)
    def test_changed_pixels_or_styles_or_clips_change_key_but_metadata_does_not(self):
        original=scene_key(self.scene);self.scene.maps.append({'focus':'metadata only'})
        self.assertEqual(original,scene_key(self.scene))
        for item in (Rect(2,1,3,3,{'fill':'red'}),Rect(1,1,3,3,{'fill':'blue'}),
                     Rect(1,1,3,3,{'fill':'red'},(0,0,2,2)),Circle(1,1,3,{'fill':'red'}),
                     Path([[(0,0),(1,1)]],style={'stroke':'red'}),Text(1,1,'Text')):
            with self.subTest(item=item):
                scene=Scene(10,10);scene.add(item);self.assertNotEqual(original,scene_key(scene))
        self.scene.width=11;self.assertNotEqual(original,scene_key(self.scene))
    def test_invalid_mutated_scene_cannot_be_returned_from_cache(self):
        key,_=self.cache.lookup(self.scene)
        with self.Image.new('RGBA',(10,10)) as image:self.cache.store(key,image)
        self.scene.items[0].style['stroke_width']=-1
        with self.assertRaises(ValueError):self.cache.lookup(self.scene)
        self.assertEqual((self.cache.hits,self.cache.bytes),(0,400))
    def test_font_revision_is_part_of_key(self):
        scene=Scene(10,10);scene.add(Text(1,1,'A'))
        first=scene_key(scene)
        with patch('pathlib.Path.read_bytes',return_value=b'different font contents'):
            self.assertNotEqual(first,scene_key(scene))
    def test_cache_limits_reject_ambiguous_or_negative_values(self):
        for key in ('max_entries','max_bytes'):
            for value in (-1,True,1.5):
                with self.subTest(key=key,value=value):
                    with self.assertRaises(ValueError):RasterCache(**{key:value})
    def test_failed_image_copy_keeps_old_entries_and_counters(self):
        with self.Image.new('RGBA',(10,10)) as image:self.cache.store(b'a',image)
        from types import SimpleNamespace
        def fail():raise MemoryError('copy failed')
        with self.assertRaises(MemoryError):self.cache.store(b'b',SimpleNamespace(mode='RGBA',width=10,height=10,copy=fail))
        self.assertEqual(list(self.cache._images),[b'a']);self.assertEqual(self.cache.bytes,400)

if __name__=='__main__':unittest.main()

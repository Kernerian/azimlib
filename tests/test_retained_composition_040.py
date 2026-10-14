"""Exact centerline reuse, public mutation, decoration protection and glyph runs."""
from array import array
import importlib.util
from pathlib import Path as FilePath
import sys
import unittest
from unittest.mock import patch

from azimlib._screen_cache import ScreenCache,ScreenPoints,screen_cache
from azimlib.projected_paths import screen_points,_screen_points_uncached,_paths
from azimlib.projections import Mercator
from azimlib.viewport import Viewport
from azimlib.scene import Path,Text,Rect
from azimlib.renderers._gpu_geometry import PreparationCache
from azimlib import font_outline


class RetainedCompositionTests(unittest.TestCase):
    def tearDown(self):_paths.clear()

    def test_centerlines_equal_old_float64_for_pan_zoom_bearing(self):
        data=array('d',(v for i in range(100) for v in (i*1.123,-i*.932))).tobytes()
        for bearing in (0,29,91,178):
            for extent in ((-30,-20,40,50),(-20,-10,20,40)):
                vp=Viewport(Mercator(),extent,(1,2,500,300),bearing=bearing)
                expected=_screen_points_uncached(data,vp)
                first=screen_points(data,vp);second=screen_points(data,vp)
                self.assertEqual(first,expected);self.assertEqual(second,expected)
                self.assertIsNot(first,second);first[0]=(1,2)
                self.assertEqual(screen_points(data,vp),expected)

    def test_all_list_mutators_invalidate_compiled_local_geometry(self):
        operations=(lambda p:p.append((3,3)),lambda p:p.extend([(3,3)]),
            lambda p:p.insert(0,(3,3)),lambda p:p.pop(),lambda p:p.remove((0,0)),
            lambda p:p.clear(),lambda p:p.reverse(),lambda p:p.sort(),
            lambda p:p.__setitem__(0,(3,3)),lambda p:p.__delitem__(slice(0,1)),
            lambda p:p.__iadd__([(3,3)]),lambda p:p.__imul__(2))
        for operation in operations:
            points=ScreenPoints(((0,0),(1,1)),(((0,0),(1,1)),b'digest'))
            operation(points);self.assertIsNone(points._compiled)

    def test_cache_bound_and_uncacheable_custom_viewport(self):
        cache=ScreenCache(limit=1800,max_entries=2)
        vp=Viewport(Mercator(),(-30,-20,40,50),(0,0,500,300))
        for i in range(20):
            cache.get(bytes([i]),vp,lambda:[(float(i),0.),(float(i)+1,1.)])
            self.assertLessEqual(cache.bytes,cache.limit);self.assertLessEqual(len(cache.entries),2)
        class Custom(Viewport):
            def xy(self,x,y):return x+123,y-456
        custom=Custom(Mercator(),(-30,-20,40,50),(0,0,500,300))
        packed=array('d',(v for i in range(100) for v in (i,i+1))).tobytes()
        with patch.object(screen_cache,'get',side_effect=AssertionError('custom viewport cached')):
            self.assertEqual(screen_points(packed,custom),[(i+123,i+1-456) for i in range(100)])

    def test_compiled_path_packets_equal_fallback_after_mutation_and_style(self):
        packed=array('d',(v for i in range(100) for v in (i,i%7))).tobytes()
        vp=Viewport(Mercator(),(-30,-20,40,50),(0,0,500,300))
        points=screen_points(packed,vp)
        for mutate in (False,True):
            if mutate:points[13]=(100.,200.)
            for style in (dict(stroke='black',stroke_width=.9),dict(fill='red',stroke='blue',stroke_width=2.)):
                a=PreparationCache(1000000).get(Path([points],True,style))
                b=PreparationCache(1000000).get(Path([list(points)],True,style))
                self.assertEqual(a,b)

    def test_geometry_pressure_does_not_evict_small_texts(self):
        cache=PreparationCache(80000)
        text=Text(2,3,'North',dict(fill='black',font_size=12))
        first,_=cache.get(text)
        for i in range(100):
            cache.get(Path([[(0,0),(i+1,2),(i+3,i+4)]],True,dict(fill='red')))
            self.assertLessEqual(cache.bytes,cache.limit)
        second,_=cache.get(text)
        self.assertIs(first,second);self.assertLessEqual(cache.protected_bytes,cache.limit//4)
        cache.clear();self.assertEqual(cache.bytes,0);self.assertFalse(cache.protected)

    def test_glyph_runs_keep_original_operation_order(self):
        # Independent expression of the previous scalar outline placement.
        import math
        from azimlib.typography import font_path,_metrics,text_width,text_baseline_offset
        for value in ('AV To fj','Latitude','Long label 123.45','Título é à'):
            for rotation in (0,31,-90):
                style=dict(font_size=13.7,anchor='middle',baseline='top',rotation=rotation)
                item=Text(19.3,-4.1,value,style);path=font_path(style);metrics=_metrics()[path.stem]
                factor=style['font_size']/metrics['units'];x=-.5*text_width(value,style);y=text_baseline_offset(value,style)
                c,s=math.cos(math.radians(rotation)),math.sin(math.radians(rotation));previous=None;commands=[]
                for char in value:
                    glyph,advance=metrics['chars'][char];x+=metrics['kern'].get(f'{previous},{glyph}',0)*factor
                    for ring in font_outline.contours(path,glyph):
                        for cmd in font_outline.glyph_commands(ring):
                            points=[]
                            for px,py in cmd[1:]:
                                dx=x+px*factor;dy=y-py*factor
                                points.append((item.x+dx*c-dy*s,item.y+dx*s+dy*c))
                            commands.append((cmd[0],*points))
                    previous=glyph;x+=advance*factor
                self.assertEqual(tuple(font_outline.text_commands(item)),tuple(commands))

    def test_long_runs_do_not_enter_bounded_short_run_cache(self):
        font_outline._cached_glyph_run.cache_clear()
        from azimlib.typography import font_path
        font_outline.glyph_run(font_path({}),'A'*257)
        self.assertEqual(font_outline._cached_glyph_run.cache_info().currsize,0)


if __name__=='__main__':unittest.main()

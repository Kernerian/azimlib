"""Contour boundary contracts, geographic holes and retained editable handles."""
import io
import json
import math
from pathlib import Path
import unittest
import azimlib as azl
from azimlib.colors import Normalize
from azimlib.fields import contour_levels,contour_segments,grid_data
from azimlib.renderers import render_png


class ContourBoundaryTests(unittest.TestCase):
    def tearDown(self):azl.close('all');azl.ioff()

    def test_constant_fields_own_empty_editable_handles_like_agg(self):
        reference=json.loads((Path(__file__).resolve().parents[1]/'docs/contour-boundaries-reference.json').read_text())
        cases={case['name']:case for case in reference['cases']}
        for value in (0.,5.,-3.):
            with self.subTest(value=value):
                native=cases[f'constant-{value:g}']
                self.assertEqual(native['status'],'accepted');self.assertFalse(any(native['segments']))
                self.assertTrue(native['labels_empty']);self.assertEqual(native['colorbar'],'drawn')
                fig,ax=azl.subplots(figsize=(2,2));ax.set_extent((-54,-44,-26,-18))
                contour=ax.contour([-54,-49,-44],[-26,-22,-18],[[value]*3]*3)
                self.assertEqual(contour.levels,(value,));self.assertEqual(contour.allsegs,[[]])
                self.assertIs(contour.axes,ax);self.assertEqual(contour.clabel(),[])
                before=contour.data;events=[];contour.add_callback(events.append)
                contour.set(linewidths=[.4],colors='red',visible=False)
                self.assertIs(contour.data,before);self.assertEqual(events,[contour])
                self.assertEqual(contour.get_edgecolors(),['red'])
                bar=fig.colorbar(contour,orientation='horizontal');bar.set_label('Constant')
                self.assertIn('Constant',fig.to_svg())
                stream=io.BytesIO();fig.savefig(stream,format='png');self.assertTrue(stream.getvalue().startswith(b'\x89PNG'))
                extent=ax.get_extent();contour.set_visible(True);bar.remove();contour.remove()
                self.assertEqual(ax.get_extent(),extent);self.assertIsNone(contour.get_figure())
                azl.close(fig)

    def test_automatic_levels_handle_float_resolution_and_overflow(self):
        cases=[(1.,math.nextafter(1.,math.inf)),(-1.,math.nextafter(-1.,math.inf)),
               (0.,math.ulp(0.)),(-1e308,1e308),(0.,1e308),(1e308,math.nextafter(1e308,math.inf))]
        for lo,hi in cases:
            for count in (1,7,30):
                with self.subTest(lo=lo,hi=hi,count=count):
                    levels=contour_levels([lo,hi],count)
                    self.assertTrue(levels);self.assertTrue(all(math.isfinite(v) and lo<=v<=hi for v in levels))
                    self.assertTrue(all(a<b for a,b in zip(levels,levels[1:])))
        # Keep the established nonconstant automatic spacing unchanged.
        self.assertEqual(contour_levels([0,2],7),tuple(i/4 for i in range(1,8)))

    def test_explicit_levels_and_missing_fields_reject_before_attachment(self):
        fig,ax=azl.subplots();ax.set_extent((-54,-44,-26,-18));extent=ax.get_extent()
        for levels in ([],[1,1],[2,1],[math.nan],[math.inf],0,-1):
            with self.subTest(levels=levels):
                fig.canvas.draw();layers=list(ax.layers)
                with self.assertRaises(ValueError):ax.contour([-54,-44],[-26,-18],[[0,2]]*2,levels=levels)
                self.assertEqual(ax.layers,layers);self.assertEqual(ax.get_extent(),extent);self.assertFalse(fig.stale)
        for values in ([[None,None]]*2,[[math.nan,math.inf]]*2):
            with self.subTest(values=values):
                fig.canvas.draw()
                with self.assertRaisesRegex(ValueError,'No finite'):ax.contour([-54,-44],[-26,-18],values,levels=[1])
                self.assertFalse(fig.stale);self.assertEqual(ax.layers,[])

    def test_missing_cells_split_isolines_without_crossing_holes(self):
        x=[-54,-51,-48,-45,-42];y=[-28,-25,-22,-19,-16]
        for missing in (None,math.nan,math.inf):
            with self.subTest(missing=missing):
                values=[[0,1,2,3,4] for _ in y];values[2][2]=missing
                grid=grid_data(x,y,values);lines=contour_segments(*grid,2.5)
                self.assertEqual(len(lines),2)
                ranges=sorted((min(p[1] for p in line),max(p[1] for p in line)) for line in lines)
                self.assertEqual(ranges,[(-28,-25),(-19,-16)])
                self.assertTrue(all(p[0]==-46.5 for line in lines for p in line))

    def test_saddle_decider_matches_edge_intersections_and_connectivity(self):
        # Clockwise corners: lower-left, lower-right, upper-right, upper-left.
        for values,level,expected in (
            # Exactly zero determinant has a documented deterministic tie rule.
            ([[0,2],[2,0]],1,{frozenset(((.5,0),(1,.5))),frozenset(((.5,1),(0,.5)))}),
            ([[0,3],[3,0]],1,{frozenset(((1/3,0),(0,1/3))),frozenset(((1,2/3),(2/3,1)))}),
            ([[0,2],[2,0]],1.5,{frozenset(((.75,0),(1,.25))),frozenset(((.25,1),(0,.75)))})):
            with self.subTest(values=values,level=level):
                lines=contour_segments([0,1],[0,1],values,level)
                expected={frozenset(tuple(round(v,12) for v in p) for p in pair) for pair in expected}
                self.assertEqual({frozenset(map(tuple,line)) for line in lines},expected)

    def test_selected_empty_and_invalid_contracts_match_recorded_agg(self):
        reference=json.loads((Path(__file__).resolve().parents[1]/'docs/contour-boundaries-reference.json').read_text())
        cases={case['name']:case for case in reference['cases']}
        for name,z,levels in (
            ('outside',[[0,1,2]]*3,[3,4]),
            ('missing-center',[[0,1,2],[0,None,2],[0,1,2]],[.5,1.5])):
            with self.subTest(name=name):
                fig,ax=azl.subplots();contour=ax.contour([-54,-49,-44],[-26,-22,-18],z,levels=levels)
                self.assertEqual(cases[name]['status'],'accepted')
                self.assertEqual([len(group) for group in contour.allsegs],cases[name]['segments'])
                self.assertEqual(contour.clabel(),[]);azl.close(fig)
        for name in ('duplicate-levels','nonfinite-level'):
            with self.subTest(name=name):self.assertEqual(cases[name]['status'],'rejected')

    def test_holes_labels_shared_norm_edits_and_static_exports(self):
        for orientation in ('vertical','horizontal'):
            for dpi in (100,200):
                with self.subTest(orientation=orientation,dpi=dpi):
                    fig,ax=azl.subplots(figsize=(2.5,2.5),dpi=dpi);ax.set_extent((-54,-42,-28,-16))
                    norm=Normalize(0,4);x=[-54,-51,-48,-45,-42];y=[-28,-25,-22,-19,-16]
                    values=[[0,1,2,3,4] for _ in y];values[2][2]=None
                    contour=ax.contour(x,y,values,levels=[.5,2.5,3.5],norm=norm)
                    points=ax.scatter([-52,-44],[-26,-18],c=[.5,3.5],norm=norm)
                    labels=contour.clabel(fmt='%.1f',fontsize=7,inline=True)
                    bar=fig.colorbar(contour,orientation=orientation);bar.set_label('Shared')
                    paths=contour.allsegs;extent=ax.get_extent();before=fig.to_svg()
                    contour.set(cmap='plasma',linewidths=[.4,.8],linestyles=['--',':'])
                    norm.vmax=5
                    self.assertIs(bar.norm,points.norm);self.assertEqual(contour.get_clim(),(0,5))
                    self.assertEqual(contour.allsegs,paths);self.assertEqual(ax.get_extent(),extent)
                    self.assertNotEqual(before,fig.to_svg());self.assertIn('Shared',fig.to_svg())
                    for label in labels:self.assertEqual(label.get_color(),contour._level_color(contour.levels.index(label.options['contour_level'])))
                    stream=io.BytesIO();render_png(fig.to_scene(),stream);self.assertGreater(len(stream.getvalue()),100)
                    contour.remove();fig.canvas.draw();self.assertTrue(all(label.get_figure() is None for label in labels))
                    contour.set_color('black');self.assertFalse(fig.stale)
                    azl.close(fig)


if __name__=='__main__':unittest.main()

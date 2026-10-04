import io,json,math,unittest
from pathlib import Path as FilePath
import azimlib as az
from azimlib.colors import Normalize,LogNorm,TwoSlopeNorm,BoundaryNorm,ListedColormap
from azimlib.cm import ScalarMappable
from azimlib.scene import Path,Rect,Text,Scene,Circle
from azimlib.hatches import add_hatches
from azimlib.fields import contour_segments,grid_data,hillshade
from azimlib.renderers import render_png

class ScientificTests(unittest.TestCase):
    def tearDown(self):az.close('all')
    def test_colorbar_layout_matches_installed_matplotlib_reference(self):
        from azimlib.colorbar_render import colorbar_layout
        reference=json.loads((FilePath(__file__).resolve().parents[1]/'docs/colorbar-layout-reference.json').read_text())
        for case in reference['cases']:
            fig,ax=az.subplots();bar=fig.colorbar(ScalarMappable(Normalize(0,2.2)),ax=ax,location=case['location'])
            mapbox,barbox=colorbar_layout(bar,reference['parent_box'])
            for actual,expected in zip(barbox,case['box']):self.assertAlmostEqual(actual,expected,places=8)
            for actual,expected in zip(mapbox,case['map_box']):self.assertAlmostEqual(actual,expected,places=8)
    def test_all_hatches_and_scalar_array_edits(self):
        for pattern in ('/','\\','|','-','+','x','o','O','.','*','/o','+*'):
            scene=Scene(120,120)
            add_hatches(scene,[[(0,0),(120,0),(120,120),(0,120)]],{'hatch':pattern})
            self.assertTrue(scene.items)
            if pattern=='.':self.assertTrue(all(isinstance(item,Circle) for item in scene.items))
        fig,ax=az.subplots()
        mesh=ax.imshow([[0,1],[2,3]],extent=(-50,-40,-20,-10))
        with self.assertRaises(ValueError):mesh.set_array([1])
        mesh.set_array([4,5,6,7]);self.assertEqual(mesh.get_array(),[4,5,6,7])
        vectors=ax.quiver([-45],[-15],[1],[0],C=[1])
        with self.assertRaises(ValueError):vectors.set_array([1,2])
        with self.assertRaises(ValueError):BoundaryNorm([0,1],0)
        with self.assertRaises(ValueError):ax.contour([0,1],[0,1],[[0,1],[0,1]],norm=Normalize(0,1),vmin=0)
    def test_normalizers_inverse_mask_clip_and_boundaries(self):
        for norm,values in ((Normalize(-2,3),[-2,0,3]),(LogNorm(1,1000),[1,10,1000]),(TwoSlopeNorm(0,-2,5),[-2,0,5])):
            for value in values:self.assertAlmostEqual(norm.inverse(norm(value)),value)
            self.assertIsNone(norm(float('nan')))
        self.assertEqual(Normalize(0,1,clip=True)([-1,.5,2]),[0,.5,1])
        self.assertEqual(Normalize()([2,4]),[0,1])
        norm=BoundaryNorm([0,1,3],5)
        self.assertEqual(norm([-.1,0,.9,1,3]),[-1,0,0,4,5])
        self.assertEqual(LogNorm(1,100)(10),.5)
        self.assertIsNone(LogNorm(1,100)(-1))
    def test_colorbar_edits_track_mappable_and_all_locations(self):
        fig,ax=az.subplots()
        layer=ax.scatter([-50,-40],[-20,-10],c=[0,2],cmap='viridis')
        bar=fig.colorbar(layer,ax=ax,label='Intensity',ticks=[0,1,2])
        before=fig.to_svg();layer.set_clim(0,4);self.assertNotEqual(before,fig.to_svg())
        self.assertIn('shape-rendering="crispEdges"',before)
        self.assertIs(bar.norm,layer.norm)
        layer.set_cmap('blues');self.assertIs(bar.cmap,layer.cmap)
        bar.set_ticks([0,2,4],labels=['low','middle','high'],fontsize=8)
        bar.set_label('Updated',fontsize=11,color='red');bar.ax.tick_params(direction='in',labelsize=9)
        bar.outline.set_linewidth(1.2)
        svg=fig.to_svg()
        for label in ('low','middle','high','Updated'):self.assertIn(label,svg)
        for location,orientation in (('left','vertical'),('right','vertical'),('bottom','horizontal'),('top','horizontal')):
            bar.set(location=location,orientation=orientation,extend='both',shrink=.8)
            scene=fig.to_scene();self.assertGreater(len(scene.items),260)
            for text in (i for i in scene.items if isinstance(i,Text)):
                self.assertTrue(math.isfinite(text.x+text.y))
        old=bar.norm;bar.update_normal(ScalarMappable(norm=Normalize(1,9),cmap='gray'))
        self.assertIsNot(old,bar.norm);self.assertIsNone(bar._ticklabels)
        bar.set_visible(False);self.assertNotIn('Updated',fig.to_svg())
        bar.remove();self.assertIsNone(ax._colorbar)
    def test_discrete_colorbar_and_standalone_mapping(self):
        fig,ax=az.subplots()
        m=ScalarMappable(BoundaryNorm([0,1,4],2),ListedColormap(['#ffffff','#000000']))
        bar=fig.colorbar(m,ax=ax,spacing='proportional',drawedges=True)
        self.assertEqual(bar.get_ticks(),(0,1,4))
        self.assertIn('#000000',fig.to_svg())
        with self.assertRaises(ValueError):ax.colorbar(m,orientation='horizontal',location='right')
        with self.assertRaises(ValueError):bar.set_ticks([0,1],labels=['one'])
    def test_hatches_density_six_patterns_and_polygon_hole(self):
        outer=[(0,0),(120,0),(120,120),(0,120)]
        hole=[(40,40),(80,40),(80,80),(40,80)]
        for char in ('/','\\','x','.','-','|'):
            scene=Scene(120,120);add_hatches(scene,[outer,hole],{'hatch':char*4,'hatch_spacing':12})
            self.assertGreater(len(scene.items),0)
            for line in [line for item in scene.items if isinstance(item,Path) for line in item.paths]:
                for a,b in zip(line,line[1:]):
                    x,y=(a[0]+b[0])/2,(a[1]+b[1])/2
                    self.assertFalse(40<x<80 and 40<y<80)
        sparse=Scene(120,120);dense=Scene(120,120)
        add_hatches(sparse,[outer],{'hatch':'/'});add_hatches(dense,[outer],{'hatch':'////'})
        self.assertGreater(len(dense.items[0].paths),len(sparse.items[0].paths)*3)
    def test_contour_topology_and_terrain_light(self):
        x,y,z=grid_data([0,1,2],[0,1,2],[[0,1,2]]*3)
        lines=contour_segments(x,y,z,.5)
        self.assertEqual(len(lines),1)
        self.assertTrue(all(abs(p[0]-.5)<1e-12 for p in lines[0]))
        self.assertEqual({p[1] for p in lines[0]},{0,1,2})
        light=hillshade([[1,1],[1,1]],altdeg=30)
        self.assertAlmostEqual(light[0][0],.5)
        self.assertLess(hillshade([[0,10],[0,10]],azdeg=90,altdeg=30)[0][0],.5)
    def test_mesh_contour_vector_scene_exports(self):
        fig,ax=az.subplots(projection='mercator')
        mesh=ax.imshow([[0,1],[2,3]],extent=(-50,-40,-20,-10),origin='lower')
        ax.contour([-50,-45,-40],[-20,-15,-10],[[0,1,2]]*3,levels=[.5,1.5],colors='black')
        ax.quiver([-48,-43],[-18,-13],[1,0],[0,1])
        fig.colorbar(mesh,label='Value')
        output=io.BytesIO();render_png(fig.to_scene(),output)
        self.assertTrue(output.getvalue().startswith(b'\x89PNG'))
        before=fig.to_svg();mesh.set_clim(0,6);self.assertNotEqual(before,fig.to_svg())
    def test_label_priorities_across_layers_and_alternate_positions(self):
        fig,ax=az.subplots();ax.set_extent((-10,10,-10,10))
        def point(name,priority):return {'type':'Feature','properties':{'name':name,'priority':priority},'geometry':{'type':'Point','coordinates':[0,0]}}
        ax.labels(point('low',0),offsets=[(0,0)])
        ax.labels(point('high',10),offsets=[(0,0)])
        texts=[i.text for i in fig.to_scene().items if isinstance(i,Text)]
        self.assertIn('high',texts);self.assertNotIn('low',texts)
        ax.clear();ax.set_extent((-10,10,-10,10))
        ax.labels({'type':'FeatureCollection','features':[point('first',1),point('second',0)]})
        texts=[i for i in fig.to_scene().items if isinstance(i,Text) and i.text in ('first','second')]
        self.assertEqual(len(texts),2);self.assertNotEqual((texts[0].x,texts[0].y),(texts[1].x,texts[1].y))

if __name__=='__main__':unittest.main()

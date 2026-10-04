import unittest
import azimlib as az
from azimlib.scene import Text,Path
from azimlib.components import MapComponent
from azimlib.navigation import viewport_from_metadata

class OrnamentTests(unittest.TestCase):
    def setUp(self):
        self.fig,self.ax=az.subplots(figsize=(8,7))
        self.ax.set_extent((-60,-40,-30,-10))
    def tearDown(self):az.close('all')

    def test_components_visibility_and_removal(self):
        for make,slot in ((self.ax.scale_bar,'_scale_bar'),(self.ax.compass,'_compass'),
                          (self.ax.north_arrow,'_north'),(self.ax.overview,'_overview')):
            component=make()
            self.assertIsInstance(component,MapComponent)
            visible=self.fig.to_svg()
            component.set_visible(False)
            hidden=self.fig.to_svg()
            self.assertNotEqual(visible,hidden)
            self.assertFalse(component.get_visible())
            component.set_visible(True)
            self.assertEqual(visible,self.fig.to_svg())
            component.remove();self.assertIsNone(getattr(self.ax,slot))

    def test_titles_and_figure_text_visibility_preserve_content(self):
        artists=[self.ax.set_title('Hidden title'),self.ax.set_xlabel('Hidden x'),
                 self.ax.set_ylabel('Hidden y'),self.ax.subtitle('Hidden subtitle'),
                 self.fig.text(.5,.95,'Hidden figure'),self.fig.suptitle('Hidden suptitle')]
        for artist in artists:artist.set_visible(False)
        self.assertNotIn('Hidden',self.fig.to_svg())
        self.assertEqual(self.ax.get_title(),'Hidden title')
        for artist in artists:artist.set_visible(True)
        for artist in artists:self.assertIn(artist.get_text(),self.fig.to_svg())

    def test_legend_title_optional_and_independent_visibility(self):
        line,=self.ax.plot([-55,-45],[-25,-15],label='Route')
        legend=self.ax.legend()
        self.assertIsNone(legend['title'])
        line.set_visible(False)
        self.assertIn('Route',self.fig.to_svg())
        legend.set_visible(False);self.assertNotIn('Route',self.fig.to_svg())
        legend.remove();self.assertIsNone(self.ax.get_legend())

    def test_scale_and_legend_share_frame(self):
        self.ax.plot([-55,-45],[-25,-15],label='Route')
        self.ax.legend();self.ax.scale_bar()
        frames=[p for p in self.fig.to_scene().items if isinstance(p,Path) and p.closed and p.style.get('opacity')==.8]
        self.assertEqual(len(frames),2)
        self.assertEqual(frames[0].style,frames[1].style)

    def test_scale_endpoint_labels_fit_inside_frame(self):
        from azimlib.typography import text_width
        self.ax.map('brazil');self.ax.scale_bar()
        scene=self.fig.to_scene();meta=scene.maps[0]
        items=scene.items[meta['decoration_start']:meta['decoration_end']]
        frame=next(i for i in items if isinstance(i,Path) and i.closed)
        left=min(x for x,y in frame.paths[0]);right=max(x for x,y in frame.paths[0])
        for text in (i for i in items if isinstance(i,Text)):
            half=text_width(text.text,text.style)/2
            self.assertGreaterEqual(text.x-half,left)
            self.assertLessEqual(text.x+half,right)

    def test_grid_visibility_keeps_coordinate_labels(self):
        grid=self.ax.grid(step=5)
        labels=lambda:[i.text for i in self.fig.to_scene().items if isinstance(i,Text)]
        before=labels();grid.set_visible(False)
        self.assertEqual(labels(),before)

    def test_grid_optional_toggle_and_paint_order(self):
        self.assertFalse(any(l.kind=='grid' for l in self.ax.layers))
        polygon=self.ax.polygon([(-59,-29),(-41,-29),(-41,-11),(-59,-11)])
        line=self.ax.line([(-55,-25),(-45,-15)])
        grid=self.ax.grid(step=5,color='red')
        self.assertLess(polygon.zorder,grid.zorder)
        self.assertLess(grid.zorder,line.zorder)
        self.ax.grid();self.assertFalse(any(l.kind=='grid' for l in self.ax.layers))
        grid=self.ax.grid();self.assertEqual(grid.style['color'],'red')
        self.ax.set_axisbelow(True);self.assertLess(grid.zorder,polygon.zorder)
        self.ax.set_axisbelow(False);self.assertGreater(grid.zorder,line.zorder)
        self.ax.grid(False)
        with az.rc_context({'axes.grid':True}):
            fig,ax=az.subplots();self.assertTrue(any(l.kind=='grid' for l in ax.layers))
        self.ax.clear();self.assertFalse(any(l.kind=='grid' for l in self.ax.layers))

    def test_scale_editable_validated_and_correct_at_each_anchor(self):
        from azimlib.scene import Rect
        from azimlib.geometry import haversine
        scale=self.ax.scale_bar()
        scale.set(length=100,units='mi',loc='upper right',fontsize=11,facecolor='#eeeeee')
        self.assertEqual(scale.get_length(),100)
        self.assertEqual(scale.get_units(),'mi')
        before=dict(scale)
        for invalid in ({'units':'bad'},{'length':-1},{'fontsize':0},{'framealpha':2},{'unknown':1}):
            with self.assertRaises((ValueError,TypeError)):scale.set(**invalid)
            self.assertEqual(dict(scale),before)
        for loc in ('upper right','upper left','lower right','lower left'):
            scale.set_loc(loc)
            scene=self.fig.to_scene();meta=scene.maps[0]
            bars=[i for i in scene.items[meta['decoration_start']:meta['decoration_end']] if isinstance(i,Rect)]
            self.assertEqual(len(bars),2)
            vp=viewport_from_metadata(self.ax.projection,meta)
            start=vp.inverse(bars[0].x,bars[0].y)
            end=vp.inverse(bars[-1].x+bars[-1].width,bars[-1].y)
            self.assertAlmostEqual(haversine(start,end)/1609.344,100,places=6)

    def test_legend_polygon_and_text_centers_match(self):
        from azimlib.scene import Rect
        self.ax.polygon([(-59,-29),(-41,-29),(-41,-11)],label='São Paulo')
        self.ax.legend()
        scene=self.fig.to_scene()
        text=next(i for i in scene.items if isinstance(i,Text) and i.text=='São Paulo')
        rect=next(i for i in reversed(scene.items) if isinstance(i,Rect))
        self.assertAlmostEqual(rect.y+rect.height/2,text.y)
        self.assertEqual(text.style['baseline'],'middle')

    def test_colorbar_visibility_restores_map_area(self):
        data={'type':'Feature','properties':{},'geometry':{'type':'Polygon','coordinates':[[[-55,-25],[-45,-25],[-45,-15],[-55,-15],[-55,-25]]]}}
        layer=self.ax.choropleth(data,[1])
        bar=self.ax.colorbar(layer,label='Index')
        self.assertIn('Index',self.fig.to_svg())
        bar.set_visible(False);self.assertNotIn('Index',self.fig.to_svg())
        bar.remove();self.assertIsNone(self.ax._colorbar)

    def test_hidden_axes_and_insets_do_not_render(self):
        child=self.ax.inset();child.set_title('Inset')
        self.assertIn('Inset',self.fig.to_svg())
        child.set_visible(False);self.assertNotIn('Inset',self.fig.to_svg())
        self.ax.set_visible(False);self.assertEqual(self.fig.to_scene().maps,[])

    def test_remove_detaches_text_and_inset(self):
        title=self.ax.set_title('Title');title.remove();self.assertIsNone(self.ax._title)
        text=self.fig.text(.5,.5,'Text');text.remove();self.assertEqual(self.fig._texts,[])
        child=self.ax.inset();child.remove();self.assertEqual(self.ax.insets,[])

    def test_native_locator_hit_test_repositions_and_records_history(self):
        from types import SimpleNamespace
        from azimlib.backends.tk import FigureWindow
        from azimlib.navigation import Navigation
        self.ax.state('SP');self.ax.overview(context='brazil')
        viewer=object.__new__(FigureWindow)
        viewer.figure=self.fig;viewer.scene=self.fig.to_scene()
        viewer.navigation=Navigation(self.fig);viewer.active=0;viewer.draw_idle=lambda:None
        viewer._draw_overview()
        index,x,y,w,h,vp=viewer._overview_box[0]
        viewer._overview_click(SimpleNamespace(x=x+w/2,y=y+h/2))
        self.assertEqual(viewer.navigation.index,1)
        center=vp.inverse(x+w/2,y+h/2)
        west,east,south,north=self.ax.get_extent()
        self.assertAlmostEqual((west+east)/2,center[0])
        self.assertAlmostEqual((south+north)/2,center[1])

    def test_compass_cardinal_symmetry_and_arrow_proportions(self):
        self.ax.compass(size=36)
        scene=self.fig.to_scene()
        labels={i.text:i for i in scene.items if isinstance(i,Text) and i.text in ('N','S','E','W')}
        self.assertAlmostEqual(labels['N'].x,labels['S'].x)
        self.assertAlmostEqual(labels['E'].y,labels['W'].y)
        self.assertAlmostEqual(labels['S'].y-labels['N'].y,labels['E'].x-labels['W'].x)
        self.ax.north_arrow(size=36)
        scene=self.fig.to_scene();m=scene.maps[0]
        points=[point for item in scene.items[m['decoration_start']:m['decoration_end']] if isinstance(item,Path) and abs(item.style.get('stroke_width',0)-.65*100/72)<1e-9 for ring in item.paths for point in ring]
        width=max(p[0] for p in points)-min(p[0] for p in points)
        height=max(p[1] for p in points)-min(p[1] for p in points)
        self.assertGreater(width/height,.8)

    def test_state_aliases_and_geographic_fit(self):
        a=az.datasets.state('SP');b=az.datasets.state('São Paulo');c=az.datasets.state('BR-SP')
        self.assertEqual(a,b);self.assertEqual(b,c)
        self.assertEqual(len(a['features']),1)
        layer=self.ax.state('SP')
        self.assertEqual(len(layer.data),1)
        w,e,s,n=self.ax.get_extent()
        self.assertTrue(-54<w<e<-43 and -26<s<n<-19)
        with self.assertRaises(ValueError):az.datasets.state('not-a-state')

    def test_locator_context_and_current_focus_survive_zoom_and_dpi(self):
        self.ax.state('SP')
        self.ax.overview(context='brazil')
        first=self.fig.to_scene();mini=first.maps[0]['overview_map']
        self.assertEqual(len(first.maps),1)
        self.assertLess(mini['focus_box'][2],mini['box'][2]/2)
        self.assertEqual(len(mini['shade_indices']),4)
        self.assertEqual(first.items[mini['focus_index']].style['stroke'],'black')
        vp=viewport_from_metadata(self.ax.projection,mini)
        p=vp.project(-47,-23)
        self.assertAlmostEqual(vp.inverse(*p)[0],-47)
        self.ax.zoom(2)
        second=self.fig.to_scene().maps[0]['overview_map']
        self.assertAlmostEqual(second['focus_box'][2],mini['focus_box'][2]/2)
        self.assertEqual(second['extent'],mini['extent'])
        self.fig.dpi=200
        third=self.fig.to_scene().maps[0]['overview_map']
        self.assertAlmostEqual(third['box'][2],second['box'][2]*2)
        self.assertIn('overview_map',self.fig.to_html())

if __name__=='__main__':unittest.main()

"""Meaningful view-state tests shared by the native viewer."""
import io
import json
import re
import tempfile
from pathlib import Path
import unittest
import azimlib as az
from azimlib.navigation import Navigation,drag_extent,zoom_extent,viewport_from_metadata


class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.fig,self.ax=az.subplots()
        self.ax.set_extent((-60,-40,-30,-10))

    def tearDown(self):az.close('all')

    def test_history_home_back_forward_and_branch(self):
        nav=Navigation(self.fig)
        self.ax.zoom(2);nav.push()
        second=self.ax.get_extent()
        self.ax.pan(2,0);nav.push()
        self.assertTrue(nav.back());self.assertEqual(self.ax.get_extent(),second)
        self.assertTrue(nav.forward())
        nav.home();self.assertEqual(self.ax.get_extent(),(-60.,-40.,-30.,-10.))
        nav.back();self.ax.zoom(2);nav.push()
        self.assertFalse(nav.forward())

    def test_zoom_cursor_anchor_and_pan(self):
        extent=zoom_extent(self.ax,2,(-55,-25))
        self.assertEqual(extent,(-57.5,-47.5,-27.5,-17.5))
        meta=self.fig.to_scene().maps[0]
        vp=viewport_from_metadata(self.ax.projection,meta)
        x,y,w,h=vp.box
        extent=drag_extent(self.ax,vp,(x+w/2,y+h/2),(x+w*.6,y+h/2),mode='pan')
        self.assertAlmostEqual(extent[0],-62,places=7)
        extent=drag_extent(self.ax,vp,(x+w*.25,y+h*.25),(x+w*.75,y+h*.75),mode='zoom')
        for value,expected in zip(extent,(-55,-45,-25,-15)):
            self.assertAlmostEqual(value,expected,places=7)

    def test_components_opt_in_and_canvas_matches_reference_margins(self):
        self.assertIsNone(self.ax._overview)
        self.assertIsNone(self.ax._legend)
        self.assertIsNone(self.ax._scale_bar)
        self.assertIsNone(self.ax._north)
        self.assertIsNone(self.ax._colorbar)
        self.assertFalse(any(l.kind=='grid' for l in self.ax.layers))
        self.assertEqual(self.ax.position,(.125,.10999999999999999,.775,.77))
        html=self.fig.to_html()
        meta=json.loads(re.search(r'<script id="map-data" type="application/json">(.*?)</script>',html,re.S).group(1))
        self.assertIs(meta[0]['overview'],False)
        self.assertIn('id="overview" aria-label="Visão geral do mapa" hidden',html)
        self.ax.overview();self.assertTrue(self.fig.to_scene().maps[0]['overview'])

    def test_savefig_is_static_show_browser_is_explicit(self):
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/'figure.html'
            with self.assertRaisesRegex(ValueError,'static'):self.fig.savefig(file)
            with self.assertRaisesRegex(ValueError,'backend'):self.fig.show(path=file)
            self.fig.show(backend='browser',open_browser=False,path=file)
            self.assertIn('Figure navigation',file.read_text(encoding='utf-8'))
            svg=Path(folder)/'figure.svg';self.fig.savefig(svg)
            self.assertNotIn('toolbar',svg.read_text(encoding='utf-8'))
            self.assertNotIn('<script',svg.read_text(encoding='utf-8'))

    def test_canvas_events_before_viewer_and_artist_setters(self):
        cid=self.fig.canvas.mpl_connect('button_press_event',lambda e:None)
        self.assertIn(cid,self.fig.canvas._callbacks)
        self.fig.canvas.mpl_disconnect(cid)
        self.assertNotIn(cid,self.fig.canvas._callbacks)
        line,=self.ax.plot([-55,-45],[-25,-15],'r--')
        line.set_color('blue');line.set_linewidth(3);line.set_label('Route')
        self.assertEqual(line.get_color(),'blue')
        self.assertEqual(line.get_linewidth(),3)
        self.assertEqual(line.get_label(),'Route')

    def test_partial_subplot_adjustment_preserves_other_settings(self):
        self.fig.subplots_adjust(left=.2)
        self.fig.subplots_adjust(bottom=.2)
        self.assertEqual(self.ax.position[0],.2)
        self.assertAlmostEqual(self.ax.position[1],.2)
        previous=self.ax.position
        with self.assertRaises(ValueError):self.fig.subplots_adjust(right=.1)
        self.assertEqual(self.ax.position,previous)
        self.assertEqual(self.fig.subplotpars['right'],.9)

    def test_dpi_scales_fonts_geometry_and_cursor_together(self):
        from azimlib.scene import Text
        self.ax.set_title('DPI')
        first=self.fig.to_scene()
        self.fig.dpi=200
        second=self.fig.to_scene()
        self.assertEqual(second.width,first.width*2)
        title1=next(item for item in first.items if isinstance(item,Text) and item.text=='DPI')
        title2=next(item for item in second.items if isinstance(item,Text) and item.text=='DPI')
        self.assertEqual(title2.style['font_size'],title1.style['font_size']*2)
        for scene in (first,second):
            vp=viewport_from_metadata(self.ax.projection,scene.maps[0])
            point=vp.project(-50,-20)
            coord=vp.inverse(*point)
            self.assertAlmostEqual(coord[0],-50)
            self.assertAlmostEqual(coord[1],-20)

    def test_release_callback_fires_without_navigation_tool(self):
        from types import SimpleNamespace
        from azimlib.backends.tk import FigureWindow
        viewer=object.__new__(FigureWindow)
        viewer.figure=self.fig
        viewer.scene=self.fig.to_scene()
        viewer.drag=None
        viewer.widget=SimpleNamespace(delete=lambda tag:None)
        viewer._event_callbacks={}
        viewer._callback_id=0
        events=[]
        viewer.mpl_connect('button_release_event',events.append)
        x,y,w,h=viewer.scene.maps[0]['box']
        viewer.release(SimpleNamespace(x=x+w/2,y=y+h/2,num=1))
        self.assertEqual(len(events),1)
        self.assertIs(events[0].inaxes,self.ax)
        self.assertAlmostEqual(events[0].xdata,-50)
        self.assertAlmostEqual(events[0].ydata,-20)


if __name__=='__main__':unittest.main()

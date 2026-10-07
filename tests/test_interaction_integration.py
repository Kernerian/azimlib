"""Picking, opt-in controls, owner-thread bridge and independent integration contracts."""
import io,json,math,threading,unittest,urllib.request,urllib.error
from types import SimpleNamespace
from unittest.mock import Mock
import azimlib as azl
from azimlib.geometry import Geometry,Feature,FeatureCollection
from azimlib.widgets import Slider,CheckButtons,LayerControl,RectangleSelector
from azimlib.interaction import Interaction
from azimlib.simplify import simplify_path,simplify_boundaries,SimplificationCache,simplify_indices
from azimlib.transforms import Affine2D

class PickingTests(unittest.TestCase):
    def setUp(self):self.fig,self.ax=azl.subplots(figsize=(4,3));self.ax.set_extent((-2,2,-2,2))
    def tearDown(self):azl.close('all')
    def event(self,lon=0,lat=0,dx=0,dy=0):
        scene=self.fig.canvas.draw();self.scene=scene
        from azimlib.navigation import viewport_from_metadata
        vp=viewport_from_metadata(self.ax.projection,scene.maps[0]);x,y=vp.project(lon,lat)
        return SimpleNamespace(canvas=self.fig.canvas,x=x+dx,y=scene.height-y+dy,inaxes=self.ax)
    def test_scatter_indices_and_callback_pixel_coordinates(self):
        layer=self.ax.scatter([0,1],[0,1],s=[36,36]);layer.set_picker(2);events=[];self.fig.canvas.mpl_connect('pick_event',events.append)
        self.fig.canvas.pick(self.event());self.assertEqual(events[0].ind,[0]);self.assertIs(events[0].artist,layer)
        self.assertEqual(layer.contains(self.event(1,1))[1]['ind'],[1])
    def test_line_tolerance_fixed_pixels_across_dpi(self):
        layer=self.ax.line([(-1,0),(1,0)],linewidth=1);layer.set_pickradius(3)
        for dpi in (100,200):
            self.fig.set_dpi(dpi);self.assertTrue(layer.contains(self.event(dy=2))[0]);self.assertFalse(layer.contains(self.event(dy=10))[0])
    def test_polygon_holes_ids_and_no_false_interior(self):
        g=Geometry('Polygon',[[(-1,-1),(1,-1),(1,1),(-1,1),(-1,-1)],[(-.3,-.3),(-.3,.3),(.3,.3),(.3,-.3),(-.3,-.3)]])
        f=Feature(g,{'name':'region'},'region');layer=self.ax.geojson(FeatureCollection([f]),facecolor='white',edgecolor='black');layer.set_pickradius(0)
        self.assertFalse(layer.contains(self.event())[0]);hit,props=layer.contains(self.event(.7,0));self.assertTrue(hit);self.assertEqual(props['features'][0].id,'region')
    def test_hidden_removed_and_custom_picker(self):
        layer=self.ax.scatter([0],[0]);layer.set_picker(lambda a,e:(True,{'ind':[7]}));events=[];self.fig.canvas.mpl_connect('pick_event',events.append)
        self.fig.canvas.pick(self.event());self.assertEqual(events[-1].ind,[7]);layer.set_visible(False);self.fig.canvas.pick(self.event());self.assertEqual(len(events),1)
        layer.remove();self.fig.canvas.pick(self.event());self.assertEqual(len(events),1)
    def test_invalid_picker_preserves_state(self):
        layer=self.ax.scatter([0],[0]);layer.set_picker(True)
        for value in (-1,float('nan'),float('inf')):
            with self.assertRaises(ValueError):layer.set_picker(value)
            self.assertIs(layer.get_picker(),True)
    def test_inset_pick_and_projection_bearing(self):
        child=self.ax.inset_axes((.5,.5,.4,.4));child.set_extent((-1,1,-1,1));p=child.scatter([0],[0]);p.set_picker(True)
        self.ax.set_bearing(35);scene=self.fig.canvas.draw();controller=Interaction(self.fig.canvas);self.fig.canvas.scene=scene
        meta=next(m for m in scene.maps if m['inset']);x,y,w,h=meta['box'];event=controller.event('button_press_event',x+w/2,y+h/2,button=1)
        self.assertIs(event.inaxes,child);self.assertTrue(p.contains(event)[0])
    def test_picking_same_data_distinct_layer_identity(self):
        a=self.ax.scatter([0],[0]);b=self.ax.scatter([0],[0]);a.set_picker(True);b.set_picker(True);events=[];self.fig.canvas.mpl_connect('pick_event',events.append)
        self.fig.canvas.pick(self.event());self.assertEqual([id(e.artist) for e in events],[id(a),id(b)])

    def test_individual_artist_pick_does_not_dispatch_other_layers(self):
        a=self.ax.scatter([0],[0]);b=self.ax.scatter([0],[0]);a.set_picker(True);b.set_picker(True)
        events=[];self.fig.canvas.mpl_connect('pick_event',events.append)
        a.pick(self.event());self.assertEqual(len(events),1);self.assertIs(events[0].artist,a)

class WidgetTests(unittest.TestCase):
    def setUp(self):self.fig,self.ax=azl.subplots(figsize=(5,3));self.ax.set_extent((-2,2,-2,2));self.box=self.fig.add_axes((.1,.02,.7,.08))
    def tearDown(self):azl.close('all')
    def test_slider_clamp_step_callbacks_and_no_static_ui(self):
        slider=Slider(self.box,'Value',0,10,3,valstep=2);values=[];slider.on_changed(values.append)
        slider.set_val(9);self.assertEqual(slider.val,8);slider.set_val(100);self.assertEqual(slider.val,10);self.assertEqual(values,[8,10])
        self.assertFalse(any(getattr(i,'text',None)=='Value' for i in self.fig.to_scene().items))
        self.assertTrue(any(getattr(i,'text',None)=='Value' for i in self.fig.to_scene(interactive=True).items))
        slider.eventson=False;slider.set_val(2);self.assertEqual(values,[8,10])
        with self.assertRaises(ValueError):slider.set_val(float('nan'))
        self.assertEqual(slider.val,2)
    def test_slider_press_drag_lost_button_and_reset(self):
        slider=Slider(self.box,'Value',0,10,5);slider.drawon=False;canvas=self.fig.canvas;controller=Interaction(canvas);canvas.scene=canvas.draw();x,y,w,h=slider._box(self.fig.dpi)
        controller.event('button_press_event',x+w*.85,y+h*.5,button=1);self.assertEqual(slider.val,10)
        controller.event('motion_notify_event',x+w*.15,y+h*.5,buttons=[]);self.assertEqual(slider.val,10);slider.reset();self.assertEqual(slider.val,5)
    def test_checkbuttons_and_external_layer_changes(self):
        layer=self.ax.scatter([0],[0],label='Points');control=LayerControl(self.box,[layer]);control.drawon=False;control.set_active(0);self.assertFalse(layer.get_visible())
        layer.set_visible(True);self.fig.to_scene(interactive=True);self.assertEqual(control.get_status(),[True])
    def test_widget_requires_empty_axes_and_invalid_constructor_no_mutation(self):
        before=len(self.fig._widgets)
        with self.assertRaises(ValueError):Slider(self.box,'bad',1,1)
        self.assertEqual(before,len(self.fig._widgets))
        self.ax.scatter([0],[0])
        with self.assertRaises(ValueError):CheckButtons(self.ax,['a'])
    def test_clear_disconnects_controls_and_occupancy(self):
        slider=Slider(self.box,'Value',0,10);self.assertTrue(self.fig.canvas._callbacks)
        self.fig.clear();self.assertFalse(self.fig._widgets);self.assertFalse(self.fig.canvas._callbacks)
    def test_selector_callback_spans_and_navigation_lock(self):
        self.fig.delaxes(self.box)
        selected=[];selector=RectangleSelector(self.ax,lambda a,b:selected.append((a,b)),minspanx=5,minspany=5);selector.drawon=False
        c=Interaction(self.fig.canvas);self.fig.canvas.scene=self.fig.canvas.draw();m=self.fig.canvas.scene.maps[0];x,y,w,h=m['box']
        c.event('button_press_event',x+w*.3,y+h*.3,button=1);c.event('motion_notify_event',x+w*.7,y+h*.7,buttons=[1]);c.event('button_release_event',x+w*.7,y+h*.7,button=1)
        self.assertEqual(len(selected),1);self.assertLess(selector.extents[0],selector.extents[1])
        c.command('pan');c.event('button_press_event',x+w*.3,y+h*.3,button=1);self.assertIsNone(selector._start)

class SimplificationTests(unittest.TestCase):
    def tearDown(self):azl.close('all')
    def test_error_bound_all_input_vertices_and_endpoints(self):
        from azimlib.picking import segment_distance
        points=[(i/10,math.sin(i/20)) for i in range(1001)];indices=simplify_indices(points,.03)
        self.assertEqual((indices[0],indices[-1]),(0,1000));self.assertLess(len(indices),len(points)/2)
        for a,b in zip(indices,indices[1:]):self.assertLessEqual(max(segment_distance(p,points[a],points[b]) for p in points[a:b+1]),.03000001)
    def test_cache_scale_invalidation_capacity_and_exact_zero(self):
        from struct import pack
        packed=b''.join(pack('<2d',i/10,math.sin(i/20)) for i in range(100));cache=SimplificationCache(10000)
        a=cache.indices(packed,10,.2);self.assertEqual(a,cache.indices(packed,10,.2));self.assertEqual(cache.hits,1)
        cache.indices(packed,20,.2);self.assertEqual(cache.misses,2);self.assertLessEqual(cache.bytes,cache.max_bytes)
        self.assertEqual(simplify_path([(0,0),(1,1),(2,0)],0),((0,0),(1,1),(2,0)))
        disabled=SimplificationCache(0);disabled.indices(packed,1,.2);self.assertEqual(disabled.info()['entries'],0)
    def test_shared_boundary_reversed_exact_and_properties(self):
        shared=[(1,0),(1.01,.25),(.99,.5),(1.01,.75),(1,1)]
        a=[(0,0),*shared,(0,1),(0,0)];b=[(1,0),(2,0),(2,1),*reversed(shared),(1,0)]
        b=b[:-1] # shared already ends at the start
        fc=FeatureCollection([Feature(Geometry('Polygon',[a]),{'name':'A'},1),Feature(Geometry('Polygon',[b]),{'name':'B'},2)])
        result=simplify_boundaries(fc,Affine2D().scale(100),2)
        self.assertEqual([f.id for f in result],[1,2]);self.assertEqual(result[0].properties,fc[0].properties)
        edges=lambda f:{tuple(sorted((a,b))) for a,b in zip(f.geometry.coordinates[0],f.geometry.coordinates[0][1:])}
        common=edges(result[0])&edges(result[1]);self.assertIn(((1.,0.),(1.,1.)),common)
        self.assertEqual(len(fc[0].geometry.coordinates[0]),8)
    def test_input_invalid_or_domain_not_silently_repaired(self):
        fc=FeatureCollection([Feature(Geometry('LineString',[(0,0),(1,1)]))])
        with self.assertRaises(ValueError):simplify_boundaries(fc,Affine2D(),1)
        for v in (-1,float('nan')):
            with self.assertRaises(ValueError):simplify_path([(0,0),(1,1)],v)
    def test_render_line_simplification_opt_in_preserves_markers_and_style(self):
        fig,ax=azl.subplots();ax.set_extent((-2,2,-2,2));p=ax.line([(-1+i/100,.01*math.sin(i)) for i in range(201)])
        original=fig.to_scene();p.set_simplify(1);reduced=fig.to_scene()
        record=lambda s:sum(len(path) for owner,i,a,b in s._pick_records if owner is p for item in s.items[a:b] if hasattr(item,'paths') for path in item.paths)
        self.assertLess(record(reduced),record(original));p.set_linestyle('--');self.assertEqual(record(fig.to_scene()),record(original))
        polygon=ax.geojson(FeatureCollection([Feature(Geometry('Polygon',[[(0,0),(1,0),(1,1),(0,0)]]))]))
        with self.assertRaises(TypeError):polygon.set_simplify(1)

class CircleCoverageTests(unittest.TestCase):
    def test_disk_square_integral_quadrants_area_and_translated_phase(self):
        from azimlib.renderers._circle_coverage import disk_area
        for r,cx,cy in ((.3,.12,.78),(1.,0.,0.),(2.35,.41,.83),(7.8,.25,.5)):
            lo=math.floor(-r-1);hi=math.ceil(r+2)
            area=sum(disk_area(x-cx,y-cy,x+1-cx,y+1-cy,r) for x in range(lo,hi) for y in range(lo,hi))
            self.assertAlmostEqual(area,math.pi*r*r,places=9)
        self.assertAlmostEqual(disk_area(0,0,1,1,1),math.pi/4,places=12)
    def test_preview_cache_phase_reuse_preserves_exact_settled_frames(self):
        from azimlib.scene import Scene,Circle
        from azimlib.renderers import render_image
        from azimlib.renderers._tile_cache import TileCache
        scene=Scene(100,100,None)
        for i in range(100):scene.add(Circle(5+(i%10)*8+.123,5+(i//10)*8+.41,1.5,dict(fill='#248bb880',stroke='black',stroke_width=.5)))
        cache=TileCache(max_entries=512);preview=render_image(scene,_interactive=True,_tile_cache=cache)
        self.assertGreater(cache.hits,90);self.assertLessEqual(cache.bytes,16*1024*1024)
        exact=render_image(scene);again=render_image(scene);self.assertEqual(exact.tobytes(),again.tobytes())
        preview.close();exact.close();again.close();cache.close()
    def test_stroke_annulus_area_alpha_and_png_transparent(self):
        from azimlib.renderers._circle_coverage import disk_mask
        from PIL import Image
        from azimlib.scene import Scene,Circle
        from azimlib.renderers import render_image
        mask=disk_mask(Image,(20,20),10.25,10.5,4,inner=3)
        self.assertAlmostEqual(sum(mask.tobytes())/255,math.pi*7,delta=.03);mask.close()
        scene=Scene(20,20,None);scene.add(Circle(10,10,3,dict(fill='#ff000080',stroke='blue',stroke_width=1)))
        image=render_image(scene);self.assertEqual(image.getpixel((10,10)),(255,0,0,128));self.assertGreater(image.getpixel((13,10))[3],0);image.close()

class AdditionalIntegrationTests(unittest.TestCase):
    def tearDown(self):azl.close('all')
    def test_feature_selection_immutable_indices_highlight_cleanup(self):
        from azimlib.widgets import FeatureSelector
        fig,ax=azl.subplots();ax.set_extent((-2,2,-2,2));layer=ax.scatter([0,1],[0,1]);calls=[];selector=FeatureSelector(ax,layer,calls.append);selector.drawon=False
        selector.set_selection([1,1]);self.assertEqual(selector.get_selection(),(1,));self.assertEqual(calls,[(1,)])
        self.assertEqual(selector.get_features(),(layer.data[1],))
        self.assertGreater(len(fig.to_scene(interactive=True).items),len(fig.to_scene().items))
        with self.assertRaises(ValueError):selector.set_selection([99])
        self.assertEqual(selector.get_selection(),(1,));selector.disconnect_events();self.assertIsNone(layer.get_picker())
    def test_static_exports_never_simplify_visual_geometry(self):
        fig,ax=azl.subplots();ax.set_extent((-2,2,-2,2));layer=ax.line([(-1+i/100,.002*math.sin(i)) for i in range(201)])
        before=fig.to_svg();layer.set_simplify(2);self.assertEqual(before,fig.to_svg())
    def test_differently_vertexized_shared_edges_fail_explicitly(self):
        a=[(0,0),(1,0),(1,.5),(1,1),(0,1),(0,0)];b=[(1,0),(2,0),(2,1),(1,1),(1,0)]
        fc=FeatureCollection([Feature(Geometry('Polygon',[a])),Feature(Geometry('Polygon',[b]))])
        with self.assertRaises(ValueError):simplify_boundaries(fc,Affine2D().scale(100),1)

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.fig,self.ax=azl.subplots(figsize=(3,2));self.ax.set_extent((-2,2,-2,2));self.ax.scatter([0],[0]);self.viewer=self.fig.show(backend='browser-live',open_browser=False)
    def tearDown(self):self.viewer.close();azl.close('all')
    def request(self,route,data=None,origin=True):
        headers={'Content-Type':'application/json'}
        if origin:headers['Origin']=self.viewer._origin
        request=urllib.request.Request(self.viewer.url+route,data=json.dumps(data).encode() if data is not None else None,headers=headers)
        return urllib.request.urlopen(request,timeout=3)
    def test_snapshots_queue_owner_events_and_callback(self):
        events=[];self.viewer.mpl_connect('button_press_event',events.append)
        with self.request('snapshot') as response:self.assertEqual(json.load(response)['revision'],1)
        m=self.viewer.scene.maps[0];x,y,w,h=m['box']
        with self.request('event',dict(op='input',name='button_press_event',x=x+w/2,y=y+h/2,button=1)) as response:self.assertEqual(response.status,202)
        self.assertFalse(events);self.viewer.flush_events();self.assertEqual(len(events),1)
    def test_reprojection_all_nine_builtins_updates_snapshot(self):
        from azimlib.viewport import _BUILTINS
        for cls in _BUILTINS:
            self.ax.set_projection(cls());self.viewer.draw_idle();self.viewer.flush_events()
            self.assertEqual(self.viewer.scene.maps[0]['projection']['name'],cls().name)
        self.assertEqual(self.viewer._revision,10)
    def test_commands_home_history_and_pan_keeps_physical_stroke(self):
        self.ax.line([(-1,0),(1,0)],linewidth=.8);self.viewer.draw();initial=self.ax.get_extent();m=self.viewer.scene.maps[0];x,y,w,h=m['box']
        self.viewer.enqueue(dict(op='command',name='pan'));self.viewer.flush_events()
        for name,xx in (('button_press_event',x+w*.5),('motion_notify_event',x+w*.6),('button_release_event',x+w*.6)):
            self.viewer.enqueue(dict(op='input',name=name,x=xx,y=y+h*.5,button=1,buttons=[1]))
        self.viewer.flush_events();self.assertNotEqual(initial,self.ax.get_extent());self.viewer.enqueue(dict(op='command',name='home'));self.viewer.flush_events();self.assertEqual(initial,self.ax.get_extent())
    def test_security_unknown_token_origin_fields_limits(self):
        for data,origin,expected in ((dict(op='command',name='pan'),False,403),(dict(op='exec',code='x'),True,400),(dict(op='input',name='motion_notify_event',x=float('nan'),y=0),True,400)):
            with self.assertRaises(urllib.error.HTTPError) as error:self.request('event',data,origin)
            self.assertEqual(error.exception.code,expected);error.exception.close()
        with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(self.viewer._origin+'/snapshot')
        error.exception.close()
        self.assertFalse(self.viewer._queue)
    def test_owner_thread_and_coalescing_queue(self):
        for i in range(1000):self.viewer.enqueue(dict(op='input',name='motion_notify_event',x=i,y=0,buttons=[]))
        self.assertEqual(len(self.viewer._queue),1);fail=[]
        def attempt():
            try:self.viewer.flush_events()
            except RuntimeError:fail.append(True)
        thread=threading.Thread(target=attempt);thread.start();thread.join();self.assertEqual(fail,[True])
    def test_resize_and_modes_are_published_with_cursor_coordinates(self):
        self.viewer.enqueue(dict(op='command',name='pan'));self.viewer.flush_events();self.assertEqual(self.viewer._snapshot['mode'],'pan')
        self.viewer.enqueue(dict(op='resize',width=400,height=300));self.viewer.flush_events();self.assertEqual(self.viewer.get_width_height(),(400,300))
        m=self.viewer.scene.maps[0];x,y,w,h=m['box'];self.viewer.enqueue(dict(op='input',name='motion_notify_event',x=x+w/2,y=y+h/2));self.viewer.flush_events()
        self.assertIn('x=',self.viewer._snapshot['coordinates'])
        with self.assertRaises(ValueError):self.viewer.enqueue(dict(op='resize',width=9999,height=200))
    def test_static_downloads_and_resources_close(self):
        with self.request('save.svg') as response:self.assertNotIn('<script',response.read().decode())
        with self.request('save.png') as response:self.assertEqual(response.read(8),b'\x89PNG\r\n\x1a\n')
        self.viewer.close();self.assertFalse(self.viewer._thread.is_alive());self.assertIsNone(self.fig._viewer)
    def test_incomplete_request_does_not_block_close(self):
        import socket,time
        sock=socket.create_connection(('127.0.0.1',self.viewer.server.server_port),timeout=3)
        try:
            sock.sendall(b'GET / HTTP/1.1\r\nHost: 127.0.0.1\r\n')
            time.sleep(.05);began=time.monotonic();self.viewer.close()
            self.assertFalse(self.viewer._thread.is_alive());self.assertLess(time.monotonic()-began,4)
        finally:sock.close()
    def test_backend_switch_fails_without_duplicate_sessions(self):
        with self.assertRaises(RuntimeError):self.fig.show(backend='tk')
        self.assertIs(self.fig.canvas,self.viewer)

class NotebookTests(unittest.TestCase):
    def tearDown(self):azl.close('all')
    def test_handle_update_hook_and_disconnect_with_public_protocol(self):
        from azimlib.backends.notebook import NotebookCanvas
        from azimlib.backends._common import attach
        fig,ax=azl.subplots();shell=SimpleNamespace(events=Mock());handle=Mock();display=Mock(return_value=handle)
        c=NotebookCanvas(fig,shell,display);attach(fig,c);c.start();self.assertEqual(display.call_count,1)
        ax.set_title('updated');c._hook(None);self.assertEqual(handle.update.call_count,1);c.flush_events();self.assertEqual(handle.update.call_count,1)
        c.close();shell.events.unregister.assert_called_once_with('post_run_cell',c._hook);self.assertIsNone(fig._viewer)
    def test_projection_invalid_atomic_and_shared_guard(self):
        fig,ax=azl.subplots();before=ax.projection
        with self.assertRaises(ValueError):ax.set_projection('not-a-projection')
        self.assertEqual(before,ax.projection);fig.add_subplot(122,sharex=ax)
        with self.assertRaises(ValueError):ax.set_projection('mercator')

if __name__=='__main__':unittest.main()

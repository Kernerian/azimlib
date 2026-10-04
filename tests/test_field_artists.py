"""Own editable field handles, compared with a development-only oracle."""
import io
import json
import math
from pathlib import Path
import unittest
import azimlib as azl
from azimlib.colors import Normalize
from azimlib.scene import Path as ScenePath

class FieldArtistTests(unittest.TestCase):
    def tearDown(self):azl.close('all');azl.ioff()
    def reference(self):return json.loads((Path(__file__).resolve().parents[1]/'docs/field-edits-reference.json').read_text())

    def test_image_editing_matches_installed_matplotlib(self):
        cases=[]
        for origin in ('lower','upper'):
            fig,ax=azl.subplots();image=ax.imshow([[0,1],[2,3]],extent=(-50,-40,-20,-10),origin=origin,norm=Normalize(0,3))
            ax.set_xlim(-60,-35);ax.set_ylim(-30,-5)
            def snapshot(name):
                fig.canvas.draw()
                cases.append(dict(name=name,origin=origin,data=image.get_data(),extent=list(image.get_extent()),
                                  clim=list(image.get_clim()),view=[*ax.get_xlim(),*ax.get_ylim()]))
            snapshot('initial');image.set_data([[10,20,30]]);snapshot('reshape')
            image.set_extent((-55,-40,-25,-15));snapshot('extent')
            image.autoscale();snapshot('autoscale')
        self.assertEqual(cases,self.reference()['images'])

    def test_mesh_arrays_and_coordinates_match_reference(self):
        fig,ax=azl.subplots();mesh=ax.pcolormesh([-60,-50,-40],[-30,-20,-10],[[0,1],[2,3]],norm=Normalize(0,3))
        cases=[]
        for name,values in (('matrix',[[5,10],[15,20]]),('flat',[1,2,3,4])):
            mesh.set_array(values);fig.canvas.draw()
            cases.append(dict(name=name,array=mesh.get_array(),coordinates=mesh.get_coordinates(),clim=list(mesh.get_clim())))
        self.assertEqual(cases,self.reference()['meshes'])

    def test_vector_updates_match_effective_field_reference(self):
        fig,ax=azl.subplots();vectors=ax.quiver([-52,-48,-44],[-25,-21,-19],[1,0,2],[0,1,1],[10,20,30],norm=Normalize(0,30),scale=10)
        cases=[]
        def snapshot(name):
            fig.canvas.draw();u,v,c=vectors.get_UVC()
            cases.append(dict(name=name,U=u,V=v,C=c,offsets=vectors.get_offsets(),clim=list(vectors.get_clim())))
        snapshot('initial');vectors.set_UVC([0,-1,2],[2,1,0]);snapshot('preserve-colors')
        vectors.set_UVC(2,1,5);snapshot('broadcast')
        vectors.set_offsets([[-54,-28],[-48,-21],[-43,-18]]);snapshot('move')
        self.assertEqual(cases,self.reference()['vectors'])

    def test_image_origin_and_legacy_flat_array_have_explicit_order(self):
        fig,ax=azl.subplots();image=ax.imshow([[0,1],[2,3]],extent=(-50,-40,-20,-10),origin='upper')
        self.assertEqual(image.get_data(),[[0,1],[2,3]])
        self.assertEqual(image.get_array(),[2,3,0,1])
        image.set_array([4,5,6,7]);self.assertEqual(image.get_data(),[[6,7],[4,5]])
        image.set_array([[8,9],[10,11]]);self.assertEqual(image.get_data(),[[8,9],[10,11]])
        data=image.get_data();data[0][0]=99;self.assertEqual(image.get_data()[0][0],8)

    def test_image_setp_data_extent_is_coherent_and_updates_colorbar(self):
        fig,ax=azl.subplots();image=ax.imshow([[0,1],[2,3]],extent=(-50,-40,-20,-10),origin='lower')
        bar=fig.colorbar(image);original_view=ax.get_extent();events=[]
        image.add_callback(lambda i:events.append((i.get_data(),i.get_extent(),i.get_array())))
        fig.canvas.draw();azl.setp(image,data=[[10,20,30]],extent=(-55,-40,-25,-15),alpha=.5)
        self.assertEqual(len(events),1);self.assertEqual(events[0][0],[[10,20,30]])
        self.assertEqual(image.get_array(),[10,20,30]);self.assertEqual(ax.get_extent(),original_view)
        self.assertIs(bar.mappable,image);image.autoscale();self.assertEqual(bar.norm.vmin,10);self.assertEqual(bar.norm.vmax,30)
        self.assertTrue(fig.stale);self.assertIsInstance(image,azl.ScalarImage)
        props=azl.getp(image);self.assertIn('data',props);self.assertIn('extent',props);self.assertNotIn('xdata',props)

    def test_bad_image_edits_do_not_change_data_extent_or_visibility(self):
        fig,ax=azl.subplots();image=ax.imshow([[0,1],[2,3]],extent=(-50,-40,-20,-10))
        before=(image.get_data(),image.get_extent(),image.get_array())
        bad=(dict(data=[]),dict(data=[[1],[2,3]]),dict(data=[['bad']]),dict(data=[[[1,2,3]]]),
             dict(extent=(-40,-50,-20,-10)),dict(extent=(-50,-40,-91,-10)),dict(extent=(math.nan,-40,-20,-10)),
             dict(data=[[4]],linewidth=-1),dict(data=[[4]],array=[4]),dict(array=[1]))
        for kwargs in bad:
            with self.subTest(kwargs=kwargs):
                fig.canvas.draw();events=[];cid=image.add_callback(events.append)
                with self.assertRaises((ValueError,TypeError)):image.set(visible=False,**kwargs)
                self.assertEqual((image.get_data(),image.get_extent(),image.get_array()),before)
                self.assertTrue(image.visible);self.assertFalse(fig.stale);self.assertFalse(events);image.remove_callback(cid)

    def test_mesh_shapes_none_and_missing_values_render_safely(self):
        fig,ax=azl.subplots();mesh=ax.pcolormesh([-60,-50,-40],[-30,-20,-10],[[0,1],[2,3]])
        for values in ([1],[[1,2,3],[4,5,6]],[[1],[2],[3],[4]]):
            with self.assertRaises(ValueError):mesh.set_array(values)
        mesh.set_array([[None,math.nan],[2,3]])
        scene=fig.to_scene();cells=[p for p in scene.items if isinstance(p,ScenePath) and p.closed and p.clip is not None]
        self.assertEqual(len(cells),2)
        mesh.set_array(None);self.assertFalse(any(isinstance(p,ScenePath) and p.closed and p.clip is not None for p in fig.to_scene().items))
        mesh.set_array([4,5,6,7]);self.assertIsInstance(mesh,azl.MeshCollection)
        coordinates=mesh.get_coordinates();coordinates[0][0][0]=99;self.assertEqual(mesh.get_coordinates()[0][0][0],-60)

    def test_vector_batch_updates_callbacks_and_preserves_omitted_colors(self):
        fig,ax=azl.subplots();vectors=ax.quiver([-52,-48],[-25,-21],[1,0],[0,1],C=[10,20],scale=10)
        bar=fig.colorbar(vectors);view=ax.get_extent();events=[]
        vectors.add_callback(lambda q:events.append((q.get_offsets(),q.get_UVC(),q.get_scale())))
        fig.canvas.draw()
        azl.setp(vectors,UVC=([0,2],[2,0],[30,40]),offsets=[[-54,-28],[-43,-18]],scale=20,linewidth=1)
        self.assertEqual(len(events),1);self.assertEqual(vectors.get_UVC(),([0,2],[2,0],[30,40]))
        self.assertEqual(ax.get_extent(),view);self.assertIsInstance(vectors,azl.VectorCollection)
        vectors.set_UVC(1,2);self.assertEqual(vectors.get_UVC(),([1,1],[2,2],[30,40]))
        vectors.autoscale();self.assertEqual((bar.norm.vmin,bar.norm.vmax),(30,40))
        vectors.set(array=None);self.assertIsNone(vectors.get_array())

    def test_vector_bad_updates_are_atomic(self):
        fig,ax=azl.subplots();vectors=ax.quiver([-52,-48],[-25,-21],[1,0],[0,1],C=[10,20])
        before=(vectors.get_offsets(),vectors.get_UVC(),vectors.get_scale())
        bad=(dict(UVC=([1,2,3],[1,2])),dict(UVC=([math.inf,1],[1,2])),dict(UVC=([1,2],[1,2],[1,2,3])),
             dict(offsets=[[-52,-25]]),dict(offsets=[[-52,-91],[-48,-21]]),dict(scale=0),dict(scale=math.nan),
             dict(UVC=([1,2],[1,2],[1,2]),array=[1,2]),dict(array=[1]),dict(UVC=([2,3],[3,4]),linewidth=-1))
        for kwargs in bad:
            with self.subTest(kwargs=kwargs):
                fig.canvas.draw();events=[];cid=vectors.add_callback(events.append)
                with self.assertRaises((ValueError,TypeError)):vectors.set(visible=False,**kwargs)
                self.assertEqual((vectors.get_offsets(),vectors.get_UVC(),vectors.get_scale()),before)
                self.assertTrue(vectors.visible);self.assertFalse(fig.stale);self.assertFalse(events);vectors.remove_callback(cid)

    def test_edited_vector_origins_and_image_extent_participate_in_relim(self):
        fig,ax=azl.subplots();image=ax.imshow([[1]],extent=(-50,-40,-20,-10))
        vectors=ax.quiver([-45],[-15],[1],[1]);fixed=ax.get_extent()
        image.set_extent((-60,-55,-30,-25));vectors.set_offsets([[-52,-22]])
        ax.relim();ax.autoscale_view();self.assertEqual(ax.get_extent(),fixed)
        ax.autoscale();self.assertEqual(ax.get_extent(),(-60.4,-51.6,-30.4,-21.6))

    def test_edited_fields_export_and_removed_handles_detach(self):
        fig,ax=azl.subplots();image=ax.imshow([[1,2]],extent=(-50,-40,-20,-10))
        vectors=ax.quiver([-45],[-15],[1],[1]);image.set_data([[2],[4]])
        vectors.set_UVC(0,2);fig.savefig(io.StringIO(),format='svg');fig.to_html()
        image.remove();vectors.remove();fig.canvas.draw()
        image.set_data([[3]]);vectors.set_UVC(2,0);self.assertFalse(fig.stale)

    def test_invalid_initial_field_input_does_not_attach_or_change_limits(self):
        fig,ax=azl.subplots();before=(len(ax.layers),ax._bounds,ax.get_extent())
        calls=(lambda:ax.imshow([[1,2],[3]],extent=(-50,-40,-20,-10)),
               lambda:ax.pcolormesh([-50,-40],[-20,-10],[[1]],cmap='missing'),
               lambda:ax.pcolormesh([-50,-40],[-100,-10],[[1]]),
               lambda:ax.quiver([-45],[-15],[1],[1],C=[1],norm='foreign'),
               lambda:ax.quiver([-45],[-100],[1],[1]),lambda:ax.quiver([-45],[-15],[math.inf],[1]))
        for call in calls:
            with self.assertRaises((ValueError,TypeError)):call()
            self.assertEqual((len(ax.layers),ax._bounds,ax.get_extent()),before)

    def test_prospective_invalid_normalization_does_not_partially_commit(self):
        fig,ax=azl.subplots();image=ax.imshow([[1]],extent=(-50,-40,-20,-10),norm=Normalize(0,1))
        image.norm._vmin=10;image.norm._vmax=None
        with self.assertRaises(ValueError):image.set_data([[2]])
        self.assertEqual(image.get_data(),[[1]])

    def test_empty_zero_and_broadcast_vectors_are_supported(self):
        fig,ax=azl.subplots();empty=ax.quiver([],[],[],[]);empty.set_UVC(0,0)
        self.assertEqual(empty.get_UVC(),([],[],None));fig.to_svg()
        vectors=ax.quiver([-52,-48],[-25,-21],1,0,C=2,scale=10)
        self.assertEqual(vectors.get_UVC(),([1,1],[0,0],[2,2]))
        vectors.set_UVC(0,0)
        self.assertFalse(any(isinstance(p,ScenePath) and p.clip is not None for p in fig.to_scene().items))

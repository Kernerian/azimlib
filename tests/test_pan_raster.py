"""Bounded asynchronous raster ownership and scheduling, without Tk/Pillow."""
from threading import Event,get_ident
import unittest
from unittest.mock import Mock
from azimlib.backends._pan_raster import PanRaster
from azimlib.scene import Path,Scene


class PanRasterTests(unittest.TestCase):
    def ready(self,worker,token):
        with worker._condition:
            self.assertTrue(worker._condition.wait_for(lambda:worker._ready is not None and worker._ready[0]==token,timeout=3))
        return worker.take()

    def test_worker_owns_primitive_data_and_runs_off_caller_thread(self):
        gate=Event();started=Event();observed=[];image=Mock()
        scene=Scene(20,20);points=[(1,2),(3,4)];style={'dash':[2,3]}
        scene.add(Path([points],style=style))
        def render(snapshot):
            started.set();gate.wait(3);observed.append((get_ident(),snapshot));return image
        worker=PanRaster(render)
        try:
            worker.submit(1,scene);self.assertTrue(started.wait(3))
            points[0]=(99,99);style['dash'][0]=100
            gate.set();token,original,result,error,key=self.ready(worker,1)
            self.assertNotEqual(observed[0][0],get_ident())
            self.assertEqual(observed[0][1].items[0].paths[0][0],(1,2))
            self.assertEqual(observed[0][1].items[0].style['dash'],[2,3])
            self.assertIs(original,scene);self.assertIs(result,image);self.assertIsNone(error)
            result.close()
        finally:gate.set();worker.close()

    def test_only_active_and_newest_pending_view_are_rendered(self):
        gate=Event();started=Event();calls=[];images=[]
        def render(scene):
            calls.append(scene.width)
            if scene.width==1:started.set();gate.wait(3)
            image=Mock();images.append(image);return image
        worker=PanRaster(render)
        try:
            worker.submit(1,Scene(1,1));self.assertTrue(started.wait(3))
            for token in range(2,21):worker.submit(token,Scene(token,1))
            self.assertEqual(calls,[1]);gate.set()
            result=self.ready(worker,20)
            self.assertEqual(calls,[1,20]);self.assertFalse(worker.busy())
            images[0].close.assert_called_once_with();result[2].close()
        finally:gate.set();worker.close()

    def test_invalidation_discards_active_result_and_closes_image(self):
        gate=Event();started=Event();image=Mock()
        def render(scene):started.set();gate.wait(3);return image
        worker=PanRaster(render)
        try:
            worker.submit(1,Scene(1,1));self.assertTrue(started.wait(3))
            worker.clear();gate.set()
            with worker._condition:self.assertTrue(worker._condition.wait_for(lambda:not worker._active,timeout=3))
            self.assertIsNone(worker.take());image.close.assert_called_once_with()
        finally:gate.set();worker.close()

    def test_close_does_not_wait_for_blocked_renderer_and_releases_result(self):
        gate=Event();started=Event();image=Mock()
        def render(scene):started.set();gate.wait(3);return image
        worker=PanRaster(render);worker.submit(1,Scene(1,1))
        self.assertTrue(started.wait(3));worker.close()
        self.assertFalse(gate.is_set());self.assertTrue(worker._closed)
        gate.set();worker._thread.join(3)
        self.assertFalse(worker._thread.is_alive());image.close.assert_called_once_with()

    def test_render_error_is_returned_and_worker_accepts_next_view(self):
        def render(scene):
            if scene.width==1:raise ValueError('bad frame')
            return Mock()
        worker=PanRaster(render)
        try:
            worker.submit(1,Scene(1,1));result=self.ready(worker,1)
            self.assertIsNone(result[2]);self.assertIsInstance(result[3],ValueError)
            worker.submit(2,Scene(2,1));result=self.ready(worker,2)
            self.assertIsNone(result[3]);result[2].close()
        finally:worker.close()


if __name__=='__main__':unittest.main()

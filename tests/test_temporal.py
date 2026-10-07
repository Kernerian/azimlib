"""Own temporal selection, mapping, scheduler lifecycle and complete static exports."""
import datetime as dt
import io,json,math,re,tempfile,unittest
from pathlib import Path
from unittest.mock import patch,MagicMock
import azimlib as azl
from azimlib.animation import FuncAnimation,PillowWriter,FFMpegWriter
from azimlib.temporal import TemporalSeries,Frame
from azimlib.timers import Timer
from azimlib.backends.backend_pdf import PdfPages
from azimlib.renderers.pdf import render_pdf,render_pdf_pages

class ManualTimer:
    def __init__(self):self.callbacks=[];self.running=False;self.interval=200
    def add_callback(self,func):self.callbacks.append(func)
    def remove_callback(self,func):self.callbacks.remove(func)
    def start(self):self.running=True
    def stop(self):self.running=False
    def fire(self):
        if self.running:
            for func in tuple(self.callbacks):func()

class Contracts(unittest.TestCase):
    def tearDown(self):azl.close('all')
    def image(self):
        fig,ax=azl.subplots(figsize=(1.6,1.6),dpi=50)
        im=ax.imshow([[1,2],[3,4]],extent=(-50,-46,-24,-20),origin='lower');ax.set_extent((-50,-46,-24,-20))
        return fig,ax,im
    def series(self):return TemporalSeries([2000,2010,2020],[[[1,2],[3,4]],[[10,20],[30,40]],[[None,None],[None,None]]],unit='year')
    def test_public_imports(self):
        import azimlib.pyplot as plt
        self.assertIs(plt.subplots,azl.subplots);self.assertTrue(callable(azl.animation.FuncAnimation))
    def test_series_freezes_input(self):
        values=[{'cells':[1,2]}];s=TemporalSeries([0],values,unit='hour');values[0]['cells'][0]=9
        self.assertEqual(s[0].data['cells'],(1,2))
        with self.assertRaises(TypeError):s[0].data['cells']=(9,)
        with self.assertRaises(Exception):s[0].time=4
    def test_series_slices(self):self.assertEqual(self.series()[1:].__len__(),2)
    def test_numeric_selection(self):
        s=TemporalSeries([0,10,20],[1,2,3],unit='s')
        self.assertEqual(s.index_at(5),0);self.assertEqual(s.at(6).data,2);self.assertEqual(s.index_at(-5),0);self.assertEqual(s.index_at(25),2)
    def test_exact_previous_next(self):
        s=TemporalSeries([0,10],[1,2],unit='s');self.assertEqual(s.index_at(10,method='exact'),1)
        self.assertEqual(s.index_at(4,method='previous'),0);self.assertEqual(s.index_at(4,method='next'),1)
        for t,m in ((4,'exact'),(-1,'previous'),(11,'next')):
            with self.subTest(t=t,m=m),self.assertRaises(KeyError):s.at(t,method=m)
    def test_date_timezone(self):
        t=dt.datetime(2020,1,1,tzinfo=dt.timezone(dt.timedelta(hours=-3)));s=TemporalSeries([t,dt.datetime(2020,1,2)],[1,2])
        self.assertEqual(s.unit,'UTC');self.assertEqual(s[0].time.hour,3);self.assertEqual(s.index_at(t,method='exact'),0)
    def test_numpy_bounded_frames(self):
        try:import numpy as np
        except ImportError:self.skipTest('NumPy optional')
        s=TemporalSeries(np.arange(2),np.array([[1,2],[3,4]]),unit='s');self.assertEqual(s[1].data,(3,4))
        fig,ax,im=self.image();seen=[];ani=FuncAnimation(fig,seen.append,np.arange(2),autoplay=False);ani.seek(1);self.assertIsInstance(seen[-1],int)
    def test_date_only(self):self.assertEqual(TemporalSeries([dt.date(2020,1,1)],[1])[0].time.tzinfo,dt.timezone.utc)
    def test_invalid_series(self):
        cases=[([],[],None),([0],[1],None),([0,0],[1,2],'s'),([1,0],[1,2],'s'),([math.inf],[1],'s'),([True],[1],'s'),([0,1],[1],'s')]
        for times,values,unit in cases:
            with self.subTest(times=times),self.assertRaises((ValueError,TypeError)):TemporalSeries(times,values,unit=unit)
    def test_time_kind_errors(self):
        with self.assertRaises(TypeError):TemporalSeries([dt.date(2020,1,1),2],[1,2])
        with self.assertRaises(ValueError):TemporalSeries([dt.date(2020,1,1)],[1],unit='day')
        with self.assertRaises(ValueError):self.series().at(2000,method='interpolate')
    def test_generators_not_consumed(self):
        with self.assertRaises(TypeError):TemporalSeries(iter([0]),[1],unit='s')
    def test_global_image_binding(self):
        fig,ax,im=self.image();before=im.get_clim();binding=self.series().bind(im)
        self.assertEqual(im.get_clim(),before);binding.apply(1);self.assertEqual(im.get_clim(),(1,40));self.assertEqual(im.get_data(),[[10,20],[30,40]])
    def test_frame_norm_missing_uses_global(self):
        fig,ax,im=self.image();binding=self.series().bind(im,scale='frame');binding.apply(0);self.assertEqual(im.get_clim(),(1,4))
        binding.apply(1);self.assertEqual(im.get_clim(),(10,40));binding.apply(2);self.assertEqual(im.get_clim(),(1,40))
    def test_explicit_global_norm(self):
        fig,ax,im=self.image();norm=azl.colors.Normalize(0,100);b=self.series().bind(im,norm=norm);b.apply(1)
        self.assertEqual(im.get_clim(),(0,100));self.assertIsNot(im.norm,norm)
    def test_static_identity_and_colorbar(self):
        fig,ax,im=self.image();title=ax.set_title('Static');north=ax.north_arrow();cb=fig.colorbar(im,ax=ax);extent=ax.get_extent()
        b=self.series().bind(im,scale='frame');b.apply(1);fig.to_scene();self.assertIs(cb.mappable,im)
        self.assertEqual(cb.mappable.get_clim(),(10,40));self.assertIn(im,ax.layers);self.assertEqual(ax.get_extent(),extent);self.assertEqual(title.get_text(),'Static');self.assertTrue(north.get_visible())
    def test_invalid_later_frame_no_mutation(self):
        fig,ax,im=self.image();state=(im.get_data(),im.get_clim())
        for values in ([[[1,2],[3,4]],[[5]]],[[[1,'bad'],[3,4]]]):
            with self.subTest(values=values),self.assertRaises((ValueError,TypeError)):TemporalSeries(list(range(len(values))),values,unit='s').bind(im)
        self.assertEqual((im.get_data(),im.get_clim()),state)
    def test_all_missing_binding_rejected(self):
        fig,ax,im=self.image()
        with self.assertRaises(ValueError):TemporalSeries([0],[[[None,None],[None,None]]],unit='s').bind(im)
    def test_mesh_binding(self):
        fig,ax=azl.subplots();im=ax.pcolormesh([-50,-48,-46],[-24,-22,-20],[[1,2],[3,4]])
        b=self.series().bind(im);b.apply(1);self.assertEqual(im.get_array(),[10,20,30,40])
    def test_scatter_binding(self):
        fig,ax=azl.subplots();sc=ax.scatter([-50,-48],[-24,-22],c=[1,2]);offsets=sc.get_offsets()
        b=TemporalSeries([0,1],[[1,2],[20,30]],unit='s').bind(sc);b.apply(1);self.assertEqual(sc.get_offsets(),offsets);self.assertEqual(sc.get_array(),[20,30])
    def test_surface_binding_preserves_mesh(self):
        fig,ax=azl.subplots(subplot_kw={'projection':'3d'});artist=ax.plot_surface([0,1],[0,1],[[1,2],[3,4]]);mesh=artist.mesh;camera=ax.camera
        b=TemporalSeries([0,1],[[1,2,3,4],[10,20,30,40]],unit='s').bind(artist);b.apply(1)
        self.assertIs(artist.mesh,mesh);self.assertEqual(ax.camera,camera);self.assertEqual(artist.get_array(),[10,20,30,40])
    def test_binding_removed_artist(self):
        fig,ax,im=self.image();b=self.series().bind(im);im.remove()
        with self.assertRaises(RuntimeError):b.apply(1)
    def test_binding_bad_index(self):
        fig,ax,im=self.image();b=self.series().bind(im)
        for i in (-1,3,True,1.2):
            with self.subTest(i=i),self.assertRaises(IndexError):b.apply(i)
    def test_binding_frame_shape_changed(self):
        fig,ax,im=self.image();b=self.series().bind(im);im.set_data([[1]])
        # Fixed frame shape is checked anew against a target edited elsewhere.
        with self.assertRaises(ValueError):b.apply(1)
    def test_animation_initial_and_fargs(self):
        fig,ax,im=self.image();seen=[];timer=ManualTimer();ani=FuncAnimation(fig,lambda i,p:seen.append((i,p)),3,fargs=('x',),event_source=timer,autoplay=False)
        self.assertEqual(seen,[(0,'x')]);ani.resume();timer.fire();self.assertEqual(ani.index,1);ani.pause();timer.fire();self.assertEqual(ani.index,1)
    def test_animation_repeat_and_end(self):
        fig,ax,im=self.image();ani=FuncAnimation(fig,lambda i:None,2,event_source=ManualTimer(),repeat=False)
        self.assertTrue(ani.step());self.assertFalse(ani.step());self.assertEqual(ani.index,1);ani.repeat=True;ani.step();self.assertEqual(ani.index,0)
    def test_animation_frame_payloads(self):
        fig,ax,im=self.image();seen=[];s=self.series();ani=FuncAnimation(fig,seen.append,s,autoplay=False);ani.seek(1);self.assertIs(seen[-1],s[1])
    def test_animation_bad_seek_no_update(self):
        fig,ax,im=self.image();seen=[];ani=FuncAnimation(fig,seen.append,2,autoplay=False)
        with self.assertRaises(IndexError):ani.seek(3)
        self.assertEqual(seen,[0])
    def test_animation_failure_stops_timer(self):
        fig,ax,im=self.image();timer=ManualTimer()
        def update(i):
            if i:raise ValueError('frame failed')
        ani=FuncAnimation(fig,update,2,event_source=timer);ani.resume()
        with self.assertRaises(ValueError):timer.fire()
        self.assertFalse(ani.playing);self.assertFalse(timer.running);self.assertEqual(ani.index,0)
    def test_animation_close_is_idempotent(self):
        fig,ax,im=self.image();timer=ManualTimer();ani=FuncAnimation(fig,lambda i:None,2,event_source=timer);ani.resume();ani.close();ani.close()
        self.assertFalse(timer.running);self.assertFalse(timer.callbacks)
        with self.assertRaises(RuntimeError):ani.resume()
    def test_figure_close_cleans_callbacks(self):
        fig,ax,im=self.image();ani=FuncAnimation(fig,lambda i:None,2,autoplay=False);azl.close(fig)
        self.assertTrue(ani.closed);self.assertTrue(ani.event_source._closed)
    def test_headless_no_implicit_thread(self):
        fig,ax,im=self.image();ani=FuncAnimation(fig,lambda i:None,2)
        with self.assertRaises(RuntimeError):ani.resume()
        fig.canvas.draw();self.assertFalse(ani.playing)
    def test_constructor_failure_disconnects(self):
        fig,ax,im=self.image();before=len(fig.canvas._callbacks)
        def fail(i):raise ValueError('init fail')
        with self.assertRaises(ValueError):FuncAnimation(fig,fail,2)
        self.assertEqual(len(fig.canvas._callbacks),before)
    def test_controls_seek_and_disconnect(self):
        fig,ax,im=self.image();ani=FuncAnimation(fig,lambda i:None,3,event_source=ManualTimer(),autoplay=False)
        controls=ani.add_controls(fig.add_axes((.1,.01,.6,.04)),fig.add_axes((.72,.01,.2,.04)))
        controls.slider.set_val(2);self.assertEqual(ani.index,2);controls.play.set_active(0);self.assertTrue(ani.playing)
        ani.seek(1);self.assertEqual(controls.slider.val,1);ani.close();self.assertFalse(fig._widgets)
    def test_controls_invalid_axes(self):
        fig,ax,im=self.image();ani=FuncAnimation(fig,lambda i:None,2,autoplay=False)
        with self.assertRaises(ValueError):ani.add_controls(ax)
    def test_timer_interval_and_factory(self):
        fig,ax,im=self.image();timer=fig.canvas.new_timer(10);self.assertEqual(timer.interval,10)
        for value in (0,math.nan,math.inf,86400001):
            with self.assertRaises(ValueError):timer.interval=value
        timer.close()
    def test_timer_native_protocol(self):
        fig,ax,im=self.image();queue={};canceled=[]
        class Window:
            def after(self,ms,func):token=len(queue)+1;queue[token]=func;return token
            def after_cancel(self,token):canceled.append(token)
        window=Window();timer=Timer(fig,10);timer._backend=lambda:('tk',type('Canvas',(),{'window':window})());seen=[]
        timer.add_callback(lambda:seen.append('tick'));timer.start();queue[1]();self.assertEqual(seen,['tick']);self.assertTrue(timer.running)
        timer.stop();self.assertFalse(timer.running);self.assertTrue(canceled);timer.close()
    def test_timer_single_and_restart(self):
        fig,ax,im=self.image();queue=[]
        class Window:
            def after(self,ms,func):queue.append(func);return len(queue)
            def after_cancel(self,token):pass
        timer=Timer(fig);timer._backend=lambda:('tk',type('C',(),{'window':Window()})());timer.add_callback(lambda:False);timer.start();queue[-1]();self.assertFalse(timer.running);self.assertFalse(timer.callbacks)
        timer.add_callback(lambda:None);timer.single_shot=True;timer.start();old=queue[-1];timer.stop();old();self.assertFalse(timer.running);timer.start();queue[-1]();self.assertFalse(timer.running);timer.close()
    def test_animation_interval_prevalidation(self):
        fig,ax,im=self.image();before=len(fig.canvas._callbacks)
        for interval in (0,math.nan,math.inf):
            with self.subTest(interval=interval),self.assertRaises(ValueError):FuncAnimation(fig,lambda i:None,2,event_source=ManualTimer(),interval=interval)
        self.assertEqual(len(fig.canvas._callbacks),before)
    def test_controls_second_axis_atomic(self):
        fig,ax,im=self.image();ani=FuncAnimation(fig,lambda i:None,2,autoplay=False);slider_ax=fig.add_axes((.1,.01,.6,.05))
        with self.assertRaises(ValueError):ani.add_controls(slider_ax,ax)
        self.assertFalse(fig._widgets);self.assertIsNone(getattr(slider_ax,'_widget_owner',None))
    def test_exports_are_repeatable(self):
        fig,ax,im=self.image();binding=self.series().bind(im);ani=FuncAnimation(fig,lambda i:binding.apply(i),3,autoplay=False)
        ani.seek(1,draw=False);first=fig.to_svg();ani.seek(2,draw=False);ani.seek(1,draw=False);self.assertEqual(first,fig.to_svg())
        first=io.BytesIO();fig.savefig(first,format='pdf');second=io.BytesIO();fig.savefig(second,format='pdf');self.assertEqual(first.getvalue(),second.getvalue())
    def test_region_extent(self):
        self.assertEqual(azl.Region('Cross',(170,-170,-20,20)).extent,(170,-170,-20,20))
        for extent in ((0,0,-2,2),(-190,10,-2,2),(-10,10,2,-2),(-10,10,-91,2),(180,-180,-10,10)):
            with self.subTest(extent=extent),self.assertRaises(ValueError):azl.Region('bad',extent)
    def test_atlas_regions_styles(self):
        regions=[azl.Region('A',(-50,-46,-24,-20)),azl.Region('B',(-70,-65,-10,-5))];before=azl.rcParams['axes.facecolor']
        atlas=azl.Atlas.from_regions(regions,lambda ax,r:ax.set_title(r.name),style='default');self.assertEqual(len(atlas),2)
        self.assertEqual(atlas.labels,('A','B'));self.assertEqual(atlas[1].axes[0].get_extent(),regions[1].extent);self.assertEqual(azl.rcParams['axes.facecolor'],before)
    def test_atlas_does_not_register_figures(self):
        count=len(azl.get_fignums());azl.Atlas.from_regions([azl.Region('A',(-50,-46,-24,-20))],lambda ax,r:None);self.assertEqual(len(azl.get_fignums()),count)
    def test_pdf_snapshot_and_pages(self):
        fig,ax,im=self.image();title=ax.set_title('One');out=io.BytesIO()
        with PdfPages(out) as pdf:
            pdf.savefig(fig);first=pdf._pages[0];title.set_text('Two');pdf.savefig(fig);self.assertEqual(pdf.get_pagecount(),2)
            self.assertEqual(first,pdf._pages[0]);self.assertNotEqual(first,pdf._pages[1])
        raw=out.getvalue();self.assertIn(b'/Count 2',raw);self.assertIn(b'page-1-DejaVu-license.txt',raw);self.assertIn(b'page-2-DejaVu-license.txt',raw)
        xref=int(re.search(rb'startxref\n([0-9]+)',raw).group(1));self.assertTrue(raw[xref:].startswith(b'xref'))
    def test_pdf_streams_unchanged(self):
        fig,ax,im=self.image();objects=render_pdf(fig.to_scene(),_objects=True);combined=render_pdf_pages([objects,objects])
        for obj in objects:
            if b'\nstream\n' in obj:self.assertIn(obj.partition(b'\nstream\n')[2],combined)
    def test_pdf_exception_preserves_target(self):
        fig,ax,im=self.image()
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/'pages.pdf';target.write_bytes(b'original')
            with self.assertRaises(ValueError):
                with PdfPages(target) as pdf:pdf.savefig(fig);raise ValueError('stop')
            self.assertEqual(target.read_bytes(),b'original')
    def test_atlas_svg_and_pdf(self):
        fig,ax,im=self.image();atlas=azl.Atlas([fig,fig])
        with tempfile.TemporaryDirectory() as temp:
            folder=atlas.save_pages(Path(temp)/'pages',format='svg');self.assertEqual(len(list(folder.glob('*.svg'))),2)
            atlas.savefig(Path(temp)/'atlas.pdf');self.assertIn(b'/Count 2',(Path(temp)/'atlas.pdf').read_bytes())
            with self.assertRaises(FileExistsError):atlas.save_pages(folder,format='svg')
    def test_gif_sequence_restore(self):
        try:from PIL import Image
        except ImportError:self.skipTest('Pillow optional')
        fig,ax,im=self.image();binding=self.series().bind(im,scale='frame');ani=FuncAnimation(fig,lambda i:binding.apply(i),3,autoplay=False);ani.seek(1,draw=False)
        with tempfile.TemporaryDirectory() as temp:
            path=ani.save(Path(temp)/'map.gif',fps=5);gif=Image.open(path)
            try:
                # Per-frame limits produce two visually identical initial frames;
                # GIF coalesces them while preserving the complete 600 ms timeline.
                self.assertEqual(gif.n_frames,2);self.assertEqual(gif.size,(80,80));self.assertEqual(gif.info['duration'],400)
                durations=[]
                for i in range(gif.n_frames):gif.seek(i);durations.append(gif.info['duration'])
                self.assertEqual(sum(durations),600)
            finally:gif.close()
            folder=ani.save_frames(Path(temp)/'frames');self.assertEqual(len(list(folder.glob('*.png'))),3)
        self.assertEqual(ani.index,1);self.assertEqual(binding.index,1);self.assertEqual(im.get_clim(),(10,40))
    def test_export_failure_preserves_state_file(self):
        try:from PIL import Image
        except ImportError:self.skipTest('Pillow optional')
        fig,ax,im=self.image();ani=FuncAnimation(fig,lambda i:im.set_data([[i+1,i+2],[i+3,i+4]]),2,autoplay=False);ani.seek(1,draw=False)
        class BadWriter:
            aborted=False
            def setup(self,path,*args):path.write_bytes(b'partial')
            def write_frame(self,image):raise ValueError('encoder failure')
            def finish(self):pass
            def abort(self):self.aborted=True
        writer=BadWriter()
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/'movie.mp4';target.write_bytes(b'original')
            with self.assertRaises(ValueError):ani.save(target,writer=writer)
            self.assertEqual(target.read_bytes(),b'original');self.assertEqual(list(Path(temp).iterdir()),[target])
        self.assertTrue(writer.aborted);self.assertEqual(ani.index,1);self.assertEqual(im.get_data(),[[2,3],[4,5]])
    def test_export_empty_writer_rejected(self):
        try:from PIL import Image
        except ImportError:self.skipTest('Pillow optional')
        fig,ax,im=self.image();ani=FuncAnimation(fig,lambda i:None,1,autoplay=False)
        class Empty:
            def setup(self,*a):pass
            def write_frame(self,*a):pass
            def finish(self):pass
            def abort(self):pass
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(RuntimeError):ani.save(Path(temp)/'empty.mp4',writer=Empty())
            self.assertFalse(list(Path(temp).iterdir()))
    def test_encoder_explicit_and_missing(self):
        fig,ax,im=self.image();ani=FuncAnimation(fig,lambda i:None,1,autoplay=False)
        with self.assertRaises(ValueError):ani.save('unused.mp4')
        with patch('azimlib.animation.shutil.which',return_value=None),self.assertRaises(RuntimeError):FFMpegWriter().setup(Path('unused.mp4'),80,80,5,2)
    def test_encoder_pipe_no_shell(self):
        process=MagicMock();process.poll.return_value=0;process.wait.return_value=0;process.stdin.closed=False
        with patch('azimlib.animation.shutil.which',return_value='/chosen/ffmpeg'),patch('azimlib.animation.subprocess.Popen',return_value=process) as launch:
            writer=FFMpegWriter();writer.setup(Path('movie.mp4'),80,80,5,2);self.assertFalse(launch.call_args.kwargs['shell']);self.assertIn('rgba',launch.call_args.args[0]);writer.finish();self.assertIsNone(writer.process)
    def test_writer_budgets(self):
        with self.assertRaises(ValueError):PillowWriter().setup(Path('unused.gif'),1000,1000,5,101)
        with patch('azimlib.animation.shutil.which',return_value='/chosen/ffmpeg'),self.assertRaises(ValueError):FFMpegWriter().setup(Path('unused.mp4'),81,80,5,2)

if __name__=='__main__':unittest.main()

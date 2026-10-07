"""Installed native temporal timer/control proof; no human/other-platform claim."""
import argparse,hashlib,json,platform,time
from pathlib import Path
import azimlib as azl
from azimlib.animation import FuncAnimation

def main():
    p=argparse.ArgumentParser();p.add_argument('--backend',choices=('tk','qt'),default='tk');p.add_argument('--output',type=Path,required=True);p.add_argument('--image',type=Path);args=p.parse_args()
    fig,ax=azl.subplots(figsize=(4,4),dpi=80);ax.set_extent((-50,-46,-24,-20));ax.set_title('Synthetic time series')
    image=ax.imshow([[1,2],[3,4]],extent=(-50,-46,-24,-20),origin='lower')
    series=azl.TemporalSeries(range(8),[[[i+1,i+2],[i+3,i+4]] for i in range(8)],unit='hour');binding=series.bind(image)
    seen=[]
    def update(index):binding.apply(index);seen.append(index)
    ani=FuncAnimation(fig,update,len(series),interval=60,repeat=False)
    controls=ani.add_controls(fig.add_axes((.15,.015,.55,.05)),fig.add_axes((.72,.015,.2,.05)))
    viewer=fig.show(backend=args.backend,block=False)
    if args.backend=='tk':viewer.window.withdraw()
    deadline=time.monotonic()+10
    while ani.playing and time.monotonic()<deadline:viewer.flush_events();time.sleep(.01)
    assert seen[:8]==list(range(8)) and not ani.playing and ani.index==7
    ani.seek(0,draw=False);ani.resume();ani.pause();paused=ani.index
    for _ in range(10):viewer.flush_events();time.sleep(.01)
    assert ani.index==paused and ani.event_source._handle is None
    controls.slider.set_val(3);assert ani.index==3 and not ani.playing
    controls.play.set_active(0);assert ani.playing
    ani.set_interval(80);ani.pause();viewer.draw()
    if args.image:
        args.image.parent.mkdir(parents=True,exist_ok=True)
        if args.backend=='qt':viewer.window.grab().save(str(args.image))
        else:viewer._image.save(args.image)
    runtime=Path(azl.__file__).parent;viewer.close()
    assert ani.closed and not ani.event_source.running and ani.event_source._handle is None and not fig._widgets
    report=dict(passed=True,version=azl.__version__,platform=platform.system(),backend=args.backend,
        automatic_ticks=True,finite_end=True,pause_resume=True,slider=True,controls=True,close_cleanup=True,
        scope='Native event loop/programmatic controls on this platform; no human/FPS/other-platform or video-codec validation',
        runtime_origin='<environment>/site-packages/azimlib',runtime_sha256={p.relative_to(runtime).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(runtime.rglob('*.py'))},tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
if __name__=='__main__':main()

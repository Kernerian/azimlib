"""Real IPython public display handle/event-loop integration, without Jupyter dependencies."""
import argparse,json,importlib.metadata
from pathlib import Path
from IPython.core.interactiveshell import InteractiveShell
import azimlib as azl
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();shell=InteractiveShell.instance()
    fig,ax=azl.subplots(figsize=(3,2));ax.set_extent((-2,2,-2,2));ax.scatter([0],[0]);v=fig.show(backend='notebook');handle=v.handle;ax.set_title('Updated display');shell.events.trigger('post_run_cell',None)
    assert v.handle is handle and not fig.stale;v.close();assert v._hook not in shell.events.callbacks['post_run_cell']
    import hashlib,sys
    runtime=Path(azl.__file__).resolve().parent
    assert runtime.is_relative_to(Path(sys.prefix).resolve()),'Install the package before this proof'
    fingerprint=dict(version=azl.__version__,runtime_origin='<environment>/site-packages/azimlib',
        runtime_sha256={p.relative_to(runtime).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(runtime.rglob('*.py'))},
        tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(dict(**fingerprint,passed=True,ipython=importlib.metadata.version('IPython'),display_handle=True,cell_hook=True,cleanup=True,scope='Real IPython shell public display protocol; not browser/Jupyter frontend acceptance'),indent=2)+'\n','utf8')
if __name__=='__main__':main()

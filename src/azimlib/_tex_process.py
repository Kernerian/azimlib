"""Bounded external typography jobs; no shell, installer or network acquisition.

Polling is a resource guard, not an OS security sandbox or a hard memory quota.
Only trusted TeX and trusted executables may be used by this interface.
"""
import os
from pathlib import Path
import subprocess
import time


def tree_bytes(directory, limit):
    total = 0
    count = 0
    for base, folders, names in os.walk(directory, followlinks=False):
        for name in (*folders, *names):
            path = Path(base)/name
            if path.is_symlink():
                raise ValueError('TeX resource directories cannot contain symbolic links')
        for name in names:
            count += 1
            total += (Path(base)/name).stat().st_size
            if count > 4096 or total > limit:
                raise ValueError('TeX file count/storage limit exceeded')
    return total


def run_tool(command, directory, config, log_name, *, acquire=False):
    try:
        import psutil
    except ImportError as exc:
        raise ImportError('Install azimlib[tex] for bounded real TeX jobs') from exc
    from .tex import TexError, TexResourceError
    directory = Path(directory)
    env = {key: os.environ[key] for key in ('SystemRoot', 'WINDIR', 'PATH', 'PATHEXT', 'USERPROFILE',
           'LD_LIBRARY_PATH', 'DYLD_LIBRARY_PATH') if key in os.environ}
    # Windows Known Folders requires the real registered USERPROFILE. Redirect
    # application config/cache/temp independently; do not falsify that OS key.
    env.update(HOME=str(directory), TMP=str(directory),
               TEMP=str(directory), TMPDIR=str(directory),
               APPDATA=str(directory), LOCALAPPDATA=str(directory),
               XDG_CACHE_HOME=str(directory), XDG_CONFIG_HOME=str(directory),
               TECTONIC_CACHE_DIR=str(config.cache_dir), TECTONIC_UNTRUSTED_MODE='1',
               openin_any='p', openout_any='p', shell_escape='f')
    start = time.monotonic()
    process = None
    peak_ram = peak_disk = peak_cache = 0
    known = {}
    try:
        with (directory/log_name).open('wb') as log:
            process = subprocess.Popen(command, cwd=directory, env=env,
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                shell=False, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            parent = psutil.Process(process.pid)
            while True:
                elapsed = time.monotonic()-start
                try:
                    children = parent.children(recursive=True)
                    processes = [parent, *children]
                    known.update({p.pid: p for p in children})
                    ram = sum(p.memory_info().rss for p in processes if p.is_running())
                    peak_ram = max(peak_ram, ram)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    ram = 0
                try:
                    disk = tree_bytes(directory, config.max_temp_bytes)
                except ValueError as exc:
                    raise TexResourceError(str(exc)) from None
                peak_disk = max(peak_disk, disk)
                if acquire:
                    import shutil
                    try: peak_cache=max(peak_cache,tree_bytes(config.cache_dir,config.max_cache_bytes))
                    except ValueError as exc: raise TexResourceError(str(exc)) from None
                    if shutil.disk_usage(config.cache_dir).free<15*1024**3:
                        raise TexResourceError('TeX acquisition must preserve 15 GiB free')
                if elapsed > config.timeout:
                    raise TexResourceError('TeX job exceeded its time limit')
                if ram > config.max_memory_bytes:
                    raise TexResourceError('TeX job exceeded its sampled process-tree RAM limit')
                if process.poll() is not None:
                    break
                time.sleep(.025)
        if process.returncode:
            # Raw compiler logs can contain source text or local paths. Keep
            # them inside the temporary job, never in an exported exception.
            raise TexError('External TeX tool failed (exit code '+str(process.returncode)+
                           '); check syntax, installed packages and font resources')
        return dict(seconds=time.monotonic()-start, peak_ram_bytes=peak_ram,
                    peak_temp_bytes=peak_disk, peak_cache_bytes=peak_cache)
    except OSError:
        raise TexError('Cannot start the configured TeX tool; check executable and dependent libraries') from None
    finally:
        if process is not None:
            # Do not leave runaway descendants after timeout, an exception, or
            # an otherwise completed tool that spawned a lingering process.
            for child in reversed(tuple(known.values())):
                try: child.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied): pass
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)

"""Capability queries for original CPU and optional GPU renderers.

GPU availability here means bindings installed, not a verified device/context.
Queries neither load optional rendering dependencies nor create a context.
"""
from dataclasses import dataclass
from importlib.util import find_spec


@dataclass(frozen=True)
class RendererCapabilities:
    name: str
    available: bool
    vector_output: bool
    raster_images: bool = True
    terrain_depth: bool = True
    mathtext: bool = True
    gpu: bool = False
    volumes: bool = False
    complex_shaping: bool = False
    full_tex: bool = False
    transparent_3d: bool = False

    def require(self, *features):
        if not self.available:
            raise RuntimeError(f'Renderer {self.name!r} requires optional dependencies')
        allowed = ('vector_output', 'raster_images', 'terrain_depth', 'mathtext',
                   'gpu', 'volumes', 'complex_shaping', 'full_tex', 'transparent_3d')
        for feature in features:
            if feature not in allowed:
                raise ValueError(f'Unknown renderer capability {feature!r}')
            if not getattr(self, feature):
                raise NotImplementedError(f'Renderer {self.name!r} does not support {feature}')
        return self


def get_capabilities(renderer, *, textengine='basic', texconfig=None):
    """Query png/svg/pdf; 3D output is embedded raster even in vector formats."""
    if renderer not in ('png', 'svg', 'pdf','gpu'):
        raise ValueError('Renderer must be exactly png, svg, pdf or gpu')
    if textengine not in ('basic','harfbuzz','tex'):raise ValueError('textengine must be basic, harfbuzz or tex')
    tex=False
    if textengine=='tex' and texconfig is not None and all(find_spec(n) is not None for n in ('fontTools','psutil')):
        from ..tex import TexConfig
        import shutil
        tex=(isinstance(texconfig,TexConfig) and texconfig.cache_dir.is_dir() and
             shutil.which(texconfig.executable) is not None and shutil.which(texconfig.converter) is not None and
             (renderer!='png' or find_spec('aggdraw') is not None))
    shaping=False
    if textengine=='harfbuzz' and all(find_spec(n) is not None for n in ('uharfbuzz','fontTools')):
        from .._unicode_icu import unicode_version,UnicodeEngineError
        try:unicode_version();shaping=renderer!='png' or find_spec('aggdraw') is not None
        except UnicodeEngineError:pass
    if renderer=='gpu':
        return RendererCapabilities(renderer,all(find_spec(n) is not None for n in ('moderngl','glcontext','PIL')),False,gpu=True,
                                    volumes=True,complex_shaping=shaping,full_tex=bool(tex))
    return RendererCapabilities(renderer, renderer != 'png' or find_spec('PIL') is not None,
                                renderer in ('svg', 'pdf'),volumes=renderer!='svg' or find_spec('PIL') is not None,complex_shaping=shaping,full_tex=bool(tex))

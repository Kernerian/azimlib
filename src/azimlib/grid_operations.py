"""Explicit horizontal/vertical grid operations and fail-closed selection."""
from dataclasses import dataclass
import math

from .coordinate_operations import CoordinateFrame, CoordinatePipeline
from .datum_grids import ShiftGrid, GridCoverageError, GridNoDataError
from .geometry import _number, wrap_longitude
from ._frames import vector3


def _epoch_limits(limits):
    if limits is None: return None
    limits = tuple(_number(v, 'valid epoch') for v in limits)
    if len(limits) != 2 or limits[0] >= limits[1]:
        raise ValueError('Require increasing valid_epochs')
    return limits


def _epoch(epoch, limits):
    if epoch is not None: epoch = _number(epoch, 'epoch')
    if limits is not None and (epoch is None or not limits[0] <= epoch <= limits[1]):
        raise ValueError('Explicit epoch within model validity is required')


@dataclass(frozen=True)
class GridOperation:
    """A verified grid with exact frame endpoints and direction.

    NTv2 horizontal shifts use east/north arcseconds, height passes through.
    GTX vertical offsets use metres: target_h = source_h + factor*grid(lon,lat).
    Geoid h -> H therefore uses factor=-1. No velocities are inferred from a
    static grid; epoch-dependent Helmert steps may be composed explicitly.
    """
    source: CoordinateFrame
    target: CoordinateFrame
    grid: ShiftGrid
    kind: str
    factor: float = 1.0
    valid_epochs: tuple = None

    def __post_init__(self):
        if not isinstance(self.source, CoordinateFrame) or not isinstance(self.target, CoordinateFrame):
            raise TypeError('Grid operation requires explicit CoordinateFrame endpoints')
        if self.source.kind != 'geographic' or self.target.kind != 'geographic' or self.source == self.target:
            raise ValueError('Grid operation requires distinct geographic 3D frame endpoints')
        if not isinstance(self.grid, ShiftGrid): raise TypeError('Require a decoded ShiftGrid')
        factor = _number(self.factor, 'factor')
        if factor not in (-1.,1.): raise ValueError('Grid factor must be +1 or -1')
        if self.kind == 'horizontal':
            if self.grid.format != 'ntv2' or factor != 1 or self.source.height_reference != self.target.height_reference:
                raise ValueError('Horizontal operation requires forward NTv2 and matching height references')
            # Binary endpoint labels are abbreviated; callers/catalog specify full
            # realization names. Ellipsoid axes must still match the file.
            for frame, suffix in ((self.source,'F'),(self.target,'T')):
                ellipsoid = frame.datum.ellipsoid
                if frame.datum.prime_meridian != 0 or abs(ellipsoid.semi_major_axis-self.grid.metadata['MAJOR_'+suffix]) > .01 or abs(ellipsoid.semi_minor_axis-self.grid.metadata['MINOR_'+suffix]) > .01:
                    raise ValueError('NTv2 endpoint ellipsoid/prime meridian mismatch')
        elif self.kind == 'vertical':
            if self.grid.format != 'gtx' or self.source.name != self.target.name or self.source.datum != self.target.datum or self.source.height_reference == self.target.height_reference:
                raise ValueError('Vertical operation requires GTX and same horizontal frame with distinct height references')
            if self.source.datum.prime_meridian != 0:
                raise ValueError('GTX registration uses Greenwich longitude')
        else: raise ValueError('Grid kind must be horizontal or vertical')
        object.__setattr__(self,'factor',factor)
        object.__setattr__(self,'valid_epochs',_epoch_limits(self.valid_epochs))

    def transform(self, x, y, z, *, epoch=None):
        lon, lat, height = vector3((x,y,z)); _epoch(epoch,self.valid_epochs)
        shift = self.grid.sample(lon,lat)
        if self.kind == 'vertical': return vector3((lon,lat,height+self.factor*shift[0]))
        result = (wrap_longitude(lon+shift[0]/3600), lat+shift[1]/3600, height)
        if not -90 <= result[1] <= 90: raise GridCoverageError('Grid shift leaves geographic latitude domain')
        return vector3(result)

    def inverse(self): return InverseGridOperation(self)

    def transform_raster(self, raster, *, epoch=None):
        """Explicit scalar-height correction at pixel centres; strict grid coverage.

        raster.height_frame must equal source. Values already missing stay None;
        any unsupported/missing correction aborts, rather than leaving old heights.
        No horizontal raster warping or height datum in GeoTIFF tags is inferred.
        """
        return _raster(self, raster, epoch)


@dataclass(frozen=True)
class InverseGridOperation:
    operation: GridOperation

    @property
    def source(self): return self.operation.target
    @property
    def target(self): return self.operation.source
    @property
    def valid_epochs(self): return self.operation.valid_epochs

    def inverse(self): return self.operation

    def transform(self, x, y, z, *, epoch=None):
        lon,lat,height = vector3((x,y,z)); op = self.operation; _epoch(epoch,op.valid_epochs)
        if op.kind == 'vertical':
            return vector3((lon,lat,height-op.factor*op.grid.sample(lon,lat)[0]))
        if not -180 <= lon <= 180 or not -90 <= lat <= 90:
            raise GridCoverageError('Require canonical target lon/lat')
        # Start inside each root as necessary, so shifted boundary points remain
        # invertible. Each solution is checked against the actual forward model.
        seeds = [(lon,lat)]
        for tile in op.grid.tiles:
            if tile.parent != 'NONE': continue
            w,s,e,n = tile.bounds; unwrapped = lon+360*round(((w+e)/2-lon)/360)
            seeds.append((wrap_longitude(min(e,max(w,unwrapped))), min(n,max(s,lat))))
        solutions = []
        missing = False
        for guess in seeds:
            try:
                for _ in range(24):
                    dl,dp = op.grid.sample(*guess)
                    candidate = (wrap_longitude(lon-dl/3600), lat-dp/3600)
                    if max(abs(wrap_longitude(candidate[0]-guess[0])),abs(candidate[1]-guess[1])) <= 1e-11:
                        check = op.transform(*candidate,height,epoch=epoch)
                        if max(abs(wrap_longitude(check[0]-lon)),abs(check[1]-lat)) <= 1e-10:
                            if not any(max(abs(wrap_longitude(candidate[0]-s[0])),abs(candidate[1]-s[1])) <= 1e-9 for s in solutions):
                                solutions.append(candidate)
                        break
                    guess = candidate
            except GridNoDataError: missing = True
            except GridCoverageError: pass
        if len(solutions) != 1:
            if len(solutions) > 1: raise ValueError('Ambiguous grid inverse: multiple source coordinates')
            if missing: raise GridNoDataError('Grid inverse requires missing values')
            raise GridCoverageError('No converged grid inverse within supported source coverage')
        return *solutions[0], height

    def transform_raster(self, raster, *, epoch=None): return _raster(self,raster,epoch)


def _raster(operation, raster, epoch):
    from .raster import GeoRaster
    forward = operation.operation if isinstance(operation,InverseGridOperation) else operation
    if forward.kind != 'vertical' or not isinstance(raster,GeoRaster) or raster.color_mode != 'scalar' or not raster.crs.is_geographic or raster.height_frame != operation.source:
        raise ValueError('Require scalar geographic GeoRaster with matching explicit height_frame for vertical operation')
    _epoch(epoch,operation.valid_epochs)
    rows = []
    for j,row in enumerate(raster.values):
        rows.append(tuple(None if h is None else operation.transform(*raster.coordinate(i,j,center=True),h,epoch=epoch)[2]
                          for i,h in enumerate(row)))
    return GeoRaster(rows,raster.affine,raster.crs,pixel_type=raster.pixel_type,
                     color_mode='scalar',height_frame=operation.target)


class OperationSet:
    """Explicit installed operations. Select one valid exact-endpoint candidate.

    Selection evaluates every pipeline at the supplied coordinate/epoch. Missing
    data or an ambiguous choice raises; no implicit lower-accuracy substitute,
    graph search, approximate datum tie, network request or best-guess ranking.
    name= allows an explicit choice among reviewed alternative models.
    """
    def __init__(self, operations):
        pairs = list(operations.items()) if hasattr(operations,'items') else list(operations)
        entries = dict(pairs)
        if len(entries) != len(pairs): raise ValueError('Duplicate operation name')
        if not entries or any(not isinstance(k,str) or not k.strip() for k in entries):
            raise ValueError('Operations require nonempty unique names')
        self._operations = {}
        for name,operation in entries.items():
            pipeline = operation if isinstance(operation,CoordinatePipeline) else CoordinatePipeline((operation,))
            self._operations[name] = pipeline

    def select(self, source, target, x, y, z, *, epoch=None, name=None):
        if name is not None and name not in self._operations: raise KeyError(name)
        candidates, errors = [], []
        for key,pipeline in self._operations.items():
            if name is not None and key != name or pipeline.source != source or pipeline.target != target: continue
            try:
                pipeline.transform(x,y,z,epoch=epoch); candidates.append(pipeline)
            except GridCoverageError:
                # Outside a model's declared coverage is not an accuracy fallback.
                # NoData/epoch/model errors below must never be treated this way.
                pass
            except (ValueError,FileNotFoundError) as exc: errors.append(exc)
        if errors:
            raise ValueError('An explicit matching operation is unavailable at this coordinate/epoch; choose a reviewed name, no fallback') from errors[0]
        if len(candidates) != 1:
            raise ValueError('No unique applicable operation; install an exact model or choose an explicit name')
        return candidates[0]

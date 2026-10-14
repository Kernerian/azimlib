"""Internal validation, conservative linear error bounds and resource budgets.

These are allocation guards and declared targets, not a global performance
promise. Geographic quantities never use screen pixels as their physical units.
"""
from dataclasses import dataclass
from numbers import Integral

from .geometry import _number


def linear_error_bound(jacobian, input_bounds):
    """Return sum(abs(J_ij)*bound_j); local linearization, not nonlinear proof.

Bounds use the units of the corresponding input; output units follow J.
No independence or probability distribution is assumed.
"""
    bounds = tuple(_number(v, 'input error bound') for v in input_bounds)
    rows = tuple(tuple(_number(v, 'Jacobian coefficient') for v in row) for row in jacobian)
    if not bounds or any(v < 0 for v in bounds) or not rows or any(len(row) != len(bounds) for row in rows):
        raise ValueError('Require nonnegative bounds and a matching finite Jacobian')
    return tuple(_number(sum(abs(v)*b for v, b in zip(row, bounds)), 'output error bound') for row in rows)


@dataclass(frozen=True)
class ResourceBudget:
    """Explicit byte/item limits; enforce before allocating or accumulating."""
    max_items: int
    max_bytes: int

    def __post_init__(self):
        for name in ('max_items', 'max_bytes'):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, Integral) or value <= 0:
                raise ValueError('Budget limits must be positive integers')
            object.__setattr__(self, name, int(value))

    def check(self, *, items=0, bytes_used=0):
        for value, maximum in ((items, self.max_items), (bytes_used, self.max_bytes)):
            if isinstance(value, bool) or not isinstance(value, Integral) or value < 0:
                raise ValueError('Usage must be a nonnegative integer')
            if value > maximum:
                raise ValueError('Resource budget exceeded; select/resample explicitly')


# Existing terrain limits remain unchanged; shared values prevent drift.
TERRAIN_MAX_VERTICES = 50000
TERRAIN_MAX_TRIANGLES = 20000
TERRAIN_MAX_PIXELS = 8000000
TERRAIN_MAX_PIXEL_TESTS = 64000000
# PBF enforces block bytes and decoded items; working bytes remain a measured
# target, not an allocator/RSS guarantee (native caches are measured separately).
STREAM_BLOCK_BUDGET = ResourceBudget(1000000, 32*1024*1024)
STREAM_WORKING_BUDGET = ResourceBudget(2000000, 256*1024*1024)

"""Internal astronomical coordinates with explicit, bounded time corrections.

Independent calendar arithmetic. No bundled leap-second/EOP table, downloads,
pre-1972 UTC, leap-second labels, inferred UT1 or celestial ephemerides.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import math

from .geometry import _number

SCALES = frozenset(('UTC', 'TAI', 'TT', 'UT1'))
TT_MINUS_TAI = 32.184
DAY_SECONDS = 86400


def utc_datetime(value):
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('Astronomical instants require an aware datetime')
    result = value.astimezone(timezone.utc)
    if result.year < 1972:
        raise ValueError('Pre-1972 UTC is outside the supported time contract')
    return result


@dataclass(frozen=True)
class JulianCoordinate:
    """Integer Julian day and seconds since noon; scale is part of identity.

UTC seconds are nominal calendar coordinates, not elapsed SI time through leaps.
Use differences on the same uniform scale (TT/TAI) for elapsed SI seconds.
UT1 is a rotation coordinate and is not a uniform atomic duration.
"""
    day: int
    seconds: float
    scale: str

    def __post_init__(self):
        if isinstance(self.day, bool) or not isinstance(self.day, int):
            raise ValueError('Julian day must be an integer')
        if self.scale not in SCALES:
            raise ValueError('Unknown time scale')
        seconds = _number(self.seconds)
        shift = math.floor(seconds/DAY_SECONDS)
        object.__setattr__(self, 'day', self.day+shift)
        object.__setattr__(self, 'seconds', seconds-shift*DAY_SECONDS)

    def seconds_since(self, other):
        if not isinstance(other, JulianCoordinate) or self.scale != other.scale:
            raise ValueError('Time differences require the same explicit scale')
        if self.scale not in ('TT', 'TAI'):
            raise ValueError('Elapsed SI duration requires TT or TAI')
        return (self.day-other.day)*DAY_SECONDS + self.seconds-other.seconds

    @property
    def jd_parts(self):
        return self.day, self.seconds/DAY_SECONDS


@dataclass(frozen=True)
class TimeOffsets:
    """Constant corrections over [start,end); caller supplies bounded provenance.

Split the interval at every leap or correction change. uncertainty_seconds is
a caller-declared bound for supplied offsets, not a guarantee made by Azimlib.
"""
    start: datetime
    end: datetime
    source: str
    tai_minus_utc: int | None = None
    ut1_minus_utc: float | None = None
    uncertainty_seconds: float = 0

    def __post_init__(self):
        start, end = utc_datetime(self.start), utc_datetime(self.end)
        if start >= end:
            raise ValueError('Time correction validity must be increasing')
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError('Corrections require source/version provenance')
        tai = self.tai_minus_utc
        if tai is not None and (isinstance(tai, bool) or not isinstance(tai, int) or not 0 <= tai <= 1000):
            raise ValueError('Post-1972 TAI-UTC must be an explicit integer in [0,1000] s')
        if self.ut1_minus_utc is not None:
            dut1 = _number(self.ut1_minus_utc)
            if abs(dut1) > 1:
                raise ValueError('UT1-UTC must lie in [-1,1] seconds')
            object.__setattr__(self, 'ut1_minus_utc', dut1)
        uncertainty = _number(self.uncertainty_seconds)
        if uncertainty < 0:
            raise ValueError('Offset uncertainty must be nonnegative')
        if tai is None and self.ut1_minus_utc is None:
            raise ValueError('Provide at least one explicit time correction')
        object.__setattr__(self, 'start', start)
        object.__setattr__(self, 'end', end)
        object.__setattr__(self, 'uncertainty_seconds', uncertainty)

    def at(self, instant):
        if not isinstance(instant, Instant) or not self.start <= instant.utc < self.end:
            raise ValueError('Instant outside time correction validity')
        return self


@dataclass(frozen=True)
class Instant:
    utc: datetime

    def __post_init__(self):
        object.__setattr__(self, 'utc', utc_datetime(self.utc))

    def coordinate(self, scale='UTC', *, offsets=None):
        if scale not in SCALES:
            raise ValueError('Unknown time scale')
        shift = 0
        if scale != 'UTC':
            if not isinstance(offsets, TimeOffsets):
                raise ValueError('Non-UTC coordinates require explicit TimeOffsets')
            offsets.at(self)
            if scale in ('TAI', 'TT'):
                if offsets.tai_minus_utc is None:
                    raise ValueError('Missing TAI-UTC correction')
                shift = offsets.tai_minus_utc + (TT_MINUS_TAI if scale == 'TT' else 0)
            elif scale == 'UT1':
                if offsets.ut1_minus_utc is None:
                    raise ValueError('Missing UT1-UTC correction')
                shift = offsets.ut1_minus_utc
        value = self.utc
        days, whole = divmod(value.hour*3600+value.minute*60+value.second+43200, DAY_SECONDS)
        seconds = whole+value.microsecond/1e6+shift
        return JulianCoordinate(value.toordinal()+1721424+days, seconds, scale)

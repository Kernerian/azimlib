"""Spherical map projections implemented directly from cartographic formulae.

All forward inputs are longitude, latitude in degrees; outputs are metres.
Inverse outputs follow the same lon/lat axis order. Coordinates outside a
projection's finite domain return None. Invalid numeric inputs raise ValueError.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import asin, atan, atan2, cos, degrees, exp, hypot, isfinite, log, pi, radians, sin, sqrt, tan
from typing import ClassVar

from .geometry import EARTH_RADIUS, _number, position, wrap_longitude


@dataclass(frozen=True)
class Projection:
    central_longitude: float = 0.0
    central_latitude: float = 0.0
    radius: float = EARTH_RADIUS
    name: ClassVar[str] = "projection"

    def __post_init__(self):
        for field in ("central_longitude", "central_latitude", "radius"):
            object.__setattr__(self, field, _number(getattr(self, field), field))
        if not -90 <= self.central_latitude <= 90:
            raise ValueError("central_latitude must lie between -90 and 90")
        if self.radius <= 0:
            raise ValueError("radius must be positive")

    def _angles(self, lon, lat):
        lon, lat = position((lon, lat))
        return radians(wrap_longitude(lon, self.central_longitude) - self.central_longitude), radians(lat)

    def _xy(self, x, y):
        return _number(x, "x") / self.radius, _number(y, "y") / self.radius

    def _lonlat(self, lam, phi):
        if not isfinite(lam) or not isfinite(phi) or abs(lam) > pi+1e-10 or abs(phi) > pi/2+1e-10:
            return None
        return wrap_longitude(self.central_longitude + degrees(lam)), max(-90.0, min(90.0, degrees(phi)))

    def forward(self, lon, lat):
        raise NotImplementedError

    def inverse(self, x, y):
        raise NotImplementedError


@dataclass(frozen=True)
class Equirectangular(Projection):
    standard_parallel: float = 0.0
    name: ClassVar[str] = "equirectangular"

    def __post_init__(self):
        super().__post_init__()
        value = _number(self.standard_parallel, "standard_parallel")
        if abs(value) >= 90:
            raise ValueError("standard_parallel must be strictly between -90 and 90")
        object.__setattr__(self, "standard_parallel", value)

    def forward(self, lon, lat):
        lam, phi = self._angles(lon, lat)
        return self.radius * lam * cos(radians(self.standard_parallel)), self.radius * (phi-radians(self.central_latitude))

    def inverse(self, x, y):
        x, y = self._xy(x, y)
        return self._lonlat(x/cos(radians(self.standard_parallel)), y+radians(self.central_latitude))


@dataclass(frozen=True)
class Mercator(Projection):
    max_latitude: float = 85.0511287798066
    name: ClassVar[str] = "mercator"

    def __post_init__(self):
        super().__post_init__()
        value = _number(self.max_latitude, "max_latitude")
        if not 0 < value < 90:
            raise ValueError("max_latitude must be strictly between 0 and 90")
        if abs(self.central_latitude) >= 90:
            raise ValueError("Mercator central_latitude cannot be a pole")
        object.__setattr__(self, "max_latitude", value)

    @property
    def _y0(self):
        return log(tan(pi/4+radians(self.central_latitude)/2))

    def forward(self, lon, lat):
        lam, phi = self._angles(lon, lat)
        # Rendering clips the polar caps; never silently changes a latitude.
        if abs(lat) > self.max_latitude + 1e-10:
            return None
        return self.radius*lam, self.radius*(log(tan(pi/4+phi/2))-self._y0)

    def inverse(self, x, y):
        x, y = self._xy(x, y)
        value = y+self._y0
        limit = log(tan(pi/4+radians(self.max_latitude)/2))
        if abs(value) > limit+1e-10:
            return None
        return self._lonlat(x, 2*atan(exp(value))-pi/2)


@dataclass(frozen=True)
class EqualEarth(Projection):
    name: ClassVar[str] = "equalearth"
    _a1: ClassVar[float] = 1.340264
    _a2: ClassVar[float] = -0.081106
    _a3: ClassVar[float] = 0.000893
    _a4: ClassVar[float] = 0.003796

    @classmethod
    def _poly(cls, theta):
        t2 = theta*theta
        return theta*(cls._a1+cls._a2*t2+t2**3*(cls._a3+cls._a4*t2))

    @classmethod
    def _derivative(cls, theta):
        t2 = theta*theta
        return cls._a1+3*cls._a2*t2+t2**3*(7*cls._a3+9*cls._a4*t2)

    @property
    def _y0(self):
        return self._poly(asin(sqrt(3)/2*sin(radians(self.central_latitude))))

    def forward(self, lon, lat):
        lam, phi = self._angles(lon, lat)
        theta = asin(sqrt(3)/2*sin(phi))
        x = 2*sqrt(3)*lam*cos(theta)/(3*self._derivative(theta))
        return self.radius*x, self.radius*(self._poly(theta)-self._y0)

    def inverse(self, x, y):
        x, y = self._xy(x, y)
        y += self._y0
        limit = pi/3
        if abs(y) > self._poly(limit)+1e-10:
            return None
        theta = max(-limit, min(limit, y/self._a1))
        for _ in range(20):
            delta = (self._poly(theta)-y)/self._derivative(theta)
            theta -= delta
            if abs(delta) < 1e-13:
                break
        phi = asin(max(-1.0, min(1.0, 2*sin(theta)/sqrt(3))))
        lam = 3*x*self._derivative(theta)/(2*sqrt(3)*cos(theta))
        return self._lonlat(lam, phi)


@dataclass(frozen=True)
class Orthographic(Projection):
    name: ClassVar[str] = "orthographic"

    def visibility(self, lon, lat):
        """Signed cosine of angular distance to the view centre (>=0 visible)."""
        lam, phi = self._angles(lon, lat)
        phi0 = radians(self.central_latitude)
        return sin(phi0)*sin(phi)+cos(phi0)*cos(phi)*cos(lam)

    def forward(self, lon, lat):
        lam, phi = self._angles(lon, lat)
        phi0 = radians(self.central_latitude)
        if sin(phi0)*sin(phi)+cos(phi0)*cos(phi)*cos(lam) < -1e-12:
            return None
        return self.radius*cos(phi)*sin(lam), self.radius*(cos(phi0)*sin(phi)-sin(phi0)*cos(phi)*cos(lam))

    def inverse(self, x, y):
        x, y = self._xy(x, y)
        rho = hypot(x, y)
        if rho > 1+1e-12:
            return None
        phi0 = radians(self.central_latitude)
        if rho < 1e-15:
            return wrap_longitude(self.central_longitude), self.central_latitude
        c = asin(min(1.0, rho))
        phi = asin(max(-1.0, min(1.0, cos(c)*sin(phi0)+y*sin(c)*cos(phi0)/rho)))
        lam = atan2(x*sin(c), rho*cos(phi0)*cos(c)-y*sin(phi0)*sin(c))
        return self._lonlat(lam, phi)


def _parallels(projection):
    try:
        values = tuple(projection.standard_parallels)
    except TypeError as exc:
        raise ValueError("standard_parallels requires two latitudes") from exc
    if len(values) != 2:
        raise ValueError("standard_parallels requires two latitudes")
    values = tuple(_number(v, "standard parallel") for v in values)
    if any(abs(v) >= 90 for v in values):
        raise ValueError("standard parallels must be strictly between -90 and 90")
    if abs(values[0]+values[1]) < 1e-10:
        raise ValueError("opposite standard parallels create a degenerate cone")
    object.__setattr__(projection, "standard_parallels", values)
    return tuple(map(radians, values))


@dataclass(frozen=True)
class LambertConformalConic(Projection):
    standard_parallels: tuple = (20.0, 50.0)
    name: ClassVar[str] = "lambert_conformal_conic"

    def __post_init__(self):
        super().__post_init__()
        phi1, phi2 = _parallels(self)
        n = sin(phi1) if abs(phi1-phi2) < 1e-12 else log(cos(phi1)/cos(phi2))/log(tan(pi/4+phi2/2)/tan(pi/4+phi1/2))
        f = cos(phi1)*tan(pi/4+phi1/2)**n/n
        phi0 = radians(self.central_latitude)
        if abs(self.central_latitude) == 90 and self.central_latitude*n < 0:
            raise ValueError("central_latitude is at the divergent pole")
        rho0 = 0.0 if abs(self.central_latitude) == 90 else f/tan(pi/4+phi0/2)**n
        object.__setattr__(self, "_n", n)
        object.__setattr__(self, "_f", f)
        object.__setattr__(self, "_rho0", rho0)

    def forward(self, lon, lat):
        lam, phi = self._angles(lon, lat)
        if abs(lat) >= 90:
            if lat*self._n < 0:
                return None
            rho = 0.0
        else:
            rho = self._f/tan(pi/4+phi/2)**self._n
        return self.radius*rho*sin(self._n*lam), self.radius*(self._rho0-rho*cos(self._n*lam))

    def inverse(self, x, y):
        x, y = self._xy(x, y)
        dy = self._rho0-y
        sign = 1 if self._n > 0 else -1
        rho = sign*hypot(x, dy)
        if abs(rho) < 1e-15:
            return wrap_longitude(self.central_longitude), 90.0*sign
        theta = atan2(sign*x, sign*dy)
        try:
            phi = 2*atan((self._f/rho)**(1/self._n))-pi/2
        except OverflowError:
            return None
        return self._lonlat(theta/self._n, phi)


@dataclass(frozen=True)
class AlbersEqualArea(Projection):
    standard_parallels: tuple = (20.0, 50.0)
    name: ClassVar[str] = "albers"

    def __post_init__(self):
        super().__post_init__()
        phi1, phi2 = _parallels(self)
        n = (sin(phi1)+sin(phi2))/2
        c = cos(phi1)**2+2*n*sin(phi1)
        rho0 = sqrt(max(0.0, c-2*n*sin(radians(self.central_latitude))))/n
        object.__setattr__(self, "_n", n)
        object.__setattr__(self, "_c", c)
        object.__setattr__(self, "_rho0", rho0)

    def forward(self, lon, lat):
        lam, phi = self._angles(lon, lat)
        rho = sqrt(max(0.0, self._c-2*self._n*sin(phi)))/self._n
        return self.radius*rho*sin(self._n*lam), self.radius*(self._rho0-rho*cos(self._n*lam))

    def inverse(self, x, y):
        x, y = self._xy(x, y)
        dy = self._rho0-y
        sign = 1 if self._n > 0 else -1
        rho = sign*hypot(x, dy)
        argument = (self._c-(rho*self._n)**2)/(2*self._n)
        if abs(argument) > 1+1e-10:
            return None
        theta = atan2(sign*x, sign*dy)
        return self._lonlat(theta/self._n, asin(max(-1, min(1, argument))))


_REGISTRY = {
    "equirectangular": Equirectangular, "platecarree": Equirectangular, "plate_carree": Equirectangular,
    "mercator": Mercator, "equalearth": EqualEarth, "equal_earth": EqualEarth,
    "orthographic": Orthographic, "ortho": Orthographic,
    "lambert_conformal_conic": LambertConformalConic, "lambert": LambertConformalConic, "lcc": LambertConformalConic,
    "albers": AlbersEqualArea, "albers_equal_area": AlbersEqualArea, "aea": AlbersEqualArea,
}


def register_projection(name, projection_class, *, replace=False):
    """Register an independently implemented Projection subclass."""
    if not isinstance(name, str) or not name.strip():
        raise ValueError("projection name must be nonempty")
    if not isinstance(projection_class, type) or not issubclass(projection_class, Projection):
        raise TypeError("projection_class must inherit Projection")
    key = name.lower().strip().replace("-", "_")
    if key in _REGISTRY and not replace:
        raise ValueError(f"projection {name!r} is already registered")
    _REGISTRY[key] = projection_class


def get_projection(projection="equirectangular", **kwargs):
    """Resolve a registered name or reuse a Projection object."""
    if isinstance(projection, Projection):
        if kwargs:
            raise TypeError("projection parameters cannot accompany an existing Projection")
        return projection
    if not isinstance(projection, str):
        raise TypeError("projection must be a name or Projection instance")
    key = projection.lower().strip().replace("-", "_")
    try:
        constructor = _REGISTRY[key]
    except KeyError as exc:
        raise ValueError(f"unknown projection {projection!r}; available: {', '.join(sorted(_REGISTRY))}") from exc
    return constructor(**kwargs)


def available_projections():
    """Return the registered projection names, including aliases."""
    return tuple(sorted(_REGISTRY))

"""Explicit spherical solar-disk definitions, not fitted eclipse corrections.

The IAU nominal radius is an exact conversion constant, not a measurement of
the photosphere. A published eclipse-model radius is a different convention.
Neither constant alone establishes the precision of a predicted contact.
"""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class SolarDiskConvention:
    name: str
    radius_m: float
    definition: str
    source: str
    def __post_init__(self):
        if any(not isinstance(v,str) or not v.strip() for v in (self.name,self.definition,self.source)):
            raise ValueError('Solar disk requires name, definition and provenance')
        if isinstance(self.radius_m,bool) or not isinstance(self.radius_m,(int,float)) or not math.isfinite(self.radius_m) or self.radius_m<=0:
            raise ValueError('Solar disk radius must be positive finite metres')


IAU2015_NOMINAL=SolarDiskConvention('iau2015-nominal',695700000.,
    'Exact IAU 2015 B3 nominal conversion constant; not a measured photospheric radius',
    'https://arxiv.org/abs/1510.07674')
NASA_SVS_696000=SolarDiskConvention('nasa-svs-696000km',696000000.,
    'Spherical eclipse-model radius published by NASA SVS; not an inferred GSFC Canon convention',
    'https://svs.gsfc.nasa.gov/4314/')


@dataclass(frozen=True)
class SolarDiskComparison:
    results: tuple
    @property
    def classification_sensitive(self):return len({result.classification for model,result in self.results})>1
    @property
    def accuracy_validated(self):return False


def compare_disks(evaluator,conventions):
    """Report every selected model. Never choose the one closest to a reference."""
    conventions=tuple(conventions)
    if len(conventions)<2 or len(conventions)>16 or any(not isinstance(v,SolarDiskConvention) for v in conventions):
        raise ValueError('Provide 2..16 explicit solar disk conventions')
    if len({v.name for v in conventions})!=len(conventions):raise ValueError('Convention names must be distinct')
    return SolarDiskComparison(tuple((model,evaluator(model)) for model in conventions))

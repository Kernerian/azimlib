"""Small public input vocabulary shared by independent Azimlib viewers.

Event objects currently expose attributes; Matplotlib's complete backend/event
class hierarchy is not implemented here.
"""
from enum import IntEnum


class MouseButton(IntEnum):
    LEFT=1
    MIDDLE=2
    RIGHT=3
    BACK=8
    FORWARD=9

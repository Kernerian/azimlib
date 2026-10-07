"""Keep legacy composition oracles for explicitly polygonized circle geometry.

The 0.3 ordinary circle is analytic; its coverage has separate mathematical tests.
This helper preserves the old geometry to isolate buffers/bands/text regressions,
instead of weakening byte comparisons or overwriting frozen renderer baselines.
"""
import copy,math
from azimlib.scene import Circle,Path
from azimlib.renderers.coverage import unit_circle

def legacy_circles(scene,scale=1):
    result=copy.copy(scene);result.items=[]
    for item in scene.items:
        if isinstance(item,Circle):
            count=max(64,min(4096,math.ceil(2*math.pi*item.r*3*scale/2)))
            item=Path([[(item.x+item.r*c,item.y+item.r*s) for c,s in unit_circle(count)]],True,item.style,item.clip)
        result.items.append(item)
    return result

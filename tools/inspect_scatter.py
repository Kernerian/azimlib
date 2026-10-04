"""Development-only scatter editing oracle; Matplotlib is not a runtime dependency."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize

fig,ax=plt.subplots()
points=ax.scatter([-52,-48],[-25,-21],s=36,c=[20,80],norm=Normalize(0,100))
cases=[]
def snapshot(name):
    fig.canvas.draw()
    cases.append(dict(name=name,offsets=points.get_offsets().tolist(),
                      sizes=points.get_sizes().tolist(),array=points.get_array().tolist(),
                      view=[*ax.get_xlim(),*ax.get_ylim()],clim=list(points.get_clim())))
snapshot('initial')
points.set_offsets([[-54,-28],[-43,-18]]);snapshot('moved-fixed-view')
points.set_sizes([25,100]);snapshot('areas')
points.set_offsets([-46.63,-23.55]);points.set_array([50]);snapshot('one-point')
points.set(offsets=[[-52,-25],[-48,-21],[-44,-19]],sizes=[16,64],array=[0,50,100]);snapshot('three-points-cycled-sizes')
points.set(offsets=np.empty((0,2)),sizes=[],array=[]);snapshot('empty')
target=Path(__file__).resolve().parents[1]/'docs/scatter-reference.json'
target.write_text(json.dumps({'matplotlib':matplotlib.__version__,'cases':cases},indent=2),encoding='utf-8')
print(target)

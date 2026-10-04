"""Development-only Matplotlib oracle for scalar/vector field edits."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize

images=[]
for origin in ('lower','upper'):
    fig,ax=plt.subplots();image=ax.imshow([[0,1],[2,3]],extent=(-50,-40,-20,-10),origin=origin,norm=Normalize(0,3))
    ax.set_xlim(-60,-35);ax.set_ylim(-30,-5)
    def snapshot(name):
        fig.canvas.draw()
        images.append(dict(name=name,origin=origin,data=image.get_array().tolist(),extent=list(image.get_extent()),
                           clim=list(image.get_clim()),view=[*ax.get_xlim(),*ax.get_ylim()]))
    snapshot('initial')
    image.set_data([[10,20,30]]);snapshot('reshape')
    image.set_extent((-55,-40,-25,-15));snapshot('extent')
    image.autoscale();snapshot('autoscale')
    plt.close(fig)

fig,ax=plt.subplots();mesh=ax.pcolormesh([-60,-50,-40],[-30,-20,-10],[[0,1],[2,3]],norm=Normalize(0,3))
meshes=[]
for name,values in (('matrix',[[5,10],[15,20]]),('flat',[1,2,3,4])):
    mesh.set_array(np.asarray(values));fig.canvas.draw()
    meshes.append(dict(name=name,array=mesh.get_array().ravel().tolist(),coordinates=mesh.get_coordinates().tolist(),clim=list(mesh.get_clim())))
plt.close(fig)

fig,ax=plt.subplots();vectors=ax.quiver([-52,-48,-44],[-25,-21,-19],[1,0,2],[0,1,1],[10,20,30],norm=Normalize(0,30),scale=10)
quivers=[]
def vector_snapshot(name):
    fig.canvas.draw()
    quivers.append(dict(name=name,U=np.broadcast_to(vectors.U,(3,)).tolist(),V=np.broadcast_to(vectors.V,(3,)).tolist(),
                         C=np.broadcast_to(vectors.get_array(),(3,)).tolist(),offsets=vectors.get_offsets().tolist(),clim=list(vectors.get_clim())))
vector_snapshot('initial');vectors.set_UVC([0,-1,2],[2,1,0]);vector_snapshot('preserve-colors')
vectors.set_UVC(2,1,5);vector_snapshot('broadcast')
vectors.set_offsets([[-54,-28],[-48,-21],[-43,-18]]);vector_snapshot('move')
plt.close(fig)
target=Path(__file__).resolve().parents[1]/'docs/field-edits-reference.json'
target.write_text(json.dumps(dict(matplotlib=matplotlib.__version__,images=images,meshes=meshes,vectors=quivers),indent=2),encoding='utf-8')
print(target)

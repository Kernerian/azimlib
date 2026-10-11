"""Original synthetic density, slices and isosurface; all spatial units are metres."""
import math
import azimlib as azl
from azimlib.colors import Normalize
from azimlib.terrain3d import LocalFrame


def cloud(shift=0.):
    n=20
    values=[[[math.exp(-((x-9.5-shift)**2+(y-9.5)**2+(z-10)**2)/23)
              for x in range(n)] for y in range(n)] for z in range(n)]
    return azl.VolumeField.from_array(values,origin=(-950,-950,100),spacing=(100,100,100),
        value_unit='relative density',frame=LocalFrame(-46,-23))


def make_cloud():
    fig=azl.figure(figsize=(5,4));ax=fig.add_subplot(111,projection='3d')
    fig.subplots_adjust(left=.18,bottom=.20,right=.84,top=.85)
    field=cloud()
    volume=ax.plot_volume(field,norm=Normalize(0,1),cmap='blues',
        opacity=azl.OpacityTransfer(((0,0),(.1,0),(.7,.12),(1,.22))),step=100,
        reference_length=100,light=azl.VolumeLight(ambient=.35,diffuse=.65,shadow_steps=4))
    ax.plot_surface([-1100,1100],[-1100,1100],[[0,0],[0,0]],color='#c1cbbb',shade=False)
    ax.set_title('Synthetic cloud · volumetric light',fontsize=11)
    ax.set_xlabel('East (m)');ax.set_ylabel('North (m)');ax.set_zlabel('Height (m)')
    fig.colorbar(volume,ax=ax,label='Relative density',shrink=.65)
    return fig,ax,volume


def make_sections():
    fig=azl.figure(figsize=(5,4));ax=fig.add_subplot(111,projection='3d');field=cloud()
    fig.subplots_adjust(left=.18,bottom=.20,right=.84,top=.85)
    ax.volume_slice(field,axis='x',position=0,norm=Normalize(0,1),cmap='viridis')
    ax.isosurface(field,.18,color='#698eab',shade=True)
    ax.set_title('Interpolated slice + isosurface (0.18)',fontsize=11)
    ax.set_xlabel('East (m)');ax.set_ylabel('North (m)');ax.set_zlabel('Height (m)')
    return fig,ax


if __name__=='__main__':
    fig,ax,volume=make_cloud()
    fig.show(block=True)

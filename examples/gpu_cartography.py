"""Explicit GPU display/export; synthetic texture and terrain are original."""
import math
import azimlib as azl


def make_map():
    fig,ax=azl.subplots(figsize=(7,5))
    ax.map('brazil',facecolor='#f0f3f5',edgecolor='#6f818c',linewidth=.6)
    ax.plot([-60,-55,-49,-44],[-10,-18,-20,-15],color='#d34c38',linestyle='--',marker='D',label='Synthetic route')
    ax.scatter([-46.63,-43.17],[-23.55,-22.90],color='#137ca4',label='Cities')
    ax.set_title('Azimlib · GPU cartography');ax.set_xlabel('Longitude');ax.set_ylabel('Latitude');ax.legend()
    ax.scale_bar();ax.north_arrow()
    return fig,ax


def make_terrain():
    fig=azl.figure(figsize=(6,4));ax=fig.add_subplot(111,projection='3d')
    axis=list(range(8));z=[[1+2*math.exp(-((x-3)**2+(y-4)**2)/6) for x in axis] for y in axis]
    pixels=bytes(v for row in range(8) for col in range(8) for v in ((42,145,98,255) if (row+col)%2 else (221,194,120,255)))
    surface=ax.plot_surface(axis,axis,z,color='white',texture=(8,8,pixels),shade=True)
    ax.set_title('Own texture + perspective depth');ax.set_xlabel('East');ax.set_ylabel('North');ax.set_zlabel('Height')
    return fig,ax,surface


if __name__=='__main__':
    fig,ax=make_map();fig.show(renderer='gpu',block=True)

"""Own solar maps and seasonal ENU sky ribbons; explicit approximate UTC clock."""
from datetime import datetime,timedelta,timezone
import azimlib as azl

MODEL=azl.SolarModel(time_policy='utc-approx')
INSTANT=datetime(2025,6,21,12,tzinfo=timezone.utc)
OBSERVER=azl.SolarObserver(-46.63,-23.55)

def make_map(projection='equirectangular'):
    options=dict(central_longitude=-45,central_latitude=15) if projection=='orthographic' else {}
    fig,ax=azl.subplots(figsize=(7,4.2),projection=projection,projection_kw=options)
    fig.subplots_adjust(left=.10,right=.95,bottom=.15,top=.83)
    ax.map('world',facecolor='#e6ebee',edgecolor='#80909a',linewidth=.3)
    ax.set_extent((-180,180,-90,90));ax.set_facecolor('#fafcfd')
    position=MODEL.position(INSTANT)
    shade=ax.nightshade(position,model=MODEL,step=3,alpha=.24)
    terminator=ax.solar_terminator(position,model=MODEL,color='#365a76',linewidth=.85)
    sun=ax.sun(position,model=MODEL,annotation='Subsolar point',markersize=7)
    sun.set_picker(4)
    ax.set_title('Terrestrial Sun · June solstice',fontsize=12)
    if projection=='orthographic':
        ax.set_axis_off();ax.grid(labels=False,color='#bdc8cf',linewidth=.35,alpha=.6)
    else:
        ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
        ax.grid(color='#bdc8cf',linewidth=.35,alpha=.6)
    return fig,ax,(sun,terminator,shade)

def make_sky():
    fig,ax=azl.subplots(figsize=(5.8,4.5),subplot_kw={'projection':'3d'})
    fig.subplots_adjust(left=.17,right=.89,bottom=.18,top=.85)
    for month,day,color in ((3,20,'#8063a8'),(6,21,'#cf7145'),(12,21,'#388b87')):
        start=INSTANT.replace(month=month,day=day,hour=0)
        path=MODEL.path([start+timedelta(minutes=15*i) for i in range(97)],OBSERVER)
        ax.sun_path(path,visual_radius=1000,width=24,color=color)
    ax.plot_surface([-1100,1100],[-1100,1100],[[0,0],[0,0]],color='#e1e7e6',shade=False)
    sun=ax.sun(MODEL.position(INSTANT+timedelta(hours=3),OBSERVER),model=MODEL,symbol_radius=45)
    ax.set_title('Seasonal apparent sky paths · São Paulo',fontsize=11)
    ax.set_xlabel('East · visual m');ax.set_ylabel('North · visual m');ax.set_zlabel('Up · visual m')
    return fig,ax,sun

if __name__=='__main__':
    make_map()[0].show(block=True)

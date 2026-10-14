"""Original metre ENU shadows and explicitly synthetic eclipse illustrations."""
import math
from datetime import datetime,timedelta,timezone
import azimlib as azl
from azimlib.terrain3d import LocalFrame
from azimlib.eclipse import SUN_RADIUS_M
from azimlib.lunar import MOON_RADIUS_M
MODEL=azl.SolarModel(time_policy='utc-approx')
INSTANT=datetime(2025,6,21,9,tzinfo=timezone.utc)
FRAME=LocalFrame(0,45)
OBSERVER=azl.SolarObserver(0,45)

def make_urban():
    fig,ax=azl.subplots(figsize=(6.4,4.6),subplot_kw={'projection':'3d'})
    fig.subplots_adjust(left=.08,right=.95,bottom=.13,top=.83)
    ax.plot_surface([-30,30],[-30,30],[[0,0],[0,0]],color='#e7e3d9')
    buildings=[]
    for x,y,w,h,z,color in ((-8,-3,9,9,13,'#a8bbc6'),(9,8,8,9,9,'#a3bdac'),(-17,12,6,7,6,'#c8b5a1')):
        ring=[[x,y],[x+w,y],[x+w,y+h],[x,y+h],[x,y]]
        data={'type':'Feature','properties':{},'geometry':{'type':'Polygon','coordinates':[ring]}}
        buildings.append(ax.buildings({'type':'FeatureCollection','features':[data]},height=z,color=color))
    light=ax.solar_light(MODEL.position(INSTANT,OBSERVER),model=MODEL,frame=FRAME,angular_radius=None,max_edge_m=1.5,samples=8,bias_m=.001)
    ax.view_init(elev=45,azim=-65);ax.set_zlim(0,25)
    ax.set_xlabel('East (m)');ax.set_ylabel('North (m)');ax.set_title('Physical urban shadows · synthetic buildings',fontsize=11)
    return fig,ax,light

def geometry(*,lunar=False,offset_m=0):
    return azl.EclipseGeometry(
        azl.ShadowSphere.from_xyz((149597870700.,0,0),radius_m=SUN_RADIUS_M),
        azl.ShadowSphere.from_xyz((-384e6 if lunar else 360e6,offset_m,0),radius_m=MOON_RADIUS_M),
        source='Azimlib original synthetic aligned spheres; no event/date prediction')

def make_eclipse_map():
    fig,ax=azl.subplots(figsize=(6.4,4.2),projection='orthographic',projection_kw={'central_longitude':0,'central_latitude':0})
    ax.map('world',facecolor='#e3e8eb',edgecolor='#89969e',linewidth=.3)
    artist=ax.eclipse_shadow(geometry(),step=2,cmap='viridis',alpha=.8)
    ax.set_title('Synthetic solar occultation · finite Sun and Moon',fontsize=11)
    fig.colorbar(artist,ax=ax,label='Blocked solar disk fraction',shrink=.75)
    return fig,ax,artist

def make_lunar():
    g=geometry(lunar=True);observer=azl.SolarObserver(0,0);distance=math.dist(g.moon.center.xyz,observer.fixed_position.xyz);az,el=observer.azimuth_elevation(g.moon.center)
    fig,ax=azl.subplots(figsize=(6.4,4.2),subplot_kw={'projection':'3d'})
    body=ax.earth_moon(azl.MoonDirection(0 if az is None else az,el,distance,observer),distance_scale=.1,moon_radius_scale=4,ambient=.08)
    body.set_eclipse_geometry(g)
    # Magnification is display-only; physical Moon remains 384,000 km away.
    ax.view_init(elev=20,azim=70);ax.set_axis_off()
    ax.set_title('Synthetic lunar shadow · distance ×0.1; Moon radius ×4',fontsize=11)
    return fig,ax,body

def make_volume():
    fig,ax=azl.subplots(figsize=(5.5,4.2),subplot_kw={'projection':'3d'})
    field=azl.VolumeField.from_array([[[math.exp(-((x-3)**2+(y-3)**2+(z-3)**2)/5) for x in range(7)] for y in range(7)] for z in range(7)],frame=FRAME)
    volume=ax.plot_volume(field,opacity=azl.OpacityTransfer(((0,0),(.1,0),(1,.35))),step=.4)
    light=ax.solar_light(MODEL.position(INSTANT,OBSERVER),model=MODEL,frame=FRAME,shadows=False)
    light.bind_volume(volume,shadow_steps=4);ax.set_axis_off();ax.set_title('Shared ENU solar light · volume self-attenuation',fontsize=11)
    return fig,ax,light

if __name__=='__main__':make_urban()[0].show(block=True)

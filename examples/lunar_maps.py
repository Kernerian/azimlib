"""Calculated lunar groundtrack, physical system and explicit visual scales."""
from datetime import datetime,timedelta,timezone
import azimlib as azl

MODEL=azl.LunarModel(time_policy='utc-approx')
INSTANT=datetime(2025,1,7,12,tzinfo=timezone.utc)

def make_map(projection='equirectangular'):
    fig,ax=azl.subplots(figsize=(7,4.2),projection=projection)
    fig.subplots_adjust(left=.10,right=.95,bottom=.15,top=.83)
    ax.map('world',facecolor='#e6ebee',edgecolor='#80909a',linewidth=.3)
    ax.set_extent((-180,180,-90,90))
    path=MODEL.path([INSTANT+timedelta(hours=i*.5) for i in range(49)])
    ax.moon_path(path,linewidth=.9,color='#9367ac')
    moon=ax.moon(MODEL.position(INSTANT),model=MODEL,annotation='Sublunar point');moon.set_picker(4)
    ax.set_title('Calculated Earth-fixed lunar groundtrack · 24 hours',fontsize=11)
    ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
    ax.grid(color='#c7cdd3',linewidth=.35)
    return fig,ax,(moon,)

def make_system(*,physical=False):
    fig,ax=azl.subplots(figsize=(6,4.5),subplot_kw={'projection':'3d'})
    fig.subplots_adjust(left=.06,right=.96,bottom=.07,top=.85)
    body=ax.earth_moon(MODEL.position(INSTANT),model=MODEL,distance_scale=1 if physical else .1,moon_radius_scale=1 if physical else 3)
    ax.set_axis_off();ax.view_init(elev=25,azim=-60)
    ax.set_title('Earth–Moon · physical metre scale' if physical else 'Earth–Moon · distance ×0.1; Moon radius ×3',fontsize=11)
    return fig,ax,body

def make_phases():
    fig,axes=azl.subplots(1,4,figsize=(9,2.8),subplot_kw={'projection':'3d'})
    fig.subplots_adjust(left=.02,right=.98,bottom=.05,top=.80,wspace=.08)
    bodies=[]
    for ax,day in zip(axes,(3,7,13,21)):
        p=MODEL.position(INSTANT.replace(day=day));body=ax.moon(p,model=MODEL,ambient=.06);center=p.fixed.xyz;r=2.6e6
        ax.set_xlim(center[0]-r,center[0]+r);ax.set_ylim(center[1]-r,center[1]+r);ax.set_zlim(center[2]-r,center[2]+r)
        # Camera toward Earth: elevation/azimuth select observer-to-Moon axis.
        from math import atan2,hypot,degrees
        ax.view_init(elev=degrees(atan2(-center[2],hypot(center[0],center[1]))),azim=degrees(atan2(-center[1],-center[0])))
        ax.set_axis_off();ax.set_title(f'Jan {day} · {p.illuminated_fraction:.0%} lit',fontsize=9);bodies.append(body)
    fig.suptitle('Geometric lunar phases · celestial orientation',fontsize=12)
    return fig,axes,tuple(bodies)

if __name__=='__main__':make_system()[0].show(block=True)

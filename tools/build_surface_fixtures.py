"""Explicit QA-only fixture generation; pyproj, GeographicLib and SpiceyPy.

No downloads, no runtime cartography implementation imported. Preset numerical
axes are frozen facts from WGS84/NAIF pck00011, not derived from Azimlib output.
"""
import argparse,json,math
from pathlib import Path


def build(output):
    import pyproj,geographiclib,spiceypy
    from geographiclib.geodesic import Geodesic
    axes={'earth':(6378137.,6378137*(1-1/298.257223563)),
          'moon':(1737400.,1737400.),'mars':(3396190.,3376200.),
          'venus':(6051800.,6051800.),'mercury':(2440530.,2438260.)}
    methods={'equirectangular':'eqc','mercator':'merc','orthographic':'ortho','stereographic':'stere',
             'transverse_mercator':'tmerc','equalearth':'eqearth','azimuthal_equidistant':'aeqd','lambert_azimuthal_equal_area':'laea'}
    projections=[];geodesics=[];areas=[];normals=[]
    for body,(a,c) in axes.items():
        geod=Geodesic(a,(a-c)/a)
        for lon,lat in ((0,0),(179,-60),(-45,25),(90,89.999),(0,-90)):
            xyz=spiceypy.georec(math.radians(lon),math.radians(lat),0,a,(a-c)/a)
            normal=spiceypy.surfnm(a,a,c,xyz)
            normals.append(dict(body=body,input=(lon,lat),xyz=list(xyz),normal=list(normal)))
        for method,code in methods.items():
            if a!=c and method in ('equalearth','azimuthal_equidistant','lambert_azimuthal_equal_area'):continue
            params=dict(central_longitude=20.,central_latitude=90. if method=='stereographic' else 15.)
            ref=pyproj.Proj(proj=code,a=a,b=c,lon_0=params['central_longitude'],lat_0=params['central_latitude'],k=1)
            origin=ref(20,params['central_latitude'])
            positions=([(17,-79),(18,-30),(20,0),(22,45),(23,83)] if method=='transverse_mercator' else
                       [(20,0),(40,45),(10,-30),(20,89.5),(90,15),(-175,10),(179,-40)])
            for lon,lat in positions:
                x,y=ref(lon,lat)
                if not math.isfinite(x+y):expected=None
                elif method=='equirectangular':
                    # EPSG:1028; PROJ<=9.8 eqc still applies spherical y.
                    arc=geod.Inverse(params['central_latitude'],20,lat,20)['s12']
                    expected=(a*math.radians((lon-20+180)%360-180),math.copysign(arc,lat-params['central_latitude']))
                else:expected=(x-origin[0],y-origin[1])
                projections.append(dict(body=body,method=method,parameters=params,input=(lon,lat),xy=expected,within_declared_domain=not(method=='mercator' and abs(lat)>85.0511287798066),
                                        reference='IOGP EQC via GeographicLib meridian' if method=='equirectangular' else 'PROJ; explicit origin translation'))
        for start,end in (((0,0),(1,1)),((170,-20),(-170,30)),((30,80),(-120,79)),((-40,-45),(90,50)),((0,0),(179.7,.1)),((0,0),(180,0))):
            r=geod.Inverse(start[1],start[0],end[1],end[0]);ambiguous=start==(0,0) and end==(180,0)
            geodesics.append(dict(body=body,start=start,end=end,distance_m=r['s12'],azimuth1=r['azi1']%360,azimuth2=r['azi2']%360,
                                  ambiguous=ambiguous,difficult=abs(end[0]-start[0])>179 and abs(end[1]-start[1])<1))
        polygons=[[(-40,-10),(10,-10),(20,40),(-20,50)],[(170,-5),(-175,-5),(-175,10),(170,10)],[(0,0),(.01,0),(.01,.01),(0,.01)]]
        if a==c:polygons.extend([[(0,0),(90,0),(0,90)],[(-120,80),(0,80),(120,80)]])
        for ring in polygons:
            p=geod.Polygon()
            for lon,lat in ring:p.AddPoint(lat,lon)
            areas.append(dict(body=body,vertices=ring,area_m2=abs(p.Compute()[2])))
    result=dict(schema=1,latitude_type='planetographic',axes_m=axes,
                reference=dict(pyproj=pyproj.__version__,PROJ=pyproj.__proj_version__,geographiclib=geographiclib.__version__,
                               projection_url='https://proj.org/en/stable/operations/projections/',
                               geodesic_url='https://geographiclib.sourceforge.io/html/python/',
                               spiceypy=spiceypy.__version__,cspice=spiceypy.tkvrsn('TOOLKIT'),
                               normal_url='https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/cspice/surfnm_c.html',
                               origin_convention='Subtract projected central origin, including methods where PROJ ignores lat_0'),
                tolerances=dict(sphere_xy_m=1e-5,oblate_xy_m=.05,tm_xy_m=.5,inverse_deg=1e-8,distance_m=.05,difficult_distance_m=.1,azimuth_deg=1e-7,area_abs_m2=10,area_relative=1e-7),
                projections=projections,geodesics=geodesics,areas=areas,normals=normals)
    Path(output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);build(p.parse_args().output)

"""Reproducible Phase B gallery, rendered only by Azimlib; no downloads.

python examples/planetary/surfaces_050.py --output OUTPUT_DIRECTORY
All non-Earth elevations/intensities are deterministic synthetic examples.
"""
import argparse
import hashlib
import html
import json
import math
from pathlib import Path
import platform
import statistics
import subprocess
import time
import tracemalloc
import azimlib as azl


def dem(body,*,regional=False,shape=None):
    ny,nx=shape or ((25,33) if regional else (24,48))
    extent=(19,23,8,12) if regional else (-180,180,-90,90)
    w,e,s,n=extent
    rows=[]
    for j in range(ny):
        lat=n-(j+.5)*(n-s)/ny;row=[]
        for i in range(nx):
            lon=w+(i+.5)*(e-w)/nx
            if regional:
                h=2400*math.exp(-((lon-21.1)**2+(lat-10)**2)/.22)-900*math.exp(-((lon-20.6)**2+(lat-10.5)**2)/.08)
            else:h=1800*math.cos(math.radians(lat))**2*math.sin(math.radians(lon*3))+800*math.sin(math.radians(lat*4))
            row.append(h)
        rows.append(row)
    return azl.PlanetaryRaster(rows,((e-w)/nx,0,w,0,(s-n)/ny,n),
        azl.PlanetaryContext.for_body(body,latitude_type='planetographic' if body==azl.EARTH else 'planetocentric'),azl.BodySource('synthetic:azimlib-phase-b','1',
        'Analytic waves/global or Gaussian hills/regional; not observed topography'),
        'BSD-3-Clause',copyright='Copyright (c) 2026 Kernerian')


def mapped(body,method='equirectangular',*,regional=False,polar=False,shade=False):
    r=dem(body,regional=regional)
    kw={'central_longitude':21,'central_latitude':10} if method=='transverse_mercator' else {'central_longitude':20,'central_latitude':90} if polar else {'central_longitude':20,'central_latitude':15} if method=='orthographic' else {}
    f,ax=azl.subplots(body=body,projection=method,projection_kw=kw,figsize=(7.5,5.5),dpi=100)
    if regional:ax.set_extent((19,23,8,12))
    if polar:ax.set_extent((-180,180,45,90));r=r.crop((-180,180,45,90))
    if shade:r=r.hillshade(azl.GeometricLight(r.context,direction=(1,-.4,.8)))
    layer=ax.raster(r,cmap='gray' if shade else 'terrain')
    ax.colorbar(layer,label='Incidence cosine (0–1)' if shade else 'Synthetic elevation (m)',shrink=.8)
    ax.set_title(body.name+' · '+method,fontsize=14)
    ax.subtitle('Synthetic '+('geometric hillshade' if shade else 'reference-surface elevation')+' · '+body.shape,fontsize=10)
    ax.set_xlabel('East longitude (°)');ax.set_ylabel(r.context.latitude_type+' latitude (°)')
    ax.grid(True,step=1 if regional else 30,labels=regional)
    if regional:
        ax.route([(19.4,8.5),(22.4,11.3)],color='#b51f38',linewidth=1.5,label='Surface geodesic')
        ax.scale_bar(length=25,units='km');ax.legend(loc='upper left')
    f.text(.5,.015,'Explicit static Body frame; no ephemeris, real terrain, or atmosphere.',ha='center',fontsize=8)
    return f,dict(body=body.identifier,projection=method,model=body.shape,units='XY metres / elevation metres',
                  data='synthetic analytic field; BSD-3-Clause',grid=list(r.shape),limits='Static reference ellipsoid/sphere; no measured terrain accuracy')


def terrain(body,*,global_view=False,textured=False):
    r=dem(body,regional=not global_view,shape=(24,48) if global_view else (19,25))
    f=azl.figure(body=body,figsize=(7.5,5.5),dpi=100);ax=f.add_subplot(111,projection='3d')
    t=ax.terrain(r,origin=None if global_view else (21,10))
    if textured:
        colors=tuple(tuple((int(70+100*(i%4)/3),int(70+100*(j%4)/3),120,255) for i in range(8)) for j in range(8))
        t.set_texture((8,8,bytes(v for row in colors for pixel in row for v in pixel)),uv=tuple((i/(r.shape[1]-1),j/(r.shape[0]-1)) for j in range(r.shape[0]) for i in range(r.shape[1])))
    else:ax.geometric_light(azl.GeometricLight(r.context,direction=(.8,-.6,1)),shadows=not global_view,max_edge_m=10000,ambient=.2,diffuse=.8)
    ax.view_init(elev=35,azim=-60);ax.set_vertical_exaggeration(1 if global_view else 4)
    ax.set_title(body.name+' · '+('body-fixed 3D' if global_view else 'regional terrain / ENU metres'),fontsize=14)
    ax.set_xlabel('X (m)' if global_view else 'East (m)');ax.set_ylabel('Y (m)' if global_view else 'North (m)');ax.set_zlabel('Z (m)' if global_view else 'Up (m)')
    f.text(.5,.02,'Synthetic terrain · '+('coarse cell-centre mesh; open seam/polar caps; vertical ×1' if global_view else 'physical heights preserved; visual vertical exaggeration ×4'),ha='center',fontsize=9)
    return f,dict(body=body.identifier,projection='existing 3D camera / '+('fixed XYZ' if global_view else 'exact ENU'),
                  model=body.shape,units='metres',data='synthetic Gaussian hills/waves; BSD-3-Clause',grid=list(r.shape),
                  limits='Coarse mesh, finite resolution; visual exaggeration does not change DEM or physical shadow geometry')


def lunar_profile():
    r=dem(azl.MOON,regional=True);s=azl.BodySurface(r.context)
    profile=r.profile((19.2,10),(22.8,10),samples=61,projection=s.projection('equirectangular'))
    f=azl.figure(body=azl.MOON,figsize=(11,5),dpi=100)
    f.subplots_adjust(wspace=.65)
    ax=f.add_subplot(121);ax.set_extent((19,23,8,12));layer=ax.raster(r,cmap='terrain')
    ax.route([(19.2,10),(22.8,10)],color='#bd2e34',linewidth=2);ax.scale_bar(length=10,units='km')
    ax.set_title('Moon · selected region');ax.colorbar(layer,label='Elevation (m)',shrink=.75)
    chart=f.add_subplot(122);chart.set_extent((0,1,0,1))
    distance=profile.distance_m[-1]/1000
    line,=chart.plot([v/profile.distance_m[-1] for v in profile.distance_m],[(h+1000)/4000 for h in profile.elevation_m],
                    color='#bd2e34',linewidth=2)
    line.set_transform(chart.transAxes)
    ticks=(0,.25,.5,.75,1)
    chart.set_xticks(ticks,labels=[f'{v*distance:.1f}' for v in ticks])
    chart.set_yticks(ticks,labels=[str(int(v*4000-1000)) for v in ticks])
    chart.set_xlabel('Surface geodesic distance (km)');chart.set_ylabel('Elevation above reference sphere (m)');chart.set_title('Geodesic elevation profile')
    f.text(.5,.02,f'Synthetic DEM · ground length {distance:.3f} km; projected length {profile.projected_distance_m[-1]/1000:.3f} km (distinct).',ha='center',fontsize=9)
    return f,dict(body='moon',projection='equirectangular / profile in layout coordinates',model='sphere',units='m / km',data='synthetic; BSD-3-Clause',
                  limits='61 geodesic samples; strict bilinear NoData; terrain resolution independent of sample count')


def incidence():
    r=dem(azl.MARS);light=azl.GeometricLight(r.context,direction=(1,-.3,.4))
    values=[[light.incidence(*r.geographic(i,j,center=True)) for i in range(r.shape[1])] for j in range(r.shape[0])]
    from dataclasses import replace
    r=replace(r,values=values,unit='1',history=('surface normal dot explicit light',))
    f,ax=azl.subplots(body=azl.MARS,figsize=(7.5,5.5),dpi=100)
    layer=ax.raster(r,cmap='viridis',vmin=-1,vmax=1);ax.colorbar(layer,label='Signed cosine of incidence',shrink=.8)
    curve=light.terminator();ax.plot([p[0] for p in curve],[p[1] for p in curve],color='#e54838',linewidth=2)
    ax.set_title('Mars · geometric incidence and terminator');ax.set_xlabel('East longitude (°)');ax.set_ylabel('Planetocentric latitude (°)')
    f.text(.5,.02,'Explicit fixed-frame direction (1, −0.3, 0.4); ideal oblate normal; no clock/atmosphere.',ha='center',fontsize=9)
    return f,dict(body='mars',projection='equirectangular',model='ellipsoid',units='dimensionless cosine',data='analytic geometry; no downloaded data',limits='Not a solar ephemeris or atmospheric model')


def comparison():
    f=azl.figure(figsize=(10,5.5),dpi=100)
    for slot,b in ((121,azl.EARTH),(122,azl.MARS)):
        ax=f.add_subplot(slot,body=b);ax.set_extent((19,23,8,12));ax.raster(dem(b,regional=True),cmap='terrain')
        ax.scale_bar(length=25,units='km');d=azl.BodySurface(ax.get_context()).distance((19,10),(23,10))/1000
        ax.set_title(f'{b.name} · width at 10° = {d:.1f} km',fontsize=12);ax.set_xlabel('Longitude (°)');ax.set_ylabel('Latitude (°)')
    f.suptitle('Independent Body contexts · equal angular extents, different ground scale',fontsize=13)
    f.text(.5,.02,'Synthetic equal-valued fields do not represent measured terrain; CPU renderer.',ha='center',fontsize=9)
    return f,dict(body='earth + mars',projection='existing Earth default / metric Mars EQC',model='two independent oblate ellipsoids',units='metres / km',data='synthetic; BSD-3-Clause',limits='Panel sizes normalized visually, not equal physical scale')


def earth():
    f,ax=azl.subplots(projection='orthographic',projection_kw={'central_longitude':-50,'central_latitude':10},figsize=(7,5.5),dpi=100)
    ax.map('world');ax.grid(True,step=30);ax.set_title('Earth · preserved terrestrial orthographic')
    return f,dict(body='earth',projection='legacy orthographic',model='existing spherical projection / Earth context',units='existing projection metres',data='bundled Natural Earth, public domain',limits='Unchanged 0.4.0 projection formula; not substituted by the new oblate orthographic')


def main(output,only=None,profile_memory=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    try:revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    except (OSError,subprocess.CalledProcessError):revision='source archive'
    cases=[('earth-globe',earth),('earth-regional',lambda:mapped(azl.EARTH,regional=True)),
        ('mars-global',lambda:mapped(azl.MARS)),('mars-orthographic',lambda:mapped(azl.MARS,'orthographic')),
        ('mars-regional',lambda:mapped(azl.MARS,'transverse_mercator',regional=True)),('mars-polar',lambda:mapped(azl.MARS,'stereographic',polar=True)),
        ('mars-hillshade',lambda:mapped(azl.MARS,regional=True,shade=True)),('mars-terrain',lambda:terrain(azl.MARS)),
        ('mars-global-3d',lambda:terrain(azl.MARS,global_view=True)),('mars-texture',lambda:terrain(azl.MARS,textured=True)),
        ('mars-incidence',incidence),('moon-global',lambda:mapped(azl.MOON)),('moon-profile',lunar_profile),
        ('moon-hillshade',lambda:mapped(azl.MOON,regional=True,shade=True)),('venus-global',lambda:mapped(azl.VENUS)),
        ('mercury-global',lambda:mapped(azl.MERCURY)),('comparison',comparison)]
    records=[]
    if only:
        unknown=set(only)-{name for name,_ in cases}
        if unknown:raise ValueError('Unknown scenes: '+str(sorted(unknown)))
        cases=[p for p in cases if p[0] in only]
    for name,build in cases:
        if profile_memory:tracemalloc.start()
        t=time.perf_counter();f,meta=build();build_ms=(time.perf_counter()-t)*1000
        cold=time.perf_counter();f.to_scene();cold=(time.perf_counter()-cold)*1000
        warm=[]
        for _ in range(3):
            t=time.perf_counter();f.to_scene();warm.append((time.perf_counter()-t)*1000)
        files=[];t=time.perf_counter()
        for fmt in ('png','svg','pdf'):
            p=output/(name+'.'+fmt);f.savefig(p);files.append(dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size))
        export_ms=(time.perf_counter()-t)*1000;peak=None
        if profile_memory:_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        azl.close(f)
        records.append(dict(name=name,**meta,pixels=[round(v*f.dpi) for v in f.figsize],dpi=f.dpi,build_ms=build_ms,first_scene_ms=cold,warm_scene_ms=warm,warm_median_ms=statistics.median(warm),
                            export_three_formats_ms=export_ms,peak_python_tracemalloc_bytes=peak,files=files))
        print(name,flush=True)
    report=dict(version=azl.__version__,source_revision=revision,working_tree='Check companion validation record for source snapshot/commit',
                platform=platform.platform(),python=platform.python_version(),dimensions='750x550 or 1000x550 at 100 DPI (Earth 700x550)',
                methodology='Sequential CPU, 1 first scene + 3 warm scenes; tracemalloc='+str(profile_memory)+'; diagnostic timings, not a p95/FPS guarantee',scenes=records)
    (output/'gallery.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
    cards=[]
    for row in records:
        links=' · '.join(f'<a href="{name}.{fmt}">{fmt.upper()}</a>' for fmt in ('png','svg','pdf') for name in (row['name'],))
        cards.append('<section><h2>'+html.escape(row['name'])+'</h2><p>'+html.escape(' | '.join(str(row[k]) for k in ('body','projection','model','units','data','limits')))+f'</p><p>{links}</p><img src="{row["name"]}.png" alt="{row["name"]}"></section>')
    (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Azimlib Phase B</title><style>body{font:16px system-ui;max-width:1100px;margin:40px auto;background:#fafafa;color:#24313b}section{background:white;padding:20px;margin:25px 0;border:1px solid #ddd}img{max-width:100%}p{line-height:1.5}</style><h1>Azimlib '+html.escape(azl.__version__)+' · Phase B</h1><p>Azimlib-rendered PNG/SVG/PDF. Synthetic non-Earth data; no mission imagery. Static models only. Source base '+html.escape(revision)+'. See gallery.json and the validation record.</p>'+''.join(cards),'utf8')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--only',action='append');p.add_argument('--profile-memory',action='store_true');args=p.parse_args()
    main(args.output,args.only,args.profile_memory)

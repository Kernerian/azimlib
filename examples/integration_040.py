"""Offline integration: synthetic city, local search, routing, CRS and overlay.

All city features and names are original synthetic inputs, not real addresses.
No downloads or reference engine. See the separate physical-light/sky examples.
"""
import hashlib,json,tempfile
from pathlib import Path
import azimlib as azl
from azimlib._pbf_decode import OSMRecord

POINTS=((-46.640,-23.550),(-46.635,-23.550),(-46.635,-23.545))
PROVENANCE='Azimlib original synthetic city; not real addresses or a navigational product'
def data():
    raw=json.dumps(POINTS,separators=(',',':')).encode()
    source=azl.RoutingSource('integration-city','1','BSD-3-Clause','Kernerian',PROVENANCE,'urn:azimlib:synthetic:integration-city',hashlib.sha256(raw).hexdigest())
    records=[OSMRecord('node',i+1,{},p) for i,p in enumerate(POINTS)]
    records.append(OSMRecord('way',10,{'highway':'residential','name':'Synthetic survey street'},refs=(1,2,3)))
    graph=azl.RoadGraph.from_records(records,source=source,profile=azl.RoutingProfile('foot'))
    gsource=azl.GeocodingSource(**source.as_dict())
    records=tuple(azl.GeocodingRecord(str(i),'poi',(name,),azl.Geometry('Point',point),source.id) for i,name,point in ((1,'Synthetic start',POINTS[0]),(3,'Synthetic laboratory',POINTS[-1])))
    with tempfile.TemporaryDirectory(prefix='azimlib-synthetic-city-') as temporary:
        with azl.LocalGeocoder.build(Path(temporary)/'index',records,sources=(gsource,)) as index:
            start=index.search('Synthetic start')[0];end=index.search('Synthetic laboratory')[0]
            route=graph.route(start,end)
            reverse=index.reverse(*POINTS[-1],radius_m=1)[0]
            if reverse.record.id!='3':raise AssertionError('Geocoder/routing coordinate contract differs')
    return graph,route

def box(w,s,e,n):return azl.Geometry('Polygon',(((w,s),(e,s),(e,n),(w,n),(w,s)),))

def make_city():
    graph,route=data();area=box(-46.638,-23.553,-46.632,-23.547)
    clipped=azl.intersection(route.geometry,area).geometry
    transform=azl.Transformer(4979,4978)
    errors=[]
    for lon,lat in POINTS:
        recovered=transform.inverse().transform(*transform.transform(lon,lat,0))
        errors.append(max(abs(recovered[0]-lon),abs(recovered[1]-lat)))
    if max(errors)>1e-9:raise AssertionError('Geocentric route roundtrip drift')
    fig,axes=azl.subplots(1,2,figsize=(9,4.5))
    fig.subplots_adjust(left=.12,right=.98,bottom=.20,top=.82,wspace=.4)
    for ax in axes:
        ax.set_extent((-46.642,-46.630,-23.554,-23.542))
        ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
        ax.xaxis.set_major_formatter(azl.ticker.LongitudeFormatter(number_format='.3f'))
        ax.yaxis.set_major_formatter(azl.ticker.LatitudeFormatter(number_format='.3f'))
        ax.grid(False)
    route_layer=axes[0].route(route,color='#277da8',linewidth=1.5,arrow=False,label='Offline foot route',fit=False)
    axes[0].scatter([p[0] for p in POINTS],[p[1] for p in POINTS],s=25,color='#bf6347')
    axes[0].legend(fontsize=8);axes[0].scale_bar(loc='lower right');axes[0].north_arrow(loc='upper left')
    axes[0].set_title('Search → route → geographic Artists',fontsize=10)
    axes[1].geojson(area,facecolor='#edf2f4',edgecolor='#889ca6',linewidth=.6,hatch='///',fit=False,label='Synthetic study area')
    axes[1].geojson(clipped,color='#8466a5',linewidth=2,fit=False,label='Exact planar clipped route')
    axes[1].legend(fontsize=8);axes[1].set_title('Topology + geocentric roundtrip',fontsize=10)
    fig.text(.5,.025,'Original synthetic city · BSD-3-Clause · no live navigation',ha='center',fontsize=8)
    return fig,axes,dict(graph=graph,route=route,route_layer=route_layer,clipped=clipped,crs_max_degrees=max(errors))

if __name__=='__main__':make_city()[0].show(block=True)

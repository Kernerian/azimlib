"""0.4 source development: own offline routing, editable layer and playback.

Uses the verified optional OSM catalog; no download, address query or live traffic.
"""
import argparse
from pathlib import Path
import azimlib as azl


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--show',action='store_true')
    args = parser.parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    catalog = azl.DatasetCatalog(Path(__file__).resolve().parents[1]/'optional-data/urban-sao-paulo-1.0/catalog.json')
    graph = azl.RoadGraph.from_catalog(catalog,'urban-sao-paulo',profile=azl.RoutingProfile('foot'))
    start = next(iter(graph.edges.values())).start
    ends = sorted(graph.nodes,key=lambda n:azl.haversine(graph.nodes[start].coordinate,graph.nodes[n].coordinate),reverse=True)
    for end in ends[:100]:
        try: route = graph.route(start,end); break
        except azl.RoutingError: continue
    else: raise RuntimeError('No nontrivial route in the imported coverage')
    fig,ax = azl.subplots(figsize=(7,6))
    ax.geojson(catalog.load('urban-sao-paulo'),facecolor='#f1f1f1',edgecolor='#a7afb5',linewidth=.5)
    layer = ax.route(route,color='#2878b5',linewidth=2.5,arrow=False,label='Rota a pé · rede OSM',fit=False)
    layer.set_picker(True)
    for snap,label,color in ((route.stops[0],'Origem','#29965f'),(route.stops[-1],'Destino','#d95f40')):
        ax.scatter([snap.coordinate[0]],[snap.coordinate[1]],s=42,color=color,label=label)
    ax.legend(loc='upper right',fontsize=9); ax.scale_bar(loc='lower right'); ax.grid(False)
    ax.set_xlabel('Longitude'); ax.set_ylabel('Latitude')
    ax.xaxis.set_major_formatter(azl.ticker.LongitudeFormatter(number_format='.3f'))
    ax.yaxis.set_major_formatter(azl.ticker.LatitudeFormatter(number_format='.3f'))
    ax.set_title(f'Roteamento local · {route.distance_m:.0f} m\n{route.duration_s/60:.1f} min estimados · sem trânsito ao vivo',fontsize=12)
    animation = route.playback(ax,frames=100,autoplay=False,s=50,color='#9a66b0',edgecolor='white',label='Playback estimado')
    animation.seek(50,draw=False)
    fig.text(.5,.025,route.source.attribution,ha='center',fontsize=8)
    fig.subplots_adjust(left=.16,right=.96,bottom=.16,top=.86)
    for extension in ('png','svg'): fig.savefig(args.output/f'local-routing.{extension}',dpi=150)
    if args.show:
        # Playback uses the own viewer timer after the window has opened.
        animation.autoplay = True
        azl.show()
    animation.close(); azl.close(fig)


if __name__=='__main__': main()

"""Reproducible offline gallery. All thematic numbers are explicitly synthetic.

python examples/gallery.py --output gallery [--png]
"""
from pathlib import Path
import argparse
import random
import azimlib as az


def hydrography():
    fig, ax = az.subplots(figsize=(9.0, 10.7))
    ax.ocean("#dbeaf5")
    ax.countries(facecolor="#d9d9d9", edgecolor="#777777", linestyle="--", linewidth=.7)
    ax.map("brazil", facecolor="white", edgecolor="black", linewidth=1.1)
    ax.states(edgecolor="#222222", linewidth=.65, facecolor="none")
    ax.rivers(color="#141414", linewidth=1.2, label="Rios · Natural Earth")
    ax.lakes(facecolor="#bdcfd8", edgecolor="none", linewidth=0)
    ax.set_extent((-76,-33,-36,7))
    ax.grid(step=5, color="#a5acb0", linestyle="--", linewidth=.5, alpha=.7)
    ax.set_title("HIDROGRAFIA BRASILEIRA", fontsize=25, fontweight="bold", color="black")
    ax.subtitle("Rios e limites territoriais", fontsize=17, color="black")
    for name,x,y in [("VENEZUELA",-67,4.7),("GUIANA",-58.8,5.2),("SURINAME",-55.4,4.8),
                     ("GUIANA\nFRANCESA",-51.8,3.2),("COLÔMBIA",-72.5,1.2),("PERU",-73,-13.3),
                     ("BOLÍVIA",-66,-16),("PARAGUAI",-58,-23.3),("ARGENTINA",-64,-29),("URUGUAI",-57,-32.4)]:
        ax.text(x,y,name,fontsize=10,ha="center",fontweight="bold",color="#292929")
    ax.text(-38,-2,"OCEANO\nATLÂNTICO",fontsize=15,ha="center",color="#4c6597",fontweight="bold")
    ax.text(-73,-23,"OCEANO\nPACÍFICO",fontsize=14,ha="center",color="#4c6597",fontweight="bold")
    ax.legend(title="Legenda",loc="lower right",fontsize=11)
    ax.scale_bar(loc="lower left")
    ax.north_arrow(loc="upper left",size=26,color="black")
    ax.overview(loc="upper right")
    fig.text(.5,.022,"Natural Earth · rios generalizados; não representa navegabilidade · Azimlib",fontsize=9,ha="center",color="#555555")
    return fig


def thematic():
    fig, axes = az.subplots(1,2,figsize=(13,7))
    states=az.datasets.load("states")
    data=[15+((i*37+11)%180) for i in range(len(states["features"]))]
    a,b=axes
    for ax in axes:
        ax.map("brazil",facecolor="#f5f5f0",edgecolor="#9dafa8")
        ax.set_extent((-75,-33,-35,7))
        ax.grid(step=10)
    layer=a.choropleth(states,data,cmap="ocean",bins=5)
    a.set_title("Valores por estado",fontsize=19,fontweight="bold")
    a.subtitle("Dados sintéticos · intervalos iguais")
    a.colorbar(layer,label="Índice demonstrativo")
    a.north_arrow(size=22)
    points=[(-46.63,-23.55,900),(-43.17,-22.9,610),(-47.88,-15.8,360),(-60.02,-3.12,440),(-38.5,-12.98,300),(-34.9,-8.1,220)]
    b.states(facecolor="white",edgecolor="#bbc5c5")
    b.scatter([p[0] for p in points],[p[1] for p in points],s=[p[2] for p in points],color="#d07035",alpha=.75,edgecolor="white",linewidth=1.4,label="Magnitude sintética")
    b.route([(-60.02,-3.12),(-47.88,-15.8),(-46.63,-23.55)],color="#226c83",linewidth=1.8,linestyle="--",arrow=True,label="Rota demonstrativa")
    b.annotate("São Paulo",(-46.63,-23.55),xytext=(-83,33),fontsize=10,background="white",color="#365966")
    b.set_title("Pontos proporcionais e rotas",fontsize=19,fontweight="bold")
    b.subtitle("Áreas dos símbolos ∝ valores · geodésicas esféricas")
    b.legend(loc="lower left")
    overview=b.inset((.04,.72,.24,.23))
    overview.map("world",facecolor="#d7dfd8",edgecolor="#889a8d",linewidth=.25)
    overview.polygon([(-75,-35),(-33,-35),(-33,7),(-75,7)],facecolor="none",edgecolor="#d66b30",linewidth=1.5)
    fig.text(.5,.028,"AZIMLIB  /  dados temáticos inteiramente sintéticos",fontsize=9,ha="center",color="#65747c")
    return fig


def projections():
    fig,axes=az.subplots(2,3,figsize=(14,9))
    specifications=[("equirectangular",{},"Equiretangular"),("mercator",{},"Mercator"),
                    ("equalearth",{},"Equal Earth"),("orthographic",{"central_longitude":-55,"central_latitude":-15},"Ortográfica"),
                    ("lambert",{"central_longitude":-55,"central_latitude":-15,"standard_parallels":(-10,-30)},"Lambert conforme"),
                    ("albers",{"central_longitude":-55,"central_latitude":-15,"standard_parallels":(-10,-30)},"Albers equivalente")]
    for ax,(name,kwargs,label) in zip(axes.flat,specifications):
        ax.projection=az.get_projection(name,**kwargs)
        ax.ocean("#eaf3f6")
        ax.map("world" if name in ("equirectangular","mercator","equalearth","orthographic") else "brazil",facecolor="#b8cab0",edgecolor="#6f846b",linewidth=.35)
        if name in ("lambert","albers"):
            ax.states(linewidth=.3)
        else:
            ax.set_extent((-180,180,-80,84))
        ax.grid(step=30 if name not in ("lambert","albers") else 10,labels=False,linewidth=.35)
        ax.set_title(label,fontsize=15,fontweight="bold")
    fig.text(.5,.025,"Seis projeções implementadas no núcleo · modelos esféricos",fontsize=10,ha="center",color="#61777e")
    return fig


def density():
    random.seed(123)
    lon=[random.gauss(-46.6,1.6) for _ in range(150)]+[random.gauss(-43.2,.9) for _ in range(100)]
    lat=[random.gauss(-23.4,1.1) for _ in range(150)]+[random.gauss(-22.8,.7) for _ in range(100)]
    fig,ax=az.subplots(figsize=(8,7),projection="mercator")
    ax.map("brazil",facecolor="#eef0e8")
    layer=ax.density(lon,lat,bins=32,smoothing=1.2,cmap="sunset",alpha=.82)
    ax.states(facecolor="none",linewidth=.7,zorder=4)
    ax.set_extent((-51,-39,-28,-18))
    ax.grid(step=2)
    ax.set_title("Densidade de pontos",fontsize=21,fontweight="bold")
    ax.subtitle("250 pontos sintéticos · suavização gaussiana em grade angular")
    ax.colorbar(layer,label="Contagem suavizada por célula (não por km²)")
    ax.scale_bar()
    return fig


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=Path("gallery"))
    parser.add_argument("--png",action="store_true")
    parser.add_argument("--only",choices=["hydrography","thematic","projections","density"])
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    for name,create in [("hydrography",hydrography),("thematic",thematic),("projections",projections),("density",density)]:
        if args.only and name!=args.only:
            continue
        fig=create()
        for suffix in ("svg","html","png") if args.png else ("svg","html"):
            target=args.output/f"{name}.{suffix}"
            path=fig.show(backend="browser",open_browser=False,path=target) if suffix=="html" else fig.savefig(target)
            print(path,flush=True)
        az.close(fig)

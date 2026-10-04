"""Run after `pip install -e .`: python examples/quickstart.py"""
import azimlib.pyplot as plt

fig, ax = plt.subplots(figsize=(8, 9), subplot_kw={"projection": "mercator"})
ax.map("brazil", facecolor="white", edgecolor="black")
ax.states(edgecolor="#606060", linewidth=.6)
ax.rivers(color="#1f77b4", linewidth=1, label="Rios")
ax.scatter(lon=[-46.63, -43.17], lat=[-23.55, -22.90], s=[50, 75], c="red", label="Cidades")
ax.set_title("Brasil", fontsize=20)
ax.grid(linestyle="--", color="#aaaaaa")
ax.legend(title="Legenda")
ax.scale_bar()
ax.north_arrow()
ax.overview()
fig.savefig("brasil.svg")
plt.show()

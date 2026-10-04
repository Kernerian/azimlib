"""Extract only CC0 color tables from an installed reference; no runtime import."""
import ast,json,sys
from pathlib import Path
source=Path(sys.argv[1]);tree=ast.parse(source.read_text())
names={'_viridis_data':'viridis','_magma_data':'magma','_inferno_data':'inferno','_plasma_data':'plasma'}
tables={}
for node in tree.body:
    if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in names:
        tables[names[node.targets[0].id]]=['#'+''.join(f'{round(c*255):02x}' for c in rgb) for rgb in ast.literal_eval(node.value)]
assert len(tables)==4 and all(len(v)==256 for v in tables.values())
target=Path(__file__).resolve().parents[1]/'src/azimlib/data/colormaps.json'
target.write_text(json.dumps({'source':'https://github.com/BIDS/colormap','license':'CC0-1.0','authors':['Nathaniel J. Smith','Stefan van der Walt','Eric Firing'],'tables':tables},separators=(',',':')),encoding='utf-8')

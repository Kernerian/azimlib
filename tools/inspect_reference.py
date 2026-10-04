"""Development-only inventory. Matplotlib is never imported by the library."""
from pathlib import Path
import inspect
import json
import importlib
import matplotlib

modules=['artist','figure','axes','axis','lines','patches','collections','text','ticker','colors','cm',
         'transforms','gridspec','layout_engine','legend','colorbar','backend_bases','widgets','animation',
         'image','contour','tri','units','scale','dates','style','pyplot']
result={'version':matplotlib.__version__,'scope':'Public module symbols, inventory only; not an Azimlib compatibility claim','modules':{}}
for name in modules:
    module=importlib.import_module('matplotlib.'+name)
    result['modules'][name]={key:('class' if inspect.isclass(value) else 'function' if callable(value) else 'object')
        for key,value in vars(module).items() if not key.startswith('_')
        and (getattr(value,'__module__','').startswith('matplotlib') or key in ('rcParams','colormaps'))}
target=Path(__file__).resolve().parents[1]/'docs/matplotlib-reference.json'
target.write_text(json.dumps(result,indent=2),encoding='utf-8')
print(f'Inventoried {len(modules)} modules; {sum(len(v) for v in result["modules"].values())} public symbols')

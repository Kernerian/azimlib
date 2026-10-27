"""Pinned local Lucide assets; safe parsing, hashes and no runtime network."""
from functools import lru_cache
import hashlib,json
from pathlib import Path
CARTOGRAPHIC_ALIASES=dict(city='building',village='map-pin',port='anchor',gold='coins',salt='diamond',ivory='original:ivory',fortress='castle',mine='pickaxe',monument='landmark',landing='flag',rover='bot',probe='satellite',instrument='microscope',battle='original:battle',temple='landmark',base='warehouse',**{'scientific-point':'crosshair','arrow':'arrow-right'})
@lru_cache(maxsize=1)
def _definitions():
 from .thematic_assets import AssetSource,parse_svg
 root=Path(__file__).resolve().parent/'assets/lucide';manifest=json.loads((root/'manifest.json').read_text('utf8'));result={}
 for row in manifest['icons']:
  raw=(root/row['file']).read_bytes()
  if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Lucide integrity mismatch: '+row['name'])
  result[row['name']]=parse_svg(raw,name='lucide:'+row['name'],source=AssetSource(row['source'],row['license'],'Lucide Icons and Contributors; Feather-derived icons retain Cole Bemis MIT notice',row['sha256']))
 return result

def lucide_catalog():return dict(_definitions())

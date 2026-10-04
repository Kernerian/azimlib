"""Build reusable font metrics; fontTools is a development tool only."""
import json
from pathlib import Path
from fontTools.ttLib import TTFont

folder=Path(__file__).resolve().parents[1]/'src/azimlib/fonts'
result={}
for path in folder.glob('*.ttf'):
    font=TTFont(path)
    cmap=font.getBestCmap()
    ids=font.getReverseGlyphMap()
    result[path.stem]={
        'units':font['head'].unitsPerEm,
        'chars':{chr(code):[ids[glyph],font['hmtx'][glyph][0]] for code,glyph in cmap.items()},
        'bounds':{chr(code):[getattr(font['glyf'][glyph],'yMin',0),getattr(font['glyf'][glyph],'yMax',0)] for code,glyph in cmap.items()},
        'kern':{f'{ids[a]},{ids[b]}':v for table in font['kern'].kernTables if table.version==0
                for (a,b),v in table.kernTable.items()},
    }
(folder/'metrics.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')),encoding='utf-8')

"""Development reference only; installed Matplotlib never enters runtime."""
import json
from pathlib import Path

CASES=(('line','linewidth','lw',1.),('line','linestyle','ls','--'),
       ('line','color','c','red'),('line','markersize','ms',5.),
       ('line','markeredgewidth','mew',.8),('line','markerfacecolor','mfc','red'),
       ('line','markeredgecolor','mec','black'),('line','antialiased','aa',True),
       ('text','fontsize','size',12.),('text','fontweight','weight','bold'),
       ('text','fontfamily','family','DejaVu Sans'),
       ('text','horizontalalignment','ha','center'),('text','verticalalignment','va','top'))

def inspect():
    import matplotlib
    from matplotlib import cbook
    from matplotlib.lines import Line2D
    from matplotlib.text import Text
    results=[]
    for kind,name,alias,value in CASES:
        artist=Line2D if kind=='line' else Text
        row=dict(kind=kind,name=name,alias=alias,value=value,
                 normalized=cbook.normalize_kwargs({alias:value},artist))
        try:cbook.normalize_kwargs({name:value,alias:value},artist)
        except Exception as exc:row['conflict_error']=type(exc).__name__
        else:row['conflict_error']=None
        results.append(row)
    return dict(matplotlib_version=matplotlib.__version__,cases=results)

if __name__=='__main__':
    target=Path(__file__).resolve().parents[1]/'docs/style-alias-reference.json'
    target.write_text(json.dumps(inspect(),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(target)

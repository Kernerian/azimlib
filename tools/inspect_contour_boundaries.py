"""Development-only Matplotlib/Agg reference for the 0.2.0 contour boundary audit."""
import json
import math
from pathlib import Path
import warnings
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    cases=[]
    inputs=[(f'constant-{value:g}',[[value]*3]*3,7) for value in (0.,5.,-3.)]
    inputs.extend([
        ('outside',[[0,1,2]]*3,[3.,4.]),
        ('duplicate-levels',[[0,1,2]]*3,[1.,1.]),
        ('nonfinite-level',[[0,1,2]]*3,[math.nan]),
        ('empty-levels',[[0,1,2]]*3,[]),
        ('all-missing',[[math.nan]*3]*3,[1.,2.]),
        ('missing-center',[[0,1,2],[0,math.nan,2],[0,1,2]],[.5,1.5]),
        ('saddle',[[0,2,0],[2,0,2],[0,2,0]],[.5,1.5]),
    ])
    for name,values,levels in inputs:
        fig,ax=plt.subplots()
        with warnings.catch_warnings(record=True) as messages:
            warnings.simplefilter('always')
            try:
                contour=ax.contour([-54,-49,-44],[-26,-22,-18],values,levels=levels,corner_mask=False)
                groups=[sum(len(segment)>1 for segment in group) for group in contour.allsegs]
                case=dict(name=name,status='accepted',levels=contour.levels.tolist(),segments=groups,
                          labels_empty=not bool(ax.clabel(contour)))
                # Several empty/nonfinite cases are accepted by Matplotlib but
                # not every such ContourSet can construct a usable colorbar.
                try:
                    fig.colorbar(contour);fig.canvas.draw();case['colorbar']='drawn'
                except (ValueError,IndexError,ZeroDivisionError) as error:
                    case['colorbar']=type(error).__name__
            except (ValueError,TypeError) as error:
                case=dict(name=name,status='rejected',error=type(error).__name__)
            case['warnings']=[str(message.message) for message in messages]
            cases.append(case)
        plt.close(fig)
    target=Path(__file__).resolve().parents[1]/'docs/contour-boundaries-reference.json'
    target.write_text(json.dumps(dict(matplotlib=matplotlib.__version__,backend='Agg',
        corner_mask=False,cases=cases),indent=2,allow_nan=False),encoding='utf-8')
    print(target)


if __name__=='__main__':main()

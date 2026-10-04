"""Development-only setter states inspected in installed Matplotlib."""
import json
from pathlib import Path
import azimlib as azl

ROOT=Path(__file__).resolve().parents[1]


def inspect(module):
    fig,ax=module.subplots()
    try:
        line,=ax.plot([-52,-48],[-25,-21],'o--')
        line.set(linewidth='2.5',markersize='8',markeredgewidth=.6,alpha=.4)
        text=ax.set_title('Título',fontsize='12',fontweight=700,fontstyle='italic')
        text.set(rotation=30)
        spine=ax.spines['left'];spine.set(linewidth='1.2',color='red',visible=False)
        states=dict(line=dict(linewidth=line.get_linewidth(),markersize=line.get_markersize(),
                              markeredgewidth=line.get_markeredgewidth(),alpha=line.get_alpha()),
                    text=dict(fontsize=text.get_fontsize(),fontweight=text.get_fontweight(),
                              fontstyle=text.get_fontstyle(),rotation=text.get_rotation()),
                    spine=dict(linewidth=spine.get_linewidth(),visible=spine.get_visible()))
        rejected=[]
        for option in (dict(fontstyle='sideways'),dict(fontweight='unknown')):
            try:text.set(**option)
            except ValueError:rejected.append(option)
        return dict(states=states,rejected=rejected)
    finally:module.close(fig)


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as mpl
    own,reference=inspect(azl),inspect(mpl)
    assert own==reference,(own,reference)
    report=dict(matplotlib=matplotlib.__version__,azimlib=own,reference=reference,
                scope='Selected final setter states/rejected font properties. Own batch atomicity is stronger for audited classes; no general rollback or color validation claim.')
    (ROOT/'docs/artist-validation-reference.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Selected artist setter states and rejected font properties match installed Matplotlib.')


if __name__=='__main__':main()

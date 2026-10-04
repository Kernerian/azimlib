"""Developer reference checks. Matplotlib is never imported by Azimlib.

Run in the isolated Matplotlib reference environment with PYTHONPATH=src.
"""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as mpl
from matplotlib.cm import ScalarMappable as MPLMappable
from matplotlib.colors import Normalize as MPLNorm
import azimlib as az
from azimlib.cm import ScalarMappable
from azimlib.colors import Normalize
from azimlib.colorbar_render import colorbar_layout
from azimlib.scene import Text,Rect

def columns():
    mf,ma=mpl.subplots();af,aa=az.subplots()
    mh=[];ah=[]
    for i in range(5):
        mh.append(ma.plot([-9+i,-9+i],[-8,8],label=f'Item {i}')[0])
        ah.append(aa.line([(-9+i,-8),(-9+i,8)],label=f'Item {i}'))
    ml=ma.legend(handles=mh,ncols=2,loc='upper left')
    al=aa.legend(ah,ncols=2,loc='upper left');mf.canvas.draw()
    scene=af.to_scene()
    def grouped(values):
        groups={}
        for label,x in values:groups.setdefault(round(x,5),[]).append(label)
        return [groups[key] for key in sorted(groups)]
    renderer=mf.canvas.get_renderer()
    expected=grouped((t.get_text(),t.get_window_extent(renderer).x0) for t in ml.get_texts())
    actual=grouped((t.text,t.x) for t in scene.items if isinstance(t,Text) and t.text.startswith('Item'))
    assert actual==expected
    mpl.close(mf);az.close(af)
    return dict(matplotlib=expected,azimlib=actual)

def placement():
    mf,ma=mpl.subplots();af,aa=az.subplots()
    ma.scatter([6,7,8],[9.5,9.5,9.5],s=36,label='Points');ma.set_xlim(-10,10);ma.set_ylim(0,10)
    aa.scatter([6,7,8],[9.5,9.5,9.5],s=36,label='Points');aa.set_extent((-10,10,0,10))
    ml=ma.legend(loc='best');al=aa.legend(loc='best');mf.canvas.draw();af.to_scene()
    box=ml.get_window_extent(mf.canvas.get_renderer());axes=ma.get_window_extent()
    chosen='upper left' if box.x0<axes.x0+axes.width/2 and box.y0>axes.y0+axes.height/2 else 'other'
    assert chosen==al._last_loc=='upper left'
    mpl.close(mf);az.close(af)
    return dict(matplotlib=chosen,azimlib=al._last_loc)

def shared():
    records=[]
    for orientation in ('vertical','horizontal'):
        mf,mas=mpl.subplots(2,2,figsize=(8,8));af,aas=az.subplots(2,2,figsize=(8,8))
        ab=af.colorbar(ScalarMappable(Normalize(0,1)),ax=aas,orientation=orientation)
        mb=mf.colorbar(MPLMappable(norm=MPLNorm(0,1)),ax=mas,orientation=orientation,use_gridspec=False)
        mf.canvas.draw()
        # Compare reserved allocation, independent of map isotropic aspect.
        originals=[a.position for a in aas.flat]
        left=min(p[0] for p in originals);bottom=min(p[1] for p in originals)
        right=max(p[0]+p[2] for p in originals);top=max(p[1]+p[3] for p in originals)
        allocated,barbox=colorbar_layout(ab,(left*800,(1-top)*800,(right-left)*800,(top-bottom)*800))
        mplpositions=[tuple(a.get_position(original=True).bounds) for a in mas.flat]
        actual=[]
        for x,y,w,h in originals:
            nx=(allocated[0]+(x-left)*800*allocated[2]/((right-left)*800))/800
            ny=(allocated[1]+(top-y-h)*800*allocated[3]/((top-bottom)*800))/800
            nw=w*allocated[2]/((right-left)*800);nh=h*allocated[3]/((top-bottom)*800)
            actual.append((nx,1-ny-nh,nw,nh))
        mbbox=tuple(mb.ax.get_position().bounds)
        abbox=(barbox[0]/800,1-(barbox[1]+barbox[3])/800,barbox[2]/800,barbox[3]/800)
        error=max(abs(x-y) for p,q in zip(actual,mplpositions) for x,y in zip(p,q))
        error=max(error,max(abs(x-y) for x,y in zip(abbox,mbbox)))
        assert error<1e-9,(orientation,error,abbox,mbbox)
        records.append(dict(orientation=orientation,max_fraction_error=error,matplotlib_bar=mbbox,azimlib_bar=abbox))
        mpl.close(mf);az.close(af)
    return records

def explicit():
    rect=(.91,.2,.025,.6)
    mf,ma=mpl.subplots();mcax=mf.add_axes(rect)
    mf.colorbar(MPLMappable(norm=MPLNorm(0,1)),cax=mcax);mf.canvas.draw()
    af,aa=az.subplots();acax=af.add_axes(rect)
    ab=af.colorbar(ScalarMappable(Normalize(0,1)),cax=acax)
    scene=af.to_scene();expected=(rect[0]*640,(1-rect[1]-rect[3])*480,rect[2]*640,rect[3]*480)
    assert any(isinstance(i,Rect) and (i.x,i.y,i.width,i.height)==expected for i in scene.items)
    assert max(abs(a-b) for a,b in zip(mcax.get_position().bounds,rect))<1e-9
    mpl.close(mf);az.close(af)
    return dict(matplotlib=rect,azimlib=acax.position)

if __name__=='__main__':
    result=dict(matplotlib_version=matplotlib.__version__,columns=columns(),best=placement(),shared=shared(),cax=explicit())
    target=Path(__file__).resolve().parents[1]/'docs/composition-reference.json'
    target.write_text(json.dumps(result,indent=2),encoding='utf-8');print(target)

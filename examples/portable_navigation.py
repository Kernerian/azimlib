"""Portable linked map viewers: all axes, or groups by row/column."""
from pathlib import Path
import azimlib as azl
from shared_axes import create


folder=Path(__file__).resolve().parents[1]/'gallery'

def export(fig,name):
    fig.show(backend='browser',open_browser=False,path=folder/f'{name}.html')
    for extension in ('png','svg'):fig.savefig(folder/f'{name}.{extension}')
    print(name,flush=True)


if __name__=='__main__':
    fig,maps=create()
    maps[0,0].overview(context='brazil',width=100)
    export(fig,'linked-navigation');azl.close(fig)
    fig,maps=azl.subplots(2,2,sharex='col',sharey='row',figsize=(9,7),layout='constrained')
    for i,ax in enumerate(maps.flat):
        ax.map('brazil',facecolor='#f1f1f1',edgecolor='#555555',linewidth=.5,fit=False)
        ax.states(facecolor='none',edgecolor='#777777',linewidth=.4,fit=False)
        ax.set_title('Painel '+str(i+1));ax.set_xlabel('Longitude');ax.set_ylabel('Latitude');ax.label_outer()
    maps[0,0].set_extent((-58,-38,-34,-16))
    maps[1,1].set_extent((-54,-42,-28,-20))
    fig.suptitle('Azimlib · longitude por coluna, latitude por linha')
    export(fig,'linked-groups');azl.close(fig)

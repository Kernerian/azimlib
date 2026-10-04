"""Optional desktop integration check, using a withdrawn test window."""
from unittest.mock import patch
import tkinter
import azimlib as azl
from azimlib.scene import Text,Path

original= tkinter.Tk
def hidden_root(*args,**kwargs):
    root=original(*args,**kwargs)
    root.withdraw()
    return root

fig,ax=azl.subplots(figsize=(4,3))
ax.set_extent((-54,-44,-27,-19))
line,=ax.plot([-52,-48,-46],[-25,-23,-21],label='Route')
title=ax.set_title('Before');ax.legend();scale=ax.scale_bar(length=200)
events=[]
try:
    with patch.object(tkinter,'Tk',hidden_root):viewer=fig.show(block=False)
    fig.canvas.mpl_connect('draw_event',lambda event:events.append(fig.stale))
    with azl.ion():
        title.set_text('After');pending=viewer._pending
        line.set_color('red');scale.set_length(100)
        assert pending is not None and pending==viewer._pending
        assert fig.stale
    viewer.flush_events()
    assert events==[False],events
    assert not fig.stale
    assert any(isinstance(item,Text) and item.text=='After' for item in viewer.scene.items)
    assert any(isinstance(item,Path) and item.style.get('stroke')=='red' for item in viewer.scene.items)
    print('Tk: three edits coalesced into one draw; live scene and stale state verified.')
finally:
    azl.close(fig);azl.ioff()

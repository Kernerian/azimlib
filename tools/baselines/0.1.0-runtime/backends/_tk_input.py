"""Own conversion of Tk input into the familiar plotting event vocabulary."""
import sys
from ..backend_bases import MouseButton


def _state(event):
    # Tk uses '??' for substitutions that do not apply to Configure/other events.
    try:return int(getattr(event,'state',0))
    except (TypeError,ValueError):return 0


def modifiers(event,*,platform=None,exclude=None):
    system=sys.platform if platform is None else platform
    masks=(('ctrl',4,'control'),('alt',131072 if system=='win32' else 16 if system=='darwin' else 8,'alt'),
           ('shift',1,'shift'))
    if system!='win32':masks+=((('cmd',8,'cmd') if system=='darwin' else ('super',64,'super')),)
    state=_state(event)
    return tuple(name for name,mask,key in masks if state & mask and key!=exclude)


def key_name(event,*,platform=None):
    system=sys.platform if platform is None else platform
    character=getattr(event,'char','')
    if character and character.isprintable():key=character
    else:
        key=getattr(event,'keysym','').lower()
        if key.startswith('kp_'):key=key[3:]
        if key.startswith('page_'):key='page'+key[5:]
        if key.endswith(('_l','_r')):key=key[:-2]
        key={'return':'enter','prior':'pageup','next':'pagedown'}.get(key,key)
        if system=='darwin' and key=='meta':key='cmd'
    names=modifiers(event,platform=system,exclude=key)
    if character:names=tuple(name for name in names if name!='shift')
    return '+'.join((*names,key))


def mouse_button(event,*,platform=None):
    number=getattr(event,'num',None)
    if (sys.platform if platform is None else platform)=='darwin':number={2:3,3:2}.get(number,number)
    try:return MouseButton(number)
    except (ValueError,TypeError):return number


def pressed_buttons(event,*,platform=None):
    system=sys.platform if platform is None else platform
    order=(MouseButton.LEFT,MouseButton.RIGHT,MouseButton.MIDDLE) if system=='darwin' else (
        MouseButton.LEFT,MouseButton.MIDDLE,MouseButton.RIGHT)
    order+=MouseButton.BACK,MouseButton.FORWARD
    state=_state(event)
    return frozenset(button for offset,button in enumerate(order,8) if state & (1<<offset))

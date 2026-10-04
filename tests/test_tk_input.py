"""Input contracts recorded from Matplotlib; tests never import the reference."""
import json,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
import azimlib as azl
from azimlib.backend_bases import MouseButton
from azimlib.backends.tk import FigureWindow
from azimlib.backends._tk_input import key_name,modifiers,mouse_button,pressed_buttons
from azimlib.navigation import Navigation

REFERENCE=json.loads((Path(__file__).resolve().parents[1]/'docs/tk-input-reference.json').read_text(encoding='utf-8'))


class TkInputTests(unittest.TestCase):
    def setUp(self):
        self.fig,self.ax=azl.subplots(figsize=(4,3));self.ax.set_extent((-60,-40,-30,-10))
        self.v=object.__new__(FigureWindow);v=self.v
        v.figure=self.fig;v.scene=self.fig.to_scene();v.navigation=Navigation(self.fig)
        v._key=v._button=None;v._last_axes_ref=None
        v._callback_id=0;v._event_callbacks={};v.closed=False
        v.mode='';v.constraint=None;v.drag=None;v._overview_box=None;v.active=0
        v.widget=Mock();v.message=Mock();v.draw_idle=Mock()
        v.set_mode=Mock();v.save=Mock();v.close=Mock();v.window=Mock()

    def tearDown(self):azl.close('all')

    def center(self):
        x,y,w,h=self.v.scene.maps[0]['box'];return x+w/2,y+h/2

    def event(self,symbol='a',char='a',state=0,inside=True,**kwargs):
        x,y=self.center() if inside else (0,0)
        return SimpleNamespace(x=x,y=y,keysym=symbol,char=char,state=state,**kwargs)

    def test_keyboard_names_from_reference_in_three_mask_tables(self):
        for case in REFERENCE['keyboard']:
            with self.subTest(system=case['system'],char=case['char'],keysym=case['keysym'],state=case['state']):
                event=SimpleNamespace(char=case['char'],keysym=case['keysym'],state=case['state'])
                self.assertEqual(key_name(event,platform=case['system']),case['key'])

    def test_modifier_and_pressed_button_masks_from_reference(self):
        for case in REFERENCE['modifier_states']:
            with self.subTest(system=case['system'],state=case['state']):
                event=SimpleNamespace(state=case['state'])
                self.assertEqual(list(modifiers(event,platform=case['system'])),case['modifiers'])
                self.assertEqual(sorted(pressed_buttons(event,platform=case['system'])),case['buttons'])
        for case in REFERENCE['pointer']:
            with self.subTest(system=case['system'],button=case['num']):
                self.assertEqual(mouse_button(SimpleNamespace(num=case['num']),platform=case['system']),case['button'])

    def test_key_event_coordinates_release_and_mouse_key(self):
        events=[];self.v.mpl_connect('key_press_event',events.append)
        self.v.key(self.event('a','a',4))
        event=events[-1];self.assertEqual(event.key,'ctrl+a');self.assertIs(event.inaxes,self.ax)
        self.assertAlmostEqual(event.xdata,-50);self.assertAlmostEqual(event.ydata,-20)
        self.assertEqual(event.modifiers,frozenset())
        mouse=[];self.v.mpl_connect('motion_notify_event',mouse.append)
        self.v.motion(self.event('a','a',4|256))
        self.assertEqual(mouse[-1].key,'ctrl+a')
        self.assertEqual(mouse[-1].modifiers,frozenset(('ctrl',)))
        self.assertEqual(mouse[-1].buttons,frozenset((MouseButton.LEFT,)))
        self.v.key_up(self.event('a','a',4));self.v.motion(self.event())
        self.assertIsNone(mouse[-1].key)

    def test_shortcuts_respect_modifiers_case_and_configuration(self):
        for symbol,char,state in (('p','p',4),('P','P',1)):
            with self.subTest(symbol=symbol,state=state):
                self.v.key(self.event(symbol,char,state));self.v.set_mode.assert_not_called()
        self.v.key(self.event('p','p'));self.v.set_mode.assert_called_once_with('pan')
        self.v.key(self.event('s','s',4));self.v.save.assert_called_once()
        self.v.key(self.event('Escape',''));self.v.close.assert_not_called()
        with azl.rc_context({'keymap.pan':['ctrl+p'],'keymap.save':[]}):
            self.v.set_mode.reset_mock();self.v.save.reset_mock()
            self.v.key(self.event('p','p'));self.v.set_mode.assert_not_called()
            self.v.key(self.event('p','p',4));self.v.set_mode.assert_called_once_with('pan')
            self.v.key(self.event('s','s'));self.v.save.assert_not_called()
        calls=[];self.v.mpl_connect('key_press_event',lambda e:calls.append('key'))
        self.v.close.side_effect=lambda:calls.append('close')
        self.v.key(self.event('w','w',4));self.assertEqual(calls,['key','close'])

    def test_keymap_defaults_and_transactional_validation(self):
        for name,expected in REFERENCE['keymaps'].items():
            with self.subTest(name=name):self.assertEqual(azl.rcParams[name],expected)
        before=list(azl.rcParams['keymap.pan'])
        with self.assertRaises(ValueError):azl.rcParams.update({'keymap.pan':['ctrl+p'],'keymap.zoom':[4]})
        self.assertEqual(azl.rcParams['keymap.pan'],before)
        source=['ctrl+p']
        with azl.rc_context({'keymap.pan':source}):
            source.append('a');self.assertEqual(azl.rcParams['keymap.pan'],['ctrl+p'])
            azl.rcParams['keymap.pan']=' p, ctrl+p '
            self.assertEqual(azl.rcParams['keymap.pan'],['p','ctrl+p'])
        self.assertEqual(azl.rcParams['keymap.pan'],before)

    def test_double_click_middle_button_and_drag_button_state(self):
        presses=[];moves=[];releases=[]
        self.v.mpl_connect('button_press_event',presses.append)
        self.v.mpl_connect('motion_notify_event',moves.append)
        self.v.mpl_connect('button_release_event',releases.append)
        self.v.mode='pan'
        with patch.object(sys,'platform','win32'):
            self.v.press(self.event(num=2),dblclick=True)
            self.assertIsNone(self.v.drag)
            self.assertIs(presses[-1].button,MouseButton.MIDDLE)
            self.assertTrue(presses[-1].dblclick)
            self.v.motion(self.event(state=512));self.assertIs(moves[-1].button,MouseButton.MIDDLE)
            self.assertEqual(moves[-1].buttons,frozenset((MouseButton.MIDDLE,)))
            self.v.release(self.event(num=2));self.v.motion(self.event())
            self.assertIs(releases[-1].button,MouseButton.MIDDLE)
            self.assertIsNone(moves[-1].button)
        with patch.object(sys,'platform','darwin'):
            self.v.press(self.event(num=3));self.assertIsNone(self.v.drag)
            self.assertIs(presses[-1].button,MouseButton.MIDDLE)

    def test_axes_and_figure_transitions_match_reference_order(self):
        fig,axes=azl.subplots(1,2,figsize=(6,3))
        self.v.figure=fig;self.v.scene=fig.to_scene()
        trace=[]
        for channel in ('figure_enter_event','figure_leave_event','axes_enter_event','axes_leave_event','motion_notify_event'):
            def callback(event,channel=channel):
                trace.append(dict(channel=channel,name=event.name,inaxes=next((i for i,a in enumerate(axes) if event.inaxes is a),None),
                                  x=event.x,y=event.y,modifiers=sorted(event.modifiers)))
            self.v.mpl_connect(channel,callback)
        names={'enter_notify_event':'enter','leave_notify_event':'leave','motion_notify_event':'motion'}
        for method,x,y in REFERENCE['transition_inputs']:
            getattr(self.v,names[method])(SimpleNamespace(x=x,y=y,state=1))
        self.assertEqual(trace,REFERENCE['transitions'])
        self.v.message.set.assert_called_with('')

    def test_grid_cycles_match_reference_and_ignore_cursor_outside(self):
        def visible(kind,name):
            return any(layer.kind=='grid' and layer.visible and layer.options.get('which','major')==kind
                       and name in layer.options['axes_config'] for layer in self.ax.layers)
        for case in REFERENCE['grid_cycle']:
            with self.subTest(key=case['key'],major=case['major'],minor=case['minor']):
                self.v.key(self.event(case['key'],case['key'],1 if case['key']=='G' else 0))
                self.assertEqual([visible('major',name) for name in ('x','y')],case['major'])
                self.assertEqual([visible('minor',name) for name in ('x','y')],case['minor'])
        before=list(self.ax.layers);self.v.key(self.event('g','g',inside=False))
        self.assertEqual(self.ax.layers,before)

    def test_navigation_extra_buttons_follow_keymap(self):
        self.ax.zoom(2);self.v.navigation.push();zoomed=self.ax.get_extent()
        self.v.press(self.event(num=8));self.assertEqual(self.ax.get_extent(),(-60.,-40.,-30.,-10.))
        self.v.press(self.event(num=9));self.assertEqual(self.ax.get_extent(),zoomed)
        with azl.rc_context({'keymap.back':[]}):
            self.v.press(self.event(num=8));self.assertEqual(self.ax.get_extent(),zoomed)

    def test_tk_non_input_substitutions_do_not_break_resize_events(self):
        self.v._drawing=False;self.v._resize_pending=None
        for state in ('??',None):
            with self.subTest(state=state):
                event=SimpleNamespace(width=420,height=310,state=state)
                self.assertEqual(modifiers(event),())
                self.assertEqual(pressed_buttons(event),frozenset())
                self.v.resize(event)

    def test_constraint_release_clears_after_modifier_changes(self):
        self.v.key(self.event('x','x'));self.assertEqual(self.v.constraint,'x')
        self.v.key_up(self.event('x','x',4));self.assertIsNone(self.v.constraint)


if __name__=='__main__':unittest.main()

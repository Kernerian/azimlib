"""Navigation toggle/cursor contracts without Tk or Matplotlib imports."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from azimlib.backends.tk import FigureWindow


class ToolbarTests(unittest.TestCase):
    def viewer(self):
        viewer = object.__new__(FigureWindow)
        viewer.mode = ''; viewer.widget = Mock(); viewer.widget.cget.return_value = ''
        viewer.message = Mock(); viewer.buttons = {'Pan': Mock(), 'Zoom': Mock()}
        return viewer

    def test_mutually_exclusive_toggle_states_and_keyboard_reactivation(self):
        viewer = self.viewer()
        for mode, expected in (('pan', 'pan'), ('zoom', 'zoom'), ('zoom', ''), ('pan', 'pan'), ('pan', '')):
            for button in viewer.buttons.values(): button.reset_mock()
            viewer.set_mode(mode)
            self.assertEqual(viewer.mode, expected)
            for name, tool in (('Pan', 'pan'), ('Zoom', 'zoom')):
                with self.subTest(mode=mode, expected=expected, button=name):
                    if expected == tool:
                        viewer.buttons[name].select.assert_called_once_with()
                        viewer.buttons[name].deselect.assert_not_called()
                    else:
                        viewer.buttons[name].deselect.assert_called_once_with()
                        viewer.buttons[name].select.assert_not_called()

    def test_cursor_changes_only_for_axes_and_navigation_mode(self):
        viewer = self.viewer()
        for mode, expected in (('', ''), ('pan', 'fleur'), ('zoom', 'crosshair')):
            viewer.mode = mode
            for index in (None, 0):
                with self.subTest(mode=mode, index=index):
                    viewer.widget.reset_mock(); viewer.widget.cget.return_value = 'previous'
                    viewer._sync_cursor(index)
                    viewer.widget.config.assert_called_once_with(cursor=expected if index is not None else '')
                    self.assertEqual(viewer._cursor_index, index)

    def test_unchanged_cursor_does_not_reconfigure_widget(self):
        viewer = self.viewer(); viewer.mode = 'pan'; viewer.widget.cget.return_value = 'fleur'
        viewer._sync_cursor(0); viewer.widget.config.assert_not_called()

    def test_leave_clears_cursor_and_preserves_leave_event(self):
        viewer = self.viewer(); viewer.mode = 'zoom'; viewer.widget.cget.return_value = 'crosshair'
        viewer._hit = Mock(return_value=None); viewer._emit = Mock()
        event = SimpleNamespace(x=0, y=0)
        viewer.leave(event)
        viewer.widget.config.assert_called_once_with(cursor='')
        viewer._emit.assert_called_once_with('figure_leave_event', event, None)


if __name__ == '__main__': unittest.main()

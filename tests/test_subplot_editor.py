"""Subplot editing math/model without opening windows."""
import unittest
from unittest.mock import Mock
from azimlib.backends._subplots import SubplotEditor


class SubplotEditorTests(unittest.TestCase):
    def editor(self, **changes):
        editor=object.__new__(SubplotEditor)
        values=dict(left=.125,right=.9,bottom=.11,top=.88,wspace=.2,hspace=.2)
        values.update(changes)
        editor.values={name:Mock(get=Mock(return_value=value)) for name,value in values.items()}
        editor.figure=Mock(subplotpars=values)
        return editor

    def test_crossed_borders_follow_changed_control_without_invalid_layout(self):
        for changed in ('left','right','bottom','top'):
            editor=self.editor(left=.95,right=.8,bottom=.7,top=.6)
            values=editor._read(changed)
            with self.subTest(changed=changed):
                self.assertTrue(0<=values['left']<values['right']<=1)
                self.assertTrue(0<=values['bottom']<values['top']<=1)

    def test_nonfinite_input_rejected_and_spacing_keeps_core_range(self):
        for value in (float('nan'),float('inf'),-float('inf')):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):self.editor(left=value)._read('left')
        self.assertEqual(self.editor(wspace=2,hspace=-1)._read()['wspace'],2)
        self.assertEqual(self.editor(wspace=2,hspace=-1)._read()['hspace'],0)

    def test_export_is_executable_figure_api_with_current_values(self):
        editor=self.editor(left=.15,right=.85)
        target=Mock();exec(editor.export_values(),{'fig':target})
        target.subplots_adjust.assert_called_once_with(**editor.figure.subplotpars)

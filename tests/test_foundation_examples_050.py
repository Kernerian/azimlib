"""The small foundation examples exercise only implemented contracts."""
import importlib.util
from pathlib import Path
import unittest
import azimlib as azl


class Examples050(unittest.TestCase):
    def test_all_demonstrations_compose_in_cpu_scene(self):
        path=Path(__file__).resolve().parents[1]/'examples/planetary/foundation_050.py'
        spec=importlib.util.spec_from_file_location('foundation_050_example',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        for name in ('terrestrial','mars','comparison','groups'):
            with self.subTest(example=name):
                fig=getattr(module,name)()
                try:
                    self.assertTrue(fig.to_scene().items)
                    self.assertIn('<svg',fig.to_svg())
                finally:azl.close(fig)

"""Review artifacts must never accept an unrelated desktop as the Tk canvas."""
import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('text_review_tool',ROOT/'tools/validate_text_engine.py')
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)


@unittest.skipUnless(importlib.util.find_spec('PIL'),'Optional Pillow not installed')
class CapturePrivacyTests(unittest.TestCase):
    def viewer(self,image):
        window=SimpleNamespace(deiconify=lambda:None,lift=lambda:None,update=lambda:None,
            winfo_rootx=lambda:100,winfo_rooty=lambda:100,winfo_width=lambda:80,winfo_height=lambda:60)
        widget=SimpleNamespace(winfo_rootx=lambda:110,winfo_rooty=lambda:110)
        return SimpleNamespace(window=window,widget=widget,_image=image)

    def test_rectangle_capture_rejected_on_ordinary_desktop(self):
        from PIL import Image
        with Image.new('RGB',(20,15),'red') as expected,tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'capture.png'
            with patch.object(review.platform,'system',return_value='Linux'),patch.dict(os.environ,{'GITHUB_ACTIONS':'false'}),patch('PIL.ImageGrab.grab') as grab:
                with self.assertRaisesRegex(RuntimeError,'isolated GitHub'):review.capture_tk(self.viewer(expected),target)
                grab.assert_not_called();self.assertFalse(target.exists())

    def test_unrelated_window_is_not_saved(self):
        from PIL import Image
        with Image.new('RGB',(20,15),'red') as expected,tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'capture.png'
            with patch.object(review.platform,'system',return_value='Linux'),patch.dict(os.environ,{'GITHUB_ACTIONS':'true'}),patch('PIL.ImageGrab.grab',return_value=Image.new('RGB',(80,60),'blue')):
                with self.assertRaisesRegex(RuntimeError,'nothing saved'):review.capture_tk(self.viewer(expected),target)
                self.assertFalse(target.exists())

    def test_verified_canvas_can_be_saved(self):
        from PIL import Image
        with Image.new('RGB',(20,15),'red') as expected,tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'capture.png';capture=Image.new('RGB',(80,60),'white');capture.paste(expected,(10,10))
            with patch.object(review.platform,'system',return_value='Linux'),patch.dict(os.environ,{'GITHUB_ACTIONS':'true'}),patch('PIL.ImageGrab.grab',return_value=capture):
                mode=review.capture_tk(self.viewer(expected),target)
                self.assertTrue(target.is_file());self.assertIn('verified',mode)


if __name__=='__main__':unittest.main()

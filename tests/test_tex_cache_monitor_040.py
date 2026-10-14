"""An active cache may rename files; offline integrity and limits stay strict."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from azimlib._tex_process import tree_bytes


class AcquisitionMonitorTests(unittest.TestCase):
    def test_complete_retry_after_atomic_rename_counts_remaining_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);target=root/'resource';target.write_bytes(b'12345')
            original=Path.stat;calls=[]
            def stat(path,*a,**kw):
                if path==target and not calls:
                    calls.append(path);raise FileNotFoundError(2,'atomic rename')
                return original(path,*a,**kw)
            with patch.object(Path,'stat',stat):self.assertEqual(tree_bytes(root,5,acquiring=True),5)
            self.assertEqual(len(calls),1)

    def test_offline_missing_entry_is_not_retried(self):
        with patch('azimlib._tex_process._tree_bytes_once',side_effect=FileNotFoundError) as scan:
            with self.assertRaises(FileNotFoundError):tree_bytes('.',100)
            self.assertEqual(scan.call_count,1)

    def test_active_persistent_failure_is_bounded(self):
        with patch('azimlib._tex_process._tree_bytes_once',side_effect=FileNotFoundError) as scan:
            with self.assertRaises(FileNotFoundError):tree_bytes('.',100,acquiring=True)
            self.assertEqual(scan.call_count,3)

    def test_size_and_permission_failures_are_never_retried_or_ignored(self):
        for error in (PermissionError(13,'private path'),ValueError('storage limit')):
            with patch('azimlib._tex_process._tree_bytes_once',side_effect=error) as scan:
                with self.assertRaises(type(error)):tree_bytes('.',100,acquiring=True)
                self.assertEqual(scan.call_count,1)
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder)/'oversize').write_bytes(b'123456')
            with self.assertRaisesRegex(ValueError,'limit'):tree_bytes(folder,5,acquiring=True)


if __name__=='__main__':unittest.main()

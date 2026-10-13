"""Fail-closed reference coverage/integrity without external datasets."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('eclipse_validation',ROOT/'tools/validate_eclipse_contract.py')
validation=importlib.util.module_from_spec(spec);spec.loader.exec_module(validation)


class EclipseValidationContracts(unittest.TestCase):
    def test_corrected_oracle_is_explicit_and_hash_frozen(self):
        import inspect
        self.assertIsNone(inspect.signature(validation.validate_central).parameters['central_oracle'].default)
        with self.assertRaisesRegex(ValueError,'outside checkout'):validation.read_central_oracle(ROOT/'test.json')
        with patch.object(Path,'read_bytes',return_value=b'{}'),self.assertRaisesRegex(ValueError,'Frozen central oracle changed'):
            validation.read_central_oracle(ROOT.parent/'oracle.json')
    def table(self):
        # Original synthetic rows, not copied NASA predictions.
        return '\n'.join(f'{i//60:02}:{i%60:02} '+
            '10 00.0N 020 00.0W '*3 for i in range(97))

    def test_incomplete_duplicate_and_missing_timed_rows_fail(self):
        table=self.table()
        self.assertEqual(len(validation.solar_rows(table,'2017-08-21')),97)
        for changed in ('\n'.join(table.splitlines()[:-1]),
                        table+'\n'+table.splitlines()[0],
                        table.replace('10 00.0N','corrupt',1)):
            with self.assertRaises(ValueError):validation.solar_rows(changed,'2017-08-21')

    def test_explicit_catalog_missing_boundary_keeps_center_and_other_boundary(self):
        table=self.table().replace('10 00.0N 020 00.0W ','-         -      ',1)
        rows=validation.solar_rows(table,'2017-08-21')
        self.assertEqual(len(rows),97)
        self.assertIsNone(rows[0][2][0])
        self.assertIsNotNone(rows[0][2][1]);self.assertIsNotNone(rows[0][2][2])

    def test_hash_mismatch_is_exception_not_disableable_assertion(self):
        contract={'references':{'test':{'sha256':hashlib.sha256(b'expected').hexdigest()}}}
        validation.require_reference_hash(b'expected','test',contract)
        with self.assertRaises(ValueError):validation.require_reference_hash(b'changed','test',contract)

    def test_frozen_contract_cannot_be_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory);(path/'frozen-contract.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'Frozen eclipse contract changed'):
                validation.verify_inputs(path)
        with self.assertRaisesRegex(ValueError,'outside checkout'):
            validation.verify_inputs(ROOT/'tests')


if __name__=='__main__':unittest.main()

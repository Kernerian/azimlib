"""Scientific reference ingestion fails closed; precision is not inferred."""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from validate_solar_circumstances import read_references,minimum


class ReferenceContracts(unittest.TestCase):
    def test_modified_or_generated_reference_does_not_replace_frozen_data(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'contract.json';path.write_text('{"cases":[],"unchanged_limits":{"solar_contact_s":300}}')
            with self.assertRaisesRegex(ValueError,'Frozen local solar contract changed'):read_references(path)
    def test_references_inside_checkout_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'outside checkout'):read_references(Path(__file__))
    def test_minimum_is_bounded_and_rejects_nonfinite_inputs(self):
        self.assertAlmostEqual(minimum(lambda x:(x-2.125)**2,-5,8),2.125,delta=.001)
        with self.assertRaises(ValueError):minimum(lambda x:x,2,1)
        with self.assertRaises(ValueError):minimum(lambda x:float('nan'),0,1)


if __name__=='__main__':unittest.main()

"""Own synthetic DAF fixtures, analytic polynomials and malformed input contracts."""
import hashlib
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from azimlib._spk import SpkKernel,chebyshev


def fixture(*,endian='<',kind=2,center=0,frame=1):
    data=bytearray(4096);data[:8]=b'DAF/SPK '
    data[88:96]=b'LTL-IEEE' if endian=='<' else b'BIG-IEEE'
    struct.pack_into(endian+'2i',data,8,2,6)
    values=[0.,10.,1.,2.,3.,4.,5.,6.]
    if kind==3:values.extend((7.,8.,9.,10.,11.,12.))
    size=len(values);first=385;last=first+size+4-1
    struct.pack_into(endian+'3i',data,76,2,2,last+1)
    struct.pack_into(endian+'3d',data,1024,0.,0.,1.)
    struct.pack_into(endian+'2d6i',data,1048,-10.,10.,301,center,frame,kind,first,last)
    struct.pack_into(endian+str(size+4)+'d',data,(first-1)*8,*values,-10.,20.,float(size),1.)
    return bytes(data)


class SpkContracts(unittest.TestCase):
    def load(self,data,sha=None):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'synthetic.bsp';path.write_bytes(data)
            return SpkKernel(path,sha256=sha or hashlib.sha256(data).hexdigest(),source='Own synthetic analytic fixture')

    def test_polynomial_and_derivative(self):
        for x in (-1.,-.4,0.,.7,1.):
            p,d=chebyshev((2.,3.,4.,5.),x)
            self.assertAlmostEqual(p,2+3*x+4*(2*x*x-1)+5*(4*x**3-3*x))
            self.assertAlmostEqual(d,3+16*x+5*(12*x*x-3))

    def test_endian_type2_position_and_velocity_at_record_boundaries(self):
        for endian in ('<','>'):
            kernel=self.load(fixture(endian=endian))
            for epoch in (-10.,0.,10.):
                state=kernel.state(301,epoch)
                self.assertEqual(state.position_m,tuple((a+b*epoch/10)*1000 for a,b in ((1,2),(3,4),(5,6))))
                self.assertEqual(state.velocity_m_s,(200.,400.,600.))
                self.assertEqual(state.frame,'ICRF/J2000')
            with self.assertRaises(ValueError):kernel.state(301,10.001)
            with self.assertRaises(ValueError):kernel.state(999,0.)
            with self.assertRaises(ValueError):kernel.state(True,0.)
            with self.assertRaises(ValueError):kernel.state(301,float('nan'))
            self.assertEqual(kernel.state(0,0).position_m,(0.,0.,0.))

    def test_type3_velocity_is_independent_coefficients(self):
        state=self.load(fixture(kind=3)).state(301,5.)
        self.assertEqual(state.velocity_m_s,(11000.,14000.,17000.))

    def test_hash_integrity_center_cycles_and_unsupported_frames(self):
        with self.assertRaisesRegex(ValueError,'SHA-256'):self.load(fixture(),'0'*64)
        with self.assertRaisesRegex(ValueError,'Cyclic'):self.load(fixture(center=301)).state(301,0.)
        with self.assertRaisesRegex(ValueError,'J2000'):self.load(fixture(frame=17))
        data=bytearray(fixture());struct.pack_into('<d',data,1024,2.)
        with self.assertRaisesRegex(ValueError,'cyclic'):self.load(bytes(data))

    def test_truncated_invalid_directory_and_nonfinite_coefficients(self):
        with self.assertRaises(ValueError):self.load(fixture()[:-1])
        data=bytearray(fixture());struct.pack_into('<d',data,(385-1+8+2)*8,9.)
        with self.assertRaisesRegex(ValueError,'layout'):self.load(bytes(data))
        data=bytearray(fixture());struct.pack_into('<d',data,(385-1+2)*8,float('nan'))
        with self.assertRaisesRegex(ValueError,'record'):self.load(bytes(data)).state(301,0.)


if __name__=='__main__':unittest.main()

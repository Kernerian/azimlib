"""Package independence and user-facing export contracts."""
from pathlib import Path
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

import azimlib as az
import azimlib.pyplot as plt


class DistributionTests(unittest.TestCase):
    def tearDown(self):
        plt.close("all")

    def test_core_svg_runs_without_site_packages(self):
        source=str(Path(az.__file__).parent.parent)
        code=f"import sys;sys.path.insert(0,{source!r});import azimlib as az;f,a=az.subplots();a.map('brazil');a.states();s=f.to_svg();assert '<svg' in s;assert not any(n in sys.modules for n in ['PIL','matplotlib','shapely','pyproj','cartopy','geopandas','folium'])"
        process=subprocess.run([sys.executable,"-S","-c",code],stdin=subprocess.DEVNULL,capture_output=True,text=True)
        self.assertEqual(process.returncode,0,process.stderr)

    def test_no_forbidden_runtime_imports(self):
        import ast
        forbidden={"matplotlib","geopandas","cartopy","shapely","pyproj","folium","geographiclib","fiona","rasterio"}
        for path in Path(az.__file__).parent.rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                modules=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module or ""] if isinstance(node,ast.ImportFrom) and not node.level else []
                self.assertFalse(any(m.split(".")[0] in forbidden for m in modules),str(path))

    def test_svg_stream_and_atomic_export(self):
        fig,ax=plt.subplots()
        ax.polygon([(0,0),(4,0),(4,4),(0,4)],holes=[[(1,1),(1,3),(3,3),(3,1),(1,1)]],facecolor="orange")
        ax.set_title("Title & <safe>")
        stream=io.StringIO()
        fig.savefig(stream,format="svg")
        root=ET.fromstring(stream.getvalue())
        self.assertTrue(root.tag.endswith("svg"))
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/"nested"/"map.svg"
            fig.savefig(target)
            original=target.read_text(encoding="utf-8")
            # Marker validation now happens before committing the artist edit.
            with self.assertRaises(ValueError):ax.layers[0].set(marker="bogus")
            self.assertEqual(target.read_text(encoding="utf-8"),original)
            # Explicit invalid export option leaves an existing file untouched.
            with self.assertRaises(ValueError):
                fig.savefig(target,format="pdf")
            self.assertEqual(target.read_text(encoding="utf-8"),original)
            self.assertFalse(list(target.parent.glob(".azimlib-*")))

    def test_html_contains_safe_metadata_and_navigation(self):
        fig,ax=plt.subplots()
        ax.map("brazil")
        ax.set_title("</script><script>alert(1)</script>")
        ax.overview()
        content=fig.to_html()
        self.assertIn('id="zoom"',content)
        self.assertIn('id="mini"',content)
        self.assertIn('id="home"',content)
        self.assertNotIn("<script>alert(1)</script>",content)
        match=re.search(r'<script id="map-data" type="application/json">(.*?)</script>',content,re.S)
        data=json.loads(match.group(1))
        self.assertEqual(len(data),1)
        self.assertEqual(data[0]["projection"]["name"],"equirectangular")
        self.assertLess(data[0]["start"],data[0]["end"])
        self.assertNotRegex(content,r'<script[^>]+src=')

    def test_familiar_pyplot_surface(self):
        fig,ax=plt.subplots(figsize=(6,5),subplot_kw={"projection":"mercator"})
        line,=ax.plot([-50,-45],[-20,-25],"r--",label="Route")
        line.set(linewidth=2)
        plt.title("Map")
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.xlim(-55,-40)
        plt.ylim(-30,-15)
        self.assertIs(plt.gca(),ax)
        self.assertEqual(plt.xlim(),(-55.,-40.))
        self.assertEqual(plt.ylim(),(-30.,-15.))
        self.assertTrue(fig.to_svg().startswith("<svg"))

    def test_add_subplot_and_layout(self):
        fig=plt.figure(figsize=(10,5))
        a=fig.add_subplot(121)
        b=fig.add_subplot(122)
        a.map("brazil")
        b.map("argentina")
        fig.subplots_adjust(left=.1,right=.9,wspace=.3)
        self.assertLess(a.position[0],b.position[0])
        fig.tight_layout()
        self.assertEqual(len(fig.to_scene().maps),2)


if __name__=="__main__":
    unittest.main()

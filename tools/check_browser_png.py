"""Development-only pixel checks for verify_portable_browser.js downloads."""
import json
import sys
from pathlib import Path
from PIL import Image, ImageColor

folder = Path(sys.argv[1])
image = Image.open(folder / 'portable-browser.png').convert('RGBA')
# The sample uses the default white Figure; a missing SVG background must fail.
assert image.getpixel((0, 0)) == (255, 255, 255, 255)
bands = json.loads((folder / 'portable-browser-raster.json').read_text())
left = round(min(b['x'] for b in bands)) + 2
right = round(max(b['x'] + b['width'] for b in bands)) - 2
checked = 0
for band in bands:
    expected = ImageColor.getrgb(band['fill']) + (255,)
    y = round(band['y'] + band['height'] / 2)
    for x in range(max(left, round(band['x'])), min(right, round(band['x'] + band['width']))):
        assert image.getpixel((x, y)) == expected, (x, y, image.getpixel((x, y)), expected)
        checked += 1
assert checked > 900
print(f'PNG: white opaque Figure and exact palette on {checked} adjacent interior pixels; no tile seams.')

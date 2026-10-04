"""Generic pixel coverage for our stroke polygons, with no plotting/GIS API.

aggdraw is optional low-level rasterization only. Azimlib computes every dash,
cap, join, stroke polygon, projection and layout before calling this adapter.
"""
import math


class AntialiasedStrokeDraw:
    def __init__(self,mask,aggdraw):
        self.mask=mask;self.aggdraw=aggdraw;self.commands=[]

    def polygon(self,points,fill=255):
        if len(points)<3:return
        # All constituent stroke polygons use the same winding: intersections
        # form a union, rather than cancelling or darkening at round joins.
        area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1]))
        if area<0:points=list(reversed(points))
        x,y=points[0];self.commands.append(f'M{x:.8g},{y:.8g}')
        self.commands.extend(f'L{x:.8g},{y:.8g}' for x,y in points[1:])
        self.commands.append('Z')

    def ellipse(self,box,fill=255):
        x0,y0,x1,y1=box;cx,cy=(x0+x1)/2,(y0+y1)/2;rx,ry=(x1-x0)/2,(y1-y0)/2
        k=4*(math.sqrt(2)-1)/3
        self.commands.append(f'M{x1:.8g},{cy:.8g}')
        for values in ((x1,cy+k*ry,cx+k*rx,y1,cx,y1),(cx-k*rx,y1,x0,cy+k*ry,x0,cy),
                       (x0,cy-k*ry,cx-k*rx,y0,cx,y0),(cx+k*rx,y0,x1,cy-k*ry,x1,cy)):
            self.commands.append('C'+','.join(f'{v:.8g}' for v in values))
        self.commands.append('Z')

    def flush(self):
        draw=self.aggdraw.Draw(self.mask)
        if self.commands:
            symbol=self.aggdraw.Symbol(' '.join(self.commands))
            # A missing pen makes aggdraw expand a filled contour by default.
            # Explicit zero width preserves the stroke polygons we computed.
            draw.symbol((0,0),symbol,self.aggdraw.Pen(0,0),self.aggdraw.Brush(255));draw.flush()

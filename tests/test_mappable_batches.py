"""Final-state Matplotlib equivalence and own prevalidated batch guarantees."""
import io
import json
import math
from pathlib import Path
import unittest
from itertools import permutations
import azimlib as azl
from azimlib.cm import ScalarMappable
from azimlib.colors import Normalize,LogNorm,TwoSlopeNorm,BoundaryNorm
from azimlib.geometry import Geometry,Feature,FeatureCollection
from azimlib.ticker import FixedLocator,MultipleLocator,AutoMinorLocator
from azimlib.renderers import render_png


def create(kind,norm=None):
    fig,ax=azl.subplots(figsize=(3,3))
    norm=norm if norm is not None else Normalize(0,10)
    x=[-52,-50,-48,-46];y=[-25,-23,-21,-19]
    if kind=='image':item=ax.imshow([[1,2],[3,4]],extent=(-54,-44,-26,-18),origin='lower',norm=norm)
    elif kind=='mesh':item=ax.pcolormesh([-54,-49,-44],[-26,-22,-18],[[1,2],[3,4]],norm=norm)
    elif kind=='scatter':item=ax.scatter(x,y,c=[1,2,3,4],norm=norm)
    elif kind=='vectors':item=ax.quiver(x,y,[1]*4,[1]*4,[1,2,3,4],norm=norm)
    else:
        features=[]
        for lon,lat in zip(x,y):
            features.append(Feature(Geometry('Polygon',[[[lon,lat],[lon+1,lat],[lon+1,lat+1],[lon,lat+1],[lon,lat]]])))
        item=ax.choropleth(FeatureCollection(features),[1,2,3,4],bins=None)
        item.set_norm(norm)
    ax.set_extent((-54,-44,-26,-18))
    return fig,ax,item


class MappableBatchTests(unittest.TestCase):
    def tearDown(self):azl.close('all');azl.ioff()

    def test_final_properties_and_colorbar_tick_reset_match_installed_matplotlib(self):
        cases=[]
        for kind in ('image','mesh','scatter','vectors'):
            fig,ax,item=create(kind);bar=fig.colorbar(item)
            bar.locator=FixedLocator([0,5,10]);locator=bar.locator
            def snapshot(name):
                cases.append(dict(kind=kind,name=name,array=item.get_array(),norm=type(item.norm).__name__,
                    clim=list(item.get_clim()),cmap=item.cmap.name,alpha=item.get_alpha(),visible=item.get_visible(),
                    bar_norm_shared=bar.norm is item.norm,locator_retained=bar.locator is locator))
            snapshot('initial')
            values=[[10,20],[30,40]] if kind in ('image','mesh') else [10,20,30,40]
            azl.setp(item,array=values,cmap='plasma',clim=(0,50),alpha=.6,visible=False)
            snapshot('mapping-batch')
            values=[[1,5],[20,80]] if kind in ('image','mesh') else [1,5,20,80]
            item.set(array=values,norm=LogNorm(1,100),cmap='viridis',visible=True)
            snapshot('norm-replaced');item.cmap='plasma';snapshot('palette-assigned')
            item.set(cmap=None,clim=(2,200));snapshot('default-palette')
            azl.close(fig)
        reference=Path(__file__).resolve().parents[1]/'docs/mappable-batches-reference.json'
        self.assertEqual(cases,json.loads(reference.read_text())['cases'])

    def test_callbacks_observe_only_committed_data_styles_and_mapping(self):
        for kind in ('image','mesh','scatter','vectors','choropleth'):
            with self.subTest(kind=kind):
                fig,ax,item=create(kind);bar=fig.colorbar(item);view=ax.get_extent()
                fig.canvas.draw();artist_events=[];mapping_events=[]
                def state(m):return m.get_array(),m.get_clim(),m.cmap.name,m.get_alpha(),m.get_visible()
                item.add_callback(lambda m:artist_events.append(state(m)))
                item.callbacks.connect('changed',lambda m:mapping_events.append(state(m)))
                values=[[10,20],[30,40]] if kind in ('image','mesh') else [10,20,30,40]
                item.set(array=values,norm=Normalize(0,50),cmap='plasma',alpha=.4,visible=False)
                expected=([10,20,30,40],(0,50),'plasma',.4,False)
                self.assertEqual(artist_events,[expected]);self.assertEqual(mapping_events,[expected])
                self.assertIs(bar.norm,item.norm);self.assertEqual(ax.get_extent(),view)
                self.assertTrue(fig.stale and item.stale and bar.stale)

    def test_invalid_batch_leaves_all_data_styles_norm_ticks_and_events_unchanged(self):
        for kind in ('image','mesh','scatter','vectors','choropleth'):
            fig,ax,item=create(kind);bar=fig.colorbar(item);bar.locator=MultipleLocator(5)
            old_norm=item.norm;locator=bar.locator;before=(item.data,item.get_array(),dict(item.style),item.cmap)
            bad=(dict(norm='foreign'),dict(cmap='missing-palette'),dict(clim=(5,2)),dict(clim=(1,)),
                 dict(clim=(0,math.nan)),dict(norm=Normalize(0,1),cmap='plasma',linewidth=-1),
                 dict(norm=Normalize(0,1),cmap='plasma',not_a_property=2))
            for options in bad:
                values=[[10,20],[30,40]] if kind in ('image','mesh') else [10,20,30,40]
                fig.canvas.draw();events=[];cid=item.add_callback(events.append)
                mid=item.callbacks.connect('changed',events.append)
                with self.subTest(kind=kind,options=options):
                    with self.assertRaises((ValueError,TypeError)):item.set(array=values,visible=False,**options)
                    self.assertEqual((item.data,item.get_array(),dict(item.style),item.cmap),before)
                    self.assertIs(item.norm,old_norm);self.assertEqual(item.get_clim(),(0,10))
                    self.assertTrue(item.get_visible());self.assertIs(bar.locator,locator)
                    self.assertFalse(fig.stale);self.assertFalse(events)
                item.remove_callback(cid);item.callbacks.disconnect(mid)
            azl.close(fig)

    def test_preview_does_not_mutate_shared_new_norm_on_failed_style(self):
        fresh=Normalize();observer=ScalarMappable(fresh);signals=[]
        observer.callbacks.connect('changed',lambda m:signals.append(m.get_clim()))
        fig,ax,item=create('image')
        with self.assertRaises(ValueError):item.set(data=[[10,20]],norm=fresh,cmap='plasma',linewidth=-1)
        self.assertEqual(observer.get_clim(),(None,None));self.assertFalse(signals)
        item.set(data=[[10,20]],norm=fresh,cmap='plasma')
        self.assertEqual(signals,[(10,20)]);self.assertEqual(item.get_clim(),(10,20))
        self.assertEqual(item.get_data(),[[10,20]])

    def test_same_shared_norm_preserves_tickers_replacement_detaches_old_norm(self):
        shared=Normalize(0,10);fig,ax,item=create('mesh',shared)
        otherfig,otherax,other=create('scatter',shared)
        bar=fig.colorbar(item);otherbar=otherfig.colorbar(other)
        bar.locator=MultipleLocator(2);bar.minorlocator=AutoMinorLocator(2)
        major,minor=bar.locator,bar.minorlocator
        signals=[];other.callbacks.connect('changed',lambda m:signals.append(m.get_clim()))
        item.set(array=[[20,30],[40,50]],cmap='plasma',clim=(10,60))
        self.assertEqual(signals,[(10,60)]);self.assertEqual(otherbar.mappable.get_clim(),(10,60))
        self.assertIs(bar.locator,major);self.assertIs(bar.minorlocator,minor)
        replacement=LogNorm(1,100);item.set(norm=replacement,cmap='viridis')
        self.assertIsNot(bar.locator,major);self.assertIsNot(bar.minorlocator,minor)
        events=[];item.callbacks.connect('changed',lambda m:events.append(m.get_clim()))
        shared.vmax=80;self.assertFalse(events);self.assertEqual(other.get_clim(),(10,80))
        replacement.vmax=200;self.assertEqual(events,[(1,200)])

    def test_mapping_order_is_independent_and_explicit_clim_wins_for_new_data(self):
        for order in permutations(('norm','array','clim','cmap')):
            with self.subTest(order=order):
                fig,ax,item=create('scatter');fresh=Normalize()
                options={'norm':fresh,'array':[10,20,30,40],'clim':(0,50),'cmap':'plasma'}
                item.set(**{key:options[key] for key in order})
                self.assertIs(item.norm,fresh);self.assertEqual(item.get_clim(),(0,50))
                self.assertEqual(item.get_array(),[10,20,30,40]);azl.close(fig)

    def test_geometry_and_color_edits_can_be_combined_in_each_field_type(self):
        fig,ax,image=create('image');image.set(data=[[10,20,30]],extent=(-55,-40,-28,-18),norm=Normalize(),cmap='plasma')
        self.assertEqual(image.get_clim(),(10,30));self.assertEqual(image.get_data(),[[10,20,30]])
        fig,ax,points=create('scatter')
        points.set(offsets=[[-52,-25],[-46,-19]],sizes=[4,16],array=[15,30],norm=Normalize(),cmap='plasma')
        self.assertEqual(points.get_clim(),(15,30));self.assertEqual(len(points.get_offsets()),2)
        fig,ax,vectors=create('vectors')
        vectors.set(UVC=([2]*4,[0]*4,[5,10,15,20]),offsets=[[-52,-24],[-50,-22],[-48,-20],[-46,-18]],norm=Normalize(),clim=(0,25))
        self.assertEqual(vectors.get_UVC(),([2]*4,[0]*4,[5,10,15,20]));self.assertEqual(vectors.get_clim(),(0,25))

    def test_palette_assignment_and_default_validation_notify_standalone_and_artist(self):
        for item in (ScalarMappable(Normalize(0,10)),create('scatter')[2]):
            with self.subTest(kind=type(item).__name__):
                events=[];item.callbacks.connect('changed',lambda m:events.append(m.cmap.name))
                item.cmap='plasma';item.set_cmap(None)
                self.assertEqual(events,['plasma','viridis']);before=item.cmap
                with self.assertRaises(ValueError):item.cmap='missing-palette'
                self.assertIs(item.cmap,before);self.assertEqual(len(events),2)

    def test_norm_reset_partial_clim_missing_values_and_discrete_mapping(self):
        for kind in ('image','mesh','scatter','vectors','choropleth'):
            fig,ax,item=create(kind)
            item.set(norm=None,clim=(None,50));self.assertEqual(item.get_clim(),(1,50))
            item.set(clim=(5,None));self.assertEqual(item.get_clim(),(5,50))
            values=[[None,math.nan],[2,6]] if kind in ('image','mesh') else [None,math.nan,2,6]
            item.set(array=values,norm=LogNorm());self.assertEqual(item.get_clim(),(2,6))
            item.set(norm=BoundaryNorm([0,3,7]),cmap='viridis');self.assertEqual(item.get_clim(),(0,7))
            if kind!='image':item.set(array=None);self.assertIsNone(item.get_array())
            fig.to_svg();azl.close(fig)
        fig,ax,item=create('mesh');item.set(norm=TwoSlopeNorm(0),array=[[2,4],[6,8]])
        self.assertEqual(item.get_clim(),(-8,8))

    def test_invalid_standalone_array_and_norm_do_not_commit_or_notify(self):
        norm=Normalize(10,None);item=ScalarMappable(norm);events=[]
        item.callbacks.connect('changed',events.append)
        with self.assertRaises(ValueError):item.set_array([2,3])
        self.assertIsNone(item.get_array());self.assertFalse(events);self.assertEqual(item.get_clim(),(10,None))
        item.set_array([12,15]);events.clear();fresh=Normalize(20,None)
        with self.assertRaises(ValueError):item.set_norm(fresh)
        self.assertIs(item.norm,norm);self.assertEqual(fresh.vmax,None);self.assertFalse(events)

    def test_batch_and_dedicated_setters_produce_same_scene_png_and_exports(self):
        for kind in ('image','mesh','scatter','vectors','choropleth'):
            with self.subTest(kind=kind):
                fig,ax,item=create(kind);bar=fig.colorbar(item);view=ax.get_extent()
                item.set_array([10,20,30,40]);item.set_norm(Normalize(0,50));item.set_cmap('plasma');item.set_alpha(.6)
                expected=fig.to_scene()
                item.set(array=[10,20,30,40],norm=Normalize(0,50),cmap='plasma',alpha=.6)
                actual=fig.to_scene();self.assertEqual(expected.items,actual.items);self.assertEqual(expected.maps,actual.maps)
                def png(scene):
                    stream=io.BytesIO();render_png(scene,stream);return stream.getvalue()
                self.assertEqual(png(expected),png(actual));self.assertEqual(ax.get_extent(),view)
                self.assertIn('<svg',fig.to_svg());self.assertIn('Figure',fig.to_html())
                props=azl.getp(item)
                self.assertIs(props['norm'],item.norm);self.assertIs(props['cmap'],item.cmap)
                self.assertEqual(props['clim'],(0,50));bar.remove();fig.canvas.draw()
                item.set(cmap='viridis');azl.close(fig)


if __name__=='__main__':unittest.main()

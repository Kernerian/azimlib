"""Own text/annotation position edits and coherent component labels."""
import io,json,unittest
from pathlib import Path
from unittest.mock import patch
import azimlib as azl
from azimlib.components import TextArtist
from azimlib.text_artists import MapText,Annotation
from azimlib.cm import ScalarMappable
from azimlib.colors import Normalize
from azimlib.scene import Text,Scene,Path as ScenePath
from azimlib.viewport import Viewport
from azimlib.render_map import _annotation
from azimlib.typography import POINT


class TextEditTests(unittest.TestCase):
    def setUp(self):
        azl.ioff();self.fig,self.ax=azl.subplots(figsize=(6,5));self.ax.set_extent((-54,-42,-28,-16))
    def tearDown(self):azl.ioff();azl.close('all');azl.rcdefaults()
    def primitive(self,value,scene=None):
        return next(p for p in (scene or self.fig.to_scene()).items if isinstance(p,Text) and p.text==value)

    def test_text_position_and_styles_edit_together_in_geographic_and_axes_space(self):
        for transform,first,last in (('data',(-48,-22),(-46,-20)),('axes',(.2,.3),(.7,.6))):
            with self.subTest(transform=transform):
                text=self.ax.text(*first,'Initial',transform=transform)
                self.assertIsInstance(text,MapText);old=self.primitive('Initial');events=[]
                text.add_callback(lambda a:events.append((a.get_position(),a.get_text(),a.get_ha(),a.get_color())))
                self.fig.canvas.draw();azl.setp(text,position=last,text='Edited',ha='center',color='red',fontsize=12)
                self.assertEqual(events,[(last,'Edited','center','red')]);self.assertTrue(self.fig.stale)
                new=self.primitive('Edited');self.assertNotEqual((old.x,old.y),(new.x,new.y))
                self.assertAlmostEqual(new.style['font_size'],12*POINT);text.remove()

    def test_text_x_y_getp_and_no_autoscale_from_label_movement(self):
        text=self.ax.text(-48,-22,'Note');extent=self.ax.get_extent();bounds=self.ax._bounds
        text.set_x(-46);text.set_y(-19)
        self.assertEqual(azl.getp(text,'position'),(-46,-19));self.assertEqual(text.get_x(),-46)
        self.assertEqual((self.ax.get_extent(),self.ax._bounds),(extent,bounds))
        self.assertEqual(text.properties()['position'],(-46,-19))

    def test_annotation_target_and_text_position_are_independent_and_editable(self):
        note=self.ax.annotate('Note',(-48,-22),(-46,-20),textcoords='data')
        self.assertIsInstance(note,Annotation);before=self.primitive('Note')
        note.xy=(-50,-24);self.assertEqual(note.get_position(),(-46,-20))
        same=self.primitive('Note');self.assertEqual((before.x,before.y),(same.x,same.y))
        note.xyann=(-45,-19);after=self.primitive('Note')
        self.assertNotEqual((after.x,after.y),(same.x,same.y));self.assertEqual(note.xy,(-50,-24))
        events=[];note.add_callback(lambda a:events.append((a.xy,a.xyann,a.get_anncoords(),a.get_text())))
        note.set(xy=(-49,-23),position=(.3,.7),anncoords='axes fraction',text='Changed')
        self.assertEqual(events,[((-49,-23),(.3,.7),'axes fraction','Changed')])

    def test_offset_points_use_physical_units_y_up_across_projections_and_dpi(self):
        for projection in ('equirectangular','mercator','orthographic'):
            for dpi in (100,150,200):
                with self.subTest(projection=projection,dpi=dpi):
                    fig,ax=azl.subplots(dpi=dpi,projection=projection,projection_kw={'central_longitude':-48})
                    ax.set_extent((-54,-42,-28,-16));note=ax.annotate('Offset',(-48,-22),(18,12),textcoords='offset points')
                    scene=fig.to_scene();box=scene.maps[0]['box'];vp=Viewport(ax.projection,ax._get_extent(),box)
                    target=vp.project(-48,-22);p=next(p for p in scene.items if isinstance(p,Text) and p.text=='Offset')
                    self.assertAlmostEqual(p.x-target[0],18*dpi/72);self.assertAlmostEqual(p.y-target[1],-12*dpi/72)
                    # The render viewport is affine in logical units; a scaled
                    # Scene retains the same geographic target in output units.
                    azl.close(fig)

    def test_legacy_pixel_offsets_and_axes_fraction_alias_preserve_contracts(self):
        note=self.ax.annotate('Legacy',(-48,-22),(18,12))
        vp=Viewport(self.ax.projection,self.ax._get_extent(),(0,0,300,300));target=vp.project(-48,-22)
        scene=Scene(300,300);_annotation(note,vp,scene);p=self.primitive('Legacy',scene)
        self.assertEqual((p.x,p.y),(target[0]+18,target[1]+12))
        for coords in ('axes','axes fraction'):
            note.set(anncoords=coords,position=(.3,.7));scene=Scene(300,300);_annotation(note,vp,scene)
            p=self.primitive('Legacy',scene);self.assertAlmostEqual(p.x,90);self.assertAlmostEqual(p.y,90)

    def test_annotation_edits_recompute_arrow_and_projection_after_pan(self):
        note=self.ax.annotate('Arrow',(-48,-22),(18,12),textcoords='offset points',color='red')
        vp=Viewport(self.ax.projection,self.ax._get_extent(),(0,0,300,300));scene=Scene(300,300);_annotation(note,vp,scene)
        old=next(p for p in scene.items if isinstance(p,ScenePath))
        note.xy=(-44,-20);note.set_position((-12,-8));scene=Scene(300,300);_annotation(note,vp,scene)
        new=next(p for p in scene.items if isinstance(p,ScenePath));self.assertNotEqual(old.paths,new.paths)
        self.assertEqual(new.paths[0][-1],vp.project(*note.xy))
        self.ax.pan(1,1);vp2=Viewport(self.ax.projection,self.ax._get_extent(),(0,0,300,300))
        scene=Scene(300,300);_annotation(note,vp2,scene)
        self.assertNotEqual(new.paths,next(p for p in scene.items if isinstance(p,ScenePath)).paths)

    def test_invalid_text_and_annotation_batches_do_not_commit_or_notify(self):
        text=self.ax.text(-48,-22,'Text');note=self.ax.annotate('Note',(-48,-22))
        for artist in (text,note):
            events=[];artist.add_callback(lambda a:events.append(a));self.fig.canvas.draw()
            before=(artist.data,dict(artist.style),dict(artist.options),artist.get_visible())
            cases=[dict(position=(0,float('nan')),text='Bad'),dict(position=(-46,95),text='Bad'),
                   dict(position=(-46,-20),ha='bad',visible=False),dict(position=(-46,-20),fontsize=-2),dict(position=(-46,-20),unsupported=True)]
            if artist is note:
                cases[1]=dict(xy=(-46,95),text='Bad')
                cases += [dict(xy=(-46,-20),anncoords='data',position=(0,100)),dict(xy=(-46,-20),anncoords='unknown')]
            for kwargs in cases:
                with self.subTest(kind=artist.kind,kwargs=kwargs):
                    with self.assertRaises((ValueError,TypeError)):artist.set(**kwargs)
                    self.assertEqual((artist.data,artist.style,artist.options,artist.get_visible()),before)
                    self.assertEqual(events,[]);self.assertFalse(self.fig.stale)

    def test_text_alignment_font_setters_and_invalid_styles_validate_immediately(self):
        handles=[TextArtist('Text'),self.ax.set_title('Title'),self.ax.text(-48,-22,'Map'),self.ax.annotate('Note',(-48,-22))]
        for text in handles:
            with self.subTest(handle=type(text).__name__):
                text.set_ha('right');text.set_va('top');text.set_fontfamily('DejaVu Sans');text.set_fontstyle('italic')
                text.set_size(13);text.set_weight('bold')
                self.assertEqual((text.get_ha(),text.get_va(),text.get_fontstyle(),text.get_size(),text.get_weight()),('right','top','italic',13,'bold'))
                before=dict(text.style)
                with self.assertRaises(ValueError):text.set(color='red',ha='bad')
                self.assertEqual(text.style,before)

    def test_legend_title_invalid_style_is_atomic_and_callbacks_see_final_state(self):
        self.ax.plot([-50,-46],[-24,-20],label='Route');legend=self.ax.legend(title='Original')
        title=legend.get_title();events=[];title.add_callback(lambda t:events.append((t.text,legend['title'],legend['title_fontsize'])))
        self.fig.canvas.draw();before=(title.text,dict(title.style),dict(legend))
        for kwargs in (dict(fontsize=-1),dict(ha='bad'),dict(unknown=True)):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((ValueError,TypeError)):legend.set_title('Bad',**kwargs)
                self.assertEqual((title.text,title.style,dict(legend)),before);self.assertEqual(events,[]);self.assertFalse(self.fig.stale)
        legend.set_title('Changed',fontsize=14,color='red');self.assertEqual(events,[('Changed','Changed',14)])
        self.assertEqual(self.primitive('Changed').style['fill'],'red')

    def test_colorbar_label_invalid_styles_do_not_change_labelpad_or_location(self):
        for orientation in ('horizontal','vertical'):
            with self.subTest(orientation=orientation):
                bar=self.fig.colorbar(ScalarMappable(Normalize(0,100)),ax=self.ax,orientation=orientation,label='Original')
                text=bar.label_artist;events=[];text.add_callback(lambda t:events.append((t.text,bar['label'],bar.labelpad,bar.label_loc)))
                self.fig.canvas.draw();before=(text.text,dict(text.style),bar.labelpad,bar.label_loc,bar['label'])
                loc='right' if orientation=='horizontal' else 'top'
                for kwargs in (dict(labelpad=12,loc=loc,fontsize=-2),dict(labelpad=12,loc=loc,ha='bad'),dict(labelpad=12,loc='wrong'),dict(labelpad=float('nan'))):
                    with self.subTest(kwargs=kwargs):
                        with self.assertRaises((ValueError,TypeError)):bar.set_label('Bad',**kwargs)
                        self.assertEqual((text.text,text.style,bar.labelpad,bar.label_loc,bar['label']),before)
                        self.assertFalse(events);self.assertFalse(self.fig.stale)
                bar.set_label('Changed',labelpad=8,loc=loc,fontsize=12)
                self.assertEqual(events,[('Changed','Changed',8,loc)]);self.assertAlmostEqual(self.primitive('Changed').style['font_size'],12*POINT)
                bar.remove()

    def test_edited_text_obstacles_are_measured_at_new_position_and_hidden_removed(self):
        from azimlib.label_layout import obstacle_boxes
        text=self.ax.text(-48,-22,'Obstacle',fontsize=20);note=self.ax.annotate('Callout',(-48,-22),arrow=False)
        vp=Viewport(self.ax.projection,self.ax._get_extent(),(0,0,300,300));before=obstacle_boxes(self.ax,vp)
        text.set_position((-44,-18));note.set_position((40,30));after=obstacle_boxes(self.ax,vp)
        self.assertNotEqual(before,after)
        text.set_visible(False);note.remove();self.assertEqual(obstacle_boxes(self.ax,vp),[])
        text.remove();self.fig.canvas.draw();text.set_position((-50,-24));note.xy=(-50,-24)
        self.assertIsNone(text.get_figure());self.assertIsNone(note.get_figure());self.assertFalse(self.fig.stale)

    def test_exports_share_updated_text_coordinates_and_do_not_import_reference(self):
        text=self.ax.text(-48,-22,'Initial');note=self.ax.annotate('Old',(-48,-22),textcoords='offset points')
        text.set(position=(-46,-20),text='Geografia editada');note.set(position=(-20,18),text='Nova anotação')
        out=io.StringIO();self.fig.savefig(out,format='svg');self.assertIn('Geografia editada',out.getvalue())
        self.assertIn('Nova anotação',self.fig.to_html())
        scene=self.fig.to_scene();self.assertTrue(all(p.clip is not None for p in scene.items if isinstance(p,Text) and p.text in ('Geografia editada','Nova anotação')))

    def test_recorded_matplotlib_contracts_without_matplotlib_import(self):
        fixture=json.loads((Path(__file__).resolve().parents[1]/'docs/text-edits-reference.json').read_text(encoding='utf-8'))
        for test in fixture['contracts']:
            with self.subTest(name=test['name']):
                text=self.ax.annotate('Initial',(-48,-22),(12,8),textcoords='offset points',arrow=False) if test['annotation'] else self.ax.text(-48,-22,'Initial')
                for op in test['operations']:
                    if 'attribute' in op:setattr(text,op['attribute'],op['value'])
                    else:getattr(text,op['method'])(*op.get('args',[]),**op.get('kwargs',{}))
                actual=dict(text=text.get_text(),position=list(text.get_position()),color=text.get_color(),fontsize=text.get_fontsize(),
                            weight=text.get_fontweight(),fontstyle=text.get_fontstyle(),ha=text.get_ha(),va=text.get_va(),rotation=text.get_rotation(),visible=text.get_visible(),in_layout=text.get_in_layout())
                if test['annotation']:actual.update(xy=list(text.xy),xyann=list(text.xyann),anncoords=text.get_anncoords())
                self.assertEqual(actual,test['state']);text.remove()

"""Global map labels, Figure text editing and hierarchical margin integration."""
import io,json,unittest
from pathlib import Path
import azimlib as azl
import azimlib.pyplot as plt
from azimlib.cm import ScalarMappable
from azimlib.colors import Normalize
from azimlib.layout_engine import item_bounds,primitive_bounds
from azimlib.scene import Text


class FigureLabelTests(unittest.TestCase):
    def tearDown(self):azl.ioff();azl.close('all');azl.rcdefaults()

    def make(self,layout='constrained',nested=False,size=(8,6),dpi=100):
        fig=azl.figure(figsize=size,dpi=dpi,layout=layout)
        if nested:
            grid=fig.add_gridspec(2,1);child=grid[1].subgridspec(1,2)
            axes=[fig.add_subplot(grid[0]),fig.add_subplot(child[0]),fig.add_subplot(child[1])]
        else:axes=list(fig.subplots(1,2).flat)
        for ax in axes:
            ax.set_extent((-54,-42,-28,-16));ax.set_title('Foco regional',fontsize=11)
            ax.tick_params(labelrotation=25,labelsize=9)
        fig.suptitle('Atlas de pesquisa\nDados demonstrativos')
        fig.supxlabel('Longitude geográfica');fig.supylabel('Latitude geográfica')
        return fig,axes

    def assert_clearance(self,fig,scene):
        groups=[item_bounds(scene,s,e) for _,s,e,_ in scene._layout_groups]
        for box in groups:
            if box is None:continue
            x,y,w,h=box
            for slot in ('_suptitle','_supxlabel','_supylabel'):
                b=getattr(scene,'_layout'+slot)
                if b is None:continue
                self.assertGreaterEqual(b[0],-.2);self.assertGreaterEqual(b[1],-.2)
                self.assertLessEqual(b[0]+b[2],scene.width+.2);self.assertLessEqual(b[1]+b[3],scene.height+.2)
                if slot=='_suptitle':self.assertGreater(y,b[1]+b[3])
                elif slot=='_supxlabel':self.assertLess(y+h,b[1])
                else:self.assertGreater(x,b[0]+b[2])

    def test_default_labels_positions_style_and_figure_getters(self):
        fig=azl.figure()
        self.assertEqual((fig.get_suptitle(),fig.get_supxlabel(),fig.get_supylabel()),('','',''))
        for name,pos,ha,va,rotation in (('suptitle',(.5,.98),'center','top',0),('supxlabel',(.5,.01),'center','bottom',0),('supylabel',(.02,.5),'left','center',90)):
            with self.subTest(label=name):
                text=getattr(fig,name)(name)
                self.assertEqual(text.get_position(),pos);self.assertEqual(text.get_fontsize(),12)
                self.assertEqual((text.get_ha(),text.get_va(),text.get_rotation()),(ha,va,rotation))
                self.assertEqual(getattr(fig,'get_'+name)(),name)
                self.assertIs(text.get_figure(),fig);self.assertEqual(fig.get_children().count(text),1)

    def test_reuse_reset_defaults_explicit_coordinate_and_aliases(self):
        fig=azl.figure();text=fig.supxlabel('First',x=.3,y=.06,size=15,weight='bold',horizontalalignment='right')
        self.assertFalse(text._autopos);self.assertEqual(text.get_fontsize(),15)
        again=fig.supxlabel('Second',color='red')
        self.assertIs(text,again);self.assertEqual(text.get_position(),(.5,.01))
        self.assertTrue(text._autopos);self.assertEqual((text.get_fontsize(),text.get_fontweight(),text.get_ha()),(12,'normal','center'))
        self.assertEqual(text.get_color(),'red')
        text.set_visible(False);self.assertIs(fig.supxlabel('Hidden'),text);self.assertFalse(text.get_visible())

    def test_figure_text_live_position_and_alignment_commit_and_invalid_batch(self):
        fig=azl.figure();text=fig.text(.2,.3,'Note');events=[]
        text.add_callback(lambda a:events.append((a.get_position(),a.get_text(),a.get_color())))
        fig.canvas.draw();azl.setp(text,position=(.8,.1),text='Changed',color='red',ha='right',va='top')
        self.assertEqual(events,[((.8,.1),'Changed','red')]);self.assertTrue(fig.stale)
        scene=fig.to_scene();p=next(p for p in scene.items if isinstance(p,Text) and p.text=='Changed')
        self.assertEqual((p.x,p.y),(512,432))
        before=(text.get_position(),dict(text.style),text.get_text(),len(events))
        for kwargs in ({'position':(float('nan'),0),'text':'bad'},{'x':.4,'fontsize':-2},{'y':.4,'ha':'bad'},{'x':.9,'rotation_mode':'unsupported'},{'x':.9,'unknown':True}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((ValueError,TypeError)):text.set(**kwargs)
                self.assertEqual((text.get_position(),text.style,text.get_text(),len(events)),before)
        text.set_x(.4);text.set_y(.5);self.assertEqual(azl.getp(text,'position'),(.4,.5))

    def test_global_labels_reserve_space_simple_nested_sizes_and_dpi(self):
        for mode in ('tight','constrained'):
            for nested in (False,True):
                for size in ((7,6),(9,7)):
                    for dpi in (100,150,200):
                        with self.subTest(mode=mode,nested=nested,size=size,dpi=dpi):
                            fig,axes=self.make(mode,nested,size,dpi)
                            fig.colorbar(ScalarMappable(Normalize(0,100)),ax=axes,orientation='horizontal',label='Indicador')
                            self.assert_clearance(fig,fig.to_scene())
                            old=[a.position for a in axes];self.assert_clearance(fig,fig.to_scene())
                            self.assertEqual(old,[a.position for a in axes]);azl.close(fig)

    def test_hide_exclude_remove_release_margins_and_clear_detaches(self):
        fig,axes=self.make();fig.to_scene();reserved=axes[0].position
        label=fig._supylabel;label.set_visible(False);fig.to_scene();hidden=axes[0].position
        self.assertLess(hidden[0],reserved[0])
        label.set_visible(True);label.set_in_layout(False);scene=fig.to_scene()
        self.assertEqual(hidden,axes[0].position)
        self.assertTrue(any(isinstance(p,Text) and p.text==label.text for p in scene.items))
        label.set(in_layout=True);fig.to_scene();self.assertEqual(reserved,axes[0].position)
        x=fig._supxlabel;x.remove();self.assertEqual(fig.get_supxlabel(),'');self.assertIsNone(x.get_figure())
        new=fig.supxlabel('Replacement');self.assertIsNot(x,new)
        text=fig.text(.5,.5,'Note');children=fig._figure_labels()+[text];fig.clear()
        for child in children:self.assertIsNone(child.get_figure());self.assertIsNone(child._owner)
        self.assertEqual(fig.get_children(),[])

    def test_constrained_automatic_edge_only_and_manual_label_has_no_reservation(self):
        fig,axes=self.make();title=fig._suptitle;label=fig._supxlabel;y=fig._supylabel
        fig.to_scene();pad=100*fig.get_layout_engine().get()['h_pad']
        self.assertAlmostEqual(title.get_y(),1-pad/600)
        self.assertAlmostEqual(label.get_y(),pad/600);self.assertAlmostEqual(y.get_x(),pad/800)
        fig.suptitle('Manual title',y=.6);fig.supxlabel('Manual X',y=.4);fig.supylabel('Manual Y',x=.4)
        scene=fig.to_scene();manual=[a.position for a in axes]
        self.assertEqual((title.get_y(),label.get_y(),y.get_x()),(.6,.4,.4))
        for text in fig._figure_labels():text.set_in_layout(False)
        fig.to_scene();self.assertEqual(manual,[a.position for a in axes])
        self.assertIsNotNone(scene._layout_suptitle)

    def test_tight_is_once_labels_stay_manual_and_future_engine_reacts(self):
        fig,axes=self.make(None);label=fig._supxlabel;position=label.get_position()
        fig.tight_layout();first=axes[0].position;self.assertEqual(label.get_position(),position)
        label.set_fontsize(24);fig.to_scene();self.assertEqual(first,axes[0].position)
        fig.set_layout_engine('tight');self.assert_clearance(fig,fig.to_scene())
        self.assertGreater(axes[0].position[1],first[1]);self.assertEqual(label.get_position(),position)

    def test_failure_restores_axes_parameters_and_automatic_text_positions(self):
        for nested in (False,True):
            with self.subTest(nested=nested):
                fig,axes=self.make('constrained',nested,(3,2))
                fig.supylabel('Far too long '*40);fig.supxlabel('Far too wide '*40)
                before=[a.position for a in axes];texts=[a.get_position() for a in fig._figure_labels()];pars=dict(fig.subplotpars)
                with self.assertWarnsRegex(UserWarning,'Previous positions'):fig.to_scene()
                self.assertEqual(before,[a.position for a in axes]);self.assertEqual(texts,[a.get_position() for a in fig._figure_labels()])
                self.assertEqual(pars,fig.subplotpars)

    def test_rotation_default_aligns_bbox_anchor_mode_preserves_origin(self):
        fig=azl.figure();text=fig.supylabel('Latitude')
        scene=fig.to_scene();box=scene._layout_supylabel
        self.assertAlmostEqual(box[0],.02*640);self.assertAlmostEqual(box[1]+box[3]/2,240)
        text.set_rotation_mode('anchor');scene=fig.to_scene();p=next(p for p in scene.items if isinstance(p,Text))
        self.assertEqual((p.x,p.y),(12.8,240));self.assertNotEqual(scene._layout_supylabel,box)
        text.set(rotation='horizontal',rotation_mode=None);self.assertEqual(text.get_rotation(),0)
        self.assertEqual(text.get_rotation_mode(),'default')

    def test_rc_fonts_and_pyplot_current_figure_entry_points(self):
        with azl.rc_context({'font.size':15,'figure.titlesize':'large','figure.labelsize':17,'figure.labelweight':'bold'}):
            fig=azl.figure();self.assertEqual(fig.suptitle('Title').get_fontsize(),18)
            text=fig.supxlabel('X');self.assertEqual((text.get_fontsize(),text.get_fontweight()),(17,'bold'))
        self.assertIs(plt.suptitle('Current'),fig._suptitle)
        note=plt.figtext(.3,.2,'Footnote');self.assertIs(note.get_figure(),fig)
        before=dict(azl.rcParams)
        with self.assertRaises(ValueError):azl.rcParams.update({'figure.labelsize':-1,'font.size':14})
        self.assertEqual(before,dict(azl.rcParams))

    def test_scene_scaling_export_and_optional_labels(self):
        fig,axes=self.make('tight');scene=fig.to_scene();scaled=scene.scaled(2)
        for name in ('_layout_suptitle','_layout_supxlabel','_layout_supylabel'):
            self.assertEqual(getattr(scaled,name),tuple(2*v for v in getattr(scene,name)))
        out=io.StringIO();fig.savefig(out,format='svg');self.assertIn('Longitude geográfica',out.getvalue())
        self.assertIn('Latitude geográfica',fig.to_html())
        blank,ax=azl.subplots();scene=blank.to_scene()
        self.assertEqual(blank._figure_labels(),[]);self.assertIsNone(scene._layout_supxlabel)
        self.assertIsNone(ax._overview);self.assertFalse(any(l.kind=='grid' for l in ax.layers))

    def test_recorded_matplotlib_label_contracts(self):
        path=Path(__file__).resolve().parents[1]/'docs/figure-labels-reference.json'
        fixture=json.loads(path.read_text(encoding='utf-8'))
        for case in fixture['contracts']:
            with self.subTest(name=case['name']):
                fig=azl.figure();artist=None
                for op in case['operations']:
                    if op['kind']=='call':
                        kwargs=dict(op['kwargs'])
                        if op['method']=='text':artist=fig.text(kwargs.pop('x'),kwargs.pop('y'),op['text'],**kwargs)
                        else:artist=getattr(fig,op['method'])(op['text'],**kwargs)
                    else:artist.set(**op['kwargs'])
                actual=dict(position=list(artist.get_position()),text=artist.get_text(),fontsize=artist.get_fontsize(),
                            weight=artist.get_fontweight(),ha=artist.get_ha(),va=artist.get_va(),rotation=artist.get_rotation(),
                            rotation_mode=artist.get_rotation_mode(),visible=artist.get_visible(),in_layout=artist.get_in_layout())
                self.assertEqual(actual,case['state'])

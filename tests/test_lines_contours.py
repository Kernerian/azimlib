"""Editable isolines/labels, line batches and renderer integration."""
import io
import json
from itertools import permutations
from pathlib import Path as FilePath
import unittest
import azimlib as azl
from azimlib.colors import Normalize,LogNorm
from azimlib.geometry import FeatureCollection
from azimlib.scene import Path,Circle,Text
from azimlib.styles import path_style
from azimlib.typography import POINT
from azimlib.renderers import render_png
from azimlib.ticker import FixedLocator,FormatStrFormatter


class LinesContoursTests(unittest.TestCase):
    def tearDown(self):azl.close('all');azl.ioff();azl.rcdefaults()
    def line(self):
        fig,ax=azl.subplots(figsize=(3,3));ax.set_extent((-54,-42,-28,-16))
        line,=ax.plot([-52,-48,-44],[-25,-22,-20],color='red',marker='o',label='Route')
        return fig,ax,line
    def contour(self,**kwargs):
        fig,ax=azl.subplots(figsize=(4,4));ax.set_extent((-54,-44,-26,-18))
        contour=ax.contour([-54,-49,-44],[-26,-22,-18],[[0,1,2]]*3,levels=[.5,1.5],**kwargs)
        return fig,ax,contour

    def test_line_final_states_match_installed_matplotlib(self):
        fig,ax,line=self.line();actual=[]
        keys=('color','linewidth','linestyle','marker','markersize','markerfacecolor',
              'markeredgecolor','markeredgewidth','solid_capstyle','dash_capstyle',
              'solid_joinstyle','dash_joinstyle','antialiased','alpha','visible','label')
        def snapshot(name):
            actual.append(dict(name=name,data=list(line.get_data()),
                **{key:getattr(line,'get_'+key)() for key in keys}))
        snapshot('initial')
        azl.setp(line,data=([-51,-47,-43],[-26,-23,-19]),color='blue',linewidth=.9,
            linestyle='--',marker='s',markersize=4,markerfacecolor='white',markeredgecolor='black',
            markeredgewidth=.4,solid_capstyle='butt',dash_capstyle='round',solid_joinstyle='miter',
            dash_joinstyle='bevel',antialiased=False,alpha=.7,visible=False,label='Edited route')
        snapshot('grouped')
        line.set(xdata=[-50,-46,-42],ydata=[-25,-22,-18],marker='None',linestyle='None',
            markerfacecolor='auto',markeredgecolor='auto',alpha=None,visible=True)
        snapshot('no-symbols');line.set_data([],[]);snapshot('empty')
        reference=json.loads((FilePath(__file__).resolve().parents[1]/'docs/lines-contours-reference.json').read_text())
        self.assertEqual(actual,reference['lines'])

    def test_line_batches_validate_before_any_edit_and_notify_final_state_once(self):
        fig,ax,line=self.line();source=line.data;extent=ax.get_extent();events=[]
        line.add_callback(lambda a:events.append((a.get_data(),a.get_marker(),a.get_visible())))
        azl.setp(line,xdata=[-53,-49,-45],ydata=[-26,-23,-19],marker='^',visible=False)
        self.assertEqual(events,[(([-53,-49,-45],[-26,-23,-19]),'^',False)])
        self.assertEqual(ax.get_extent(),extent);self.assertEqual(source[0].geometry.coordinates[0],(-52,-25))
        bad=[dict(data=([1,2],[3])),dict(data=([1,2],[3,91])),dict(data=([1,2],[3,4]),linewidth=-1),
             dict(data=([1,2],[3,4]),marker='bad'),dict(data=([1,2],[3,4]),dash_capstyle='bad'),
             dict(data=([1,2],[3,4]),xdata=[1,2]),dict(data=([1,2],[3,4]),unknown=3)]
        for kwargs in bad:
            with self.subTest(kwargs=kwargs):
                fig.canvas.draw();events.clear();before=(line.data,dict(line.style),line.get_visible())
                with self.assertRaises((ValueError,TypeError)):line.set(visible=True,**kwargs)
                self.assertEqual((line.data,line.style,line.get_visible()),before)
                self.assertFalse(fig.stale);self.assertEqual(events,[])
        line.set_visible(True);ax.relim();ax.autoscale_view();self.assertEqual(ax.get_extent(),extent)

    def test_data_keywords_order_and_single_axis_setters(self):
        for order in permutations(('xdata','ydata','color','marker')):
            with self.subTest(order=order):
                fig,ax,line=self.line();props=dict(xdata=[-51,-47],ydata=[-26,-20],color='blue',marker='s')
                line.set(**{key:props[key] for key in order})
                self.assertEqual(line.get_data(),([-51,-47],[-26,-20]));self.assertEqual(line.get_marker(),'s')
                line.set_xdata([-50,-46]);line.set_ydata([-25,-19])
                self.assertEqual(line.get_data(),([-50,-46],[-25,-19]));azl.close(fig)

    def test_cap_join_selection_physical_width_and_hidden_stroke(self):
        for ls,family in (('-','solid'),('--','dash'),(':','dash')):
            for cap in ('butt','round','projecting'):
                for join in ('miter','round','bevel'):
                    with self.subTest(ls=ls,cap=cap,join=join):
                        style=path_style(dict(linewidth=.8,linestyle=ls,**{
                            **dict(solid_capstyle='round',dash_capstyle='butt'),
                            family+'_capstyle':cap,family+'_joinstyle':join}))
                        self.assertEqual(style['linecap'],'square' if cap=='projecting' else cap)
                        self.assertEqual(style['linejoin'],join);self.assertEqual(style['stroke_width'],.8*POINT)
        self.assertEqual(path_style({'linestyle':'None'})['stroke'],'none')

    def test_marker_getters_setters_auto_and_hidden_markers(self):
        fig,ax,line=self.line();line.set(markerfacecolor='auto',markeredgecolor='auto',color='blue')
        scene=fig.to_scene();dots=[p for p in scene.items if isinstance(p,Circle)]
        self.assertEqual(len(dots),3);self.assertTrue(all(p.style['fill']=='blue' and p.style['stroke']=='blue' for p in dots))
        for setter,value in (('marker','s'),('markersize',4),('markerfacecolor','white'),('markeredgecolor','black'),
                             ('markeredgewidth',.4),('antialiased',False),('dash_capstyle','round'),('solid_joinstyle','miter')):
            getattr(line,'set_'+setter)(value);self.assertEqual(azl.getp(line,setter),value)
        line.set_marker(None);self.assertFalse(any(isinstance(p,Circle) for p in fig.to_scene().items))
        line.set_marker('o');line.set_markersize(0);self.assertFalse(any(isinstance(p,Circle) for p in fig.to_scene().items))
        line.set_data([-49],[-22]);line.set_markersize(6);line.set_marker('None')
        self.assertFalse(any(isinstance(p,Circle) for p in fig.to_scene().items))
        line.set_marker('o');self.assertEqual(sum(isinstance(p,Circle) for p in fig.to_scene().items),1)

    def test_text_and_annotation_batch_editing(self):
        fig,ax,line=self.line();artists=[ax.text(-50,-22,'Old'),ax.annotate('Old',(-50,-22))]
        for item in artists:
            with self.subTest(kind=item.kind):
                azl.setp(item,text='New',fontsize=9,color='red',rotation=15,visible=False)
                self.assertEqual(item.get_text(),'New');self.assertEqual(item.get_fontsize(),9)
                self.assertFalse(item.get_visible());fig.canvas.draw()
                with self.assertRaises(ValueError):item.set(text='Invalid',visible=True,fontsize=-1)
                self.assertEqual(item.get_text(),'New');self.assertFalse(item.get_visible());self.assertFalse(fig.stale)

    def test_contour_final_states_and_label_protocol_match_matplotlib(self):
        fig,ax,item=self.contour(linewidths=[.4,.8]);actual=[]
        def snapshot(name):
            actual.append(dict(name=name,levels=list(item.levels),array=item.get_array(),
                linewidths=item.get_linewidths(),alpha=item.get_alpha(),visible=item.get_visible(),
                clim=list(item.get_clim()),cmap=item.cmap.name))
        snapshot('initial');item.set(linewidth=[1,2],linestyle=['--',':'],alpha=.5,cmap='plasma',clim=(0,2));snapshot('grouped')
        labels=ax.clabel(item,levels=[.5,1.5],fmt={.5:'Low',1.5:'High'},inline=False)
        protocol=dict(is_list=isinstance(labels,list),texts=[t.get_text() for t in labels])
        azl.setp(labels,fontsize=9,color='black');labels[0].set_text('Edited');labels[1].set_visible(False)
        protocol.update(texts_after=[t.get_text() for t in labels],visibility_after=[t.get_visible() for t in labels],
            fontsize=[t.get_fontsize() for t in labels])
        item.set_visible(False);protocol['visibility_after_hidden_contour']=[t.get_visible() for t in labels];snapshot('hidden')
        item.remove();protocol['removed_with_contour']=all(t.axes is None and t.get_figure() is None for t in labels)
        reference=json.loads((FilePath(__file__).resolve().parents[1]/'docs/lines-contours-reference.json').read_text())
        self.assertEqual(actual,reference['contours']);self.assertEqual(protocol,reference['label_protocol'])

    def test_contour_widths_styles_colors_cycle_by_level_not_segment(self):
        fig,ax=azl.subplots();x=[-54,-52,-50,-48,-46,-44];y=[-26,-22,-18]
        item=ax.contour(x,y,[[0,2,0,2,0,2]]*3,levels=[.5,1,1.5],colors=['red','blue'],linewidths=[.3,.8],linestyles=['--',':'])
        self.assertIsInstance(item,azl.ContourSet)
        self.assertEqual(item.get_linewidths(),[.3,.8,.3]);self.assertEqual(item.get_linestyles(),['--',':','--'])
        self.assertEqual(item.get_edgecolors(),['red','blue','red']);self.assertEqual(len(item.allsegs),3)
        props=azl.getp(item)
        self.assertEqual(props['linewidth'],[.3,.8,.3]);self.assertEqual(props['linestyle'],['--',':','--'])
        self.assertEqual(props['color'],['red','blue','red'])
        self.assertTrue(all(len(segments)==5 for segments in item.allsegs))
        for i,feature in enumerate(item.data):
            with self.subTest(feature=i):
                level=item.levels.index(feature.properties['level']);style=item._feature_style(i,feature)
                self.assertEqual(style['color'],['red','blue','red'][level]);self.assertEqual(style['linewidth'],[.3,.8,.3][level])
        copy=item.allsegs;copy[0][0][0][0]=999;self.assertNotEqual(item.allsegs[0][0][0][0],999)
        item.set_color('black');item.set_cmap('plasma');item.set_clim(0,3)
        self.assertEqual(item.get_edgecolors(),['black']*3)
        item.set_color(None);self.assertNotEqual(item.get_edgecolors(),['black']*3)

    def test_contour_invalid_creation_and_batches_preserve_state(self):
        fig,ax,item=self.contour();labels=ax.clabel(item);bar=fig.colorbar(item);bar.locator=FixedLocator([.5,1.5]);locator=bar.locator
        for props in (dict(linewidths=[]),dict(linewidths=[1,-1]),dict(linestyles=['bad']),dict(colors=[]),
                      dict(colors=[3]),dict(clim=(3,1)),dict(array=[1]),dict(linewidth=1,lw=2),dict(data=[[0],[1]])):
            with self.subTest(props=props):
                fig.canvas.draw();events=[];cid=item.add_callback(events.append)
                before=(dict(item.options),dict(item.style),item.get_array(),item.get_cmap(),item.get_clim(),[l.get_color() for l in labels])
                with self.assertRaises((ValueError,TypeError)):item.set(visible=False,**props)
                self.assertEqual((item.options,item.style,item.get_array(),item.get_cmap(),item.get_clim(),[l.get_color() for l in labels]),before)
                self.assertTrue(item.visible);self.assertFalse(fig.stale);self.assertEqual(events,[]);self.assertIs(bar.locator,locator)
                item.remove_callback(cid)
        for props in (dict(colors=[]),dict(linewidths=[-1]),dict(linestyles='bad'),dict(cmap='bad'),dict(norm=object())):
            with self.subTest(creation=props):
                fig.canvas.draw();before=list(ax.layers)
                with self.assertRaises((ValueError,TypeError)):ax.contour([-54,-44],[-26,-18],[[0,2],[0,2]],levels=[1],**props)
                self.assertEqual(ax.layers,before);self.assertFalse(fig.stale)

    def test_contour_mapping_labels_colorbar_callbacks_and_manual_view(self):
        fig,ax,item=self.contour();extent=ax.get_extent();labels=ax.clabel(item)
        bar=fig.colorbar(item);bar.locator=FixedLocator([.5,1.5]);old=bar.locator;seen=[]
        item.add_callback(lambda a:seen.append((a.get_clim(),a.get_linewidths(),a.get_visible())))
        azl.setp(item,cmap='plasma',clim=(0,2),linewidths=[.7,1.2],linestyles=['--',':'],visible=False)
        self.assertEqual(seen,[((0,2),[.7,1.2],False)]);self.assertIs(bar.locator,old)
        self.assertTrue(all(t.visible for t in labels));self.assertEqual([t.get_color() for t in labels],item.get_color())
        labels[0].set_color('black');item.set(norm=LogNorm(.1,10),cmap='viridis')
        self.assertIsNot(bar.locator,old);self.assertIs(bar.norm,item.norm);self.assertEqual(labels[0].get_color(),'black')
        self.assertEqual(labels[1].get_color(),item.get_color()[1]);self.assertEqual(ax.get_extent(),extent)

    def test_clabel_selected_levels_formatters_visibility_removal_and_validation(self):
        fig,ax,item=self.contour();labels=ax.clabel(item,[.5],fmt=FormatStrFormatter('%.1f'),colors='black',fontsize=8)
        self.assertEqual([label.get_text() for label in labels],['0.5'])
        self.assertIsInstance(labels[0],azl.ContourLabel);self.assertIn(labels[0],fig.findobj())
        azl.setp(labels,text='Isoline',fontsize=10,alpha=.7)
        self.assertEqual(labels[0].get_text(),'Isoline');self.assertIn('Isoline',fig.to_svg())
        for props in (dict(levels=[7]),dict(fontsize=-1),dict(inline_spacing=-1),dict(fmt=lambda x:1/0)):
            with self.subTest(props=props):
                fig.canvas.draw();before=list(ax.layers)
                with self.assertRaises((ValueError,ZeroDivisionError)):ax.clabel(item,**props)
                self.assertEqual(ax.layers,before);self.assertFalse(fig.stale)
        with self.assertRaises(ValueError):fig.add_axes((0,0,.2,.2)).clabel(item)
        labels.set_visible(False);self.assertNotIn('Isoline',fig.to_svg())
        labels.set_visible(True);self.assertIn('Isoline',fig.to_svg())
        labels[0].remove();self.assertEqual(item.labelTexts,[]);self.assertIsNone(labels[0].axes)
        labels=ax.clabel(item,fmt=lambda value:f'{value} units');item.remove()
        self.assertTrue(all(l.axes is None and l.get_figure() is None for l in labels));self.assertEqual(item.labelTexts,[])

    def test_empty_contours_and_labels(self):
        fig,ax=azl.subplots();item=ax.contour([-54,-44],[-26,-18],[[0,0],[0,0]],levels=[1,2])
        self.assertEqual(item.allsegs,[[],[]]);self.assertEqual(item.get_array(),[1,2])
        self.assertEqual(ax.clabel(item),[]);item.set(linewidths=[.5],colors='red')
        self.assertEqual(item.get_color(),['red','red']);fig.to_svg();item.remove()

    def test_contour_culling_with_per_level_widths_matches_complete_png(self):
        for projection in ('equirectangular','mercator'):
            with self.subTest(projection=projection):
                fig,ax=azl.subplots(figsize=(3,3),projection=projection)
                x=[-60+i*.25 for i in range(81)];y=[-30,-20,-10]
                item=ax.contour(x,y,[[0 if i%2==0 else 2 for i in range(81)]]*3,
                    levels=[.5,1.5],colors=['red','blue'],linewidths=[.4,8])
                self.assertGreaterEqual(len(item.data),64)
                ax.set_extent((-54,-44,-26,-18));buffers=[]
                for cull in (False,True):
                    buffer=io.BytesIO();render_png(fig.to_scene(cull=cull),buffer);buffers.append(buffer.getvalue())
                self.assertEqual(*buffers)
                item.set(linewidths=[9,.4],colors=['blue','red'])
                buffers=[]
                for cull in (False,True):
                    buffer=io.BytesIO();render_png(fig.to_scene(cull=cull),buffer);buffers.append(buffer.getvalue())
                self.assertEqual(*buffers)

    def test_clear_detaches_contours_labels_and_later_edits(self):
        fig,ax,item=self.contour();labels=item.clabel()
        ax.clear();fig.canvas.draw()
        item.set_clim(0,3);azl.setp(labels,text='Detached',visible=False)
        self.assertFalse(fig.stale)
        self.assertIsNone(item.get_figure());self.assertTrue(all(l.get_figure() is None for l in labels))
        with self.assertRaises(ValueError):item.clabel()

    def test_original_linecap_and_linejoin_overrides_are_preserved(self):
        fig,ax=azl.subplots()
        line,=ax.plot([-52,-44],[-26,-18],linecap='butt',linejoin='bevel')
        self.assertEqual(path_style(line.style)['linecap'],'butt')
        self.assertEqual(path_style(line.style)['linejoin'],'bevel')
        self.assertEqual(line.get_solid_capstyle(),'butt');self.assertEqual(line.get_solid_joinstyle(),'bevel')

    def test_scene_exports_and_equivalent_dedicated_edits(self):
        first=[];second=[]
        for grouped in (True,False):
            fig,ax,line=self.line();item=ax.contour([-54,-49,-44],[-26,-22,-18],[[0,1,2]]*3,levels=[.5,1.5])
            labels=ax.clabel(item,fmt='%.1f');bar=fig.colorbar(item,orientation='horizontal')
            if grouped:
                line.set(data=([-51,-47,-43],[-26,-23,-19]),marker='s',markerfacecolor='white',markeredgewidth=.4,linestyle='--')
                item.set(linewidths=[.4,.8],linestyles=['--',':'],cmap='plasma',clim=(0,2),alpha=.7)
                azl.setp(labels,fontsize=8,color='black')
            else:
                line.set_data([-51,-47,-43],[-26,-23,-19]);line.set_marker('s');line.set_markerfacecolor('white')
                line.set_markeredgewidth(.4);line.set_linestyle('--')
                item.set_linewidths([.4,.8]);item.set_linestyles(['--',':']);item.set_cmap('plasma');item.set_clim(0,2);item.set_alpha(.7)
                for label in labels:label.set_fontsize(8);label.set_color('black')
            scene=fig.to_scene();png=io.BytesIO();render_png(scene,png)
            (first if grouped else second).extend((scene.items,scene.maps,png.getvalue()))
            self.assertIn('<svg',fig.to_svg());self.assertIn('Figure',fig.to_html());self.assertNotIn('class="toolbar"',fig.to_svg())
        self.assertEqual(first,second)


if __name__=='__main__':unittest.main()

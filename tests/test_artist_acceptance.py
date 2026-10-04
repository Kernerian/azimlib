"""0.2.0 step-1 acceptance: combined real geometry and edited synthetic fields."""
import importlib.util
import io
import json
from pathlib import Path
import unittest
import azimlib as azl
from azimlib.colors import Normalize

ROOT=Path(__file__).resolve().parents[1]
def tool(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'tools'/f'{name}.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
case_tool=tool('artist_acceptance_case')


class ArtistAcceptanceTests(unittest.TestCase):
    def tearDown(self):azl.close('all');azl.ioff();azl.rcdefaults()

    def test_selected_aliases_and_rejections_match_installed_reference(self):
        reference=json.loads((ROOT/'docs/artist-acceptance-reference.json').read_text())
        self.assertEqual(tool('inspect_artist_acceptance').inspect(azl),reference['reference'])

    def test_six_shared_mappables_edit_callbacks_visibility_and_exports(self):
        for orientation in ('vertical','horizontal'):
            for dpi in (100,200):
                with self.subTest(orientation=orientation,dpi=dpi):
                    case=case_tool.build(dpi=dpi,orientation=orientation,figsize=(3,2.8))
                    fig,ax,norm=case['fig'],case['ax'],case['norm'];items=case_tool.mappables(case)
                    self.assertEqual(ax.get_extent(),(-54,-42,-28,-16))
                    self.assertTrue(all(item.norm is norm for item in items));paths=case['contour'].allsegs
                    extent=ax.get_extent();before=fig.to_svg();seen=[]
                    for index,item in enumerate(items):item.callbacks.connect('changed',lambda obj,i=index:seen.append((i,obj.get_clim())))
                    norm.vmax=6
                    self.assertEqual(sorted(seen),[(i,(0,6)) for i in range(6)])
                    self.assertIs(case['bar'].norm,norm);case_tool.edit(case)
                    self.assertTrue(all(item.get_clim()==(0,5) for item in items))
                    self.assertEqual(ax.get_extent(),extent);self.assertEqual(case['contour'].allsegs,paths)
                    edited=fig.to_svg();self.assertNotEqual(before,edited)
                    for item in items:item.set_visible(False)
                    hidden=fig.to_svg();self.assertNotEqual(edited,hidden)
                    for item in items:item.set_visible(True)
                    self.assertEqual(edited,fig.to_svg())
                    for label in case['labels']:self.assertEqual(label.get_color(),case['contour']._level_color(case['contour'].levels.index(label.options['contour_level'])))
                    png=io.BytesIO();fig.savefig(png,format='png');self.assertTrue(png.getvalue().startswith(b'\x89PNG'))
                    case_tool.dispose(case);fig.canvas.draw();norm.vmax=7
                    self.assertFalse(fig.stale);self.assertTrue(all(item.get_figure() is None for item in items))
                    self.assertTrue(all(label.get_figure() is None for label in case['labels']));azl.close(fig)

    def test_all_catalogue_families_reject_unknown_before_controls_change(self):
        case=case_tool.build();families=case_tool.audited_families(case);fig=case['fig']
        fig.canvas.draw();before=fig.to_svg()
        for name,item in families.items():
            with self.subTest(family=name):
                visible=item.get_visible() if hasattr(item,'get_visible') else None;seen=[]
                cid=item.add_callback(seen.append)
                with self.assertRaises((TypeError,AttributeError)):item.set(visible=False,azimlib_unknown=1)
                self.assertEqual(item.get_visible() if hasattr(item,'get_visible') else None,visible)
                self.assertFalse(fig.stale);self.assertEqual(seen,[]);self.assertEqual(fig.to_svg(),before)
                item.remove_callback(cid)

    def test_alias_conflicts_and_unsupported_data_leave_mappables_untouched(self):
        case=case_tool.build();fig=case['fig']
        for name in ('theme','scatter','mesh','image','vector','contour','line'):
            item=case[name]
            for props in (dict(c='red',color='blue'),dict(lw=.4,linewidth=.8),dict(unsupported=3)):
                with self.subTest(name=name,props=props):
                    fig.canvas.draw();before=(item.data,dict(item.style),item.norm,item.cmap,item.get_array());seen=[]
                    cid=item.add_callback(seen.append)
                    with self.assertRaises((TypeError,ValueError)):item.set(visible=False,norm=Normalize(0,50),**props)
                    self.assertEqual((item.data,item.style,item.norm,item.cmap,item.get_array()),before)
                    self.assertTrue(item.get_visible());self.assertFalse(fig.stale);self.assertEqual(seen,[]);item.remove_callback(cid)
        for name in ('theme','scatter','mesh','vector','contour'):
            with self.subTest(data=name):
                item=case[name];fig.canvas.draw();before=item.data
                with self.assertRaises((TypeError,ValueError)):item.set(data=[1],visible=False)
                self.assertIs(item.data,before);self.assertTrue(item.get_visible());self.assertFalse(fig.stale)

    def test_label_alignment_and_tick_creation_fail_before_any_commit(self):
        case=case_tool.build(figsize=(2.5,2.5));fig,ax=case['fig'],case['ax']
        labels=ax.labels({'type':'Feature','properties':{'name':'Point'},'geometry':{'type':'Point','coordinates':[-48,-21]}})
        for item in (labels,case['labels'][0]):
            for prop in ('ha','horizontalalignment','va','verticalalignment'):
                with self.subTest(kind=type(item).__name__,prop=prop):
                    fig.canvas.draw();before=(item.data,dict(item.style),dict(item.options))
                    with self.assertRaises(ValueError):item.set(visible=False,text='Changed',**{prop:'wrong'}) if item is not labels else item.set(visible=False,**{prop:'wrong'})
                    self.assertEqual((item.data,item.style,item.options),before);self.assertTrue(item.get_visible());self.assertFalse(fig.stale)
        for axis in ('x','y'):
            with self.subTest(axis=axis):
                fig.canvas.draw();controller=getattr(ax,axis+'axis');locator=controller.get_major_locator();extent=ax.get_extent()
                with self.assertRaises(ValueError):getattr(ax,'set_'+axis+'ticks')([-48] if axis=='x' else [-22],['Invalid'],ha='wrong')
                self.assertIs(controller.get_major_locator(),locator);self.assertEqual(ax.get_extent(),extent);self.assertFalse(fig.stale)

    def test_choropleth_invalid_mapping_preserves_layers_extent_and_norm(self):
        fig,ax=azl.subplots();ax.set_extent((-54,-42,-28,-16));data=azl.datasets.load('states','brazil')
        values=[i%5 for i in range(len(data['features']))];norm=Normalize();seen=[];norm.callbacks.connect('changed',lambda:seen.append(1))
        for props in (dict(norm=object()),dict(norm=Normalize(0,4),vmin=0),dict(norm=norm,unknown_style=1),dict(norm=norm,cmap='missing')):
            with self.subTest(props=props):
                fig.canvas.draw();extent=ax.get_extent();before=list(ax.layers)
                with self.assertRaises((TypeError,ValueError)):ax.choropleth(data,values,**props)
                self.assertEqual(ax.layers,before);self.assertEqual(ax.get_extent(),extent);self.assertFalse(fig.stale)
                self.assertFalse(norm.scaled());self.assertEqual(seen,[])

    def test_getp_resolves_style_alias_but_retains_component_size_semantics(self):
        fig,ax=azl.subplots();text=ax.text(-48,-22,'Text',fontsize=11);north=ax.north_arrow(size=24)
        self.assertEqual(azl.getp(text,'size'),11);self.assertEqual(azl.getp(north,'size'),24)
        line,=ax.plot([-52,-48],[-25,-21],mfc='white',lw=.7)
        for alias,canonical in (('lw','linewidth'),('ls','linestyle'),('mfc','markerfacecolor'),('mec','markeredgecolor'),('ms','markersize')):
            with self.subTest(alias=alias):self.assertEqual(azl.getp(line,alias),azl.getp(line,canonical))

    def test_text_families_reject_point_and_area_properties_before_commit(self):
        case=case_tool.build();families=case_tool.audited_families(case);fig=case['fig']
        for name in ('text','annotation','title','figure_text','tick','labels','contour_label','legend_text','colorbar_label'):
            item=families[name]
            for props in (dict(marker='o'),dict(ms=4),dict(hatch='//'),dict(symbol='★')):
                with self.subTest(name=name,props=props):
                    fig.canvas.draw();before=dict(item.style);seen=[];cid=item.add_callback(seen.append)
                    with self.assertRaises(TypeError):item.set(visible=False,**props)
                    self.assertEqual(item.style,before);self.assertTrue(item.get_visible());self.assertFalse(fig.stale)
                    self.assertEqual(seen,[]);item.remove_callback(cid)

    def test_new_text_rejections_do_not_move_figure_text_or_replace_ticks(self):
        fig,ax=azl.subplots();text=fig.text(.2,.2,'Fixed');old=ax.set_xticks([-52],['Original'])[0]
        for props in (dict(marker='o'),dict(hatch='//')):
            with self.subTest(props=props):
                fig.canvas.draw();position=text.get_position();locator=ax.xaxis.get_major_locator()
                with self.assertRaises(TypeError):text.set(position=(.8,.8),visible=False,**props)
                self.assertEqual(text.get_position(),position);self.assertTrue(text.visible);self.assertFalse(fig.stale)
                with self.assertRaises(TypeError):ax.set_xticks([-48],['Changed'],**props)
                self.assertIs(ax.xaxis.get_major_locator(),locator);self.assertIs(old.get_figure(),fig);self.assertFalse(fig.stale)

    def test_imshow_retains_manual_limits_per_axis(self):
        reference=json.loads((ROOT/'docs/artist-acceptance-reference.json').read_text())['reference']['manual_image_views']
        for case in reference:
            with self.subTest(case=case):
                fig,ax=azl.subplots()
                if case['manual_x']:ax.set_xlim(-54,-42)
                if case['manual_y']:ax.set_ylim(-28,-16)
                image=ax.imshow([[0,1],[2,3]],extent=(-47,-43,-25,-20))
                self.assertEqual(list(ax.get_xlim()),case['xlim']);self.assertEqual(list(ax.get_ylim()),case['ylim'])
                self.assertEqual(image.get_extent(),(-47,-43,-25,-20));azl.close(fig)


if __name__=='__main__':unittest.main()

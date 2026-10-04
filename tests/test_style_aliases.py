"""Ambiguous caller aliases fail before editing any attached Artist."""
import json
from pathlib import Path
import unittest
import azimlib as azl
from azimlib.styles import normalize_aliases,style_dict
from azimlib.components import MapComponent

class StyleAliasTests(unittest.TestCase):
    def tearDown(self):azl.close('all');azl.rcdefaults()

    def test_selected_aliases_and_conflicts_match_recorded_matplotlib(self):
        report=json.loads((Path(__file__).resolve().parents[1]/'docs/style-alias-reference.json').read_text(encoding='utf-8'))
        for row in report['cases']:
            with self.subTest(name=row['name']):
                # Azimlib stores ha/va internally; the public spellings agree.
                self.assertEqual(normalize_aliases({row['alias']:row['value']}),normalize_aliases(row['normalized']))
                self.assertEqual(row['conflict_error'],'TypeError')
                with self.assertRaises(TypeError):style_dict({row['name']:row['value'],row['alias']:row['value']})

    def test_geographic_factories_accept_aliases_over_their_defaults(self):
        fig,ax=azl.subplots()
        for factory,args in ((ax.map,('brazil',)),(ax.state,('SP',)),(ax.states,()),(ax.countries,())):
            with self.subTest(factory=factory.__name__):
                layer=factory(*args,fc='white',ec='red',lw=.2)
                self.assertEqual(layer.style['facecolor'],'white');self.assertEqual(layer.style['edgecolor'],'red')
                self.assertEqual(layer.style['linewidth'],.2)

    def test_failed_factories_do_not_fit_add_or_consume_cycle(self):
        fig,ax=azl.subplots();ax.set_extent((-54,-42,-28,-16));fig.canvas.draw()
        for create in (lambda:ax.map('brazil',linewidth=1,lw=1),
                       lambda:ax.state('SP',facecolor='white',fc='white'),
                       lambda:ax.plot([-52,-48],[-25,-21],color='red',c='red')):
            before=(len(ax.layers),ax.get_extent(),ax._plot_index)
            with self.assertRaises(TypeError):create()
            self.assertEqual(before,(len(ax.layers),ax.get_extent(),ax._plot_index));self.assertFalse(fig.stale)

    def test_ambiguous_artist_edit_keeps_data_visibility_callbacks_and_dirty_state(self):
        fig,ax=azl.subplots();line,=ax.plot([-52,-48],[-25,-21])
        fig.canvas.draw();before=(line.data,dict(line.style));events=[];line.add_callback(events.append)
        with self.assertRaises(TypeError):line.set(data=([-51,-47],[-24,-20]),visible=False,linewidth=2,lw=2)
        self.assertEqual(before,(line.data,dict(line.style)));self.assertTrue(line.get_visible())
        self.assertFalse(fig.stale);self.assertEqual(events,[])

    def test_grid_alias_edits_override_previous_styles_and_failed_pair_preserves_grid(self):
        fig,ax=azl.subplots();ax.set_extent((-10,10,-10,10));ax.grid(lw=.8,color='black')
        ax.grid(lw=.3,c='red');grid=next(l for l in ax.layers if l.kind=='grid')
        self.assertEqual(grid.style['linewidth'],.3);self.assertEqual(grid.style['color'],'red')
        fig.canvas.draw();before=fig.to_svg()
        with self.assertRaises(TypeError):ax.grid(which='both',linewidth=1,lw=1)
        self.assertEqual(before,fig.to_svg());self.assertFalse(fig.stale)

    def test_text_aliases_override_defaults_and_conflicts_preserve_each_text(self):
        fig,ax=azl.subplots()
        factories=(ax.set_title,ax.set_xlabel,ax.set_ylabel,fig.suptitle,fig.supxlabel,fig.supylabel)
        for factory in factories:
            with self.subTest(factory=factory.__name__):
                text=factory('Before',size=13,family='DejaVu Sans',c='red',horizontalalignment='right')
                self.assertEqual(text.get_fontsize(),13);self.assertEqual(text.get_color(),'red')
                self.assertEqual(text.get_ha(),'right');fig.canvas.draw()
                with self.assertRaises(TypeError):factory('After',fontsize=12,size=12)
                self.assertEqual(text.get_text(),'Before');self.assertFalse(fig.stale)

    def test_explicit_initial_visibility_is_valid_for_owned_cartographic_component(self):
        for value in (True,False):
            with self.subTest(value=value):
                component=MapComponent(visible=value,in_layout=False)
                self.assertEqual(component.get_visible(),value);self.assertFalse(component.get_in_layout())

    def test_fontdict_and_keyword_styles_are_separate_override_layers(self):
        fig,ax=azl.subplots()
        title=ax.set_title('Title',fontdict={'size':8,'c':'black'},fontsize=12,color='red')
        self.assertEqual(title.get_fontsize(),12);self.assertEqual(title.get_color(),'red')

if __name__=='__main__':unittest.main()

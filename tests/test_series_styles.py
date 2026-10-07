"""Multi-series preparation, conditional cycles, style contexts and ownership."""
import importlib.util,json,tempfile,unittest,warnings
from pathlib import Path
import azimlib as azl
import azimlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
X=[-52,-49,-45];A=[-25,-23,-20];B=[-24,-22,-19]


class SeriesStylesTests(unittest.TestCase):
    def setUp(self):azl.ioff();azl.rcdefaults();self.fig,self.ax=azl.subplots()
    def tearDown(self):azl.close('all');azl.rcdefaults();azl.ioff()

    def test_recorded_actual_matplotlib_contracts(self):
        spec=importlib.util.spec_from_file_location('series_reference',ROOT/'tools/inspect_series_styles.py')
        tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)
        report=json.loads((ROOT/'docs/series-styles-reference.json').read_text())
        # The historical oracle retains cycle roles, not the retired RGB table.
        # Materialize those roles with AZIM10; all other measured states remain.
        groups=('multi','columns','broadcast_x','matrix_pair','data','implicit')
        from azimlib.cycles import AZIM10
        expected=report['matplotlib'];index=0
        for name in groups:
            for row in expected[name]:
                self.assertEqual(row['color'],f'cycle:{index}')
                row['color']=AZIM10[index];index+=1
        self.assertEqual(index,10)
        self.assertEqual(tool.contracts(azl,azl.cycler),expected)
        self.assertEqual(tool.style_contracts(azl,azl.cycler),report['styles_matplotlib'])
        self.assertEqual(tool.failed_group(azl),report['failed_group_azimlib'])

    def test_multiple_groups_edit_independently_and_legend_tracks_handles(self):
        lines=self.ax.plot(X,A,'--',X,B,':',label='routes')
        self.assertEqual(len(lines),2);self.assertEqual(lines[0].get_data(),(X,A))
        legend=self.ax.legend(lines,['A','B'])
        before=self.ax.get_extent();source=lines[1].data
        lines[0].set(data=([-51,-47],[-24,-20]),visible=False)
        self.assertEqual(lines[1].get_data(),(X,B));self.assertIs(lines[1].data,source)
        self.assertEqual(self.ax.get_extent(),before);self.assertFalse(lines[0].get_visible())
        self.assertEqual([text.get_text() for text in legend.get_texts()],['A','B'])
        lines[0].remove();self.assertIsNone(lines[0].get_figure());self.assertIn(lines[1],self.ax.layers)

    def test_matrix_broadcast_and_generator_inputs(self):
        for x,y,expected in [(X,list(zip(A,B)),[(X,A),(X,B)]),
                              (list(zip(X,[-51,-48,-44])),A,[(X,A),([-51,-48,-44],A)]),
                              (list(zip(X,X)),list(zip(A,B)),[(X,A),(X,B)])]:
            with self.subTest(x=x,y=y):
                lines=self.ax.plot(iter(x),iter(y),label=['first','second'])
                self.assertEqual([l.get_data() for l in lines],expected)
                self.assertEqual([l.get_label() for l in lines],['first','second'])

    def test_numpy_matrices_are_optional_and_not_required(self):
        try:import numpy as np
        except ImportError:self.skipTest('optional NumPy unavailable')
        for shape in ((3,2),(3,1)):
            with self.subTest(shape=shape):
                y=np.array(list(zip(A,B))) if shape[1]==2 else np.array(A).reshape(shape)
                lines=self.ax.plot(np.array(X),y)
                self.assertEqual(len(lines),shape[1]);self.assertEqual(lines[0].get_data(),(X,A))

    def test_geo_coordinate_shorthand_implicit_indices_scalar_and_empty(self):
        for args,expected in [((list(zip(X,A)),),(X,A)),(([2,4,6],),([0,1,2],[2,4,6])),
                              ((-52,-25),([-52],[-25])),(([],[]),([],[])),(([],),([],[]))]:
            with self.subTest(args=args):
                line,=self.ax.plot(*args);self.assertEqual(line.get_data(),expected)
        self.assertEqual(self.ax.plot(),[])
        self.assertEqual(self.ax.plot([[],[]],[[],[]]),[])

    def test_named_data_default_labels_and_keyword_compatibility(self):
        data={'lon':X,'lat':A,'o':B}
        first,=self.ax.plot('lon','lat','--',data=data)
        self.assertEqual(first.get_data(),(X,A));self.assertEqual(first.get_label(),'lat')
        second,=self.ax.plot('lon','o',data=data,label='explicit')
        self.assertEqual(second.get_data(),(X,B));self.assertEqual(second.get_label(),'explicit')
        third,=self.ax.plot(lon=X,lat=A,fmt='r--')
        self.assertEqual(third.get_color(),'#ff0000')
        line,=self.ax.plot('lat',data=data);self.assertEqual(line.get_data(),([0,1,2],A))

    def test_invalid_later_groups_are_atomic_and_do_not_consume_cycle(self):
        self.ax.set_prop_cycle(color=['red','blue']);self.fig.canvas.draw()
        before=(tuple(self.ax.layers),self.ax.get_extent(),self.ax._bounds,self.ax._plot_index)
        bad=[(X,A,X,[1,2]),(X,A,X,[1,91,3]),(X,A,X,[1,float('inf'),3]),
             (X,A,X,[[1,2],[3],[4,5]]),(X,A,[[1,2],[3,4],[5,6]],[[1,2,3]]*3),
             (X,A,X,[[[1]]]*3),(X,A,'r--','invalid'),(X,A,42)]
        events=[];self.ax.add_callback(lambda artist:events.append(artist))
        for args in bad:
            with self.subTest(args=args):
                with self.assertRaises((ValueError,TypeError)):self.ax.plot(*args)
                self.assertEqual((tuple(self.ax.layers),self.ax.get_extent(),self.ax._bounds,self.ax._plot_index),before)
                self.assertFalse(self.fig.stale);self.assertEqual(events,[])
        line,=self.ax.plot(X,A);self.assertEqual(line.get_color(),'red')

    def test_invalid_labels_styles_and_named_data_are_atomic(self):
        for args,kwargs in [((X,list(zip(A,B))),{'label':['one']}),((X,A),{'unknown':2}),
                            ((X,A),{'linewidth':-1}),((X,A),{'marker':'bad'}),
                            (('lon','bad'),{'data':{'lon':X}}),((X,A,X,B),{'data':{}}),
                            ((),{'unknown':1})]:
            with self.subTest(args=args,kwargs=kwargs):
                self.fig.canvas.draw();before=(len(self.ax.layers),self.ax.get_extent(),self.ax._plot_index)
                with self.assertRaises((ValueError,TypeError)):self.ax.plot(*args,**kwargs)
                self.assertEqual((len(self.ax.layers),self.ax.get_extent(),self.ax._plot_index),before)
                self.assertFalse(self.fig.stale)

    def test_explicit_color_partial_cycle_and_scatter_are_independent(self):
        self.ax.set_prop_cycle(color=['red','blue'],marker=['o','s'])
        explicit,=self.ax.plot(X,A,color='black',marker='^')
        self.assertEqual(self.ax._plot_index,0)
        first,=self.ax.plot(X,A,color='black');self.assertEqual(first.get_marker(),'o')
        self.ax.scatter(X,A,c=[0,1,2]);self.assertEqual(self.ax._scatter_index,0)
        points=self.ax.scatter(X,A);self.assertEqual(points.get_color(),'red')
        second,=self.ax.plot(X,B);self.assertEqual((second.get_color(),second.get_marker()),('blue','s'))
        self.assertEqual(self.ax._scatter_index,1)
        self.ax.scatter(X,A,color='black');self.assertEqual(self.ax._scatter_index,1)
        self.assertEqual(explicit.get_color(),'black')

    def test_cycles_are_snapshots_clear_and_reset_follow_rc(self):
        with azl.rc_context({'axes.prop_cycle':azl.cycler(color=['red','blue'])}):
            fig,ax=azl.subplots();line,=ax.plot(X,A)
        self.assertEqual(ax.plot(X,A)[0].get_color(),'blue')
        ax.set_prop_cycle(None);self.assertEqual(ax.plot(X,A)[0].get_color(),'#237f96')
        ax.set_prop_cycle(color=['black']);ax.clear()
        self.assertEqual(ax.plot(X,A)[0].get_color(),'#237f96');self.assertIsNone(line.get_figure())

    def test_invalid_cycle_changes_are_atomic(self):
        cases=[{},dict(color=[]),dict(color=['red','blue'],marker=['o']),dict(unknown=[1]),
               dict(linewidth=[-1]),dict(color=[None]),dict(c=['red'],color=['blue'])]
        before=self.ax._prop_cycle
        for values in cases:
            with self.subTest(values=values):
                self.fig.canvas.draw()
                with self.assertRaises((ValueError,TypeError)):self.ax.set_prop_cycle(**values)
                self.assertEqual(self.ax._prop_cycle,before);self.assertFalse(self.fig.stale)

    def test_cycler_zip_product_aliases_copies_and_validation(self):
        colors=azl.cycler(color=['red','blue']);marks=azl.cycler('marker',['o','s'])
        self.assertEqual(len(colors+marks),2);self.assertEqual(len(colors*marks),4)
        rows=list(colors);rows[0]['color']='black';self.assertEqual(list(colors)[0]['color'],'red')
        values=colors.by_key();values['color'][0]='black';self.assertEqual(list(colors)[0]['color'],'red')
        self.assertEqual(azl.cycler(c=['r','b']).by_key(),{'color':['#ff0000','#0000ff']})
        self.assertEqual(azl.cycler(color=[(1,0,0)]).by_key(),{'color':['#ff0000']})
        for callback in (lambda:colors+colors,lambda:colors*colors,
                         lambda:colors+azl.cycler(marker=['o']),lambda:azl.cycler(color=[(2,0,0)])):
            with self.subTest(callback=callback):
                with self.assertRaises(ValueError):callback()

    def test_aliases_take_precedence_over_formats_with_warning(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always');line,=self.ax.plot(X,A,'r--',c='blue',ls=':')
        self.assertEqual(line.get_color(),'blue');self.assertEqual(line.get_linestyle(),':')
        self.assertEqual(len(caught),2)

    def test_rc_cycle_update_is_atomic_and_existing_axes_keep_snapshot(self):
        previous=dict(azl.rcParams)
        with self.assertRaises((ValueError,TypeError)):azl.rcParams.update({'figure.dpi':200,'axes.prop_cycle':[]})
        self.assertEqual(dict(azl.rcParams),previous)
        azl.rcParams['axes.prop_cycle']=azl.cycler(color=['red'])
        self.assertEqual(self.ax.plot(X,A)[0].get_color(),'#237f96')
        _,ax=azl.subplots();self.assertEqual(ax.plot(X,A)[0].get_color(),'red')

    def test_pyplot_series_cycle_and_shared_limits(self):
        fig,axes=azl.subplots(1,2,sharex=True)
        azl.sca(axes[0]);lines=plt.plot(X,list(zip(A,B)),label=['A','B'])
        self.assertEqual(len(lines),2);self.assertEqual(axes[0].get_xlim(),axes[1].get_xlim())
        self.assertEqual(len(plt.legend().get_texts()),2)
        axes[0].set_xlim(-54,-42);lines[0].set_data([-50,-46],[-24,-20])
        self.assertEqual(axes[0].get_xlim(),(-54,-42));self.assertEqual(axes[1].get_xlim(),(-54,-42))

    def test_style_stacks_context_restore_and_after_reset(self):
        previous=dict(azl.rcParams)
        with self.assertRaisesRegex(RuntimeError,'body'):
            with azl.style.context(['dark_background',{'lines.linewidth':.9}]):
                self.assertEqual(azl.rcParams['figure.facecolor'],'black')
                self.assertEqual(azl.rcParams['lines.linewidth'],.9)
                with azl.style.context({'figure.dpi':150},after_reset=True):
                    self.assertEqual(azl.rcParams['figure.facecolor'],'white')
                raise RuntimeError('body')
        self.assertEqual(dict(azl.rcParams),previous)
        with self.assertRaises((KeyError,ValueError)):azl.style.use([{'figure.dpi':200},{'lines.linewidth':-1}])
        self.assertEqual(dict(azl.rcParams),previous)

    def test_local_stylesheet_quotes_comments_cycles_and_order(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'route.mplstyle'
            path.write_text('figure.figsize: 8, 6\nlines.linewidth: 0.8 # thin\naxes.grid: False\n'
                            'axes.facecolor: "#eeeeee"\naxes.prop_cycle: cycler("color", ["red", "blue"]) + cycler(marker=["o", "s"])\n',encoding='utf-8')
            values=azl.style.read(path);self.assertEqual(values['figure.figsize'],(8.,6.))
            with azl.style.context([path,{'lines.linewidth':1.2}]):
                fig,ax=azl.subplots();lines=ax.plot(X,A,X,B)
                self.assertEqual(fig.figsize,(8.,6.));self.assertEqual(ax.facecolor,'#eeeeee')
                self.assertEqual([(line.get_color(),line.get_marker(),line.get_linewidth()) for line in lines],
                                 [('red','o',1.2),('blue','s',1.2)])

    def test_malformed_styles_are_atomic_and_never_execute_expressions(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'bad.mplstyle';previous=dict(azl.rcParams)
            contents=['lines.linewidth: -1','unsupported: 1','broken line','axes.facecolor: #abcdef',
                      'figure.dpi: 100\nfigure.dpi: 200',
                      'axes.prop_cycle: __import__("os").system("echo unsafe")',
                      'axes.prop_cycle: cycler(color=["red"]).by_key()',
                      'axes.prop_cycle: cycler(**{"color":["red"]})']
            for value in contents:
                with self.subTest(value=value):
                    path.write_text('figure.dpi: 150\n'+value,encoding='utf-8')
                    with self.assertRaises(ValueError):azl.style.use([{'lines.linewidth':.8},path])
                    self.assertEqual(dict(azl.rcParams),previous)

    def test_dark_legend_inherits_axes_background_and_ornaments_stay_optional(self):
        with azl.style.context('dark_background'):
            fig,ax=azl.subplots();ax.plot(X,A,label='Route');legend=ax.legend()
            self.assertEqual(legend.get_frame().get_facecolor(),'black')
            self.assertEqual(legend.get_texts()[0].get_color(),'white')
            self.assertEqual(ax.spines['left'].get_edgecolor(),'white')
            self.assertTrue(all(getattr(ax,name) is None for name in ('_scale_bar','_overview','_north','_compass')))
            self.assertIsNone(ax._grid_config);self.assertIn('<svg',fig.to_svg())

    def test_legend_rc_defaults_overrides_and_alpha_validation(self):
        with azl.rc_context({'legend.facecolor':'#eeeeee','legend.edgecolor':'black','legend.framealpha':.6}):
            self.ax.plot(X,A,label='Route');legend=self.ax.legend()
            self.assertEqual((legend.get_frame().get_facecolor(),legend.get_frame().get_edgecolor(),legend.get_frame().get_alpha()),('#eeeeee','black',.6))
            self.assertEqual(self.ax.legend(facecolor='white',framealpha=.9).get_frame().get_alpha(),.9)
        previous=dict(azl.rcParams)
        with self.assertRaises(ValueError):azl.rcParams['legend.framealpha']=1.1
        self.assertEqual(dict(azl.rcParams),previous)

    def test_lazy_legend_texts_preserve_creation_context_after_restore(self):
        with azl.style.context(['dark_background',{'font.family':'DejaVu Sans'}]):
            fig,ax=azl.subplots();line,=ax.plot(X,A,label='Initial')
            legend=ax.legend()
        azl.rcParams['font.family']='DejaVu Serif'
        text=legend.get_texts()[0]
        self.assertEqual(text.get_color(),'white');self.assertEqual(text.style['fontfamily'],'DejaVu Sans')
        line.set_label('Renamed');replacement=legend.get_texts()[0]
        self.assertIsNot(text,replacement);self.assertIsNone(text.get_figure())
        self.assertEqual(replacement.get_color(),'white');self.assertEqual(replacement.style['fontfamily'],'DejaVu Sans')
        self.assertIn('Renamed',fig.to_svg())

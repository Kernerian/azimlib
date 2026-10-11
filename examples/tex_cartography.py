"""Real TeX is explicitly configured; this example never installs tools."""
import azimlib as azl


def make(config):
    with azl.tex_context(config):
        fig, ax = azl.subplots(figsize=(7, 5))
        ax.map('brazil', facecolor='#f0f3f5', edgecolor='#73838e', linewidth=.6)
        ax.set_title(r'Cartography: $\displaystyle A=\int_{\Omega}\rho(x,y)\,dA$', fontsize=15, pad=12)
        ax.set_xlabel(r'Longitude $\lambda$')
        ax.set_ylabel(r'Latitude $\varphi$')
        ax.plot([-60,-52,-44],[-10,-20,-15],color='#147d92',label=r'Route $r(t)$')
        ax.text(-58,-7,r'$\displaystyle\frac{\partial f}{\partial x}=2x$',fontsize=14,
                rotation=15,halo='white',halo_width=2)
        ax.text(-57,-28,r'$\displaystyle\sqrt{a^2+b^2}$',fontsize=14)
        ax.legend()
        fig.tight_layout()
        return fig


if __name__ == '__main__':
    raise SystemExit('Import make(config) with an explicit prepared TexConfig; see docs/tex-0.4.md')

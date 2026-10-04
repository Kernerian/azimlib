"""Stateful plotting entry point, modeled on matplotlib.pyplot vocabulary.

There is intentionally no Matplotlib import or backend. The common call shape
is shared; cartographic coordinates remain explicit longitude/latitude degrees.
"""
from .artist import setp,getp,ion,ioff,isinteractive
from . import (figure,subplots,subplot_mosaic,subplot,gcf,gca,sca,savefig,show,close,
               get_fignums,get_figlabels,fignum_exists,clf,cla)
from .config import rcParams,rc,rc_context,rcdefaults
from . import style
from .cycles import cycler

def xticks(ticks=None,labels=None,**kwargs):
    ax=gca()
    if ticks is None:return ax.get_xticks(),ax._tick_labels['x'] or []
    artists=ax.set_xticks(ticks,labels,**kwargs)
    return ax.get_xticks(),artists

def yticks(ticks=None,labels=None,**kwargs):
    ax=gca()
    if ticks is None:return ax.get_yticks(),ax._tick_labels['y'] or []
    artists=ax.set_yticks(ticks,labels,**kwargs)
    return ax.get_yticks(),artists

def tick_params(**kwargs):return gca().tick_params(**kwargs)
def ticklabel_format(**kwargs):return gca().ticklabel_format(**kwargs)
def minorticks_on():return gca().minorticks_on()
def minorticks_off():return gca().minorticks_off()
def draw():return gcf().canvas.draw_idle()


def plot(*args,**kwargs):
    return gca().plot(*args,**kwargs)


def scatter(*args,**kwargs):
    return gca().scatter(*args,**kwargs)


def imshow(*args,**kwargs):return gca().imshow(*args,**kwargs)
def pcolormesh(*args,**kwargs):return gca().pcolormesh(*args,**kwargs)
def contour(*args,**kwargs):return gca().contour(*args,**kwargs)
def clabel(*args,**kwargs):return gca().clabel(*args,**kwargs)
def quiver(*args,**kwargs):return gca().quiver(*args,**kwargs)


def title(label,**kwargs):
    return gca().set_title(label,**kwargs)

def suptitle(text,**kwargs):return gcf().suptitle(text,**kwargs)
def figtext(x,y,text,**kwargs):return gcf().text(x,y,text,**kwargs)


def xlabel(label,**kwargs):
    return gca().set_xlabel(label,**kwargs)


def ylabel(label,**kwargs):
    return gca().set_ylabel(label,**kwargs)


def xlim(*args,**kwargs):
    return gca().set_xlim(*args,**kwargs) if args or kwargs else gca().get_xlim()


def ylim(*args,**kwargs):
    return gca().set_ylim(*args,**kwargs) if args or kwargs else gca().get_ylim()


def grid(*args,**kwargs):
    return gca().grid(*args,**kwargs)


def legend(*args,**kwargs):
    return gca().legend(*args,**kwargs)


def text(*args,**kwargs):
    return gca().text(*args,**kwargs)


def annotate(*args,**kwargs):
    return gca().annotate(*args,**kwargs)


def colorbar(mappable,*,ax=None,cax=None,**kwargs):
    return gcf().colorbar(mappable,ax=ax,cax=cax,**kwargs)


def tight_layout(*,pad=1.08,w_pad=None,h_pad=None,rect=(0,0,1,1)):
    return gcf().tight_layout(pad=pad,w_pad=w_pad,h_pad=h_pad,rect=rect)


def subplots_adjust(**kwargs):
    return gcf().subplots_adjust(**kwargs)

def margins(*args,**kwargs):return gca().margins(*args,**kwargs)
def autoscale(enable=True,axis='both',tight=None):return gca().autoscale(enable,axis,tight)

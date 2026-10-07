"""Transfer existing subscriptions without importing any GUI toolkit."""
def attach(figure,canvas):
    previous=figure.canvas
    callbacks=getattr(previous,'_callbacks',getattr(previous,'_event_callbacks',{}))
    canvas._callbacks=dict(callbacks);canvas._next_id=getattr(previous,'_next_id',getattr(previous,'_callback_id',0))
    figure.canvas=canvas;figure._viewer=canvas;figure._closed=False
    return previous

def detach(canvas):
    from ..figure import FigureCanvas
    figure=canvas.figure
    try:canvas._dispatch('close_event',type('CloseEvent',(),dict(name='close_event',canvas=canvas))())
    finally:
        canvas.closed=True
        if figure.canvas is canvas:
            fresh=FigureCanvas(figure);fresh._callbacks=dict(canvas._callbacks);fresh._next_id=canvas._next_id
            figure.canvas=fresh;figure._viewer=None
        canvas._callbacks.clear();figure._closed=True
        from .. import _figures
        if figure in _figures:_figures.remove(figure)

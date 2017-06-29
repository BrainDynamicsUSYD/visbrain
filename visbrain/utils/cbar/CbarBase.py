
from ..color import color2tuple

__all__ = ['CbarBase']


class CbarBase(object):
    """Base class for colorbar."""

    def __init__(self, config=None, cmap='viridis', clim=(0, 1), vmin=None,
                 vmax=None, under='gray', over='red', cblabel='', cbtxtsz=26,
                 cbtxtsh=2.3, txtcolor='white', txtsz=20, txtsh=1.2, width=.14,
                 border=True, bw=2., limtxt=True, bgcolor=(.1, .1, .1),
                 ndigits=2, name='Colorbar'):
        """Init."""
        # Cmap/Clim/Vmin/Vmax/Under/Over :
        self._cmap, self._clim = cmap, clim
        self._vmin, self._vmax = vmin, vmax
        self._under, self._over = under, over
        # Cb text :
        self._cblabel = cblabel
        self._cbtxtsz = cbtxtsz
        self._cbtxtsh = cbtxtsh
        # Text :
        self._txtcolor = txtcolor
        self._txtsz = txtsz
        self._txtsh = txtsh
        self._limtxt = limtxt
        # Settings :
        self._config = config
        self._name = name
        self._bgcolor = bgcolor
        self._border = border
        self._bw = bw
        self._ndigits = ndigits
        self._width = width
        self._minmax = clim

    # -------------------------------------------------------------------------
    #                             USER METHODS
    # -------------------------------------------------------------------------
    def set_data(self, data, cmap=None, clim=None, vmin=None, vmax=None,
                 under=None, over=None):
        # Cmap/Clim/Vmin/Vmax/Under/Over :
        self._cmap, self._clim = cmap, clim
        self._vmin, self._vmax = vmin, vmax
        self._under, self._over = under, over
        self._minmax = (data.min(), data.max())

    def autoscale(self):
        self._clim = self._minmax

    def to_kwargs(self):
        """Return a dictionary for input arguments."""
        kwargs = {}
        kwargs['cmap'] = self._cmap
        kwargs['clim'] = self._clim
        kwargs['vmin'] = self._vmin
        kwargs['under'] = self._under
        kwargs['vmax'] = self._vmax
        kwargs['over'] = self._over
        return kwargs

    def to_dict(self):
        """Return a dictionary of colorbar args."""
        todict = {}
        # cmap/clim/vmin/vmax/under/over :
        todict['cmap'] = self._cmap
        todict['clim'] = self._clim
        todict['vmin'] = self._vmin
        todict['under'] = list(color2tuple(self._under, float))
        todict['vmax'] = self._vmax
        todict['over'] = list(color2tuple(self._over, float))
        # Cblabel :
        todict['cblabel'] = self._cblabel
        todict['cbtxtsz'] = self._cbtxtsz
        todict['cbtxtsh'] = self._cbtxtsh
        # Text :
        todict['txtcolor'] = list(color2tuple(self._txtcolor, float))
        todict['txtsz'] = self._txtsz
        todict['txtsh'] = self._txtsh
        # Settings :
        todict['border'] = self._border
        todict['bw'] = self._bw
        todict['name'] = self._name
        todict['limtxt'] = self._limtxt
        todict['bgcolor'] = list(color2tuple(self._bgcolor, float))
        todict['ndigits'] = self._ndigits
        todict['width'] = self._width

        return todict
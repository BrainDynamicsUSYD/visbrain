"""Base class for objects of type ROI."""
import numpy as np

from vispy import scene
from vispy.geometry.isosurface import isosurface

from .visbrain_obj import VisbrainObject, CombineObjects
from ..io import is_pandas_installed
from ..utils import load_predefined_roi, mni2tal, smooth_3d
from ..visuals import BrainMesh


class RoiObj(VisbrainObject):
    """Create a Region Of Interest (ROI) object.

    Parameters
    ----------
    name : string
        Name of the ROI object. If name is 'brodmann', 'aal' or 'talairach' a
        predefined ROI object is used and vol, index and label are ignored.
    vol : array_like | None
        ROI volume. Sould be an array with three dimensions.
    label : array_like | None
        Array of labels. A structured array can be used (i.e
        label=np.zeros(n_sources, dtype=[('brodmann', int), ('aal', object)])).
    index : array_like | None
        Array of index that make the correspondance between the volumne values
        and labels. The length of index must be the same as label.
    hdr : array_like | None
        Array of transform source's coordinates into the volume space. Must be
        a (4, 4) array.
    system : {'mni', 'tal'}
        The system of the volumne. Can either be MNI ('mni') or Talairach
        ('tal').
    transform : VisPy.visuals.transforms | None
        VisPy transformation to set to the parent node.
    parent : VisPy.parent | None
        ROI object parent.
    verbose : string
        Verbosity level.

    Examples
    --------
    >>> import numpy as np
    >>> from visbrain.objects import RoiObj
    >>> r = RoiObj('brodmann')
    >>> r.get_roi_vertices(level=[4, 6, 38], unique_color=True, plot=True,
    >>>                    smooth=7)
    >>> r.preview(axis=True)
    """

    ###########################################################################
    ###########################################################################
    #                                BUILT IN
    ###########################################################################
    ###########################################################################

    def __init__(self, name, vol=None, label=None, index=None, hdr=None,
                 system='mni', transform=None, parent=None, verbose=None):
        """Init."""
        # Init Visbrain object base class :
        VisbrainObject.__init__(self, name, parent, transform, verbose)
        self.change_roi_object(name, vol, label, index, hdr, system)

    def __len__(self):
        """Return the number of ROI."""
        return self._n_roi

    def __getitem__(self, index):
        """Get the ref item at index."""
        if isinstance(index, (int, list, np.ndarray, slice)):
            return self.ref.iloc[index]

    def __ge__(self, idx):
        """Test if x >= idx."""
        assert len(idx) == 3
        sh = self.vol.shape
        return (sh[0] >= idx[0]) and (sh[1] >= idx[1]) and (sh[2] >= idx[2])

    def __gt__(self, idx):
        """Test if x > idx."""
        assert len(idx) == 3
        sh = self.vol.shape
        return (sh[0] > idx[0]) and (sh[1] > idx[1]) and (sh[2] > idx[2])

    def __le__(self, idx):
        """Test if x <= idx."""
        assert len(idx) == 3
        sh = self.vol.shape
        return (sh[0] <= idx[0]) and (sh[1] <= idx[1]) and (sh[2] <= idx[2])

    def __lt__(self, idx):
        """Test if x < idx."""
        assert len(idx) == 3
        sh = self.vol.shape
        return (sh[0] < idx[0]) and (sh[1] < idx[1]) and (sh[2] < idx[2])

    def change_roi_object(self, name, vol=None, label=None, index=None,
                          hdr=None, system='mni'):
        """Load an roi object.

        Parameters
        ----------
        name : string
            Name of the ROI object. If name is 'brodmann', 'aal' or
            'talairach' a predefined ROI object is used and vol, index and
            label are ignored.
        vol : array_like | None
            ROI volume. Sould be an array with three dimensions.
        label : array_like | None
            Array of labels. A structured array can be used (i.e
            label=np.zeros(n_sources, dtype=[('brodmann', int),
            ('aal', object)])).
        index : array_like | None
            Array of index that make the correspondance between the volumne
            values and labels. The length of index must be the same as label.
        hdr : array_like | None
            Array of transform source's coordinates into the volume space.
            Must be a (4, 4) array.
        system : {'mni', 'tal'}
            The system of the volumne. Can either be MNI ('mni') or Talairach
            ('tal').
        """
        # Test if pandas is installed :
        if not is_pandas_installed():
            raise ImportError("In order to work properly, pandas package "
                              "should be installed using *pip install pandas*")
        import pandas as pd
        # _______________________ PREDEFINED _______________________
        if name in ['brodmann', 'talairach', 'aal']:
            vol, label, index, hdr, system = load_predefined_roi(name)
        self._offset = -1 if name == 'talairach' else 0

        # _______________________ CHECKING _______________________
        # vol :
        assert vol.ndim == 3
        # Index and label :
        assert len(index) == len(label)
        index = np.asarray(index).astype(int)
        label = np.asarray(label)
        self.vol = vol
        self._n_roi = len(index)
        # hdr :
        self.hdr = np.eye(4) if hdr is None else hdr
        assert self.hdr.shape == (4, 4)
        # System :
        assert system in ['mni', 'tal']
        self.system = system

        # _______________________ REFERENCE _______________________
        label_dict = self._struct_array_to_dict(label)
        label_dict['index'] = index
        cols = list(label_dict.keys())
        self.ref = pd.DataFrame(label_dict, columns=cols)
        self.analysis = pd.DataFrame({}, columns=cols)

    ###########################################################################
    ###########################################################################
    #                                ANALYSE
    ###########################################################################
    ###########################################################################

    def localize_sources(self, xyz, source_name=None, replace_bad=True,
                         bad_patterns=[-1, 'undefined', 'None'],
                         replace_with='Not found'):
        """Localize source's using this ROI object.

        Parameters
        ----------
        xyz : array_like
            Array of source's coordinates of shape (n_sources, 3)
        source_name : array_like/list | None
            List of source's names.
        replace_bad : bool | True
            Replace bad values (True) or not (False).
        bad_patterns : list | [None, -1, 'undefined', 'None']
            Bad patterns to replace if replace_bad is True.
        replace_with : string | 'Not found'
            Replace bad patterns with this string.
        """
        # Check xyz :
        assert (xyz.ndim == 2) and (xyz.shape[1] == 3)
        n_sources = xyz.shape[0]
        if self.system == 'tal':
            xyz = mni2tal(xyz)
        # Check source_name :
        if source_name is None:
            source_name = ['s' + str(k) for k in range(n_sources)]
        assert len(source_name) == n_sources
        # Loop over sources :
        xyz = np.c_[xyz, np.ones((n_sources,), dtype=xyz.dtype)].T
        for k in range(n_sources):
            # Apply HDR transformation :
            pos = np.linalg.lstsq(self.hdr, xyz[:, k])[0][0:-1]
            sub = np.round(pos).astype(int)
            # Find where is the point if inside the volume :
            if self >= sub:  # use __ge__ of RoiObj
                idx_vol = self.vol[sub[0], sub[1], sub[2]] + self._offset
                location = self._find_roi_label(idx_vol)
            else:
                location = None
            self.analysis.loc[k] = location
        # Add Text and (X, Y, Z) to the table :
        new_col = ['Text'] + self.analysis.columns.tolist() + ['X', 'Y', 'Z']
        self.analysis['Text'] = source_name
        self.analysis['X'] = xyz[0]
        self.analysis['Y'] = xyz[1]
        self.analysis['Z'] = xyz[2]
        self.analysis = self.analysis[new_col]
        if replace_bad:
            # Replace NaN values :
            self.analysis.fillna(replace_with, inplace=True)
            # Replace bad patterns :
            for k in bad_patterns:
                self.analysis.replace(k, replace_with, inplace=True)
        return self.analysis

    def _find_roi_label(self, vol_idx):
        """Find the ROI label associated to a volume index."""
        ref_index = np.where(self.ref['index'] == vol_idx)[0]
        return self[int(ref_index[0])] if ref_index.size else None

    @staticmethod
    def _struct_array_to_dict(arr):
        """Convert a structured array into a dictionnary."""
        try:
            if arr.dtype.names is None:
                return {'label': arr}
            else:
                return {k: arr[k] for k in arr.dtype.names}
        except:
            return {'label': arr}

    def get_roi_vertices(self, level=.5, unique_color=False, smooth=3,
                         plot=False):
        """Get the vertices of ROI's.

        Parameters
        ----------
        level : int, float, list | .5
            Threshold for extracting vertices from isosuface method.
        unique_color : bool | False
            Use a random unique color for each ROI.
        smooth : int | 3
            Smoothing level. Must be an odd integer (smooth % 2 = 1).
        plot : bool | False
            Specify if a mesh object have to be defined.
        """
        # Get vertices / faces :
        if not unique_color:
            vert, faces = self._get_roi_vertices(self.vol, level, smooth)
        else:
            assert not isinstance(level, float)
            level = [level] if isinstance(level, int) else level
            vert, faces, color = np.array([]), np.array([]), np.array([])
            # Generate a (n_levels, 3, 4) array of unique colors :
            col_unique = np.random.uniform(.1, .9, (len(level), 4))
            col_unique[..., -1] = 1.
            for i, k in enumerate(level):
                v, f = self._get_roi_vertices(self.vol, k, smooth)
                # Concatenate vertices / faces :
                faces = np.r_[faces, f + faces.max() + 1] if faces.size else f
                vert = np.r_[vert, v] if vert.size else v
                # Concatenate color :
                col = np.tile(col_unique[[i], ...], (v.shape[0], 1))
                color = np.r_[color, col] if color.size else col
        if plot and vert.size:
            if not hasattr(self, 'mesh'):
                self.mesh = BrainMesh(vertices=vert, faces=faces,
                                      parent=self._node)
                self.mesh.set_camera(scene.cameras.TurntableCamera())
                if unique_color:
                    self.mesh.mask = 1.
                    self.mesh.color = color

    @staticmethod
    def _get_roi_vertices(vol, level, smooth):
        vol = vol.copy()
        if isinstance(level, int):
            vol[vol != level] = 0
        elif isinstance(level, float):
            vol[vol > level] = 0
        elif isinstance(level, (np.ndarray, list, tuple)):
            vol[np.logical_and.reduce([vol != k for k in level])] = 0
        return isosurface(smooth_3d(vol, smooth), level=.5)

    def _get_camera(self):
        """Get the most adapted camera."""
        self.mesh._camera.scale_factor = self.mesh._camratio[0]
        return self.mesh._camera

    # ----------- TRANSLUCENT -----------
    @property
    def translucent(self):
        """Get the translucent value."""
        return self.mesh.translucent if hasattr(self, 'mesh') else False

    @translucent.setter
    def translucent(self, value):
        """Set translucent value."""
        if hasattr(self, 'mesh'):
            self.mesh.translucent = value


class CombineRoi(CombineObjects):
    """Combine Roi objects.

    Parameters
    ----------
    robjs : RoiObj/list | None
        List of Roi objects.
    select : string | None
        The name of the Roi object to select.
    parent : VisPy.parent | None
        Roi object parent.
    """

    def __init__(self, robjs=None, select=None, parent=None):
        """Init."""
        CombineObjects.__init__(self, RoiObj, robjs, select, parent)

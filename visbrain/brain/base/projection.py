"""Source projection."""
import logging
import numpy as np

from ...utils import array2colormap, color2vb


logger = logging.getLogger('visbrain')


__all__ = ['Projections']


class Projections(object):
    """Set of methods for sources projection.

    This class must be instantiate at the top level of Brain because need
    access to vertices & sources coordinates / data.
    """

    def __init__(self, project_radius=10.0, project_on='brain',
                 project_contribute=False, project_type='activity',
                 project_mask_color='gray', **kwargs):
        """Init."""
        logger.debug("Problème avec proj_obj : on enregistre les mesh dans "
                     "proj_obj pour récupérer les vertices + définir ensuite "
                     "la couleur. Le problème c'est que en enregistrant tout "
                     "l objet, on enregistre pas une copie et donc tout les "
                     "objects on la même taille...")
        assert isinstance(project_radius, (int, float))
        assert project_type in ['activity', 'repartition']
        self._proj_obj = {}
        self._proj_radius = project_radius
        self._proj_on = project_on
        self._proj_type = project_type
        self._proj_contribute = project_contribute
        self._proj_mask_color = color2vb(project_mask_color)
        self._proj_data = None

    # ======================================================================
    # PROJECTIONS
    # ======================================================================
    def _get_obj_vertices(self, obj):
        """Find the vertices from the object."""
        if obj in self._proj_obj.keys():
            sh = [k + str(i.mesh.get_vertices.shape) for k, i in self._proj_obj.items()]
            logger.debug("Wrong shapes : %s" % ', '.join(sh))
            return self._proj_obj[obj].mesh.get_vertices
        else:
            lst_obj = ', '.join(list(self._proj_obj.keys()))
            raise ValueError(obj + " not found. Use : " + lst_obj)

    def _run_source_projection(self):
        """Apply corticale projection."""
        # =============== CHECKING ===============
        assert isinstance(self._proj_radius, (int, float))
        assert self._proj_type in ['activity', 'repartition']
        self._clean_source_projection()

        # =============== VERTICES ===============
        v = self._get_obj_vertices(self._proj_on)
        self._vsh = v.shape

        # ============= MODULATIONS =============
        r, c = self._proj_radius, self._proj_contribute
        log_str = ("Project {} onto the %s (radius=%f contribute="
                   "%r" % (self._proj_on, float(self._proj_radius),
                           self._proj_contribute))
        if self._proj_type == 'activity':
            logger.info(log_str.format("source's activity"))
            mod = self.sources.project_modulation(v, r, c)
        elif self._proj_type == 'repartition':
            logger.info(log_str.format("source's repartition"))
            mod = self.sources.project_repartition(v, r, c)
        self._proj_data = mod
        self.sources._minmax = (mod.min(), mod.max())

        # ============= MASKED =============
        mesh = self._proj_obj[self._proj_on].mesh
        mask = np.zeros((len(mesh)), dtype=np.float32)
        if self.sources.is_masked:
            mask_idx = self.sources.get_masked_index(v, self._proj_radius, c)
            mask[mask_idx] = 2.
            mesh.mask_color = self._proj_mask_color
            logger.info("Set masked sources cortical activity to the "
                        "color %s" % str(list(mesh.mask_color.ravel())[0:-1]))
        if mod.mask.sum():
            mask[~mod.mask] = 1.
        self._proj_obj[self._proj_on].mesh.mask = mask

        # ============= COLOR =============
        self._projection_to_color()

    def _projection_to_color(self):
        """Turn the projection into colormap."""
        # Get color arguents :
        kwargs = self.cbobjs._objs['Projection'].to_kwargs()
        # Get the colormap :
        color = array2colormap(self._proj_data, **kwargs)

        # ============= MESH =============
        self._proj_obj[self._proj_on].mesh.color = color

    def _clean_source_projection(self):
        """Clean projection variables."""
        self._proj_data = None

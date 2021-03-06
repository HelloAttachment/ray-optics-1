#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 10:59:29 2017

@author: Mike
"""


import unittest
import numpy as np
import numpy.testing as npt
from math import log10, pow
import optical.sequential as seq
import optical.profiles as prof

import ag_dblgauss_s as dblg
import marginal_ray as f1r2


class RayTraceTestCase(unittest.TestCase):
    def setUp(self):
        self.ldm = seq.SequentialModel()
        # lump defocus into back focal distance
        dblg.ag_dblgauss[-2][1] += dblg.ag_dblgauss[-1][1]
        dblg.ag_dblgauss[-1][1] = 0.

        self.ldm.gaps[0].thi = dblg.ag_dblgauss[0][1]
        # self.ldm.sg.edge[0][1]['g'].thi = dblg.ag_dblgauss[0][1]
        # self.ldm.sg.edges[0, 1]['g'].thi = dblg.ag_dblgauss[0][1]
        for s in dblg.ag_dblgauss[1:]:
            self.ldm.add_surface(s)

        self.p0 = np.array([0., 0., 0.])
        self.p1 = np.array([0., 0., dblg.ag_dblgauss[0][1]])
        self.epd = np.array([25., 0., 0.])
        self.d0 = prof.normalize((self.p1 + self.epd) - self.p0)

    def test_dbgauss_axial_ray(self):
        ray, op_delta = self.ldm.trace(self.p0, self.d0, 587.6)

        def rel_err(v, def_err):
            if v == 0.:
                return def_err
            else:
                vmag = round(log10(abs(v)), 1)
                if vmag < 0.:
                    return def_err/pow(10, vmag)
                else:
                    return def_err

        def rel_err_vec(v, def_err):
            vflt = list(abs(x) for x in v if x != 0)
            if len(vflt) == 0:
                return def_err
            else:
                return rel_err(min(vflt), def_err)

        for i, rtup in enumerate(zip(ray, f1r2.rayf1r2)):
            xyztol = rel_err_vec(rtup[1][0], 1e-6)
#            print(i, rtup[0][0], rtup[1][0], xyztol)
            npt.assert_allclose(rtup[0][0], rtup[1][0], rtol=xyztol)
            # compute direction tangents from direction cosines
            tantol = rel_err_vec(rtup[1][1], 1e-6)
            npt.assert_allclose([rtup[0][1][0]/rtup[0][1][2],
                                 rtup[0][1][1]/rtup[0][1][2]], rtup[1][1],
                                rtol=tantol, atol=1e-10)

            # don't compare path length in object or image space
            if i > 1 and i < 12:
                dsttol = rel_err(rtup[1][2], 1e-6)
                npt.assert_allclose(rtup[0][2], rtup[1][2], rtol=dsttol)


if __name__ == '__main__':
    unittest.main(verbosity=3)

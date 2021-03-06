#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 25 11:01:04 2018

@author: Mike
"""

import numpy as np
from numpy.linalg import norm
from math import sqrt, copysign
from . import transform as trns

Surf, Gap = range(2)


def bend(d_in, normal, n_in, n_out):
    """ refract incoming direction, d_in, about normal """
    normal_len = norm(normal)
    cosI = np.dot(d_in, normal)/normal_len
    sinI_sqr = 1.0 - cosI*cosI
    n_cosIp = copysign(sqrt(n_out*n_out - n_in*n_in*sinI_sqr), cosI)
    alpha = n_cosIp - n_in*cosI
    d_out = (n_in*d_in + alpha*normal)/n_out
    return d_out


def reflect(d_in, normal):
    """ reflect incoming direction, d_in, about normal """
    normal_len = norm(normal)
    cosI = np.dot(d_in, normal)/normal_len
    d_out = d_in - 2.0*cosI*normal
    return d_out


def trace(path, pt0, dir0, wl, eps=1.0e-12):
    ray = []
    # trace object surface
    obj = next(path)
    srf_obj = obj[Surf]
    gap_obj = obj[Gap]
    op_delta, pt = srf_obj.profile.intersect(pt0, dir0)
    ray.append([pt, dir0, op_delta])
#    print("obj:", pt, dir0)
    n_before = gap_obj.medium.rindex(wl)
#    print(n_before, op_delta)
    op_delta *= n_before

    before = obj
    before_pt = pt
    before_dir = dir0

    # loop of remaining surfaces in path
    while True:
        try:
            after = next(path)

            gap_before = before[Gap]

            r, t = trns.forward_transform(before[Surf], before[Gap],
                                          after[Surf])
            rt = r.transpose()
            b4_pt, b4_dir = rt.dot(before_pt - t), rt.dot(before_dir)

            pp_dst = -b4_pt.dot(b4_dir)
            pp_pt_before = b4_pt + pp_dst*b4_dir

            n_before = gap_before.medium.rindex(wl)
            srf = after[Surf]
            if after[Gap]:
                n_after = after[Gap].medium.rindex(wl)
            else:
                n_after = n_before

            # intersect ray with profile
            pp_dst_intrsct, pt = srf.profile.intersect(pp_pt_before,
                                                       b4_dir, eps)
            eic_dst_before = ((pt.dot(b4_dir) + pt[2]) /
                              (1 + b4_dir[2]))
            normal = srf.profile.normal(pt)

            # refract or reflect ray at interface
            if srf.refract_mode == 'REFL':
                after_dir = reflect(b4_dir, normal)
            else:
                after_dir = bend(b4_dir, normal, n_before, n_after)

            eic_dst_after = ((pt.dot(after_dir) + pt[2]) /
                             (1 + after_dir[2]))

            dW = n_after*eic_dst_after - n_before*eic_dst_before
            op_delta += dW
            dst_before = pp_dst + pp_dst_intrsct
            ray.append([pt, after_dir, dst_before])
#            print("after:", pt, after_dir)

            before_pt = pt
            before_dir = after_dir
            before = after
#            print(n_before, eic_dst_before, n_after, eic_dst_after, dW)
        except StopIteration:
            dW = -n_before*eic_dst_before
            op_delta += dW
#            print(eic_dst_before, dW)
            break

    return ray, op_delta

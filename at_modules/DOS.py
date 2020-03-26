"""
Author: Daniel Garcia
Email: garciad@ifca.unican.es
Github: garciadd
"""

from functools import reduce
import operator
import os, re
import shutil
import numpy as np
import json
import time

from osgeo import gdal, osr
from netCDF4 import Dataset


class DOS(object):

    def __init__(self, config, band, arr_band):
        """
        initialize the variables used to preprocess landsat images
        and apply DOS1 atmospheric correction
        """

        self.band = band
        self.arr_band = arr_band
        self.name_bands = {'SRB1': 'BAND_1', 'SRB2': 'BAND_2', 'SRB3': 'BAND_3', 'SRB4': 'BAND_4', 'SRB5': 'BAND_5', 'SRB6': 'BAND_6', 'SRB7': 'BAND_7', 'B8': 'BAND_8', 'SRB9': 'BAND_9', 'SRB10': 'BAND_10', 'SRB11': 'BAND_11'}

        self.metadata = config

        self.Tz = 1
        self.Ed = 0
        self.Tv = 1

    def sr_radiance(self, arr, min_value):

        Lmin = self.Ml * min_value + self.Al
        L1 = 0.01 * ((self.Esun * np.cos(self.z * np.pi / 180.) * self.Tz) + self.Ed) * self.Tv / (np.pi * self.d**2)
        Lp = Lmin - L1

        L = self.Ml * arr + self.Al
        Lsr = L - Lp

        return Lsr

    def sr_thermal(self, arr):

        L = self.Ml * arr + self.Al
        Tb = self.k2 / np.log((self.k1 / L) + 1)

        return Tb

    def sr_reflectance(self):

        name = self.name_bands[self.band]

        if self.band=='SRB10' or self.band=='SRB11':

            self.Ml = float(self.metadata['RADIOMETRIC_RESCALING']['RADIANCE_MULT_{}'.format(name)])
            self.Al = float(self.metadata['RADIOMETRIC_RESCALING']['RADIANCE_ADD_{}'.format(name)])
            self.k1 = float(self.metadata['TIRS_THERMAL_CONSTANTS']['K1_CONSTANT_{}'.format(name)])
            self.k2 = float(self.metadata['TIRS_THERMAL_CONSTANTS']['K2_CONSTANT_{}'.format(name)])

            T = self.sr_thermal(self.arr_band)

            return T

        else:

            self.Ml = float(self.metadata['RADIOMETRIC_RESCALING']['RADIANCE_MULT_{}'.format(name)])
            self.Al = float(self.metadata['RADIOMETRIC_RESCALING']['RADIANCE_ADD_{}'.format(name)])
            self.rad_max = float(self.metadata['MIN_MAX_RADIANCE']['RADIANCE_MAXIMUM_{}'.format(name)])
            self.ref_max = float(self.metadata['MIN_MAX_REFLECTANCE']['REFLECTANCE_MAXIMUM_{}'.format(name)])
            self.d = float(self.metadata['IMAGE_ATTRIBUTES']['EARTH_SUN_DISTANCE'])
            self.z = 90 - float(self.metadata['IMAGE_ATTRIBUTES']['SUN_ELEVATION'])
            self.Esun = (np.pi * self.d**2) * self.rad_max / self.ref_max

            min_value = np.amin(self.arr_band)
            Lsr = self.sr_radiance(self.arr_band, min_value)
            sr = (np.pi * self.d**2 * Lsr) / (((self.Esun * np.cos(self.z * np.pi / 180.) * self.Tz) + self.Ed) * self.Tv)
            sr[sr>=1] = 1
            sr[sr<0] = 0

            return sr

#APIs
import os
import numpy as np
import time

from osgeo import gdal, osr
from netCDF4 import Dataset

#Subfunctions
from at_modules import utils
from at_modules import DOS

class atcor():

    def __init__(self, local_path, tile, output_path):

        self.local_path = local_path
        self.tile = tile

        self.tif_path = os.path.join(local_path, '{}.tif'.format(tile))
        self.zip_path = os.path.join(local_path, '{}.zip'.format(tile))

        self.nc_path = os.path.join(output_path, '{}.nc'.format(tile))

    def GetExtent(self, gt, cols, rows):
        ''' Return list of corner coordinates from a geotransform
            @type gt:   C{tuple/list}
            @param gt: geotransform
            @type cols:   C{int}
            @param cols: number of columns in the dataset
            @type rows:   C{int}
            @param rows: number of rows in the dataset
            @rtype:    C{[float,...,float]}
            @return:   coordinates of each corner
        '''

        ext=[]
        xarr=[0,cols]
        yarr=[0,rows]

        for px in xarr:
            for py in yarr:
                x=gt[0]+(px*gt[1])+(py*gt[2])
                y=gt[3]+(px*gt[4])+(py*gt[5])
                ext.append([x,y])
            yarr.reverse()
        return ext


    def get_latslons(self):

        xlow, ylow = (self.coord['Corner Coordinates'])[0][1], (self.coord['Corner Coordinates'])[0][0]
        xup, yup = (self.coord['Corner Coordinates'])[2][1], (self.coord['Corner Coordinates'])[2][0]

        lats = np.linspace(ylow, yup, num=self.coord['Ysize'])
        lons = np.linspace(xlow, xup, num=self.coord['Xsize'])

        return lats, lons


    def save_netCDF(self):

        #latitudes & longitudes arrays
        lats, lons = self.get_latslons()

        # create a file (Dataset object, also the root group).
        dsout = Dataset(self.nc_path, 'w', format='NETCDF4')
        dsout.description = 'Super Resoved bands'
        dsout.history = 'Created {}'.format(time.ctime(time.time()))
        dsout.source = 'netCDF4 python module'

        # dimensions.
        lat = dsout.createDimension('lat', len(lats))
        lon = dsout.createDimension('lon', len(lons))

        # variables.
        latitudes = dsout.createVariable('lat','f4',('lat',))
        longitudes = dsout.createVariable('lon','f4',('lon',))

        latitudes.standard_name = 'latitude'
        latitudes.units = 'm north'
        latitudes.axis = "Y"
        latitudes[:] = lats

        longitudes.standard_name = 'longitude'
        longitudes.units = 'm east'
        longitudes.axis = "X"
        longitudes[:] = lons

        for b in self.arr_bands:

            name = b.split(' ')[0]
            band = dsout.createVariable(name, 'f4',
                                        ('lat', 'lon'),
                                        least_significant_digit=4,
                                        fill_value=np.nan)

            band[:] = self.arr_bands[b]
            band.standard_name = b
            band.units = 'rad'
            band.setncattr('grid_mapping', 'spatial_ref')

        crs = dsout.createVariable('spatial_ref', 'i4')
        crs.spatial_ref = self.coord['geoprojection']

        dsout.close()


    def load_bands(self):

        if (self.tile).startswith('LC'):
            config = utils.read_config_file(self.zip_path, self.local_path)
            config = config['L1_METADATA_FILE']

        src_ds = gdal.Open(self.tif_path)
        if src_ds is None:
            print ('not recognized as a supported file format.')
        else:
            pass

        self.coord = {}
        self.coord['geotransform'] = src_ds.GetGeoTransform()
        self.coord['geoprojection'] = src_ds.GetProjection()
        self.coord['Xsize'] = src_ds.RasterXSize
        self.coord['Ysize'] = src_ds.RasterYSize
        self.coord['Corner Coordinates'] = self.GetExtent(src_ds.GetGeoTransform(), src_ds.RasterXSize, src_ds.RasterYSize)

        self.arr_bands = {}

        for band in range(src_ds.RasterCount):

            band += 1
            srcband = src_ds.GetRasterBand(band)

            if srcband is None:
                continue

            name = srcband.GetDescription()
            b = name.split(' ')[0]
            arr = srcband.ReadAsArray()

            if (self.tile).startswith('LC'):
                at = DOS.DOS(config, b, arr)
                ref = at.sr_reflectance()

            elif (self.tile).startswith('S2'):
                ref = arr/ 10000

            self.arr_bands[name] = ref
        self.save_netCDF()

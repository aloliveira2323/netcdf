import unittest
from netCDF4 import Dataset
from netcdf import netcdf as nc
import os
import stat
import numpy as np


class TestNetcdf(unittest.TestCase):

    def create_ref_file(self, filename):
        ref = Dataset(
            filename,
            mode="w",
            clobber=True,
            format='NETCDF3_CLASSIC')
        ref.createDimension('auditCount', 2)
        ref.createDimension('auditSize', 80)
        ref.createDimension('xc', 200)
        ref.createDimension('yc', 100)
        ref.createDimension('time')
        var = ref.createVariable(
            'time',
            'i4',
            dimensions=('time',),
            zlib=True,
            fill_value=0)
        var[0] = 1
        var = ref.createVariable(
            'lat',
            'f4',
            dimensions=('yc', 'xc'),
            zlib=True,
            fill_value=0.0)
        var[:] = 1
        var = ref.createVariable(
            'lon',
            'f4',
            dimensions=('yc', 'xc'),
            zlib=True,
            fill_value=0.0)
        var[:] = 1
        var = ref.createVariable(
            'data',
            'f4',
            dimensions=('time', 'yc', 'xc'),
            zlib=True,
            fill_value=0.0)
        var[0, :] = 1
        var = ref.createVariable(
            'auditTrail',
            'S1',
            dimensions=('auditCount', 'auditSize'),
            zlib=True,
            fill_value=0.0)
        var[:] = self.auditTrail
        return ref

    def setUp(self):
        audit = np.array([['1', '4', '0', '0', '1', ' ', '2', '3', '2', '3',
                           '5', '2', ' ', 'I', 'M', 'G', 'C', 'O', 'P', 'Y',
                           ' ', 'D', 'E', 'L', 'I', 'V', 'E', 'R', 'Y', '/',
                           'I', 'N', '1', '2', '6', '7', '8', '3', '3', '1',
                           '9', '4', '.', '1', ' ', 'D', 'E', 'L', 'I', 'V',
                           'E', 'R', 'Y', '/', 'N', 'C', '1', '2', '6', '7',
                           '8', '3', '3', '1', '9', '4', '.', '1', ' ', 'L',
                           'I', 'N', 'E', 'L', 'E', '=', '1', '1', '0', '1'],
                          [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                           ' ', ' ', ' ', '0', ' ', '1', '6', '8', '5', '2',
                           ' ', 'I', ' ', 'P', 'L', 'A', 'C', 'E', '=', 'U',
                           'L', 'E', 'F', 'T', ' ', 'B', 'A', 'N', 'D', '=',
                           '1', ' ', 'D', 'O', 'C', '=', 'Y', 'E', 'S', ' ',
                           'M', 'A', 'G', '=', '-', '1', ' ', '-', '1', ' ',
                           'S', 'I', 'Z', 'E', '=', '1', '0', '6', '7', ' ',
                           '2', '1', '6', '6', ' ', ' ', ' ', ' ', ' ', ' ']])
        self.auditTrail = audit
        self.refs = [self.create_ref_file('unittest%s.nc' % (str(i).zfill(2)))
                     for i in range(5)]
        list(map(lambda ref: ref.sync(), self.refs))
        self.ro_ref = self.create_ref_file('ro_unittest.nc')
        self.ro_ref.sync()

    def tearDown(self):
        list(map(lambda ref: ref.close(), self.refs))
        self.ro_ref.close()
        os.chmod('ro_unittest.nc', stat.S_IWRITE | stat.S_IRUSR |
                 stat.S_IRGRP | stat.S_IROTH)
        os.system('rm *.nc')

    def test_open_unexistent_file(self):
        with self.assertRaisesRegexp(Exception, u'There is not file list or '
                                     'pattern to open.'):
            nc.open([])

    def test_open_unexistent_pattern(self):
        with self.assertRaisesRegexp(Exception, u'There is not file list or '
                                     'pattern to open.'):
            nc.open('')

    def test_open_close_existent_file(self):
        # check if open an existent file.
        root, is_new = nc.open('unittest00.nc')
        self.assertEquals(root.files, ['unittest00.nc'])
        self.assertEquals(root.pattern, 'unittest00.nc')
        self.assertEquals(len(root.roots), 1)
        self.assertFalse(is_new)
        self.assertFalse(root.read_only)
        # check if close an existent file.
        nc.close(root)
        with self.assertRaisesRegexp(RuntimeError, u'NetCDF: Not a valid ID'):
            nc.close(root)

    def test_open_close_new_file(self):
        # delete the filename from the system.
        filename = 'unittest-1.nc'
        if os.path.isfile(filename):
            os.remove(filename)
        # check if create and open a new file.
        root, is_new = nc.open(filename)
        self.assertEquals(root.files, ['unittest-1.nc'])
        self.assertEquals(root.pattern, 'unittest-1.nc')
        self.assertEquals(len(root.roots), 1)
        self.assertTrue(is_new)
        self.assertFalse(root.read_only)
        # check if close the created file.
        nc.close(root)
        with self.assertRaisesRegexp(RuntimeError, u'NetCDF: Not a valid ID'):
            nc.close(root)

    def test_open_close_readonly_file(self):
        # set the file to be readonly.
        filename = 'ro_unittest.nc'
        if os.path.isfile(filename):
            os.chmod(filename, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        # check if create and open a new file.
        root, is_new = nc.open(filename)
        self.assertEquals(root.files, [filename])
        self.assertEquals(root.pattern, filename)
        self.assertEquals(len(root.roots), 1)
        self.assertFalse(is_new)
        self.assertTrue(root.read_only)
        # check if close the readonly file.
        nc.close(root)
        with self.assertRaisesRegexp(RuntimeError, u'NetCDF: Not a valid ID'):
            nc.close(root)

    def test_open_close_multiple_files(self):
        # check if open the pattern selection using using a package instance.
        root, is_new = nc.open('unittest0*.nc')
        self.assertEquals(root.files, ['unittest0%i.nc' % i for i in range(5)])
        self.assertEquals(root.pattern, 'unittest0*.nc')
        self.assertEquals(len(root.roots), 5)
        self.assertFalse(is_new)
        self.assertFalse(root.read_only)
        # check if close the package with all the files.
        nc.close(root)
        with self.assertRaisesRegexp(RuntimeError, u'NetCDF: Not a valid ID'):
            nc.close(root)

    def test_open_close_using_with(self):
        # check if open the pattern selection using using a package instance.
        with nc.loader('unittest0*.nc') as root:
            self.assertEquals(root.files,
                              ['unittest0%i.nc' % i for i in range(5)])
            self.assertEquals(root.pattern, 'unittest0*.nc')
            self.assertEquals(len(root.roots), 5)
            self.assertFalse(root.is_new)
            self.assertFalse(root.read_only)
        # check if close the package with all the files.
        with self.assertRaisesRegexp(RuntimeError, u'NetCDF: Not a valid ID'):
            nc.close(root)

    def test_get_existing_dim_single_file(self):
        # check if get the dimension in a single file.
        root = nc.open('unittest00.nc')[0]
        self.assertEquals(len(nc.getdim(root, 'time')), 1)
        nc.close(root)

    def test_get_not_existing_dim_single_file(self):
        # check if get the dimension in a single file.
        root = nc.open('unittest00.nc')[0]
        self.assertFalse(root.has_dimension('the_12th_dimension'))
        self.assertEquals(len(nc.getdim(root, 'the_12th_dimension', 123)), 1)
        self.assertTrue(root.has_dimension('the_12th_dimension'))
        nc.close(root)

    def test_get_existing_dim_multiple_file(self):
        # check if get the dimension in a single file.
        root = nc.open('unittest0*.nc')[0]
        self.assertEquals(len(nc.getdim(root, 'time')), 5)
        nc.close(root)

    def test_get_not_existing_dim_multiple_file(self):
        # check if get the dimension in a single file.
        root = nc.open('unittest0*.nc')[0]
        self.assertFalse(root.has_dimension('the_12th_dimension'))
        self.assertEquals(len(nc.getdim(root, 'the_12th_dimension', 123)), 5)
        self.assertTrue(root.has_dimension('the_12th_dimension'))
        nc.close(root)

    def test_get_existing_var_single_file(self):
        # check if get the variable in a single file.
        root = nc.open('unittest00.nc')[0]
        self.assertNotIn('data', root.variables)
        var = nc.getvar(root, 'data')
        self.assertEquals(var.shape, (1, 100, 200))
        self.assertIn('data', root.variables)
        are_equals = (var[:] == np.zeros(var.shape) + 1.)
        self.assertTrue(are_equals.all())
        nc.close(root)

    def test_get_non_existing_var_single_file(self):
        # check if get the variable in a single file.
        root = nc.open('unittest00.nc')[0]
        self.assertNotIn('new_variable', root.variables)
        var = nc.getvar(root, 'new_variable',
                        'f4', ('time', 'yc', 'xc'),
                        digits=3, fill_value=1.2)
        self.assertEquals(var.shape, (1, 100, 200))
        self.assertIn('new_variable', root.variables)
        ref = np.zeros(var.shape) + 1.2
        # the comparison is true if the error is less than 0.002
        are_equals = (var[:] - ref) < 0.002
        self.assertTrue(are_equals.all())
        nc.close(root)

    def test_get_existing_var_multiple_file(self):
        # check if get the variable with multiples files.
        root = nc.open('unittest0*.nc')[0]
        self.assertNotIn('data', root.variables)
        var = nc.getvar(root, 'data')
        self.assertEquals(var.shape, (5, 100, 200))
        self.assertIn('data', root.variables)
        are_equals = (var[:] == np.zeros(var.shape) + 1.)
        self.assertTrue(are_equals.all())
        nc.close(root)

    def test_get_non_existing_var_multiple_file(self):
        # check if get the variable with multiples files.
        root = nc.open('unittest0*.nc')[0]
        self.assertNotIn('new_variable', root.variables)
        var = nc.getvar(root, 'new_variable',
                        'f4', ('time', 'yc', 'xc'),
                        digits=3, fill_value=1.2)
        self.assertEquals(var.shape, (5, 100, 200))
        self.assertIn('new_variable', root.variables)
        ref = np.zeros(var.shape) + 1.2
        # the comparison is true if the error is less than 0.002
        are_equals = (var[:] - ref) < 0.002
        self.assertTrue(are_equals.all())
        nc.close(root)

    def test_single_file_var_operations(self):
        # check if get and set the numpy matrix.
        root = nc.open('unittest00.nc')[0]
        var = nc.getvar(root, 'data')
        self.assertEquals(var.__class__, nc.SingleNCVariable)
        self.assertEquals(var[:].__class__, np.ndarray)
        tmp = var[:]
        var[:] = var[:] + 1
        nc.close(root)
        # check if value was saved into the file.
        root = nc.open('unittest00.nc')[0]
        var = nc.getvar(root, 'data')
        self.assertTrue(var, tmp + 1)
        nc.close(root)

    def test_multiple_file_var_operations(self):
        # check if get and set the numpy matrix.
        root = nc.open('unittest0*.nc')[0]
        var = nc.getvar(root, 'data')
        self.assertEquals(var.__class__, nc.DistributedNCVariable)
        self.assertEquals(var[:].__class__, np.ndarray)
        tmp = var[:]
        var[:] = var[:] + 1
        nc.close(root)
        # check if value was saved into the file.
        root = nc.open('unittest0*.nc')[0]
        var = nc.getvar(root, 'data')
        self.assertTrue(var, tmp + 1)
        nc.close(root)

    def test_single_file_new_var_operations(self):
        # check if create a new var.
        root = nc.open('unittest00.nc')[0]
        var = nc.getvar(root, 'new_variable',
                        'f4', ('time', 'yc', 'xc'),
                        digits=3, fill_value=1.0)
        self.assertEquals(var.__class__, nc.SingleNCVariable)
        self.assertEquals(var[:].__class__, np.ndarray)
        tmp = var[:]
        var[:] = var[:] + 1
        nc.close(root)
        # check if value was saved into the file.
        root = nc.open('unittest00.nc')[0]
        var = nc.getvar(root, 'new_variable')
        self.assertTrue(var, tmp + 1)
        nc.close(root)

    def test_multiple_file_new_var_operations(self):
        # check if create a new var.
        root = nc.open('unittest0*.nc')[0]
        var = nc.getvar(root, 'new_variable',
                        'f4', ('time', 'yc', 'xc'),
                        digits=3, fill_value=1.0)
        self.assertEquals(var.__class__, nc.DistributedNCVariable)
        self.assertEquals(var[:].__class__, np.ndarray)
        tmp = var[:]
        var[:] = var[:] + 1
        nc.close(root)
        # check if value was saved into the files.
        root = nc.open('unittest00.nc')[0]
        var = nc.getvar(root, 'new_variable')
        self.assertTrue(var, tmp + 1)
        nc.close(root)

    def test_character_variables_in_single_file(self):
        # check if get and set the numpy string matrix in single files.
        root = nc.open('unittest00.nc')[0]
        var = nc.getvar(root, 'auditTrail')
        self.assertEquals(var.shape, (1, 2, 80))
        self.assertEquals(var, self.auditTrail)
        self.auditTrail[:].data[0:6] = 'CHANGE'
        var[0, 0:6] = np.array(list('CHANGE'))
        self.assertEquals(var, self.auditTrail)
        nc.close(root)

    def test_character_variables_in_multiple_file(self):
        # check if get and set the numpy string matrix in multiple files.
        root = nc.open('unittest0*.nc')[0]
        var = nc.getvar(root, 'auditTrail')
        self.assertEquals(var.shape, (5, 2, 80))
        result = np.vstack([[self.auditTrail] for i in range(5)])
        self.assertEquals(var, result)
        for i in range(5):
            result[i, i % 2].data[0:6] = 'CHANGE'
            var[i, i % 2, 0:6] = np.array(list('CHANGE'))
        self.assertEquals(var, result)
        nc.close(root)
        # check if was writed to each file.
        root = nc.open('unittest0*.nc')[0]
        var = nc.getvar(root, 'auditTrail')
        self.assertEquals(var, result)
        nc.close(root)

    def test_get_var_copy_from_source(self):
        root = nc.open('unittest0*.nc')[0]
        if os.path.isfile('unittest_destiny.nc'):
            os.remove('unittest_destiny.nc')
        root_d = nc.open('unittest_destiny.nc')[0]
        # check if getvar copy a variable from a complex file to a simple file.
        var_source = nc.getvar(root, 'data')
        var = nc.getvar(root_d, 'data_copy', source=var_source)
        self.assertEquals(var, var_source)
        # check if getvar copy a variable from a simple file to a complex file.
        var_distributed = nc.getvar(root, 'data_copy', source=var)
        self.assertEquals(var, var_distributed)
        # check if getvar copy changing the vtype to a simple file.
        var_int = nc.getvar(root_d, 'data_int', 'i4', source=var_source)
        self.assertEquals(var_source.vtype, 'f4')
        self.assertEquals(var_int.vtype, 'i4')
        diff = var_source[:] - var_int[:]
        self.assertTrue((diff < 1).all())
        # check if getvar copy changing the vtype to a multiple file.
        var_distributed_int = nc.getvar(root, 'data_int', 'i4', source=var)
        self.assertEquals(var_distributed.vtype, 'f4')
        self.assertEquals(var_distributed_int.vtype, 'i4')
        diff = var_distributed[:] - var_distributed_int[:]
        self.assertTrue((diff < 1).all())


if __name__ == '__main__':
        unittest.main()

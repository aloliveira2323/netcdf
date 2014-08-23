#!/usr/bin/env python
# -*- coding: utf-8 -*-
from distutils.core import setup
from distutils.command.build import build
from setuptools.command import easy_install
import os
import subprocess
from pip.req import parse_requirements
from urllib import urlretrieve
from datetime import datetime
import sys


def calculate_version():
    # Fetch version from git tags, and write to version.py.
    # Also, when git is not available (PyPi package), use stored version.py.
    version_py = os.path.join(os.path.dirname(__file__), 'version.py')
    try:
        git_version = subprocess.check_output(["git", "describe"]).rstrip()
    except Exception:
        with open(version_py, 'r') as filehandler:
            git_version = (open(version_py).read()
                           .strip().split('=')[-1].replace('"', ''))
    version_msg = ('# Do not edit this file, pipeline versioning is '
                   'governed by git tags')
    with open(version_py, 'w') as filehandler:
        filehandler.write(version_msg + os.linesep + "__version__=" +
                          git_version)
    return git_version


REQUIREMENTS = [str(ir.req) for ir in parse_requirements('requirements.txt')]
VERSION_GIT = calculate_version()
import platform as p
TMP_PATH = '/tmp/'
OS_NAME = p.system()
BINARIES = {
    'hdf5': {
        'version': '1.8.12',
        'name': 'hdf5-%s',
        'url': 'http://www.hdfgroup.org/ftp/HDF5/releases/%s/src',
        'compile': {
            'depends': ['pyandoc==0.0.1', 'numpy==1.8.0'],
            'config': {
                'pre': '',
                'post': '--prefix=/usr/local --enable-shared --enable-hl',
            },
        },
    },
    'netcdf': {
        'version': '4.3.1-rc4',
        'name': 'netcdf-%s',
        'url': 'ftp://ftp.unidata.ucar.edu/pub/netcdf',
        'compile': {
            'depends': [],
            'config': {
                'pre': ('LDFLAGS=-L/usr/local/lib '
                        'CPPFLAGS=-I/usr/local/include '
                        'LD_LIBRARY_PATH=/usr/local'),
                'post': ('--enable-netcdf-4 --enable-dap --enable-shared'
                         ' --prefix=/usr/local'),
            },
        },
    },
}
SYSTEMS = {
    'Linux': {
        'update_shared_libs': 'sudo ldconfig',
        'libs': {
            'hdf5': '/usr/local/lib/libhdf5.so.8.0.1',
            'netcdf': '/usr/local/lib/libnetcdf.so.7.2.0',
        },
    },
    'Darwin': {
        'update_shared_libs': '',
        'libs': {
            'hdf5': '/usr/local/lib/libhdf5_hl.8.dylib',
            'netcdf': '/usr/local/lib/libnetcdf.7.dylib',
        },
    },
}


def get_long_description():
    readme_file = 'README.md'
    if not os.path.isfile(readme_file):
        return ''
    # Try to transform the README from Markdown to reStructuredText.
    try:
        import pandoc
        pandoc.core.PANDOC_PATH = 'pandoc'
        doc = pandoc.Document()
        doc.markdown = open(readme_file).read()
        description = doc.rst
    except Exception:
        description = open(readme_file).read()
    return description


class Builder(object):

    def __init__(self, lib):
        self.lib_key = lib
        self.lib = BINARIES[lib]
        self.name = self.lib['name'] % self.lib['version']
        self.local_unpacked = '%s%s' % (TMP_PATH, self.name)
        self.local_filename = ''

    def call(self, cmd):
        return subprocess.call(cmd, shell=True)

    def download(self):
        url = self.lib['url']
        if url.find('%s') > 0:
            url = url % self.name
        filename = '%s.tar.gz' % self.name
        self.local_filename = '%s%s' % (TMP_PATH, filename)
        if not os.path.isfile(self.local_filename):
            begin = datetime.now()

            def dl_progress(count, block_size, total_size):
                transfered = (count * block_size
                              if total_size >= count * block_size
                              else total_size)
                progress = transfered * 100. / total_size
                speed = (transfered /
                         ((datetime.now() - begin).total_seconds())) / 1024
                print '\r%s' % (' ' * 78),
                print (u'\rDownloaded %s '
                       '(\033[33m%03.2f %%\033[0m at \033[35m%i KB/s\033[0m)'
                       % (filename, progress, speed)),
                sys.stdout.flush()
            source = '%s/%s' % (url, filename)
            destiny = '%s%s' % (TMP_PATH, filename)
            self.local_filename, _ = urlretrieve(source, destiny,
                                                 reporthook=dl_progress)

    def uncompress(self):
        if not os.path.isdir(self.local_unpacked):
            self.download()
            # self.call('rm -rf %s*' % self.local_unpacked)
            import tarfile as tar
            tfile = tar.open(self.local_filename, mode='r:gz')
            tfile.extractall(TMP_PATH)
            tfile.close()
            self.call('chmod -R ugo+rwx %s*' % self.local_unpacked)

    def build(self):
        filename = SYSTEMS[OS_NAME]['libs'][self.lib_key]
        if not os.path.isfile(filename):
            self.uncompress()
            depends = self.lib['compile']['depends']
            install = lambda dep: easy_install.main(['-U', dep])
            map(install, depends)
            title = '%s %s' % (OS_NAME, p.architecture()[0])
            spacer = '-' * len(title)
            print '+%s+\n|%s|\n+%s+' % (spacer, title, spacer)
            import multiprocessing
            # self.call('sudo rm %s' % filename)
            path = '%s%s' % (TMP_PATH, self.lib['name'] % self.lib['version'])
            config = self.lib['compile']['config']
            ncores = multiprocessing.cpu_count()
            self.call(('cd %s; %s ./configure %s; make -j %s; '
                       ' sudo make install')
                      % (path, config['pre'], config['post'], ncores))
            update_shared_libs = SYSTEMS[OS_NAME]['update_shared_libs']
            if update_shared_libs:
                self.call(update_shared_libs)


class build_wrapper(build):
    def initialize_options(self):
        # Deploy all the described libraries in the BINARIES dictionary.
        libs = sorted(BINARIES.keys())
        build_lib = lambda lib: Builder(lib).build()
        map(build_lib, libs)
        return build.initialize_options(self)


setup(
    name='netcdf',
    version=VERSION_GIT,
    author=u'Eloy Adonis Colell',
    author_email='eloy.colell@gmail.com',
    packages=['netcdf', ],
    url='https://github.com/ecolell/netcdf',
    license='MIT License, see LICENCE.txt',
    description='A python library that allow to use one or multiple NetCDF '
                'files in a transparent way through polimorphic methods.',
    long_description=get_long_description(),
    zip_safe=True,
    install_requires=REQUIREMENTS,
    classifiers=[
        "Intended Audience :: Science/Research",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering :: Physics",
    ],
    cmdclass={
        'build': build_wrapper,
    },
)

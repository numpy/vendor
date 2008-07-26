#! /usr/bin/python

from subprocess import Popen
import shutil
import os.path
from os.path import join as pjoin, dirname
import glob
import tarfile
from ConfigParser import ConfigParser
import sys

if os.name == 'nt' and not sys.platform == 'cygwin':
    raise ValueError("You should use cygwin python on windows for now !")

# Configuration (this should be put in a config file at some point)
LAPACK_SRC = pjoin('src', 'lapack-lite-3.1.1')
LAPACK_LIB = pjoin(LAPACK_SRC, 'lapack_MINGW32.a')
ATLAS_SRC = pjoin('src', 'atlas-3.8.2')
ATLAS_BUILDDIR = os.path.join(ATLAS_SRC, "MyObj")
# Use INT_ETIME for lapack if building with gfortran
#TIMER = 'INT_ETIME'

def build_atlas_tarball():
    print "====== Building ATLAS tarbal ======"
    files = glob.glob(ATLAS_BUILDDIR + '/lib/*.a')
    fid = tarfile.open(ATLAS_TARBALL, 'w:bz2')
    try:
        for f in files:
            fid.add(f)
    finally:
        fid.close()

def build_atlas():
    print "====== Building ATLAS ======"
    p = Popen(['make'], cwd = ATLAS_BUILDDIR)
    os.waitpid(p.pid, 0)

def configure_atlas():
    print "====== Configuring ATLAS ======"
    if os.path.exists(ATLAS_BUILDDIR):
        shutil.rmtree(ATLAS_BUILDDIR)
    os.makedirs(ATLAS_BUILDDIR)
    p = Popen(['../configure',  '--with-netlib-lapack=%s' % LAPACK_LIB, '-C', 'if', FC], cwd = ATLAS_BUILDDIR)
    os.waitpid(p.pid, 0)

def build_lapack():
    print "====== Build LAPACK ======"
    p = Popen(["make", "lapacklib", "FORTRAN=%s" % FC, "LOADER=%s" % FC, "OPTS=%s" % LAPACK_F77_FLAGS], cwd = LAPACK_SRC)
    os.waitpid(p.pid, 0)

def clean_lapack():
    print "====== Clean LAPACK ======"
    p = Popen(['make', 'cleanlib'],  cwd = LAPACK_SRC)
    os.waitpid(p.pid, 0)

def clean_atlas():
    print "====== Clean ATLAS ======"
    if os.path.exists(ATLAS_BUILDDIR):
        shutil.rmtree(ATLAS_BUILDDIR)

def clean():
    clean_atlas()
    clean_lapack()

TARGETS = {'atlas' : [configure_atlas, build_atlas, build_atlas_tarball],
        'lapack' : build_lapack}

class Config(object):
    def __init__(self):
        self.arch = None
        self.cpuclass = 'i386'
        self.freq = 0
        self.pw = 32
        self.targets = ['blas', 'lapack']
        self.lapack_flags = ""
        self.f77 = 'g77'

    def __repr__(self):
        r = ["Cpu Configurations: "]
        r += ['\tArch: %s' % self.arch]
        r += ['\tCpu Class: %s' % self.cpuclass]
        r += ['\tFreq: %d MHz' % self.freq]
        r += ['\tPointer width: %d bits' % self.pw]
        r += ["Targets to build: %s" % str(self.targets)]
        return "\n".join(r)

def read_config(file):
    cfgp = ConfigParser()
    f = cfgp.read(file)
    if len(f) < 1:
        raise IOError("file %s not found" % file)

    cfg = Config() 
    if cfgp.has_section('CPU'):
        if cfgp.has_option('CPU', 'ARCH'):
            cfg.arch = cfgp.get('CPU', 'ARCH')
        if cfgp.has_option('CPU', 'CLASS'):
            cfg.cpuclass = cfgp.get('CPU', 'CLASS')
        if cfgp.has_option('CPU', 'MHZ'):
            cfg.freq = cfgp.getint('CPU', 'MHZ')
    if cfgp.has_section('BUILD_OPTIONS'):
        if cfgp.has_option('BUILD_OPTIONS', 'TARGETS'):
            cfg.targets = cfgp.get('BUILD_OPTIONS', 'TARGETS').split(',')
        if cfgp.has_option('BUILD_OPTIONS', 'F77'):
            cfg.f77 = cfgp.get('BUILD_OPTIONS', 'F77')
        if cfgp.has_option('BUILD_OPTIONS', 'LAPACK_F77FLAGS'):
            cfg.lapack_flags = " ".join(cfgp.get('BUILD_OPTIONS', 'LAPACK_F77FLAGS').split(','))

    return cfg

if __name__ == '__main__':
    try:
        cfg = read_config(pjoin(dirname(__file__), 'site.cfg'))
    except IOError:
        print "Using default config (site.cfg not found)"
        cfg = Config()

    ARCH = cfg.arch
    FC = cfg.f77
    LAPACK_F77_FLAGS = cfg.lapack_flags
    ATLAS_TARBALL = 'atlas-3.8.2-%s.tbz2' % ARCH

    clean()
    #for i in cfg.targets:
    #    TARGETS[i]()
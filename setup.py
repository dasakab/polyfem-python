import os
import re
import sys
# import sysconfig
import platform
import subprocess

from distutils.version import LooseVersion
from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext


class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=''):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext):
    def run(self):
        if platform.system() == 'Darwin':
            self.build_temp = self.build_temp.replace("build", "build.nosync")

        try:
            out = subprocess.check_output(['cmake', '--version'])
        except OSError:
            raise RuntimeError(
                "CMake must be installed to build the following extensions: , ".join(e.name for e in self.extensions))

        # self.debug = True

        cmake_version = LooseVersion(re.search(r'version\s*([\d.]+)', out.decode()).group(1))
        if cmake_version < '3.1.0':
            raise RuntimeError("CMake >= 3.1.0 is required")

        for ext in self.extensions:
            self.build_extension(ext)


    def build_extension(self, ext):
        extdir = os.path.join(os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name))),"polyfempy")

        cmake_args = ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + extdir,
                      '-DPYTHON_EXECUTABLE=' + sys.executable,
                      '-DENABLE_PARDISO=OFF',
                      '-DLIBIGL_WITH_OPENGL=OFF',
                      '-DLIBIGL_WITH_OPENGL_GLFW=OFF',
                      '-DLIBIGL_WITH_OPENGL_GLFW_IMGUI=OFF',
                      '-DLIBIGL_WITH_PNG=OFF',
                      '-DLIBIGL_WITH_PNG=OFF',
                      '-DLIBIGL_WITH_VIEWER=OFF',
                      '-DGEOGRAM_WITH_GRAPHICS=OFF',
                      '-DPOLYFEM_WITH_APPS=OFF',
                      '-DPOLYFEM_WITH_MISC=OFF']

        if platform.system() == 'Darwin':
            cmake_args.append('-DINPUT_THIRD_PARTY_DIR=3rdparty.nosync')


        cfg = 'Debug' if self.debug else 'Release'
        build_args = ['--config', cfg]

        if platform.system() == "Windows":
            cmake_args += ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{}={}'.format(cfg.upper(), extdir)]
            if sys.maxsize > 2**32:
                cmake_args += ['-A', 'x64']
            build_args += ['--', '/m:4']
        else:
            cmake_args += ['-DCMAKE_BUILD_TYPE=' + cfg]
            build_args += ['--', '-j2']

        env = os.environ.copy()
        env['CXXFLAGS'] = '{} -DVERSION_INFO=\\"{}\\"'.format(env.get('CXXFLAGS', ''),self.distribution.get_version())

        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)
        subprocess.check_call(['cmake', ext.sourcedir] + cmake_args, cwd=self.build_temp, env=env)

        subprocess.check_call(['cmake', '--build', '.'] + build_args, cwd=self.build_temp)

        print()  # Add an empty line for cleaner output


with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name="polyfempy",
    version="0.2.3",
    author="Teseo Schneider",
    author_email="",
    description="Polyfem Python Bindings",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://polyfem.github.io/",
    ext_modules=[CMakeExtension('polyfempy')],
    cmdclass=dict(build_ext=CMakeBuild),
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License"
    ],
    test_suite="test"
)

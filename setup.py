import os
from setuptools import setup, find_packages, Extension


camlipy_rollsum = Extension('camlipy._rollsum',
                            sources=['camlipy/rollsum_wrap.c', 'camlipy/rollsum.c'],
                            )


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='camlipy',
    version='0.1.1',
    author='Thomas Sileo',
    author_email='thomas.sileo@gmail.com',
    description='Unofficial Python client for Camlistore',
    license='MIT',
    keywords='camlistore storage backups blob',
    url='https://github.com/tsileo/camlipy',
    packages=find_packages(exclude=['ez_setup', 'tests', 'tests.*']),
    ext_modules=[camlipy_rollsum],
    long_description=read('README.rst'),
    install_requires=['dirtools', 'docopt', 'requests', 'ujson', 'futures'],
    test_requires=['sh'],
    test_suite="camlipy.tests",
    entry_points={'console_scripts': ['camlipy = camlipy.cli:main']},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: System :: Archiving :: Backup",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
    ],
    zip_safe=False,
)

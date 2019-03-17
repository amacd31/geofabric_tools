import os
import versioneer

from setuptools import setup


setup(
    name='geofabric_tools',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description='Python library for accessing the Australian Hydrological Geospatial Fabric (Geofabric).',
    author='Andrew MacDonald',
    author_email='andrew@maccas.net',
    license='BSD',
    url='https://github.com/amacd31/geofabric_tools',
    install_requires=[
        'gdal',
    ],
    packages=['geofabric_tools'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: BSD License',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)

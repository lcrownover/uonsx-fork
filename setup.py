import os

from setuptools import setup, find_namespace_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "uonsx",
    version = "0.1.4",
    author = "University of Oregon",
    author_email = "lcrown@uoregon.edu",
    description = ("Utilities to automate NSX-T DFW"),
    license = "BSD",
    url = "https://github.com/lcrownover/uonsx",
    package_dir={'uonsx': 'uonsx'},
    packages=find_namespace_packages(),
    long_description=read('README.md'),
    python_requires='>=3.7.5',
    entry_points = {
        'console_scripts': [ 'uonsx=uonsx.command_line.uonsx:cli', ],
    },
    install_requires = [
        'requests',
        'colorama',
        'click',
        'columnar',
        'typing_extensions',
        'pyyaml',
    ],
)

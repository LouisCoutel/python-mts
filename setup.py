import os
from codecs import open as codecs_open
from setuptools import setup, find_packages

from mts_handler import __version__

# Get the long description from the relevant file
with codecs_open("README.md", encoding="utf-8") as f:
    long_description = f.read()


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="python-mts",
    version=__version__,
    description="Backend Python tool to interact with Mapbox Tiling Service",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[],
    keywords="",
    author="LC",
    author_email="louiscoutel75@gmail.com",
    url="",
    license="BSD-2",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    install_requires=[
        "boto3",
        "numpy",
        "requests",
        "requests-toolbelt",
        "jsonschema~=3.0",
        "jsonseq~=1.0",
        "mercantile~=1.1.6",
        "geojson~=2.5.0",
    ],
    include_package_data=True,
    zip_safe=False,
    extras_require={
        "estimate-area": [
            "supermercado~=0.2.0",
        ],
    },
)

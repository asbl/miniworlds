from codecs import open
from os import path

from setuptools import setup, find_packages # type: ignore

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="miniworlds",
    version="3.1.0.1",
    description="Create 2D worlds and Games",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords=["games", "education", "mini-worlds", "pygame"],  # arbitrary keywords
    author="Andreas Siebel",
    author_email="andreas.siebel@it-teaching.de",
    url="https://github.com/asbl/miniworlds",
    download_url="https://github.com/asbl/miniworlds",
    license="OSI Approved :: MIT License",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Topic :: Education",
    ],
    packages=find_packages(
        exclude=["contrib", "docs", "tests", "examples"]
    ),  # Required
    package_dir={"miniworlds": "miniworlds"},
    install_requires=["pygame-ce", "numpy", ],
    include_package_data=True,
    package_data={"miniworlds": ["py.typed"]},
)

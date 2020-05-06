#!/usr/bin/python3
from distutils.core import setup
import qtobsmidi

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="Midi2OBSConfigurator", # Replace with your own username
    version="0.0.1",
    author="Christopher P Yarger",
    author_email="cpyarger@gmail.com",
    description="A small example package",
    url="https://github.com/cpyarger/Midi2OBS-Configurator",
    packages=['qtobsmidi'] ,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    
)

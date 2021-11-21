
from setuptools import setup, find_packages
import sys, os

setup(name='webcampak',
    version='3.0',
    description="Webcampak is a set of tools to reliably capture high definition pictures, at pre-defined interval, over a very long period of time and automatically generate timelapse videos. Built to scale and adapt to a variety of use cases, Webcampak will drive a DSLR camera from projects ranging from 6 months to years. Failsafe mechanisms are available to ensure no pictures get lost during that time.",
    long_description="Webcampak is a set of tools to reliably capture high definition pictures, at pre-defined interval, over a very long period of time and automatically generate timelapse videos. Built to scale and adapt to a variety of use cases, Webcampak will drive a DSLR camera from projects ranging from 6 months to years. Failsafe mechanisms are available to ensure no pictures get lost during that time.",
    classifiers=[],
    keywords='',
    author='Francois Gerthoffert',
    author_email='support@webcampak.com',
    url='http://www.webcampak.com/',
    license='GPL v3',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    test_suite='nose.collector',
    install_requires=[
        ### Required to build documentation
        # "Sphinx >= 1.0",
        ### Required for testing
        # "nose",
        # "coverage",
        ### Required to function
        'cement==2.10.4',
        ],
    setup_requires=[],
    entry_points="""
        [console_scripts]
        webcampak = webcampak.cli.main:main
    """,
    namespace_packages=[],
    )

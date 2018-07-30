import os
from setuptools import setup, find_packages

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name="kudago-mapper",
    version='0.1',
    description="Mapping external data to django models.",
    long_description="Generic, reusable class-based mappings from external data sources to your django models.",
    keywords="django, models, external data",
    author="Fedor Turbabin <fed.tf@yandex.ru>",
    author_email="fed.tf@yandex.ru",
    url="https://github.com/fed_tf/kudago-mapper/",
    license="BSD License",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Framework :: Django",
        "Framework :: Django :: 2.0"
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
    ],
)

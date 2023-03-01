#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.md') as history_file:
    history = history_file.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

test_requirements = ['pytest>=3', ]

setup(
    author="Robert Tu",
    author_email='tsy0716@gmail.com',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="A package to download and save jobs in Australian and New Zealand from SEEK.",
    install_requires=requirements,
    license="GNU General Public License v3",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='au_nz_jobs',
    name='au_nz_jobs',
    packages=find_packages(include=['au_nz_jobs', 'au_nz_jobs.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/tsy0716/au_nz_jobs',
    version='0.1.2',
    zip_safe=False,
    long_description_content_type='text/markdown',
)

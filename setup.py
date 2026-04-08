"""
Setup script for pandasv2 - Advanced Pandas for Web Applications

Installation: pip install -e .
PyPI deployment: twine upload dist/*

Built by Mahesh Makvana
"""

from setuptools import setup, find_packages
import os

# Read long description from README
def read_file(filename):
    path = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ''

setup(
    name='pandasv2',
    version='2.0.0',
    author='Mahesh Makvana',
    author_email='mahesh.makvana@example.com',
    description='Full pandas replacement with built-in JSON serialization and web framework integration',
    long_description=read_file('README.md'),
    long_description_content_type='text/markdown',
    url='https://github.com/maheshmakvana/pandasv2',
    project_urls={
        'Source': 'https://github.com/maheshmakvana/pandasv2',
        'Tracker': 'https://github.com/maheshmakvana/pandasv2/issues',
        'Documentation': 'https://github.com/maheshmakvana/pandasv2#readme',
    },
    license='MIT',
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=[
        'numpy>=1.20.0',
        'pandas>=1.3.0',
    ],
    extras_require={
        'fastapi': ['fastapi>=0.70.0'],
        'flask': ['flask>=2.0.0'],
        'django': ['django>=3.2'],
        'dev': ['pytest>=6.0', 'pytest-cov>=2.12.0'],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Office/Business',
        'Topic :: Scientific/Engineering :: Information Analysis',
    ],
    keywords=[
        'pandas',
        'json',
        'serialization',
        'fastapi',
        'flask',
        'django',
        'dataframe',
        'web',
        'api',
        'data-science',
    ],
    include_package_data=True,
    zip_safe=False,
)

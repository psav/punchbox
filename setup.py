# dummy for editable installs
from setuptools import setup, find_packages

setup(
    setup_requires=['pbr'],
    pbr=True,

    name='punchbox',

    entry_points={
        'console_scripts': [
            'punchbox = punchbox:main',
        ],
    },
    packages=find_packages(),
)

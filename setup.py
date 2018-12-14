# dummy for editable installs
from setuptools import find_packages
from setuptools import setup

setup(
    setup_requires=["pbr"],
    pbr=True,
    name="punchbox",
    entry_points={"console_scripts": ["punchbox = punchbox:main"]},
    packages=find_packages(),
    install_requires=["pre-commit", "click", "mido", "pbr", "PyYAML", "svgwrite"],
)

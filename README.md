punchbox
========

punchbox is a simple to use music box card creator. It will take a standard MIDI file and convert it into SVG files suitable for printing

Features
--------

* MIDI file reading
* Custom page size
* Reversible staves
* Custom music box definitions
* Automatic note transposition for best fit
* Multiple staves per page
* Cut markers with custom size
* Margin support

Coming soon:

* Gap analysis
* Note proximity


Example Render
--------------

![alt text](https://github.com/psav/punchbox/raw/master/mozart0.png "Example Render")

Usage
-----

To install, clone the repo, cd into it and then execute the following:

```
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install .
```

To get an example output, use
```
punchbox <yourfile.mid> --output <name>
```

And multiple svg files will be generated with `<name>.svg` and a numerical appendix

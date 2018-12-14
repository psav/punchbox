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

.. image:: https://github.com/psav/punchbox/raw/master/mozart0.png


Usage
-----

To install, clone the repo, and then execute the following:

```
virtualenv -p python2 .pb2
pip install -U pip
source .pb2/bin/activate
pip install .
```

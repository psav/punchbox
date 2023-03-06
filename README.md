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

Commandline options
-------------------

```
Usage: punchbox [OPTIONS] [FILENAME]

  Run punchbox on a file

Options:
  --output TEXT                Sets the output file name prefix (filenames
                               will have [0-9].mid appended)
  --name TEXT                  sets the name of the piece added to the output
                               sheets for identification
  --musicbox TEXT              choose from multiple music box configurations
                               from the yaml
  --marker-offset INTEGER      sets the offset for the cut marker lines (top +
                               bottom) in mm
  --marker-offset-top TEXT     sets the offset for the marker (top only), in
                               mm
  --marker-offset-bottom TEXT  sets the offset for the marker (bottom only),
                               in mm
  --marker-size INTEGER        sets the size of the cut marker, in mm
  --margin FLOAT               sets gap between two sheets on a page, in mm
  --font-size FLOAT            sets the font size, in mm
  --divisor FLOAT              adjustment variable to compress/expand time
                               (change tempo)
  --transpose-upper INTEGER    sets a limit on the upper transposition (avoids
                               high notes)
  --transpose-lower INTEGER    sets a limit on the lower transposition (avoids
                               high notes)
  --page-width FLOAT           sets page size width, in mm
  --page-height FLOAT          sets page size height, in mm
  --debug BOOLEAN              all the output
  --help                       Show this message and exit.
```

Note:
*****

Command line options should really be placed inside the punchbox.yaml file,
which can be edited freely. Options to configure the specific music box can be
inspected in the default config file. Command line variables always override
config file variables.

Currently the punchbox.yaml file config is not "configurable" if you are 
pulling a newer version of punchbox, backup your config file and delete the
`punchbox.yaml` file - this will be solved in an update soon.

```
boxen:
  35note:
    note_data: [60, 62, 67, 69, 71, 72, 74, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 98, 100]
    pitch: 2.0
    reverse: True
    note_collision: 5.0
divisor: 49.5
filename: mozart.mid
transpose:
    lower: -100
    upper: 100
page:
    width: 297.0
    height: 210.0
margin: 20.0
output: mozart
font_size: 1.0
marker_offset: 6
marker_size: 5
default_musicbox: 35note
```
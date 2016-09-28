import svgwrite
import math
import yaml
from collections import defaultdict
from mido import MidiFile

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def mm(val):
    return "{}mm".format(val)


def cross(dwg, size, x, y):
    hs = size / 2.0
    dwg.add(
        dwg.line((mm(y - hs), mm(x)), (mm(y + hs), mm(x)),
            stroke=svgwrite.rgb(0, 0, 0, '%'), stroke_width=".1mm")
    )
    dwg.add(
        dwg.line((mm(y), mm(x - hs)), (mm(y), mm(x + hs)),
            stroke=svgwrite.rgb(0, 0, 0, '%'), stroke_width=".1mm")
    )


def note_name(val):
    mod = val % 12
    name = "{}{}".format(NOTE_NAMES[mod], (val / 12) - 2)
    return name


with open('punchbox.yaml') as f:
    config = yaml.load(f)
print config
note_data = config['note_data']

if config['reverse']:
    note_data = note_data[::-1]

divisor = config['divisor']
pitch = config['pitch']
font_size = config['font_size']
margin = config['margin']
marker_offset = config['marker_offset']
marker_size = config['marker_size']
filename = config['filename']
notes = []
with MidiFile(filename) as midi_file:
    transpose = range(config['transpose']['lower'], config['transpose']['upper'])
    best_transpose = (0, 0)
    written = False
    for trans in transpose:
        unavail = defaultdict(int)
        avail = defaultdict(int)
        tpos = 0
        tneg = 0
        count = 0
        for i, track in enumerate(midi_file.tracks):
            time = 0
            for message in track:
                time += message.time
                if message.type == "note_on":
                    count += 1
                    if message.velocity == 0:
                        continue
                    if not written:
                        notes.append((message.note, time))
                    if (message.note + trans) in note_data:
                        tpos += 1
                        avail[note_name(message.note)] += 1
                    else:
                        tneg += 1
                        unavail[note_name(message.note)] += 1
        written = True
        percen = tpos / float(tpos + tneg)
        if percen > best_transpose[1]:
            print "Transposition Candidate Report"
            print "Transposition: {}".format(trans)
            print "Total Notes: {}".format(count)
            print "Notes OK: {}".format(tpos)
            print "Distinct Notes Missing: {}".format(len(unavail))
            print "Total Notes Missing: {}".format(tneg)
            print "Unavailables: {}".format(unavail)
            print "========================================"
            best_transpose = (trans, percen)
        if percen == 1:
            print "PERFECT Transposition Found"
            break
print best_transpose
max_time = max([p[1] for p in notes])
notes = sorted(notes, key=lambda p: p[1])
max_length = max_time / divisor

stave_width = (len(note_data) - 1) * pitch + margin
staves_per_page = int(math.floor((config['page']['height'] - margin) / (stave_width)))

max_stave_length = config['page']['width'] - (margin * 2)

no_staves_required = int(math.ceil(max_length / max_stave_length))

pages = int(math.ceil(no_staves_required / staves_per_page))

no_staves = 0
offset = 0
for page in range(pages):
    print page

    dwg = svgwrite.Drawing("{}{}.svg".format(config['output'], str(page)),
        size=(mm(config['page']['width']), mm(config['page']['height'])))

    for stave in range(staves_per_page):
        max_time = ((page * staves_per_page) + stave) * max_stave_length + max_stave_length
        offset_time = max_time - max_stave_length
        if no_staves > no_staves_required:
            break

        line_offset = (stave * (stave_width)) + margin
        cross(dwg, marker_size, line_offset - marker_offset, margin + max_stave_length)
        cross(dwg, marker_size,
            line_offset + stave_width - margin + marker_offset, margin + max_stave_length)
        cross(dwg, marker_size, line_offset - marker_offset, margin)
        cross(dwg, marker_size, line_offset + stave_width - margin + marker_offset, margin)
        dwg.add(dwg.text('STAVE {}'.format((page * staves_per_page) + stave),
            insert=(mm(margin * 2),
                mm(line_offset + stave_width - margin + marker_offset)),
            fill='blue', font_size=mm(font_size))
        )
        for i, note in enumerate(note_data):
            line_x = (i * pitch) + line_offset
            dwg.add(
                dwg.line((mm(margin), mm(line_x)), (mm(max_stave_length + margin), mm(line_x)),
                    stroke=svgwrite.rgb(0, 0, 0, '%'), stroke_width=".1mm")
            )
            dwg.add(dwg.text(note_name(note), insert=(mm(-2 + margin), mm(line_x + font_size / 2)),
                             fill='red', font_size=mm(font_size)))

        for note in notes[offset:]:
            offset += 1
            try:
                note_pos = note_data.index(note[0] + best_transpose[0])
                note_time = (note[1] / divisor) - offset_time

                if note_time > max_stave_length:
                    offset = offset - 1
                    break
                dwg.add(
                    dwg.circle(
                        (mm(note_time + margin),
                         mm((note_pos * pitch) + line_offset)),
                        "1mm"))
            except:
                continue
                print "couldn't add note"
    dwg.save()

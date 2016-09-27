import svgwrite
import math
import yaml
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
    return "{}{}".format(NOTE_NAMES[note % 12], val / 12)


with open('punchbox.yaml') as f:
    config = yaml.load(f)
print config
note_data = config['note_data']
divisor = config['divisor']
pitch = config['pitch']
font_size = config['font_size']
margin = config['margin']

for note in note_data:
    print note_name(note)

filename = config['filename']
notes = []
with MidiFile(filename) as midi_file:
    transpose = range(config['transpose']['lower'], config['transpose']['upper'])
    best_transpose = (0, 0)
    written = False
    for trans in transpose:
        tpos = 0
        tneg = 0
        for i, track in enumerate(midi_file.tracks):
            time = 0
            for message in track:
                time += message.time
                if message.type == "note_on":
                    if message.velocity == 0:
                        continue
                    if not written:
                        notes.append((message.note, time))
                    if (message.note + trans) in note_data:
                        tpos += 1
                    else:
                        tneg += 1
        written = True
        percen = tpos / float(tpos + tneg)
        if percen > best_transpose[1]:
            best_transpose = (trans, percen)
        if percen == 1:
            break
print best_transpose
max_time = max([p[1] for p in notes])
notes = sorted(notes, key=lambda p: p[1])
max_length = max_time / divisor

stave_width = len(note_data) * pitch + margin
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
        max_time = (page * stave * max_stave_length) + (stave * max_stave_length) + max_stave_length
        offset_time = max_time - max_stave_length
        print "---------", stave, max_time
        if no_staves > no_staves_required:
            break

        line_offset = (stave * (stave_width)) + margin
        cross(dwg, 5, line_offset - 5, margin + max_stave_length)
        cross(dwg, 5, line_offset + stave_width - margin + 5, margin + max_stave_length)
        cross(dwg, 5, line_offset - 5, margin)
        cross(dwg, 5, line_offset + stave_width - margin + 5, margin)
        for i, note in enumerate(note_data):
            line_x = (i * pitch) + line_offset
            dwg.add(
                dwg.line((mm(margin), mm(line_x)), (mm(max_stave_length + margin), mm(line_x)),
                    stroke=svgwrite.rgb(0, 0, 0, '%'), stroke_width=".1mm")
            )
            dwg.add(dwg.text(note_name(note), insert=(mm(-2 + margin), mm(line_x + font_size / 2)),
                fill='red', font_size='{}mm'.format(font_size)))

        for note in notes[offset:]:
            print offset, len(notes)
            offset += 1
            try:
                note_pos = note_data.index(note[0] + best_transpose[0])
                note_time = (note[1] / divisor) - offset_time
                if note_time > max_time:
                    offset = offset - 1
                    break
                dwg.add(
                    dwg.circle(
                        ("{}mm".format(note_time + margin),
                         "{}mm".format((note_pos * pitch) + line_offset)),
                        "1mm"))
            except:
                print "couldn't add note"
    dwg.save()

import click
import svgwrite
import math
import yaml
from collections import defaultdict
from mido import MidiFile

with open('punchbox.yaml') as f:
    config = yaml.load(f)

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


@click.command(help="Run punchbox on a file")
@click.argument('filename', default=config.get('filename'))
@click.option('--output', default=config.get('output', 'output'))
@click.option('--musicbox', default=config.get('default_musicbox'))
@click.option('--marker-offset', default=config.get('marker_offset', 6))
@click.option('--marker-offset-top', default=config.get('marker_offset_top', None))
@click.option('--marker-offset-bottom', default=config.get('marker_offset_bottom', None))
@click.option('--marker-size', default=config.get('marker_size', 5))
@click.option('--margin', default=config.get('margin', 20))
@click.option('--font-size', default=config.get('font_size', 1.0))
@click.option('--divisor', default=config.get('divisor', 67.0))
@click.option('--transpose-upper', default=config.get('transpose', {}).get('upper', 100))
@click.option('--transpose-lower', default=config.get('transpose', {}).get('lower', -100))
@click.option('--page-width', default=config.get('page', {}).get('width', 297.0))
@click.option('--page-height', default=config.get('page', {}).get('height', 210.0))
@click.option('--debug', default=False)
def main(filename, output, musicbox, marker_offset, marker_offset_top, marker_offset_bottom,
         marker_size, margin, font_size, divisor, debug,
         transpose_upper, transpose_lower, page_width, page_height):
    note_data = config['boxen'][musicbox].get('note_data',
                                              [60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72])
    reverse = config['boxen'][musicbox].get('reverse', False)
    pitch = config['boxen'][musicbox].get('pitch', 2)

    if reverse:
        note_data = note_data[::-1]

    divisor = float(divisor)
    font_size = float(font_size)
    page_width = float(page_width)
    page_height = float(page_height)

    mark_top = float(marker_offset_top or marker_offset)
    mark_btm = float(marker_offset_bottom or marker_offset)

    notes = []
    with MidiFile(filename) as midi_file:
        transpose = range(transpose_lower, transpose_upper)
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
                        if message.velocity == 0:
                            continue
                        count += 1
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
                if debug:
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
    print "TRANSPOSE: {}".format(best_transpose[0])
    print "PERCENTAGE HIT: {}%".format(best_transpose[1] * 100)
    max_time = max([p[1] for p in notes])
    notes = sorted(notes, key=lambda p: p[1])
    max_length = max_time / divisor
    print "MAX LENGTH: {}".format(max_length)

    stave_width = (len(note_data) - 1) * pitch + margin
    staves_per_page = int(math.floor((page_height - margin) / (stave_width)))

    max_stave_length = page_width - (margin * 2)
    print "MAX STAVE LENGTH: {}".format(max_stave_length)
    no_staves_required = int(math.ceil(max_length / max_stave_length))
    print "NO STAVES: {}".format(no_staves_required)

    pages = int(math.ceil(float(no_staves_required) / staves_per_page))
    print "PAGES: {}".format(pages)

    no_staves = 0
    offset = 0
    for page in range(pages):
        print "Writing page {}..".format(page)

        dwg = svgwrite.Drawing("{}{}.svg".format(output, str(page)),
            size=(mm(page_width), mm(page_height)))

        for stave in range(staves_per_page):
            max_time = ((page * staves_per_page) + stave) * max_stave_length + max_stave_length
            offset_time = max_time - max_stave_length
            if no_staves > no_staves_required:
                break

            line_offset = (stave * (stave_width)) + margin
            cross(dwg, marker_size, line_offset - mark_top, margin + max_stave_length)
            cross(dwg, marker_size,
                line_offset + stave_width - margin + mark_btm, margin + max_stave_length)
            cross(dwg, marker_size, line_offset - mark_top, margin)
            cross(dwg, marker_size, line_offset + stave_width - margin + mark_btm, margin)
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
                dwg.add(dwg.text(
                    note_name(note), insert=(mm(-2 + margin), mm(line_x + font_size / 2)),
                    fill='red', font_size=mm(font_size)))

            for note in notes[offset:]:
                offset += 1
                try:
                    note_pos = note_data.index(note[0] + best_transpose[0])
                    fill = "black"
                except:
                    for i, dta in enumerate(note_data[::-1] if reverse else note_data):
                        #print note[0] + best_transpose[0], dta
                        if note[0] + best_transpose[0] > dta:
                            continue
                        else:
                            break
                    note_pos = note_data.index(dta)
                    fill = "red"
                note_time = (note[1] / divisor) - offset_time

                if note_time > max_stave_length:
                    offset = offset - 1
                    break
                dwg.add(
                    dwg.circle(
                        (mm(note_time + margin),
                         mm((note_pos * pitch) + line_offset)),
                        "1mm", fill=fill))
        dwg.save()
        if best_transpose[1] != 1:
            print "PERFECT TRANSPOSITION NOT FOUND!"


if __name__ == '__main__':
    main()

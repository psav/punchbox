import math
from collections import defaultdict

import click
import svgwrite
import yaml
from mido import MidiFile


with open("punchbox.yaml") as f:
    config = yaml.safe_load(f)

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
DEBUG = False


def mm(val):
    return "{}mm".format(val)


def cross(dwg, size, x, y):
    hs = size / 2.0
    dwg.add(
        dwg.line(
            (mm(y - hs), mm(x)),
            (mm(y + hs), mm(x)),
            stroke=svgwrite.rgb(0, 0, 0, "%"),
            stroke_width=".1mm",
        )
    )
    dwg.add(
        dwg.line(
            (mm(y), mm(x - hs)),
            (mm(y), mm(x + hs)),
            stroke=svgwrite.rgb(0, 0, 0, "%"),
            stroke_width=".1mm",
        )
    )


def note_name(val):
    mod = val % 12
    name = "{}{}".format(NOTE_NAMES[mod], (val / 12) - 2)
    return name


def get_notes_from_midi(filename, transpose_lower, transpose_upper, note_data, tracks=range(16)):
    notes = []
    notes_use = defaultdict(int)
    with MidiFile(filename) as midi_file:
        transpose = range(transpose_lower, transpose_upper)
        best_transpose = (0, 0)
        written = False
        for i, track in enumerate(midi_file.tracks):
            if i not in tracks:
                continue
            time = 0
            track_count = 0
            for message in track:
                time += message.time
                if message.type == "note_on":
                    if message.velocity == 0:
                        continue
                    if not written:
                        notes.append((message.note, time))
                        notes_use[message.note] += 1
                    track_count += 1
            if DEBUG:
                print("Track {}: {} note_on messages processed".format(i, track_count))

    notes = sorted(notes, key=lambda p: p[1])

    best_transpose = (0, 0)
    for trans in transpose:
        avail = sum([freq for note, freq in notes_use.items() if note + trans in note_data])
        unavail = {
            note_name(note): freq
            for note, freq in notes_use.items()
            if note + trans not in note_data
        }
        percen = avail / float(len(notes))
        if percen == 1:
            best_transpose = (trans, 1)
            print("PERFECT TRANSPOSITION FOUND")
        elif percen > best_transpose[1]:
            if DEBUG:
                print("Transposition Candidate Report")
                print("Transposition: {}".format(trans))
                print("Total Notes: {}".format(len(notes)))
                print("Notes OK: {}".format(avail))
                print("Distinct Notes Missing: {}".format(len(unavail)))
                print("Total Notes Missing: {}".format(len(notes) - avail))
                print("Unavailables: {}".format(unavail))
                print("========================================")
            best_transpose = (trans, percen)
    return notes, best_transpose


def create_staves(
    filename,
    output,
    musicbox,
    marker_offset,
    marker_offset_top,
    marker_offset_bottom,
    marker_size,
    margin,
    font_size,
    divisor,
    debug,
    name,
    transpose_upper,
    transpose_lower,
    page_width,
    page_height,
):
    global DEBUG
    DEBUG = debug
    name = name or filename
    music_box = MusicBox(config["boxen"][musicbox])

    divisor = float(divisor)
    font_size = float(font_size)
    page_width = float(page_width)
    page_height = float(page_height)

    mark_top = float(marker_offset_top or marker_offset)
    mark_btm = float(marker_offset_bottom or marker_offset)

    notes, best_transpose = get_notes_from_midi(
        filename, transpose_lower, transpose_upper, music_box.note_data
    )

    min_note_distance = {}
    for note, ntime in notes:
        if note not in min_note_distance:
            min_note_distance[note] = [ntime, None]
        else:
            diff = ntime - min_note_distance[note][0]
            if min_note_distance[note][1] is None:
                min_note_distance[note][1] = diff
            elif min_note_distance[note][1] > diff:
                min_note_distance[note][1] = diff
            min_note_distance[note][0] = ntime

    min_distance = min([v[1] for v in min_note_distance.values() if v[1] is not None])
    print("MINIMUM NOTE DISTANCE: {}".format(min_distance / divisor))
    if min_distance / divisor < music_box.note_collision:
        print(
            "WARNING: SOME NOTES MAY NOT PLAY!! "
            "{}mm note distance is less than {}mm REQUIRED".format(
                min_distance / divisor, music_box.note_collision
            )
        )

    print("TRANSPOSE: {}".format(best_transpose[0]))
    print("PERCENTAGE HIT: {}%".format(best_transpose[1] * 100))
    max_time = max([p[1] for p in notes])
    notes = sorted(notes, key=lambda p: p[1])
    max_length = max_time / divisor
    print("MAX LENGTH: {}".format(max_length))

    stave_width = (len(music_box.note_data) - 1) * music_box.pitch + margin
    staves_per_page = int(math.floor((page_height - margin) / (stave_width)))

    max_stave_length = page_width - (margin * 2)
    print("MAX STAVE LENGTH: {}".format(max_stave_length))
    no_staves_required = int(math.ceil(max_length / max_stave_length))
    print("NO STAVES: {}".format(no_staves_required))

    pages = int(math.ceil(float(no_staves_required) / staves_per_page))
    print("PAGES: {}".format(pages))

    no_staves = 0
    offset = 0
    for page in range(pages):
        print("Writing page {}..".format(page))

        dwg = svgwrite.Drawing(
            "{}{}.svg".format(output, str(page)), size=(mm(page_width), mm(page_height))
        )

        for stave in range(staves_per_page):
            max_time = ((page * staves_per_page) + stave) * max_stave_length + max_stave_length
            offset_time = max_time - max_stave_length
            if no_staves > no_staves_required:
                break

            line_offset = (stave * (stave_width)) + margin
            cross(dwg, marker_size, line_offset - mark_top, margin + max_stave_length)
            cross(
                dwg,
                marker_size,
                line_offset + stave_width - margin + mark_btm,
                margin + max_stave_length,
            )
            cross(dwg, marker_size, line_offset - mark_top, margin)
            cross(dwg, marker_size, line_offset + stave_width - margin + mark_btm, margin)
            dwg.add(
                dwg.text(
                    "STAVE {} - {}".format((page * staves_per_page) + stave, name),
                    insert=(mm(margin * 2), mm(line_offset + stave_width - margin + marker_offset)),
                    fill="blue",
                    font_size=mm(font_size),
                )
            )
            for i, note in enumerate(music_box.note_data):
                line_x = (i * music_box.pitch) + line_offset
                dwg.add(
                    dwg.line(
                        (mm(margin), mm(line_x)),
                        (mm(max_stave_length + margin), mm(line_x)),
                        stroke=svgwrite.rgb(0, 0, 0, "%"),
                        stroke_width=".1mm",
                    )
                )
                dwg.add(
                    dwg.text(
                        note_name(note),
                        insert=(mm(-2 + margin), mm(line_x + font_size / 2)),
                        fill="red",
                        font_size=mm(font_size),
                    )
                )

            for note in notes[offset:]:
                offset += 1
                try:
                    note_pos = music_box.note_data.index(note[0] + best_transpose[0])
                    fill = "black"
                except Exception as e:
                    print(e)
                    for i, dta in enumerate(
                        music_box.note_data[::-1] if music_box.reverse else music_box.note_data
                    ):
                        if note[0] + best_transpose[0] > dta:
                            continue
                        else:
                            break
                    note_pos = music_box.note_data.index(dta)
                    fill = "red"
                note_time = (note[1] / divisor) - offset_time

                if note_time > max_stave_length:
                    offset = offset - 1
                    break
                dwg.add(
                    dwg.circle(
                        (mm(note_time + margin), mm((note_pos * music_box.pitch) + line_offset)),
                        "1mm",
                        fill=fill,
                    )
                )
        dwg.save()
        if best_transpose[1] != 1:
            print("PERFECT TRANSPOSITION NOT FOUND!")


class MusicBox(object):
    def __init__(self, config):
        self.note_data = config.get(
            "note_data", [60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72]
        )
        self.reverse = config.get("reverse", False)
        self.pitch = config.get("pitch", 2.0)
        self.note_collision = config.get("note_collision", 5.0)
        if self.reverse:
            self.note_data = self.note_data[::-1]


@click.command(help="Run punchbox on a file")
@click.argument("filename", default=config.get("filename"))
@click.option("--output", default=config.get("output", "output"), help="Sets the output file name prefix (filenames will have [0-9].mid appended)")
@click.option("--name", default=config.get("name"), help="sets the name of the piece added to the output sheets for identification")
@click.option("--musicbox", default=config.get("default_musicbox"), help="choose from multiple music box configurations from the yaml")
@click.option("--marker-offset", default=config.get("marker_offset", 6), help="sets the offset for the cut marker lines (top + bottom) in mm")
@click.option("--marker-offset-top", default=config.get("marker_offset_top", None), help="sets the offset for the marker (top only), in mm")
@click.option("--marker-offset-bottom", default=config.get("marker_offset_bottom", None), help="sets the offset for the marker (bottom only), in mm")
@click.option("--marker-size", default=config.get("marker_size", 5), help="sets the size of the cut marker, in mm")
@click.option("--margin", default=config.get("margin", 20), help="sets gap between two sheets on a page, in mm")
@click.option("--font-size", default=config.get("font_size", 1.0),help="sets the font size, in mm")
@click.option("--divisor", default=config.get("divisor", 67.0),help="adjustment variable to compress/expand time (change tempo)")
@click.option("--transpose-upper", default=config.get("transpose", {}).get("upper", 100), help="sets a limit on the upper transposition (avoids high notes)")
@click.option("--transpose-lower", default=config.get("transpose", {}).get("lower", -100), help="sets a limit on the lower transposition (avoids high notes)")
@click.option("--page-width", default=config.get("page", {}).get("width", 297.0), help="sets page size width, in mm")
@click.option("--page-height", default=config.get("page", {}).get("height", 210.0), help="sets page size height, in mm")
@click.option("--debug", default=False, help="all the output")
def main(
    filename,
    output,
    musicbox,
    marker_offset,
    marker_offset_top,
    marker_offset_bottom,
    marker_size,
    margin,
    font_size,
    divisor,
    debug,
    name,
    transpose_upper,
    transpose_lower,
    page_width,
    page_height,
):

    create_staves(
        filename,
        output,
        musicbox,
        marker_offset,
        marker_offset_top,
        marker_offset_bottom,
        marker_size,
        margin,
        font_size,
        divisor,
        debug,
        name,
        transpose_upper,
        transpose_lower,
        page_width,
        page_height,
    )


if __name__ == "__main__":
    main()

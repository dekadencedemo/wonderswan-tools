#!/usr/bin/env python3


import click
import struct
import sys

from collections import namedtuple


ModChannelRow = namedtuple('ModChannelRow', ['period', 'sample', 'effect', 'effect_value'])
ModPatternRow = namedtuple('ModPatternRow', ['channel_rows'])
ModPattern = namedtuple('ModPattern', ['rows'])
ModSong = namedtuple('ModSong', ['patterns'])
Mod = namedtuple('Mod', ['song', 'positions'])

period_map = {
    # no note
    0: 0x0,
    # c-1 to b-1
    856: 0x1, 808: 0x2, 762: 0x3, 720: 0x4, 678: 0x5, 640: 0x6, 604: 0x7, 570: 0x8, 538: 0x9, 508: 0xa, 480: 0xb, 453: 0xc,
    # c-2 to b-2
    428: 0xd, 404: 0xe, 381: 0xf, 360: 0x10, 339: 0x11, 320: 0x12, 302: 0x13, 285: 0x14, 269: 0x15, 254: 0x16, 240: 0x17, 226: 0x18,
    # c-3 to b-3
    214: 0x19, 202: 0x1a, 190: 0x1b, 180: 0x1c, 170: 0x1d, 160: 0x1e, 151: 0x1f, 143: 0x20, 135: 0x21, 127: 0x22, 120: 0x23, 113: 0x24
}


def parse_mod_channel_rows(mod_bytes, pattern_index, row_index):
    channel_rows = []
    channel_count = 4
    patterns_start = 1084
    pattern_length = 1024
    row_length = 16
    channel_length = 4

    for channel_index in range(0, channel_count):
        index = patterns_start + (pattern_index * pattern_length) + (row_index * row_length) + (channel_index * channel_length)
        channel_row_bytes = struct.unpack('BBBB', mod_bytes[index:index + channel_length])
        sample = (channel_row_bytes[0] & 0xf0) + ((channel_row_bytes[2] & 0xf0) >> 4)
        period = ((channel_row_bytes[0] & 0xf) << 8) + channel_row_bytes[1]
        effect = channel_row_bytes[2] & 0xf
        # TODO: Add parsing for effect 0 and 14.
        effect_value = channel_row_bytes[3]

        channel_rows.append(ModChannelRow(period, sample, effect, effect_value))

    return ModPatternRow(channel_rows)


def parse_pattern_rows(mod_bytes, pattern_index):
    rows = []
    pattern_length = 64

    for row_index in range(0, pattern_length):
        rows.append(parse_mod_channel_rows(mod_bytes, pattern_index, row_index))

    return ModPattern(rows)


def parse_patterns(mod_bytes, max_pattern):
    patterns = []

    for pattern_index in range(0, max_pattern):
        patterns.append(parse_pattern_rows(mod_bytes, pattern_index))

    return ModSong(patterns)


def parse_mod(input_mod):
    with open(input_mod, mode='rb') as file:
        mod_bytes = file.read()

    mk_header_start = 1080
    mk_header_length = 4
    mk_header = struct.unpack('4s', mod_bytes[mk_header_start:mk_header_start + mk_header_length])[0].decode('ascii')

    if mk_header != 'M.K.':
        sys.exit('not a valid mod file')

    title_start = 0
    title_length = 20
    mod_title = struct.unpack('20s', mod_bytes[title_start:title_length])[0].decode('ascii')

    position_start = 950
    position_length = 1
    position_count = struct.unpack('B', mod_bytes[position_start:position_start + position_length])[0]

    positions_start = 952
    positions = struct.unpack('B' * position_count, mod_bytes[positions_start:positions_start + position_count])

    max_pattern = max(positions)

    print('title: {}'.format(mod_title))
    print('position count: {}'.format(position_count))
    print('positions: {}'.format(positions))
    print('max pattern: {}'.format(max_pattern))

    song = parse_patterns(mod_bytes, max_pattern)

    return Mod(song, positions)


def write_ws_file(mod, output_file):
    ws_bytes = bytearray()

    # 32 byte header, actual content TBD
    for _ in range(0, 32):
        ws_bytes.append(0)

    # 31 x 32 byte instruments, actual content TBD
    for _ in range(0, 31):
        for _ in range(0, 32):
            ws_bytes.append(0)

    # 256 byte order list, 0xff = end of list
    for position_index in range(0, 256):
        max_position = len(mod.positions) - 1

        if position_index <= max_position:
            ws_bytes.append(mod.positions[position_index])
        else:
            ws_bytes.append(0xff)

    # ?? x 1024 byte patterns, 64 rows per pattern, 16 bytes per row
    for pattern_index, pattern in enumerate(mod.song.patterns):
        for row_index, row in enumerate(pattern.rows):
            for channel_index, channel_row in enumerate(row.channel_rows):
                if channel_row.period in period_map:
                    ws_bytes.append(period_map[channel_row.period])
                else:
                    print('error on pattern {}, row {}, channel {}: unknown period {}'.format(pattern_index, row_index, channel_index, channel_row.period))
                    ws_bytes.append(0)

                ws_bytes.append(channel_row.sample)
                ws_bytes.append(channel_row.effect)
                ws_bytes.append(channel_row.effect_value)

    with open(output_file, mode='wb') as file:
        file.write(ws_bytes)


@click.command()
@click.argument('input_mod')
@click.argument('output_file')
@click.option('--debug', is_flag=True)
def convert(input_mod, output_file, debug):
    mod = parse_mod(input_mod)

    if debug:
        print()

        for pattern_index, pattern in enumerate(mod.patterns):
            print('pattern {}:'.format(pattern_index))

            for row_index, row in enumerate(pattern.rows):
                print('row {}:'.format(row_index))

                for channel_index, channel in enumerate(row.channel_rows):
                    print('channel {}: {}'.format(channel_index, channel))
    
    write_ws_file(mod, output_file)


if __name__ == "__main__":
    convert()

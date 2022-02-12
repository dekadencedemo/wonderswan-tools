#!/usr/bin/env python3


import click
import struct
import sys

from collections import namedtuple


ModChannelRow = namedtuple('ModChannelRow', ['period', 'sample', 'effect', 'effect_value'])
ModPatternRow = namedtuple('ModPatternRow', ['channel_rows'])
ModPattern = namedtuple('ModPattern', ['rows'])
ModSong = namedtuple('ModSong', ['patterns'])


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

    return parse_patterns(mod_bytes, max_pattern)


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


if __name__ == "__main__":
    convert()

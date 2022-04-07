#!/usr/bin/env python3


import click
import struct
import sys

from collections import namedtuple


ModSample = namedtuple('ModSample', ['name', 'length', 'finetune', 'volume', 'repeat_start', 'repeat_length', 'data'])
ModChannelRow = namedtuple('ModChannelRow', ['period', 'sample', 'effect', 'effect_value'])
ModPatternRow = namedtuple('ModPatternRow', ['channel_rows'])
ModPattern = namedtuple('ModPattern', ['rows'])
ModSong = namedtuple('ModSong', ['patterns'])
Mod = namedtuple('Mod', ['song', 'positions', 'samples'])

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
repeat_lengths = [128, 64, 32, 16]
patterns_start = 1084
pattern_length = 1024


def parse_mod_channel_rows(mod_bytes, pattern_index, row_index):
    channel_rows = []
    channel_count = 4
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

    for pattern_index in range(0, max_pattern + 1):
        patterns.append(parse_pattern_rows(mod_bytes, pattern_index))

    return ModSong(patterns)


def parse_samples(mod_bytes, max_pattern):
    sample_header_start = 20
    sample_header_offset = 30
    position = sample_header_start
    name_length = 22
    sample_length_offset = name_length
    sample_length_length = 2
    finetune_offset = sample_length_offset + sample_length_length
    finetune_length = 1
    volume_offset = finetune_offset + finetune_length
    volume_length = 1
    repeat_start_offset = volume_offset + volume_length
    repeat_start_length = 2
    repeat_length_offset = repeat_start_offset + repeat_start_length
    repeat_length_length = 2
    samples = []
    sample_data_position = patterns_start + ((max_pattern + 1) * pattern_length)

    for _ in range(0, 31):
        name_start = position
        name_end = name_start + name_length
        name = struct.unpack('22s', mod_bytes[name_start:name_end])[0].decode('ascii').rstrip('\x00')

        length_start = position + sample_length_offset
        length_end = length_start + sample_length_length
        length = struct.unpack('>H', mod_bytes[length_start:length_end])[0] * 2

        finetune_start = position + finetune_offset
        finetune_end = finetune_start + finetune_length
        finetune = struct.unpack('B', mod_bytes[finetune_start:finetune_end])[0] & 0b1111

        volume_start = position + volume_offset
        volume_end = volume_start + volume_length
        volume = struct.unpack('B', mod_bytes[volume_start:volume_end])[0]

        repeat_start_start = position + repeat_start_offset
        repeat_start_end = repeat_start_start + repeat_start_length
        repeat_start = struct.unpack('>H', mod_bytes[repeat_start_start:repeat_start_end])[0] * 2

        repeat_length_start = position + repeat_length_offset
        repeat_length_end = repeat_length_start + repeat_length_length
        repeat_length = struct.unpack('>H', mod_bytes[repeat_length_start:repeat_length_end])[0] * 2

        if length > 0:
            sample_data = struct.unpack('{}B'.format(length), mod_bytes[sample_data_position:sample_data_position + length])
            sample_data_position += length
        else:
            sample_data = bytes(0)

        sample = ModSample(name, length, finetune, volume, repeat_start, repeat_length, sample_data)

        samples.append(sample)

        position += sample_header_offset

    return samples


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
    samples = parse_samples(mod_bytes, max_pattern)

    return Mod(song, positions, samples)


def write_ws_file(mod, output_file):
    ws_bytes = bytearray()

    # 32 byte header, actual content TBD
    for _ in range(0, 32):
        ws_bytes.append(0)

    # 31 x 32 byte instruments, actual content TBD
    for sample_index in range(0, 31):
        sample = mod.samples[sample_index]

        if sample.length > 0 and sample.repeat_length not in repeat_lengths:
            print('error in sample {}: repeat length should be one of the following: {}'.format(sample_index, repeat_lengths))

        ws_bytes.append(sample.volume)

        # insert blank data for now
        for _ in range(0, 15):
            ws_bytes.append(0)
        
        smp = sample.data
        rep_start = sample.repeat_start
        # convert samples to signed and store highest 4 bits
        # TODO: implement optional interpolation
        if sample.repeat_length == 16:
            for byte_index in range(0, 16):
                lo_sample = smp[rep_start + byte_index] + 0x80
                hi_sample = lo_sample
                ws_bytes.append((hi_sample & 0xf0) | ((lo_sample >> 4) & 0x0f))
        elif sample.repeat_length == 32:
            for byte_index in range(0, 16):
                # convert to signed and store highest 4 bits
                hi_sample = smp[rep_start + byte_index * 2 + 1] + 0x80
                lo_sample = smp[rep_start + byte_index * 2] + 0x80
                ws_bytes.append((hi_sample & 0xf0) | ((lo_sample >> 4) & 0x0f))
        elif sample.repeat_length == 64:
            for byte_index in range(0, 16):
                # convert to signed and store highest 4 bits
                hi_sample = smp[rep_start + byte_index * 4 + 2] + 0x80
                lo_sample = smp[rep_start + byte_index * 4] + 0x80
                ws_bytes.append((hi_sample & 0xf0) | ((lo_sample >> 4) & 0x0f))
        elif sample.repeat_length == 128:
            for byte_index in range(0, 16):
                # convert to signed and store highest 4 bits
                hi_sample = smp[rep_start + byte_index * 8 + 4] + 0x80
                lo_sample = smp[rep_start + byte_index * 8] + 0x80
                ws_bytes.append((hi_sample & 0xf0) | ((lo_sample >> 4) & 0x0f))
        else:
            for _ in range(0, 16):
                ws_bytes.append(0)

    # 256 byte order list, 0xff = end of list
    for position_index in range(0, 256):
        max_position = len(mod.positions) - 1

        if position_index <= max_position:
            ws_bytes.append(mod.positions[position_index])
        else:
            ws_bytes.append(0xff)

    sample_buffer = [0, 0, 0, 0]

    # ?? x 1024 byte patterns, 64 rows per pattern, 16 bytes per row
    for pattern_index, pattern in enumerate(mod.song.patterns):
        for row_index, row in enumerate(pattern.rows):
            for channel_index, channel_row in enumerate(row.channel_rows):
                if channel_row.period in period_map:
                    note = period_map[channel_row.period]
                else:
                    print('error on pattern {}, row {}, channel {}: unknown period {}'.format(pattern_index, row_index, channel_index, channel_row.period))
                    note = 0

                if channel_row.sample > 0:
                    sample_number = channel_row.sample - 1
                    sample = mod.samples[sample_number]
                    sample_buffer[channel_index] = sample
                else:
                    sample = sample_buffer[channel_index]
                
                # the repeat_length is either 16, 32, 64 or 128 bytes. bump octaves according to the length
                if note > 0:
                    if channel_row.sample < 23:
                        multiplier = repeat_lengths.index(sample.repeat_length)
                        note_offset = 0xc * multiplier
                        note += note_offset

                ws_bytes.append(note)
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

        for pattern_index, pattern in enumerate(mod.song.patterns):
            print('pattern {}:'.format(pattern_index))

            for row_index, row in enumerate(pattern.rows):
                print('row {}:'.format(row_index))

                for channel_index, channel in enumerate(row.channel_rows):
                    print('channel {}: {}'.format(channel_index, channel))
        
        print('\nsamples:')

        for sample_index, sample in enumerate(mod.samples):
            print('sample {}: {}'.format(sample_index, sample))

    write_ws_file(mod, output_file)


if __name__ == "__main__":
    convert()

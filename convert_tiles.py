#!/usr/bin/env python3


import click
import png


@click.command()
@click.argument('filename')
def convert_tiles(filename):
    reader = png.Reader(filename)
    image_info = reader.asRGB()

    width = image_info[0]
    height = image_info[1]
    rows = list(image_info[2])
    info = image_info[3]

    if width % 8 != 0 or height % 8 != 0:
        print('width and height must both be divisible by 8: ({}, {})'.format(width, height))
        return

    print('w x h: {} x {}'.format(width, height))

    colors = find_colors(rows)
    if len(colors) > 4:
        print('too many colors in input: {}'.format(len(colors)))
        return

    tiles = generate_tiles(rows)

    write_tiles(tiles, colors, '{}.tiles'.format(filename))


def write_tiles(tiles, colors, out_filename):
    print(out_filename)

    ws_bytes = bytearray()

    for tile in tiles:
        for tile_row in tile:
            byte1 = 0
            byte2 = 0

            for index, color in enumerate(tile_row):
                color_index = colors.index(color)

                if color_index % 2 == 1:
                    byte1 = byte1 | (1 << (7 - index))
                
                if color_index > 1:
                    byte2 = byte2 | (1 << (7 - index))
                
            ws_bytes.append(byte1)
            ws_bytes.append(byte2)

    with open(out_filename, mode='wb') as file:
        file.write(ws_bytes)


def generate_tiles(rows):
    tile_length = 8
    stride = 3
    tiles = []

    for row_offset in range(0, len(rows), tile_length):
        rows_for_tile = rows[row_offset:row_offset + tile_length]

        for column_offset in range(0, len(rows[row_offset]), tile_length * stride):
            current_tile_rows = []

            for row in rows_for_tile:
                rgb_row = row[column_offset:column_offset + (tile_length * stride)]
                color_row = []

                for i in range(0, len(rgb_row), stride):
                    color = (rgb_row[i], rgb_row[i + 1], rgb_row[i + 2])
                    color_row.append(color)
                
                current_tile_rows.append(color_row)

            tiles.append(current_tile_rows)

    return tiles


def find_colors(rows):
    found_colors = []

    for row in rows:
        for i in range(0, len(row), 3):
            color = (row[i], row[i + 1], row[i + 2])

            if color not in found_colors:
                found_colors.append(color)

    return sorted(found_colors, key=lambda color: color[0])


if __name__ == '__main__':
    convert_tiles()


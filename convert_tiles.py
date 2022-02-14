#!/usr/bin/env python3


import click
import png


TILE_LENGTH = 8
FLIP_NONE = 0
FLIP_VERTICAL = 1
FLIP_HORIZONTAL = 2
FLIP_VERTICAL_AND_HORIZONTAL = 3


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
    minimized_tiles = minimize_tiles(tiles)

    write_map(minimized_tiles[0], colors, "{}.map".format(filename))
    write_tiles(minimized_tiles[1], colors, '{}.tiles'.format(filename))


# returns tuple: ([(tile_index, flip)], [tiles])
def minimize_tiles(tiles):
    map = []
    map_tiles = []

    for tile in tiles:
        vertical_flip_tile = flip_vertical(tile)
        horizontal_flip_tile = flip_horizontal(tile)
        vertical_horizontal_flip_tile = flip_horizontal(vertical_flip_tile)

        if tile in map_tiles:
            map.append((map_tiles.index(tile), FLIP_NONE))
        elif vertical_flip_tile in map_tiles:
            map.append((map_tiles.index(vertical_flip_tile), FLIP_VERTICAL))
        elif horizontal_flip_tile in map_tiles:
            map.append((map_tiles.index(horizontal_flip_tile), FLIP_HORIZONTAL))
        elif vertical_horizontal_flip_tile in map_tiles:
            map.append((map_tiles.index(vertical_horizontal_flip_tile), FLIP_VERTICAL_AND_HORIZONTAL))
        else:
            map_tiles.append(tile)
            map.append((map_tiles.index(tile), FLIP_NONE))

    print("total tile count: {}".format(len(tiles)))
    print("minimized tile count: {}".format(len(map_tiles)))

    return (map, map_tiles)


def flip_vertical(tile):
    flipped = []

    for i in range(len(tile), 0, -TILE_LENGTH):
        flipped.extend(tile[i - TILE_LENGTH : i])

    return flipped


def flip_horizontal(tile):
    flipped = []

    for i in range(0, len(tile), TILE_LENGTH):
        flipped_row = tile[i : i + TILE_LENGTH]
        flipped_row.reverse()

        flipped.extend(flipped_row)

    return flipped


def write_map(map, colors, out_filename):
    ws_bytes = bytearray()

    for map_position_info in map:
        map_index = map_position_info[0]
        flip = map_position_info[1]

        byte1 = map_index & 0xff
        byte2 = (
            ((map_index >> 8) & 0x01)
            | flip << 6
        )

        ws_bytes.append(byte1)
        ws_bytes.append(byte2)

    with open(out_filename, mode='wb') as file:
        file.write(ws_bytes)

    print("map written to file: {}".format(out_filename))


def write_tiles(tiles, colors, out_filename):
    ws_bytes = bytearray()

    for tile in tiles:
        for column in range(0, 8):
            column_start = column * 8
            byte1 = 0
            byte2 = 0

            for pixel_index in range(column_start, column_start + 8):
                color = tile[pixel_index]
                color_index = colors.index(color)
                index = pixel_index % 8

                if color_index % 2 == 1:
                    byte1 = byte1 | (1 << (7 - index))

                if color_index > 1:
                    byte2 = byte2 | (1 << (7 - index))

            ws_bytes.append(byte1)
            ws_bytes.append(byte2)

    with open(out_filename, mode='wb') as file:
        file.write(ws_bytes)

    print("tiles written to file: {}".format(out_filename))


def generate_tiles(rows):
    stride = 3
    tiles = []

    for row_offset in range(0, len(rows), TILE_LENGTH):
        rows_for_tile = rows[row_offset:row_offset + TILE_LENGTH]

        for column_offset in range(0, len(rows[row_offset]), TILE_LENGTH * stride):
            tile = []

            for row in rows_for_tile:
                rgb_row = row[column_offset:column_offset + (TILE_LENGTH * stride)]

                for i in range(0, len(rgb_row), stride):
                    color = (rgb_row[i], rgb_row[i + 1], rgb_row[i + 2])
                    tile.append(color)

            tiles.append(tile)

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


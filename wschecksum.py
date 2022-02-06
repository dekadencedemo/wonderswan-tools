#!/usr/bin/env python3


import click


def patch_ws_rom(input_file):
    with open(input_file, mode='rb') as file:
        file_bytes = file.read()

    file_length = len(file_bytes)

    if file_length < 3:
        print('file too short')
        return
    
    sum = 0

    for i in range(0, file_length - 2):
        b = file_bytes[i]
        sum += b
    
    checksum = sum & 0b1111111111111111
    left = checksum & 0b11111111
    right = checksum >> 8

    new_bytes = bytearray(file_bytes)

    new_bytes[file_length - 2] = left
    new_bytes[file_length - 1] = right

    with open(input_file, mode='wb') as file:
        file.write(new_bytes)
    
    print('file patched')


@click.command()
@click.argument('input_file')
def checksum(input_file):
    mod = patch_ws_rom(input_file)


if __name__ == "__main__":
    checksum()

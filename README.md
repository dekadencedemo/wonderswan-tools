# Dekadence Console Tools

**A Rust rewrite is in progress. The Python versions will be removed once the rewrite is complete.**

Various tools and code for WonderSwan related things. The tools have been used in the following demos:

- "Ihmesorsa" by Dekadence (WonderSwan) ([YouTube](https://youtu.be/qGR-qJp_PQI), [Pouet](https://www.pouet.net/prod.php?which=91299))
- "Rakointro" by Dekadence (WonderSwan) ([YouTube](https://youtu.be/05Z6NCcLBAc), [Pouet](https://www.pouet.net/prod.php?which=91546))
- "Vesilintu" by Dekadence (WonderSwan Color) ([YouTube](https://youtu.be/6qItOEf43xQ), [Pouet](https://www.pouet.net/prod.php?which=91900))
- "Bar Frog Tux" by Dekadence (PC Engine) ([YouTube](https://www.youtube.com/watch?v=OrriYNyjBrk), [Pouet](https://www.pouet.net/prod.php?which=92735))

## Requirements

- Install `pipenv`
- Install dependencies: `pipenv install`

## `wschecksum`

Generates a checksum for a WonderSwan ROM. No real validation is performed, so be careful.

    pipenv run python3 wschecksum.py INPUT_FILE

Note that this will overwrite the original file.

## `convert_mod`

Converts an Amiga MOD to a format compatible with Dekadence's WonderSwan player. More to come.

    pipenv run python3 convert_mod.py [--debug] INPUT_MOD OUTPUT_FILE

Use `--debug` to print the converter's interpretation of the MOD.

## `convert_tiles`

Converts a PNG file to a tile map. Two files are created: a file containing the tileset, and a file containing the tile map. Images with up to four colors are supported, and both width and height must be divisible by 8.

    pipenv run python3 convert_tiles.py INPUT_PNG

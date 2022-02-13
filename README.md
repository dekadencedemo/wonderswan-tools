# Dekadence WonderSwan Tools

Various tools and code for WonderSwan related things.

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

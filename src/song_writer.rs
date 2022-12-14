use std::fs;
use std::collections::HashMap;
use crate::song::{Sample, Song};

lazy_static::lazy_static! {
    static ref PERIOD_MAP: HashMap<u16, u8> = [
        // no note
        (0, 0),
        // c-1 to b-1
        (856, 0x1), (808, 0x2), (762, 0x3), (720, 0x4), (678, 0x5), (640, 0x6), (604, 0x7), (570, 0x8), (538, 0x9), (508, 0xa), (480, 0xb), (453, 0xc),
        // c-2 to b-2
        (428, 0xd), (404, 0xe), (381, 0xf), (360, 0x10), (339, 0x11), (320, 0x12), (302, 0x13), (285, 0x14), (269, 0x15), (254, 0x16), (240, 0x17), (226, 0x18),
        // c-3 to b-3
        (214, 0x19), (202, 0x1a), (190, 0x1b), (180, 0x1c), (170, 0x1d), (160, 0x1e), (151, 0x1f), (143, 0x20), (135, 0x21), (127, 0x22), (120, 0x23), (113, 0x24)
    ].iter().cloned().collect();
}

const REPEAT_LENGTHS: [u16; 4] = [128, 64, 32, 16];

pub fn write_song(output_file: &String, song: Song) {
    let mut output: Vec<u8> = Vec::new();

    // 32 byte header, actual content TBD
    for _ in 0..32 {
        output.push(0);
    }

    // 31 x 32 byte instruments
    for sample_index in 0..31 {
        let sample = &song.samples[sample_index];

        if sample.length > 0 && !REPEAT_LENGTHS.contains(&sample.repeat_length) && sample_index < 23 {
            println!("error in sample {}: invalid repeat length", sample_index);
        }

        output.push(sample.volume);

        // insert blank data for now
        for _ in 0..15 {
            output.push(0);
        }

        let sample_data = &sample.sample_data;
        let repeat_start = sample.repeat_start as usize;

        // convert samples to signed and store highest 4 bits
        // TODO: implement optional interpolation
        if sample.repeat_length == 16 {
            for byte_index in 0..16 {
                let lo_sample = sample_data[repeat_start + byte_index] as u16 + 0x80;
                let hi_sample = lo_sample;
                output.push(((hi_sample & 0xf0) as u8) | ((lo_sample >> 4) & 0x0f) as u8);
            }
        } else if sample.repeat_length == 32 {
            for byte_index in 0..16 {
                // convert to signed and store highest 4 bits
                let hi_sample = sample_data[repeat_start + byte_index * 2 + 1] as u16 + 0x80;
                let lo_sample = sample_data[repeat_start + byte_index * 2] as u16 + 0x80;
                output.push(((hi_sample & 0xf0) as u8) | ((lo_sample >> 4) & 0x0f) as u8);
            }
        } else if sample.repeat_length == 64 {
            for byte_index in 0..16 {
                // convert to signed and store highest 4 bits
                let hi_sample = sample_data[repeat_start + byte_index * 4 + 2] as u16 + 0x80;
                let lo_sample = sample_data[repeat_start + byte_index * 4] as u16 + 0x80;
                output.push(((hi_sample & 0xf0) as u8) | ((lo_sample >> 4) & 0x0f) as u8);
            }
        } else if sample.repeat_length == 128 {
            for byte_index in 0..16 {
                // convert to signed and store highest 4 bits
                let hi_sample = sample_data[repeat_start + byte_index * 8 + 4] as u16 + 0x80;
                let lo_sample = sample_data[repeat_start + byte_index * 8] as u16 + 0x80;
                output.push(((hi_sample & 0xf0) as u8) | ((lo_sample >> 4) & 0x0f) as u8);
            }
        } else {
            for _ in 0..16 {
                output.push(0);
            }
        }
    }

    // 256 byte order list, 0xff = end of list
    for position_index in 0..256 {
        let max_position = song.positions.len() - 1;

        if position_index <= max_position {
            output.push(song.positions[position_index]);
        } else {
            output.push(0xff);
        }
    }

    let empty_sample = Sample::empty();
    let mut sample_buffer: Vec<&Sample> = (0..song.channel_count).map(|_| &empty_sample).collect();

    // ?? x 1024 byte patterns, 64 rows per pattern, 16 bytes per row
    for pattern_index in 0..song.patterns.len() {
        let pattern = &song.patterns[pattern_index];

        for row_index in 0..pattern.rows.len() {
            let row = &pattern.rows[row_index];

            for channel_index in 0..row.channel_rows.len() {
                let channel_row = &row.channel_rows[channel_index];
                let mut note = if PERIOD_MAP.contains_key(&channel_row.period) {
                    PERIOD_MAP[&channel_row.period]
                } else {
                    0
                };

                if song.mangle_notes && note > 0 {
                    // the repeat_length is either 16, 32, 64 or 128 bytes. bump octaves according to the length
                    let sample = if channel_row.sample > 0 {
                        let sample_number = (channel_row.sample - 1) as usize;
                        let smp = &song.samples[sample_number];
                        sample_buffer[channel_index] = &*smp;
                        smp
                    } else {
                        &sample_buffer[channel_index]
                    };

                    if channel_row.sample < 23 {
                        let multiplier = REPEAT_LENGTHS.iter().position(|&x| x == sample.repeat_length).unwrap() as u8;
                        let note_offset = 0xc * multiplier;
                        note += note_offset;
                    }
                }

                output.push(note);
                output.push(channel_row.sample);
                output.push(channel_row.effect);
                output.push(channel_row.effect_value);
            }
        }
    }

    match fs::write(output_file, output) {
        Ok(_v) => println!("song converted successfully to file: {}", output_file),
        Err(_e) => println!("conversion failed"),
    };
}

use crate::song::{ChannelRow, Pattern, PatternRow, Sample, Song};
use std::str;

const PATTERNS_START: u16 = 1084;
const PATTERN_LENGTH: u16 = 1024;

pub fn is_mod_file(mod_bytes: &Vec<u8>) -> bool {
    let mk_header_start = 1080;
    let mk_header_length = 4;
    let mk_header_bytes = &mod_bytes[mk_header_start..(mk_header_start + mk_header_length)];
    let mk_header = match String::from_utf8(mk_header_bytes.to_vec()) {
        Ok(v) => v,
        Err(_e) => return false,
    };

    mk_header == "M.K."
}

pub fn read_mod(mod_bytes: &Vec<u8>) -> Result<Song, &'static str> {
    let title_start = 0;
    let title_length = 20;
    let mod_title_bytes = &mod_bytes[title_start..(title_start + title_length)];
    let mod_title = match String::from_utf8(mod_title_bytes.to_vec()) {
        Ok(v) => v,
        Err(_e) => return Err("Could not read title"),
    };

    let position_start = 950;
    let position_count = mod_bytes[position_start] as usize;

    let positions_start = 952;
    let positions = (&mod_bytes[positions_start..(positions_start + position_count)]).to_vec();

    let max_pattern = match positions.iter().max() {
        Some(v) => *v,
        None => return Err("Could not get max pattern"),
    };

    println!("title: {}", mod_title);
    println!("position count: {}", position_count);
    println!("read positions: {}", positions.len());
    println!("max pattern: {}", max_pattern);

    let patterns = parse_patterns(&mod_bytes, max_pattern);
    let samples = parse_samples(&mod_bytes, max_pattern);

    Ok(Song { patterns, positions, samples, channel_count: 4, mangle_notes: true })
}

fn parse_patterns(mod_bytes: &Vec<u8>, max_pattern: u8) -> Vec<Pattern> {
    let mut patterns: Vec<Pattern> = Vec::new();

    for pattern_index in 0..=max_pattern {
        patterns.push(Pattern { rows: parse_pattern_rows(&mod_bytes, pattern_index) });
    }

    patterns
}

fn parse_pattern_rows(mod_bytes: &Vec<u8>, pattern_index: u8) -> Vec<PatternRow> {
    let mut rows: Vec<PatternRow> = Vec::new();
    let pattern_length = 64;

    for row_index in 0..pattern_length {
        rows.push(PatternRow { channel_rows: parse_mod_channel_rows(&mod_bytes, pattern_index, row_index) })
    }

    rows
}

fn parse_mod_channel_rows(mod_bytes: &Vec<u8>, pattern_index: u8, row_index: u8) -> Vec<ChannelRow> {
    let mut channel_rows: Vec<ChannelRow> = Vec::new();
    let channel_count = 4;
    let row_length = 16;
    let channel_length = 4;

    for channel_index in 0..channel_count {
        let index = (PATTERNS_START
            + (pattern_index as u16 * PATTERN_LENGTH)
            + (row_index as u16 * row_length)
            + (channel_index * channel_length)) as usize;
        let channel_row_bytes = &mod_bytes[index..(index + channel_length as usize)];
        let sample = (channel_row_bytes[0] & 0xf0) + ((channel_row_bytes[2] & 0xf0) >> 4);
        let period = (((channel_row_bytes[0] & 0xf) as u16) << 8) + channel_row_bytes[1] as u16;
        let effect = channel_row_bytes[2] & 0xf;
        // TODO: Add parsing for effect 0 and 14.
        let effect_value = channel_row_bytes[3];

        channel_rows.push(ChannelRow { sample, period, effect, effect_value })
    }

    channel_rows
}

fn parse_samples(mod_bytes: &Vec<u8>, max_pattern: u8) -> Vec<Sample> {
    let sample_header_start = 20;
    let sample_header_offset = 30;
    let name_length = 22;
    let sample_length_offset = name_length;
    let sample_length_length = 2;
    let finetune_offset = sample_length_offset + sample_length_length;
    let finetune_length = 1;
    let volume_offset = finetune_offset + finetune_length;
    let volume_length = 1;
    let repeat_start_offset = volume_offset + volume_length;
    let repeat_start_length = 2;
    let repeat_length_offset = repeat_start_offset + repeat_start_length;
    let repeat_length_length = 2;

    let mut samples = Vec::new();
    let mut position = sample_header_start;
    let mut sample_data_position = (PATTERNS_START + (((max_pattern as u16) + 1) * PATTERN_LENGTH)) as usize;

    for _ in 0..31 {
        let name_start = position;
        let name_end = name_start + name_length;
        let name_bytes = &mod_bytes[name_start..name_end];
        let name = match String::from_utf8(name_bytes.to_vec()) {
            Ok(v) => v.strip_suffix("\x00").unwrap_or("").to_string(),
            Err(_e) => "".to_string(),
        };

        let length_start = position + sample_length_offset;
        let length_end = length_start + sample_length_length;
        let length_bytes = &mod_bytes[length_start..length_end];
        let length = (u16::from_be_bytes([length_bytes[0], length_bytes[1]]) * 2) as usize;

        let finetune_start = position + finetune_offset;
        let finetune = mod_bytes[finetune_start] & 0b1111;

        let volume_start = position + volume_offset;
        let volume = mod_bytes[volume_start];

        let repeat_start_start = position + repeat_start_offset;
        let repeat_start_end = repeat_start_start + repeat_start_length;
        let repeat_start_bytes = &mod_bytes[repeat_start_start..repeat_start_end];
        let repeat_start = u16::from_be_bytes([repeat_start_bytes[0], repeat_start_bytes[1]]) * 2;

        let repeat_length_start = position + repeat_length_offset;
        let repeat_length_end = repeat_length_start + repeat_length_length;
        let repeat_length_bytes = &mod_bytes[repeat_length_start..repeat_length_end];
        let repeat_length = u16::from_be_bytes([repeat_length_bytes[0], repeat_length_bytes[1]]) * 2;

        let sample_data = if length > 0 {
            let data = &mod_bytes[sample_data_position..(sample_data_position + length)];
            sample_data_position += length;
            data.to_vec()
        } else {
            Vec::new()
        };

        samples.push(
            Sample { name, length: length as u16, finetune, volume, repeat_start, repeat_length, sample_data }
        );

        position += sample_header_offset;
    }

    samples
}

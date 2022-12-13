pub struct Sample {
    pub name: String,
    pub length: u16,
    pub finetune: u8,
    pub volume: u8,
    pub repeat_start: u16,
    pub repeat_length: u16,
    pub sample_data: Vec<u8>,
}

impl Sample {
    pub const fn empty() -> Self {
        Sample { name: String::new(), length: 0, finetune: 0, volume: 0, repeat_start: 0, repeat_length: 0, sample_data: Vec::new() }
    }
}

pub struct ChannelRow {
    pub sample: u8,
    pub period: u16,
    pub effect: u8,
    pub effect_value: u8,
}

pub struct PatternRow {
    pub channel_rows: Vec<ChannelRow>,
}

pub struct Pattern {
    pub rows: Vec<PatternRow>,
}

pub struct Song {
    pub patterns: Vec<Pattern>,
    pub positions: Vec<u8>,
    pub samples: Vec<Sample>,
}

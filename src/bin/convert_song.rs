use std::env;
use std::fs;
use std::process::exit;
use wonderswan_tools::mod4::is_mod_file;
use wonderswan_tools::song::SongFormat;
use wonderswan_tools::{mod4, song_writer};

fn main() {
    let args: Vec<String> = env::args().collect();

    if args.len() != 3 {
        println!("usage: {} INPUT_FILE OUTPUT_FILE", args[0]);
        exit(1)
    }

    let input_file = args[1].clone();
    let output_file = args[2].clone();

    let input_bytes = match fs::read(input_file) {
        Ok(v) => v,
        Err(_e) => {
            println!("Could not read input file");
            exit(1)
        }
    };

    let song = match determine_format(&input_bytes) {
        Some(format) => match format {
            SongFormat::Mod => match mod4::read_mod(&input_bytes) {
                Ok(song) => song,
                Err(e) => {
                    println!("{}", e);
                    exit(1)
                }
            },
            SongFormat::S3m => {
                println!("s3m not yet supported");
                exit(1)
            }
        },
        None => {
            println!("Unsupported format");
            exit(1)
        }
    };

    song_writer::write_song(&output_file, song);
}

fn determine_format(input_bytes: &[u8]) -> Option<SongFormat> {
    if is_mod_file(input_bytes) {
        Some(SongFormat::Mod)
    } else {
        None
    }
}

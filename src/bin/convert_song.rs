use std::env;
use std::process::exit;
use wonderswan_tools::{mod4, song_writer};

fn main() {
    let args: Vec<String> = env::args().collect();

    if args.len() != 3 {
        println!("usage: {} INPUT_FILE OUTPUT_FILE", args[0]);
        exit(1)
    }

    let input_file = args[1].clone();
    let output_file = args[2].clone();

    let song = match mod4::read_mod(&input_file) {
        Ok(v) => v,
        Err(e) => {
            println!("{}", e.to_string());
            exit(1)
        },
    };

    song_writer::write_song(&output_file, song);
}

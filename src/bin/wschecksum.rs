use std::{env, fs};
use std::process::exit;

/// Note that this program assumes that the input ROM is unpatched.
fn main() {
    let args: Vec<String> = env::args().collect();

    if args.len() != 3 {
        println!("usage: {} INPUT_FILE OUTPUT_FILE", args[0]);
        exit(1)
    }

    let input_file = args[1].clone();
    let output_file = args[2].clone();

    let input_bytes = match fs::read(&input_file) {
        Ok(v) => v,
        Err(_e) => {
            println!("Could not read input file");
            exit(1)
        }
    };

    let file_length = input_bytes.len();

    if file_length < 3 {
        println!("File too short");
        exit(1)
    }

    let mut sum = 0;

    for i in 0..(file_length - 2) {
        let b = input_bytes[i] as u32;
        sum += b;
    }

    let checksum = sum & 0xffff;
    let left = (checksum & 0xff) as u8;
    let right = (checksum >> 8) as u8;

    let mut output_bytes = input_bytes.clone();
    output_bytes[file_length - 2] = left;
    output_bytes[file_length - 1] = right;

    match fs::write(&output_file, output_bytes) {
        Ok(_v) => println!("File patched"),
        Err(_e) => println!("Patching failed"),
    };
}

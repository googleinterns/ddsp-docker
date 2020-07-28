"""Program groups and compresses files from NSynth Dataset.

NSynth Dataset (https://magenta.tensorflow.org/datasets/nsynth)
consists of .wav files containing various instruments' sounds.
This program groups those files into separate folders based on
the information about instrument category present in the filename
and compresses those folders into .tar.gz files.
"""

import argparse
import os
import re
import tarfile


def group_files(input_directory, temporary_directory):
    """Groups files into separate directories.

    Groups .wav files from the input directory into separate folders
    based on the instrument category present in the filename.

    Args:
        input_directory:
          A directory where mixed audio files are located.
        temporary_directory:
          A base directory where separate instruments' folders will be stored.
    """
    instruments = set()

    for filename in os.listdir(input_directory):
        # Filename is concatenation of instrument category, example number
        # and audio file extension, for example: instrument_category_012-345-678.wav.
        # We only want to extract the instrument category.
        if re.fullmatch(r'.+_[0-9\-]{11}\.wav', filename):
            instruments.add(filename[:-16])

    for instrument in instruments:
        new_file_location = os.path.join(temporary_directory, instrument)
        try:
            os.mkdir(new_file_location)
        except OSError:
            print(f'Failed to create directory {new_file_location}')
        else:
            print(f'Successfully created directory {new_file_location}')

    for filename in os.listdir(input_directory):
        os.rename(os.path.join(input_directory, filename),
                  os.path.join(temporary_directory, filename[:-16], filename))


def compress_folders(temporary_directory, output_directory):
    """Compresses folders into .tar.gz files.

    Compresses all not yet compressed folders from temporary_directory
    and stores .tar.gz files in output_directory.

    Args:
        temporary_directory:
          A directory where folders we want to compress are stored.
        output_directory:
          A directory where compressed folders will be stored.
    """
    folders_already_compressed = set()

    for filename in os.listdir(output_directory):
        # We want to check what folders are already compressed. Compresed folders are named
        # as follows: instrument_category.tar.gz. We want to store only instrument_category.
        if re.fullmatch(r'.+\.tar\.gz', filename):
            folders_already_compressed.add(filename[:-7])

    for foldername in os.listdir(temporary_directory):
        if foldername in folders_already_compressed:
            print(f'{foldername} is already compressed')
        else:
            with tarfile.open(os.path.join(output_directory, foldername + '.tar.gz'),
                              'w:gz') as compressed_folder:
                compressed_folder.add(os.path.join(temporary_directory, foldername),
                                      arcname=os.path.join('.', foldername))
            print(f'{foldername} compressed successfully')


def get_args():
    """Parses arguments.

    Returns:
      Dictionary of program arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir',
                        type=str,
                        help='Where to read audio files from')
    parser.add_argument('--temp-dir',
                        type=str,
                        help='Where grouped files should be stored')
    parser.add_argument('--output-dir',
                        type=str,
                        help='Where compressed folders should be stored')

    args = parser.parse_args()

    return args


def main():
    args = get_args()
    if args.input_dir is None or args.temp_dir is None or args.output_dir is None:
        print('Provide input, temporary and output directories')
    else:
        group_files(args.input_dir, args.temp_dir)
        compress_folders(args.temp_dir, args.output_dir)

if __name__ == '__main__':
    main()

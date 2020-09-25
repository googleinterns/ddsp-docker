"""Program groups and compresses files from NSynth Dataset.

NSynth Dataset (https://magenta.tensorflow.org/datasets/nsynth)
consists of .wav files containing various instruments' sounds.
This program groups those files into separate folders based on
the information about instrument category present in the filename
and compresses those folders into .tar.gz files.
"""

import os
import re
import tarfile

from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_string('input_dir', None,
                    'Path where audio mixed files are stored.')
flags.DEFINE_string('output_dir', None,
                    'Path were compressed folders will be stored.')

# Example filename matching: instrument_category_012-345-678.wav
FILENAME_REGEX = re.compile(r'_[0-9\-]{11}\.wav')

def compress_files(input_directory, output_directory):
  """Groups the .wav files based on instrument in the filename.
    Compresses them into into .tar.gz files.
    Args:
        input_directory:
          A directory where files we want to compress are stored.
        output_directory:
          A directory where compressed folders will be stored.
  """
  instruments = {}

  for filename in os.listdir(input_directory):
    match = re.search(FILENAME_REGEX, filename)
    if match is not None:
      instrument = filename[:match.span()[0]]
      if instrument not in instruments:
        instruments[instrument] = tarfile.open(
            os.path.join(
                output_directory,
                f'{instrument}.tar.gz'),
            'w:gz')
      instruments[instrument].add(
          os.path.join(input_directory, filename),
          arcname=os.path.join('.', instrument, filename))

  for _, file_name in instruments.items():
    file_name.close()

def main(unused_argv):
  compress_files(FLAGS.input_dir, FLAGS.output_dir)

if __name__ == '__main__':
  flags.mark_flag_as_required('input_dir')
  flags.mark_flag_as_required('output_dir')
  app.run(main)

"""Script for running a containerized preprocessing on AI Platform."""

import os
import subprocess

from absl import app
from absl import flags
from absl import logging
import ddsp.training
import magenta_stats_utils.utils as utils

FLAGS = flags.FLAGS

flags.DEFINE_string('input_audio_filepatterns', None, 'Audio file pattern.')
flags.DEFINE_string('output_tfrecord_path', None,
                    'Path were processed files will be stored.')
flags.DEFINE_string('statistics_path', None,
                    'Path were statistics file will be stored.')


def main(unused_argv):

  preprocess_command = [
      'ddsp_prepare_tfrecord',
      '--num_shards=10',
      '--alsologtostderr',
      f'--input_audio_filepatterns={FLAGS.input_audio_filepatterns}',
      f'--output_tfrecord_path={FLAGS.output_tfrecord_path}']

  subprocess.run(args=preprocess_command, check=True)

  # Compute statistics for timbre transfer
  tfrecord_filepattern = (
      os.path.split(FLAGS.output_tfrecord_path)[0] +
      '/train.tfrecord*')
  logging.info('TF_RECORD filepattern: %s', tfrecord_filepattern)
  data_provider = ddsp.training.data.TFRecordProvider(
      tfrecord_filepattern)
  dataset = data_provider.get_dataset(shuffle=False)
  pickle_file_path = os.path.join(
      FLAGS.statistics_path,
      'dataset_statistics.pkl')
  utils.save_dataset_statistics(data_provider, pickle_file_path)

if __name__ == '__main__':
  flags.mark_flag_as_required('input_audio_filepatterns')
  flags.mark_flag_as_required('output_tfrecord_path')
  flags.mark_flag_as_required('statistics_path')
  app.run(main)

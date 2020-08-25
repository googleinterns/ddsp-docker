"""
This script is still developed.
"""

import json
import os

from absl import app
from absl import flags
from absl import logging

FLAGS = flags.FLAGS

flags.DEFINE_string('save_dir', None,
                    'Path where checkpoints and summary events will be saved '
                    'during training and evaluation.')
flags.DEFINE_string('restore_dir', '',
                    'Path from which checkpoints will be restored before '
                    'training. Can be different than the save_dir.')
flags.DEFINE_string('data_pattern', None, "Data pattern")
flags.DEFINE_integer('num_steps', 30000, 'NUmber of training steps')
flags.DEFINE_float('early_stop_loss_value', 5.0, 'Early stopping. When the total_loss '
                   'reaches below this value training stops.')
flags.DEFINE_integer('batch_size', 32, 'Batch size')
flags.DEFINE_float('learning_rate', 0.003, 'Learning rate')
flags.DEFINE_integer('steps_per_summary', 300, 'Steps per summary')
flags.DEFINE_integer('steps_per_save', 300, 'Steps per save')



def main(unused_argv):
  flags.mark_flag_as_required('data_pattern')
  flags.mark_flag_as_required('save_dir')
    
  cluster_config = ''

  os.system(("ddsp_run "
             "--mode=train "
             "--alsologtostderr "
             "--gin_file=models/solo_instrument.gin "
             "--gin_file=datasets/tfrecord.gin "
             f"--cluster_config='{cluster_config}' "
             f"--save_dir='{FLAGS.save_dir}' "
             f"--restore_dir='{FLAGS.restore_dir}' "
             f"--gin_param=batch_size={FLAGS.batch_size} "
             f"--gin_param=learning_rate={FLAGS.learning_rate} "
             f"--gin_param=\"TFRecordProvider.file_pattern='{FLAGS.data_pattern}'\" "
             f"--gin_param=train_util.train.num_steps={FLAGS.num_steps} "
             f"--gin_param=train_util.train.steps_per_save={FLAGS.steps_per_save} "
             f"--gin_param=train_util.train.steps_per_summary={FLAGS.steps_per_summary} "))



def console_entry_point():
  """From pip installed script."""
  app.run(main)


if __name__ == '__main__':
  console_entry_point()
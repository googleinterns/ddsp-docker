# Copyright 2020 The DDSP Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Lint as: python3
"""Tests for ddsp.training.cloud"""

from unittest import mock

import cloud
import tensorflow.compat.v2 as tf

class UploadToGstorageTest(tf.test.TestCase):

  @mock.patch('google.cloud.storage.Client.bucket')
  def test_bucket_name(self, bucket_function):
    """Check if proper bucket name is infered from path."""
    cloud.copy_hypertune_file_from_container(
        'gs://bucket-name/bucket/dir/some_file.gin',
        'local/path/some_file.gin')
    bucket_function.assert_called_with('bucket-name')

if __name__ == '__main__':
  tf.test.main()
"""Tests for task.py."""

import os
from unittest import mock

import task
import tensorflow.compat.v2 as tf

class GetWorkerBehaviorInfoTest(tf.test.TestCase):

  def test_no_tf_config(self):
    """Tests behavior when there is no TF_CONFIG set."""
    cluster_config, save_dir = task.get_worker_behavior_info('some/dir/')
    self.assertEqual(save_dir, 'some/dir/')
    self.assertEqual(cluster_config, '')

  def test_incomplete_tf_config(self):
    """Test behavior when set TF_CONFIG is incomplete."""
    with mock.patch.dict(os.environ, {'TF_CONFIG': '{"cluster": {}}'}):
      cluster_config, save_dir = task.get_worker_behavior_info('some/dir/')
      self.assertEqual(save_dir, 'some/dir/')
      self.assertEqual(cluster_config, '')

    with mock.patch.dict(os.environ, {'TF_CONFIG': '{"task": {}}'}):
      cluster_config, save_dir = task.get_worker_behavior_info('some/dir/')
      self.assertEqual(save_dir, 'some/dir/')
      self.assertEqual(cluster_config, '')

  @mock.patch.dict(
      os.environ,
      {'TF_CONFIG': ('{"cluster": {"worker": ["worker0.example.com:2221"]},'
                     '"task": {"type": "worker", "index": 0}}')})
  def test_single_worker(self):
    """Tests behavior when cluster has only one worker."""
    cluster_config, save_dir = task.get_worker_behavior_info('some/dir/')
    self.assertEqual(save_dir, 'some/dir/')
    self.assertEqual(cluster_config, '')

  @mock.patch.dict(
      os.environ,
      {'TF_CONFIG': ('{"cluster": {"worker": ["worker0.example.com:2221"],'
                     '"chief": ["chief.example.com:2222"]},'
                     '"task": {"type": "chief", "index": 0}}')})
  def test_multi_worker_as_chief(self):
    """Tests multi-worker behavior when task type chief is set in TF_CONFIG."""
    cluster_config, save_dir = task.get_worker_behavior_info('some/dir/')
    self.assertEqual(save_dir, 'some/dir/')
    self.assertEqual(
        cluster_config,
        ('{"cluster": {"worker": ["worker0.example.com:2221"],'
         '"chief": ["chief.example.com:2222"]},'
         '"task": {"type": "chief", "index": 0}}'))

  @mock.patch.dict(
      os.environ,
      {'TF_CONFIG': ('{"cluster": {"worker": ["worker0.example.com:2221"],'
                     '"chief": ["chief.example.com:2222"]},'
                     '"task": {"type": "worker", "index": 0}}')})
  def test_multi_worker_as_worker(self):
    """Tests multi-worker behavior when task type worker is set in TF_CONFIG."""
    cluster_config, save_dir = task.get_worker_behavior_info('some/dir/')
    self.assertEqual(save_dir, '')
    self.assertEqual(
        cluster_config,
        ('{"cluster": {"worker": ["worker0.example.com:2221"],'
         '"chief": ["chief.example.com:2222"]},'
         '"task": {"type": "worker", "index": 0}}'))


if __name__ == '__main__':
  tf.test.main()

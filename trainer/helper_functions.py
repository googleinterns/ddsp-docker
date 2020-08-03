import json
import os
from absl import logging
from ddsp.training import train_util
import tensorflow.compat.v2 as tf

def get_strategy(tpu='', gpus=None):
    tf_config_str = os.environ.get('TF_CONFIG')
    tf_config_dict = json.loads(tf_config_str)
    
    if len(tf_config_dict["cluster"]) > 1:
        strategy = strategy=tf.distribute.experimental.MultiWorkerMirroredStrategy()
        logging.info('Cluster spec: %s', strategy.cluster_resolver.cluster_spec())
    else:
        strategy = train_util.get_strategy(tpu=tpu, gpus=gpus)

    return strategy

# if __name__ == "__main__":
#     os.environ['TF_CONFIG'] = json.dumps({
#                                             "cluster": {
#                                             "worker": ["localhost:12345", "localhost:23456"],
#                                             "ps": ["localhost:34567"]
#                                         },
#                                             "task": {'type': 'worker', 'index': 0}
#                                         })
#     get_strategy()
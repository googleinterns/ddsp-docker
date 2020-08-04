import json
import os
from absl import logging
from ddsp.training import train_util
import tensorflow.compat.v2 as tf

def get_strategy(tpu='', gpus=None):
    """Chooses a distribution strategy.

    AI Platform automatically sets TF_CONFIG environment variable based 
    on provided config file. If training is run on multiple VMs different strategy
    needs to be chosen than when it is run on only one VM. This function determines 
    the strategy based on the information in TF_CONFIG variable.

    Args:
        tpu: 
            Argument for DDSP library function call.
            Address of the TPU. No TPU if left blank.
        gpus: 
            Argument for DDSP library function call.
            List of GPU addresses for synchronous training.
    Returns:
        A distribution strategy.
    """
    
    tf_config_str = os.environ.get('TF_CONFIG')
    tf_config_dict = json.loads(tf_config_str)

    # Exactly one chief worker is always specified inside the TF_CONFIG variable
    # in the cluster section. If there are any other workers specified MultiWorker
    # strategy needs to be chosen.
    if len(tf_config_dict["cluster"]) > 1:
        strategy = strategy=tf.distribute.experimental.MultiWorkerMirroredStrategy()
        logging.info('Cluster spec: %s', strategy.cluster_resolver.cluster_spec())
    else:
        strategy = train_util.get_strategy(tpu=tpu, gpus=gpus)

    return strategy

## DDSP-Docker 


## User Interaction
**Author:** anasimionescu

**Reviewers:** zeos, dwalter, jesseengel

**Status:** Final 

**Originally Proposed:** 2020-07-30 

**Last Updated:** 2020-09-22

**Self link:** go/ddsp-user



## Background

[Magenta DDSP](https://github.com/magenta/ddsp/tree/3e891aaae0d724c4a6318036108483d6b58e86ee) (Differentiable Digital Signal Processing) library enables integration of signal processing elements with deep learning methods.

Existing code examples have following functionalities::



1. **[Training DDSP Autoencoder](https://github.com/magenta/ddsp/blob/master/ddsp/colab/demos/train_autoencoder.ipynb)**- it is possible to specify training parameters (batch size, number of training steps) and necessary directories (dataset, snapshots, trained parameters) as arguments of command line call `ddsp_run` or as a [gin](https://github.com/google/gin-config) file (command line arguments overwrite gin specification)
2. **[DDSP Timbre Transfer](https://github.com/magenta/ddsp/blob/master/ddsp/colab/demos/timbre_transfer.ipynb)** - it is possible to use a pretrained model to transfer instrument timbre on to user-provided audio.


## Objective

_The purpose of this project is to provide users a different kind of workflow oriented towards usage for production rather than on research and interactive experience. Using the existing [colab notebooks](https://github.com/magenta/ddsp/tree/master/ddsp/colab/demos) and the [DDSP](https://github.com/magenta/ddsp/tree/master/ddsp)(Differentiable Digital Signal Processing) library, we aim to create a containerized version that can use the AI Platform in Google Cloud for fast and distributed training._

_The [timbre transfer colab notebook](https://colab.research.google.com/github/magenta/ddsp/blob/master/ddsp/colab/demos/timbre_transfer.ipynb) (where the user can upload a piece of music and transform it according to the characteristics of the sound extracted from a trained model) offers a very user friendly experience, while **the process of training your own DDSP autoencoder model can be quite complex,** as it requires running code, connecting to Google Drive and restoring previous states of the training due to the limited lifetime of a Colab instance. **Our purpose is to make it easier to use by everyone by taking advantage of the Google AI Platform API**._


## Design Decisions


### Training and storing options for the user

The user should be able to choose whether they want to **train the model locally**, using only their personal resources or **train on [Google Cloud AI Platform](https://cloud.google.com/ai-platform)**.

**For local training**, the container would use paths to local directories or [Google Cloud Storage](https://cloud.google.com/storage)(GCS) Buckets as paths for retrieving the data set and for saving the final model (or snapshots) .The user should also specify the option of using a gpu or a cpu, as the base image of the docker container has to be chosen beforehand.

**For training on Cloud AI Platform**, the data set and the final model can be saved to and retrieved from a GCS Bucket. Using a GCS bucket gives the advantage of using a large dataset and the ability to save more snapshots without using local memory. A disadvantage is longer data retrieval and saving time (~4.3 – 4.6s for each snapshot saved).


#### Implementation

For the user to input their preferences of local/remote training, paths to data storage, and other training options we initially decided to use a script that would provide prompts for input, giving a smooth experience and detaching the user from line commands. This way the user can easily use the app without having to read too much documentation or have knowledge of terminal commands. 

Currently, the script achieves the following: gathers the input via prompts, builds the image of the docker, runs the image with the custom preferences, submits the job on the Google Cloud AI Platform, and also enables Tensorboard for visualization of the learning process.


#### Alternatives considered

**<span style="text-decoration:underline;">Using flags</span>** instead of a script. These would be specified at the end of the command that runs the image locally or that submits the training job on AI Platform, being passed to the containerized call of the training.

Pro: This alternative gives more liberty in customizing the training job, since the user can take advantage of all the flags accepted by the **<code>ddsp_run</code></strong> function.

Con: The user would be expected to have more than minimal knowledge of terminal commands, and also read enough documentation to actually use the flags that would not be part of our input script.


### Tensorboard Support

The [existing code example](https://github.com/magenta/ddsp/blob/master/ddsp/colab/demos/train_autoencoder.ipynb) in Colab gives the possibility of observing training in Tensorboard. We also provide the option of launching Tensorboard on a local - port after starting the training. The command looks like this`:`


```
tensorboard --logdir=<storingPath> --port=8080
```


The command for enabling Tensorboard is also part of the script that encapsulates gathering input, building the docker image and running the training job. For `&lt;storingPath>` the script will automatically  provide the path to where checkpoints and summaries of the training are stored. 

When the storing location is a GCS bucket, authentication for Cloud SDK is required, so when running the script, the user will be asked to follow a link and authenticate in order to grant permission for using Cloud SDK.

In order to share their ML experiment’s results, the script also uploads the logs to **TensorBoard.dev. **Following the link provided, the user can watch their experiment on a hosted web page  or share it with others.


### Hyperparameter tuning

Since we are using a [custom container](https://cloud.google.com/ai-platform/training/docs/containers-overview) for training we must use the <code>[cloudml-hypertune](https://github.com/GoogleCloudPlatform/cloudml-hypertune)</code> Python package to report the hyperparameter metric to AI Platform Training. The Dockerfile will include this package in order to install it in the custom container. The training function, <code>train_util.py</code> will use <code>cloudml-hypertune</code> to report the results of each trial by calling its helper function, <code>[report_hyperparameter_tuning_metric](https://github.com/GoogleCloudPlatform/cloudml-hypertune/blob/master/hypertune/hypertune.py#L49)</code>. This reporting function will be part of an internal change in the Magenta library, in the <code>cloud.py</code> file.

In the `config.yaml` file we define configuration for distributed training, we also have to define hyperparameter spec.

Using the function `copy_hypertune_file_from_container `from `cloud.py`, the final report of hypertuning can be copied from the container and uploaded to a bucket for further investigations.


#### Conclusions

When trying to tune only the learning rate for a set batch size of 8, the results are the following, showing that for a learning rate too big the model does not converge:


<table>
  <tr>
   <td><strong>Learning rate</strong>
   </td>
   <td><strong>Loss</strong>
   </td>
  </tr>
  <tr>
   <td>0.0001
   </td>
   <td>7.28
   </td>
  </tr>
  <tr>
   <td>0.001
   </td>
   <td>7.93
   </td>
  </tr>
  <tr>
   <td>0.01
   </td>
   <td>13.09
   </td>
  </tr>
  <tr>
   <td>0.1
   </td>
   <td>35.67
   </td>
  </tr>
</table>


Batch size 32:


<table>
  <tr>
   <td><strong>Learning rate</strong>
   </td>
   <td><strong>Loss</strong>
   </td>
  </tr>
  <tr>
   <td>0.0001
   </td>
   <td>7.77
   </td>
  </tr>
  <tr>
   <td>0.001
   </td>
   <td>7.85
   </td>
  </tr>
  <tr>
   <td>0.0003
   </td>
   <td>7.99
   </td>
  </tr>
  <tr>
   <td>0.01
   </td>
   <td>10.06
   </td>
  </tr>
</table>


Here are the results for batch size 16:


<table>
  <tr>
   <td><strong>Learning rate</strong>
   </td>
   <td><strong>Loss</strong>
   </td>
  </tr>
  <tr>
   <td>0.0001
   </td>
   <td>7.45
   </td>
  </tr>
  <tr>
   <td>0.001
   </td>
   <td>7.54
   </td>
  </tr>
  <tr>
   <td>0.0003
   </td>
   <td>7.59
   </td>
  </tr>
  <tr>
   <td>0.01
   </td>
   <td>12.82
   </td>
  </tr>
</table>


Batch size 64:


<table>
  <tr>
   <td><strong>Learning rate</strong>
   </td>
   <td><strong>Loss</strong>
   </td>
  </tr>
  <tr>
   <td>0.01
   </td>
   <td>11.70
   </td>
  </tr>
  <tr>
   <td>0.0001
   </td>
   <td>16.13
   </td>
  </tr>
  <tr>
   <td>0.001
   </td>
   <td>17.43
   </td>
  </tr>
  <tr>
   <td>0.1
   </td>
   <td>29.75
   </td>
  </tr>
</table>


Batch size 128:


<table>
  <tr>
   <td><strong>Learning rate</strong>
   </td>
   <td><strong>Loss</strong>
   </td>
  </tr>
  <tr>
   <td>0.001
   </td>
   <td>6.62
   </td>
  </tr>
  <tr>
   <td>0.0001
   </td>
   <td>26.24
   </td>
  </tr>
  <tr>
   <td>0.0003
   </td>
   <td>26.44
   </td>
  </tr>
  <tr>
   <td>0.01
   </td>
   <td>34.37
   </td>
  </tr>
</table>



## Milestones


<table>
  <tr>
   <td><strong>Milestone</strong>
   </td>
   <td><strong>Planned finish date</strong>
   </td>
   <td><strong>State</strong>
   </td>
  </tr>
  <tr>
   <td>Create a base Docker image which enables training on AI Platform.
   </td>
   <td>2020 - 07 - 24
   </td>
   <td><strong>Completed</strong>
   </td>
  </tr>
  <tr>
   <td>Create a simple UI script that gathers input, builds the image and runs the training job
   </td>
   <td>2020 - 08 - 05
   </td>
   <td><strong>Completed</strong>
   </td>
  </tr>
  <tr>
   <td>Enable hyperparameter tuning using <code>cloudml-hypertune</code>
   </td>
   <td>2020 - 08 - 12
   </td>
   <td><strong>Completed</strong>
   </td>
  </tr>
  <tr>
   <td>Make internal change in Magenta DDSP Library with hyperparameter reporting function.
   </td>
   <td>        
<p>
2020 - 08 - 25
   </td>
   <td><strong>Completed</strong>
   </td>
  </tr>
  <tr>
   <td>PR with final Docker configuration (Dockerfile, task.py, configs, documentation)
   </td>
   <td>2020 - 09 - 18
   </td>
   <td><strong>Completed</strong>
   </td>
  </tr>
  <tr>
   <td>Web interface (uploading audio files to bucket, submitting training job, downloading model, enabling tensorboard)
   </td>
   <td>2020 - 09 - 25
   </td>
   <td><strong>Completed</strong>
   </td>
  </tr>
</table>



## Future Work


### Training with TPUs



*   **_Our docker container uses a base image optimised for GPUs, so in this case the master VM and the TPU workers each have to run different containers._**
*   **_The TPU workers'  tpuTfVersion has to be set to a runtime version that includes the version of TensorFlow that the main container uses. That would be TensorFlow 2.3._**
*   **_When using a custom container, we have to wait for the TPU to be provisioned before we can call TPUClusterResolver to use it. This can be achieved by writing a new function<code> wait_for_tpu_cluster_resolver_ready().</code></em></strong>

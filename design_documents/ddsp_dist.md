
## DDSP-Docker 


## Distributed Training


**Author:** werror

**Reviewers:** zeos, dwalter, jesseengel

**Status:** Final 

**Originally Proposed:** 2020-07-30 

**Last Updated:** 2020-09-22

**Self link:** go/ddsp-dist


## Objective  

_[Magenta library](https://magenta.tensorflow.org/) provides two code examples (demos) which can be accessed via Google Colab. We would like to make it possible to run them on [Cloud AI Platform](https://cloud.google.com/ai-platform). We aim to make the training quicker and smoother._


## Background

[Magenta DDSP](https://github.com/magenta/ddsp/tree/3e891aaae0d724c4a6318036108483d6b58e86ee) (Differentiable Digital Signal Processing) library enables integration of signal processing elements with deep learning methods.

Existing code examples have following functionalities::



1. **[Training DDSP Autoencoder](https://github.com/magenta/ddsp/blob/master/ddsp/colab/demos/train_autoencoder.ipynb)**- it is possible to specify training parameters (batch size, number of training steps) and necessary directories (dataset, snapshots, trained parameters) as arguments of command line call `ddsp_run` or as a [gin](https://github.com/google/gin-config) file (command line arguments overwrite gin specification)
2. **[DDSP Timbre Transfer](https://github.com/magenta/ddsp/blob/master/ddsp/colab/demos/timbre_transfer.ipynb)** - it is possible to use a pretrained model to transfer instrument timbre on to user-provided audio.

Training can take up to 20 hours which is a little bit problematic in Colab because a maximum lifetime of a Colab instance is 12 hours, so the user needs to manually resume training. By enabling training on [Cloud AI Platform](https://cloud.google.com/ai-platform) we would like to simplify this process. 

When the DDSP library is installed it comes with its internal functions implementation and example usage code pieces (**<code>[ddsp_run.py](https://github.com/magenta/ddsp/blob/3e891aaae0d724c4a6318036108483d6b58e86ee/ddsp/training/ddsp_run.py)</code>** with gin configuration files). Example code can be easily separated from the library internals so we are able to edit it without interfering with core library functions.

We plan to use [custom Docker containers](https://cloud.google.com/ai-platform/training/docs/containers-overview) to run the application.


## Design Decisions


### Enabling various machine configurations


#### One Virtual Machine

Current implementation enables to train the model on more than one GPU but on a single VM. To enable the training on Cloud AI Platform [configuration file](https://cloud.google.com/ai-platform/training/docs/using-gpus#submit-job) should be attached to the job submission, where scaleTier is specified as CUSTOM and masterType is one of the machine types mentioned here in the [Comparing machine types](https://cloud.google.com/ai-platform/training/docs/machine-types#compare-machine-types) section. Detailed description of the config file parameters can be found in [AI Platform Training & Prediction API documentation](https://developers.google.com/resources/api-libraries/documentation/ml/v1/python/latest/ml_v1.projects.jobs.html).


#### More Virtual Machines

To run the training on multiple machines the existing implementation needs to change. 

MultiWorkerMirroredStrategy can be added to <code>[train_util.get_strategy()](https://github.com/magenta/ddsp/blob/3e891aaae0d724c4a6318036108483d6b58e86ee/ddsp/training/train_util.py)</code> function. To avoid mandatory global injection in library internals I will add the possibility to pass cluster configuration as a function parameter not as a set environment variable (default option of <code>[tf.distribute.experimental.MultiWorkerMirroredStrategy()](https://www.tensorflow.org/api_docs/python/tf/distribute/experimental/MultiWorkerMirroredStrategy?hl=TR)</code>). I will also add a flag for cluster specification in <strong><code>ddsp_run.py</code></strong>.

While training on AI Platform I will infer the cluster configuration from the environment variable and pass it inside the function.

An alternative solution is discussed in the 
[Alternatives Considered](#heading=h.pttsmxvrf1hf) section.


#### Change in hyperparameters

During the training provided data points are distributed among all the GPUs present in the cluster. Batch size given  in configuration is a total batch size which gets divided between available workers (total\_batch\_size = number\_of\_VMs\*batch\_size\_per\_worker). The default batch size for the training is 16 data examples.

If we want our cluster to have more than 16 properly utilized GPUs we will need to enlarge the total batch size. This will influence the choice of learning rate. We need to find out how big batches can be for this model to train well and how to adjust the learning rate accordingly. 


#### Disabling writing for non-chief workers

Workers shouldn’t write model checkpoints and training summaries to the same directory at once. I decided that non-chief workers will skip the writing completely so additional space in GCS bucket or in VM memory is not taken. To accomplish this I will add a possibility to pass None as a save\_dir in <code>train_util.train()<strong> </strong></code>as an indicator of writing skipping.


### Enabling early stopping

According to the instructions in [Train a DDSP Autoencoder Colab](https://github.com/magenta/ddsp/blob/master/ddsp/colab/demos/train_autoencoder.ipynb) it is recommended to stop the training when the loss drops to the range of ~4.5-5.0. However, current implementation doesn’t provide a way to tell the training loop to stop the training after the loss function reaches some specific value. It is not an issue in Colab as there you can quickly stop and resume the training using stored checkpoints, but if we want to provide a training pipeline that doesn’t involve user interaction it would be a nice feature to have. To the best of my knowledge it can’t be done from the **<code>ddsp_run.py</code></strong> file so I would need to modify the library internals.

It can be achieved by adding an early\_stop\_loss\_value parameter to the <code>[train_utils.train()](https://github.com/magenta/ddsp/blob/3e891aaae0d724c4a6318036108483d6b58e86ee/ddsp/training/train_util.py) </code>function. Then inside the training loop current loss function value would be compared with the value specified by the provided parameter and training would be stopped or continued accordingly. This new parameter may be set in the gin file or as a <strong><code>ddsp_run.py</code></strong> parameter.


### Adding the possibility to resume training

Existing code enables to save training snapshots so the user can resume the training. However, when bucket directory is provided as `restore_dir`, `gin.parse_config_file()` function is not able to access it, which results in error.
In order to overcome this issue, I will add a function which downloads the most recent operative\_config (file created when a new job is run) from the bucket to the container directory: `/root/trainer/gin`. 


### Determining the most efficient machine configuration

I would like to specify the most time efficient and the most cost efficient configurations for the given training and write configuration files for these setups. The user will have the possibility to specify their own config.yaml file or to use one of the configs provided by us.

After reading about [GPUs available on Google Cloud Platform](https://cloud.google.com/blog/products/ai-machine-learning/your-ml-workloads-cheaper-and-faster-with-the-latest-gpus) and running some comparison experiments I decided to use only NVIDIA T4 GPUs in specified configurations as they are the most cost efficient. I compared NVIDIA T4 with NVIDIA K80 and NVIDIA V100. Training with K80s is more expensive and slower. V100s are quicker than T4s but they are very expensive.

I ran all the training sessions on the dataset consisting of ~13 minutes of music. I took following approach while determining the most efficient configurations:



1. **Determine the batch size which fosters model convergence in the most effective way**. 

    I wanted to find the batch size and learning rate that will make the loss function converge in the smallest number of steps


    For batch sizes listed below I ran training sessions which ended when 30000 training steps were made or when total\_loss reached a value of 5.0 whichever happened first.


    I asked my STEP partner for help in determining the best learning rate for each batch size as she was working on hyperparameter tuning at that time. Following hyperparameters gave promising results:


<table>
  <tr>
   <td>
Batch size
   </td>
   <td colspan="2" >8
   </td>
   <td>16
   </td>
   <td colspan="2" >32
   </td>
   <td colspan="3" >64
   </td>
   <td>128
   </td>
   <td>256
   </td>
  </tr>
  <tr>
   <td>Learning rate
   </td>
   <td>0.0001
   </td>
   <td>0.001
   </td>
   <td>0.0001
   </td>
   <td>0.0001
   </td>
   <td>0.001
   </td>
   <td>0.0001*
   </td>
   <td>0.0003*
   </td>
   <td>0.001*
   </td>
   <td>0.001
   </td>
   <td>0.001**
   </td>
  </tr>
</table>


\*No promising results found with hyper-parameter tuning so I’ve chosen the same value as for batch size 32.

\*\*It was not possible to tune the learning rate  for batch size 256 so I’ve chosen the same value as for batch size 128 in addition to the standard lr for this batch\_size (0.0003)


    I ran 3 training sessions for each (batch_size, learning rate) pair. Averages and medians of the results are presented below:


<table>
  <tr>
   <td>Batch_size/
<p>
learning rate
   </td>
   <td>Loss converged to value of 5.0 in 30000 steps
   </td>
   <td>Number of steps after loss converged to value of 5.0
   </td>
   <td>Value of loss function at step 30000
   </td>
  </tr>
  <tr>
   <td>8/0.0001
   </td>
   <td>0/3
   </td>
   <td>-
   </td>
   <td>Avg: 5.70, Med: 5.68
   </td>
  </tr>
  <tr>
   <td>8/0.001
   </td>
   <td>0/3
   </td>
   <td>-
   </td>
   <td>Avg: 6.10, Med: 6.03
   </td>
  </tr>
  <tr>
   <td>16/0.0001
   </td>
   <td>0/3
   </td>
   <td>-
   </td>
   <td>Avg: 5.16,  Med:5.16
   </td>
  </tr>
  <tr>
   <td>32/0.0001
   </td>
   <td>0/3
   </td>
   <td>-
   </td>
   <td>Avg: 5.28,  Med:5.24
   </td>
  </tr>
  <tr>
   <td>32/0.001
   </td>
   <td>0/3
   </td>
   <td>-
   </td>
   <td>Avg: 5.51,  Med:5.50
   </td>
  </tr>
  <tr>
   <td><strong>64/0.0001</strong>
   </td>
   <td><strong>3/3</strong>
   </td>
   <td><strong>Avg: 24 937,  Med:24 405</strong>
   </td>
   <td><strong>-</strong>
   </td>
  </tr>
  <tr>
   <td>64/0.0003
   </td>
   <td>2/3
   </td>
   <td>Avg: 19 870
   </td>
   <td> 6.70
   </td>
  </tr>
  <tr>
   <td>64/0.001
   </td>
   <td>0/3
   </td>
   <td>-
   </td>
   <td>Avg: 5.38,  Med:5.39
   </td>
  </tr>
  <tr>
   <td><strong>128/0.001*</strong>
   </td>
   <td><strong>3/3</strong>
   </td>
   <td><strong>Avg: 13 963,  Med:14 787</strong>
   </td>
   <td><strong>-</strong>
   </td>
  </tr>
  <tr>
   <td><strong>256/0.001</strong>
   </td>
   <td><strong>3/3</strong>
   </td>
   <td><strong>Avg: 12 364, 13 505</strong>
   </td>
   <td><strong>-</strong>
   </td>
  </tr>
</table>


\* Result for training with 4x2 cluster configuration. For more details, see 
[Detailed data](#heading=h.e15naja6ovck) section.


    Seeing that  for some of the above setups loss would probably converge given more training steps I reran two of them (16/0.0001, 32/0.0001) with the ceiling number of steps set to 45000. 


<table>
  <tr>
   <td>Batch_size/
<p>
learning rate
   </td>
   <td>Loss converged to value of 5.0 in 45000 steps
   </td>
   <td>Number of steps after loss converged to value of 5.0
   </td>
   <td>Value of loss function at step 45000
   </td>
  </tr>
  <tr>
   <td><strong>16/0.0001</strong>
   </td>
   <td><strong>3/3</strong>
   </td>
   <td><strong>Avg: 39 762,  Med: 39 401</strong>
   </td>
   <td><strong>-</strong>
   </td>
  </tr>
  <tr>
   <td><strong>32/0.0001</strong>
   </td>
   <td><strong>3/3</strong>
   </td>
   <td><strong>Avg: 39 419,  Med: 38 649</strong>
   </td>
   <td><strong>-</strong>
   </td>
  </tr>
</table>



**Conclusion**: As 5 of the (batch\_size, learning\_rate) pairs converged to the recommended value of 5.0 I decided to proceed with them to the next stage.



2. **Picking the right number of GPUs.**

    Maximum batch size per GPU is 32. 

*   As for batch size 128 and 256 loss converges in a small number of steps which means quicker training I decided to optimise this setup for the speed of training. 
*   Because batch size 64 lets us use less GPUs I decided to optimise the setup with batch size 64 for the cost efficiency. I also compared it with longer training jobs (16/0.0001, 32/0.0001) because they would make it possible to use only one GPU.
1. The most time efficient setup

    Having two batch sizes that let the loss function converge in a similar number of steps (128, 256) I decided to go with the smaller batch size because it leads to smaller batch\_size/GPU ratio and shorter time of training step. I decided to distribute this batch size to 8 GPUs instead of 4GPUs because then the length of each training step shortens from around 1.3 seconds to around 1.1 seconds. Maximum number of T4 GPUs per VM is 4. I saw slightly better time performance for 4x2GPUs than 2x4GPUs setup. Ceiling number of steps for this setup should be set to 15000.


    **Conclusion**:


<table>
  <tr>
   <td rowspan="2" >
<strong>Most time efficient setup</strong>
   </td>
   <td>Number of VMs
   </td>
   <td>Number of GPUs in total
   </td>
   <td>GPU type
   </td>
   <td>Machine type
   </td>
   <td>Average length of training (hh:mm)
   </td>
   <td>Price
<p>
 (ML units*)
   </td>
  </tr>
  <tr>
   <td>4
   </td>
   <td>8
   </td>
   <td>NVIDIA Tesla T4
   </td>
   <td>n1-highcpu-16
   </td>
   <td><strong>4:11</strong>
   </td>
   <td>43.9
   </td>
  </tr>
</table>


\*[Current ML unit prices](https://cloud.google.com/ai-platform/training/pricing#ml-units)



2. The most cost efficient setup

    I ran training sessions with batch size 64 on 2 GPUs and 4 GPUs. I observed that given 2 GPUs one training step lasts around 1.2s while given 4 GPUs it lasts around 1.0s. Simultaneously, doubling the number of GPUs doubles the cost of training (from around 23 ML units to around 44 ML units). **However running the training with only 1 GPU and batch\_size=16 lets lowers the number of consumed ML units to around 18.6, so I decided to choose this setup as the most cost efficient.**  Ceiling number of steps for this setup should be set to 40000.


    **Conclusion**:


<table>
  <tr>
   <td rowspan="2" >
<strong>Most cost efficient setup</strong>
   </td>
   <td>Number of VMs
   </td>
   <td>Number of GPUs in total
   </td>
   <td>GPU type
   </td>
   <td>Machine type
   </td>
   <td>Average length of training (hh:mm)
   </td>
   <td>Price
<p>
 (ML units*)
   </td>
  </tr>
  <tr>
   <td>1
   </td>
   <td>1
   </td>
   <td>NVIDIA Tesla T4
   </td>
   <td>n1-highcpu-16
   </td>
   <td>9:48
   </td>
   <td><strong>18.6</strong>
   </td>
  </tr>
</table>


\*[Current ML unit prices](https://cloud.google.com/ai-platform/training/pricing#ml-units)

**Note on V100s**

Running the training with 8 V100s instead of 8 T4s and with the same hyperparameters setting reduced the length of the training from slightly above 4 hours to slightly above 3 hours. However, as V100 is 4 times more expensive than T4 I decided to prepare the configs with T4s.


## Alternatives Considered


### Enabling various machine configurations


#### More Virtual Machines

The example code can be copied inside the docker container together with all necessary gin configuration files. Then we need to change strategy function call from <code>[train_utils.get_strategy()](https://github.com/magenta/ddsp/blob/3e891aaae0d724c4a6318036108483d6b58e86ee/ddsp/training/train_util.py)</code> (a ddsp library function, which chooses between possible strategies for single machine) to <code>[tf.distribute.experimental.MultiWorkerMirroredStrategy()](https://www.tensorflow.org/api_docs/python/tf/distribute/experimental/MultiWorkerMirroredStrategy?hl=TR).</code> While submitting the job to Cloud AI Platform we need to attach config.yaml file with chosen cluster specification (as in [One Virtual Machine](#heading=h.jv86a8dic0a4) section). The AI Platform will then automatically set the <code>[TF_CONFIG](https://cloud.google.com/ai-platform/training/docs/distributed-training-details)</code> environment variable on each machine (<code>TF_CONFIG</code> is needed for MultiWorkerMirroredStrategy).

This solution was easier to implement than the one described in [Design Decisions](#heading=h.kgjxkc7lm1vc) and was enough for our Internship repository, however its structure was not proper for the PR to the Magenta DDSP library so at last I decided against it. 


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
   <td>2020-07-24
   </td>
   <td>Completed
   </td>
  </tr>
  <tr>
   <td>Enable training on multiple VMs to make the training even faster.
   </td>
   <td>2020-08-03
   </td>
   <td>Completed
   </td>
  </tr>
  <tr>
   <td>Determine most efficient cluster configurations.
   </td>
   <td>2020-08-21
   </td>
   <td>Completed
   </td>
  </tr>
  <tr>
   <td>Make internal Magenta DDSP changes (described above) together with their unit tests.
   </td>
   <td>2020-08-28
   </td>
   <td>Completed
   </td>
  </tr>
  <tr>
   <td>PR with final Docker configuration  \
(Dockerfile, task.py, task_test.py, configs, documentation)
   </td>
   <td>2020-09-03
   </td>
   <td>Completed
   </td>
  </tr>
  <tr>
   <td>Web interface (authentication, setting up a VM with server, containerizing data preprocessing and statistics computation, documentation)
   </td>
   <td>2020-09-15
   </td>
   <td>Completed
   </td>
  </tr>
</table>



## Future Work



*   **Write dockerfile for evaluation**, with externally visible entry-point for online timbre transfer


## 


## Detailed data (go/ddsp-dist-training-data)


<table>
  <tr>
   <td>Batch_size/
<p>
learning_rate
   </td>
   <td>Number of training steps
   </td>
   <td>Loss function value at the last step
   </td>
   <td>Cluster setup
   </td>
   <td>Length (hh:mm)
   </td>
   <td>Consumed ML units
   </td>
   <td>Time/Number of steps (s)
   </td>
   <td>ML Unit/Time
   </td>
  </tr>
  <tr>
   <td colspan="8" >30000 training steps or loss vale 5.0, whichever happens first
   </td>
  </tr>
  <tr>
   <td rowspan="3" >8/0.0001
   </td>
   <td>30000
   </td>
   <td>5.76
   </td>
   <td>1x1
   </td>
   <td>6:31:00
   </td>
   <td>12.34
   </td>
   <td>0.78
   </td>
   <td>45.45
   </td>
  </tr>
  <tr>
   <td>30000
   </td>
   <td>5.68
   </td>
   <td>1x1
   </td>
   <td>6:17:00
   </td>
   <td>11.88
   </td>
   <td>0.75
   </td>
   <td>45.38
   </td>
  </tr>
  <tr>
   <td>30000
   </td>
   <td>5.66
   </td>
   <td>1x1
   </td>
   <td>6:27:00
   </td>
   <td>12.21
   </td>
   <td>0.77
   </td>
   <td>45.43
   </td>
  </tr>
  <tr>
   <td><strong>AVG</strong>
   </td>
   <td><strong>30000</strong>
   </td>
   <td><strong>5.70</strong>
   </td>
   <td>
   </td>
   <td><strong>6:25:00</strong>
   </td>
   <td><strong>12.14</strong>
   </td>
   <td><strong>0.77</strong>
   </td>
   <td><strong>45.42</strong>
   </td>
  </tr>
  <tr>
   <td><strong>MEDIAN</strong>
   </td>
   <td><strong>30000</strong>
   </td>
   <td><strong>5.68</strong>
   </td>
   <td>
   </td>
   <td><strong>6:27:00</strong>
   </td>
   <td><strong>12.21</strong>
   </td>
   <td><strong>0.77</strong>
   </td>
   <td><strong>45.43</strong>
   </td>
  </tr>
  <tr>
   <td rowspan="3" >8/0.001
   </td>
   <td>30000
   </td>
   <td>6.02
   </td>
   <td>1x1
   </td>
   <td>6:30:00
   </td>
   <td>12.29
   </td>
   <td>0.78
   </td>
   <td>45.38
   </td>
  </tr>
  <tr>
   <td>30000
   </td>
   <td>6.24
   </td>
   <td>1x1
   </td>
   <td>6:32:00
   </td>
   <td>12.37
   </td>
   <td>0.78
   </td>
   <td>45.44
   </td>
  </tr>
  <tr>
   <td>30000
   </td>
   <td>6.03
   </td>
   <td>1x1
   </td>
   <td>6:14:00
   </td>
   <td>11.80
   </td>
   <td>0.75
   </td>
   <td>45.43
   </td>
  </tr>
  <tr>
   <td><strong>AVG</strong>
   </td>
   <td><strong>30000</strong>
   </td>
   <td><strong>6.10</strong>
   </td>
   <td>
   </td>
   <td><strong>6:25:20</strong>
   </td>
   <td><strong>12.15</strong>
   </td>
   <td><strong>0.77</strong>
   </td>
   <td><strong>45.42</strong>
   </td>
  </tr>
  <tr>
   <td><strong>MEDIAN</strong>
   </td>
   <td><strong>30000</strong>
   </td>
   <td><strong>6.03</strong>
   </td>
   <td>
   </td>
   <td><strong>6:30:00</strong>
   </td>
   <td><strong>12.29</strong>
   </td>
   <td><strong>0.78</strong>
   </td>
   <td><strong>45.38</strong>
   </td>
  </tr>
  <tr>
   <td rowspan="3" >16/0.0001
   </td>
   <td>30000
   </td>
   <td>5.16
   </td>
   <td>1x1
   </td>
   <td>7:29:00
   </td>
   <td>14.17
   </td>
   <td>0.90
   </td>
   <td>45.44
   </td>
  </tr>
  <tr>
   <td>30000
   </td>
   <td>5.17
   </td>
   <td>1x1
   </td>
   <td>7:24:00
   </td>
   <td>13.99
   </td>
   <td>0.89
   </td>
   <td>45.37
   </td>
  </tr>
  <tr>
   <td>30000
   </td>
   <td>5.15
   </td>
   <td>1x1
   </td>
   <td>7:29:00
   </td>
   <td>14.16
   </td>
   <td>0.90
   </td>
   <td>45.41
   </td>
  </tr>
  <tr>
   <td><strong>AVG</strong>
   </td>
   <td><strong>30000</strong>
   </td>
   <td><strong>5.16</strong>
   </td>
   <td>
   </td>
   <td><strong>7:27:20</strong>
   </td>
   <td><strong>14.11</strong>
   </td>
   <td><strong>0.89</strong>
   </td>
   <td><strong>45.41</strong>
   </td>
  </tr>
  <tr>
   <td><strong>MEDIAN</strong>
   </td>
   <td><strong>30000</strong>
   </td>
   <td><strong>5.16</strong>
   </td>
   <td>
   </td>
   <td><strong>7:29:00</strong>
   </td>
   <td><strong>14.16</strong>
   </td>
   <td><strong>0.90</strong>
   </td>
   <td><strong>45.41</strong>
   </td>
  </tr>
  <tr>
   <td rowspan="3" >32/0.0001
   </td>
   <td>30000
   </td>
   <td>5.24
   </td>
   <td>1x1
   </td>
   <td>9:40:00
   </td>
   <td>18.29
   </td>
   <td>1.16
   </td>
   <td>45.41
   </td>
  </tr>
  <tr>
   <td>30000
   </td>
   <td>5.24
   </td>
   <td>1x1
   </td>
   <td>9:57:00
   </td>
   <td>18.85
   </td>
   <td>1.19
   </td>
   <td>45.47
   </td>
  </tr>
  <tr>
   <td>30000
   </td>
   <td>5.36
   </td>
   <td>1x1
   </td>
   <td>9:49:00
   </td>
   <td>18.58
   </td>
   <td>1.18
   </td>
   <td>45.42
   </td>
  </tr>
  <tr>
   <td><strong>AVG</strong>
   </td>
   <td><strong>30000</strong>
   </td>
   <td><strong>5.28</strong>
   </td>
   <td>
   </td>
   <td><strong>9:48:40</strong>
   </td>
   <td><strong>18.57</strong>
   </td>
   <td><strong>1.18</strong>
   </td>
   <td><strong>45.43</strong>
   </td>
  </tr>
  <tr>
   <td><strong>MEDIAN</strong>
   </td>
   <td><strong>30000</strong>
   </td>
   <td><strong>5.24</strong>
   </td>
   <td>
   </td>
   <td><strong>9:49:00</strong>
   </td>
   <td><strong>18.58</strong>
   </td>
   <td><strong>1.18</strong>
   </td>
   <td><strong>45.42</strong>
   </td>
  </tr>
  <tr>
   <td rowspan="3" >32/0.001
   </td>
   <td>30000
   </td>
   <td>5.49
   </td>
   <td>1x1
   </td>
   <td>9:58:00
   </td>
   <td>18.88
   </td>
   <td>1.20
   </td>
   <td>45.46
   </td>
  </tr>
  <tr>
   <td>30000
   </td>
   <td>5.50
   </td>
   <td>1x1
   </td>
   <td>9:48:00
   </td>
   <td>18.58
   </td>
   <td>1.18
   </td>
   <td>45.50
   </td>
  </tr>
  <tr>
   <td>30000
   </td>
   <td>5.55
   </td>
   <td>1x1
   </td>
   <td>9:48:00
   </td>
   <td>18.58
   </td>
   <td>1.18
   </td>
   <td>45.50
   </td>
  </tr>
  <tr>
   <td><strong>AVG</strong>
   </td>
   <td><strong>30000</strong>
   </td>
   <td><strong>5.51</strong>
   </td>
   <td>
   </td>
   <td><strong>9:51:20</strong>
   </td>
   <td><strong>18.68</strong>
   </td>
   <td><strong>1.18</strong>
   </td>
   <td><strong>45.49</strong>
   </td>
  </tr>
  <tr>
   <td><strong>MEDIAN</strong>
   </td>
   <td><strong>30000</strong>
   </td>
   <td><strong>5.50</strong>
   </td>
   <td>
   </td>
   <td><strong>9:48:00</strong>
   </td>
   <td><strong>18.58</strong>
   </td>
   <td><strong>1.18</strong>
   </td>
   <td><strong>45.50</strong>
   </td>
  </tr>
  <tr>
   <td rowspan="3" >64/0.0001
   </td>
   <td>24405
   </td>
   <td>5.00
   </td>
   <td>1x2
   </td>
   <td>8:29:00
   </td>
   <td>21.95
   </td>
   <td>1.25
   </td>
   <td>62.10
   </td>
  </tr>
  <tr>
   <td>24248
   </td>
   <td>5.00
   </td>
   <td>1x2
   </td>
   <td>8:35:00
   </td>
   <td>22.22
   </td>
   <td>1.27
   </td>
   <td>62.13
   </td>
  </tr>
  <tr>
   <td>26157
   </td>
   <td>5.00
   </td>
   <td>1x2
   </td>
   <td>9:08:00
   </td>
   <td>23.67
   </td>
   <td>1.26
   </td>
   <td>62.20
   </td>
  </tr>
  <tr>
   <td><strong>AVG</strong>
   </td>
   <td><strong>24937</strong>
   </td>
   <td><strong>5.00</strong>
   </td>
   <td>
   </td>
   <td><strong>8:44:00</strong>
   </td>
   <td><strong>22.61</strong>
   </td>
   <td><strong>1.26</strong>
   </td>
   <td><strong>62.14</strong>
   </td>
  </tr>
  <tr>
   <td><strong>MEDIAN</strong>
   </td>
   <td><strong>24405</strong>
   </td>
   <td><strong>5.00</strong>
   </td>
   <td>
   </td>
   <td><strong>8:35:00</strong>
   </td>
   <td><strong>22.22</strong>
   </td>
   <td><strong>1.26</strong>
   </td>
   <td><strong>62.13</strong>
   </td>
  </tr>
  <tr>
   <td rowspan="3" >64/0.0003
   </td>
   <td>30000
   </td>
   <td>6.70
   </td>
   <td>1x2
   </td>
   <td>10:39:00
   </td>
   <td>27.60
   </td>
   <td>1.28
   </td>
   <td>62.20
   </td>
  </tr>
  <tr>
   <td>20420
   </td>
   <td>5.00
   </td>
   <td>1x2
   </td>
   <td>7:15:00
   </td>
   <td>18.74
   </td>
   <td>1.28
   </td>
   <td>62.04
   </td>
  </tr>
  <tr>
   <td>19320
   </td>
   <td>5.00
   </td>
   <td>1x2
   </td>
   <td>6:46:00
   </td>
   <td>17.52
   </td>
   <td>1.26
   </td>
   <td>62.14
   </td>
  </tr>
  <tr>
   <td><strong>AVG</strong>
   </td>
   <td><strong>23247</strong>
   </td>
   <td><strong>5.57</strong>
   </td>
   <td>
   </td>
   <td><strong>8:13:20</strong>
   </td>
   <td><strong>21.29</strong>
   </td>
   <td><strong>1.27</strong>
   </td>
   <td><strong>62.12</strong>
   </td>
  </tr>
  <tr>
   <td><strong>MEDIAN</strong>
   </td>
   <td><strong>20420</strong>
   </td>
   <td><strong>5.00</strong>
   </td>
   <td>
   </td>
   <td><strong>7:15:00</strong>
   </td>
   <td><strong>18.74</strong>
   </td>
   <td><strong>1.28</strong>
   </td>
   <td><strong>62.14</strong>
   </td>
  </tr>
  <tr>
   <td rowspan="3" >64/0.001
   </td>
   <td>30000
   </td>
   <td>5.39
   </td>
   <td>1x2
   </td>
   <td>10:33:00
   </td>
   <td>27.34
   </td>
   <td>1.27
   </td>
   <td>62.20
   </td>
  </tr>
  <tr>
   <td>30000
   </td>
   <td>5.27
   </td>
   <td>1x2
   </td>
   <td>10:25:00
   </td>
   <td>26.99
   </td>
   <td>1.25
   </td>
   <td>62.18
   </td>
  </tr>
  <tr>
   <td>30000
   </td>
   <td>5.47
   </td>
   <td>1x4
   </td>
   <td>8:26:00
   </td>
   <td>43.87
   </td>
   <td>1.01
   </td>
   <td>124.85
   </td>
  </tr>
  <tr>
   <td><strong>AVG</strong>
   </td>
   <td><strong>30000</strong>
   </td>
   <td><strong>5.38</strong>
   </td>
   <td>
   </td>
   <td><strong>9:48:00</strong>
   </td>
   <td>
   </td>
   <td>
   </td>
   <td>
   </td>
  </tr>
  <tr>
   <td><strong>MEDIAN</strong>
   </td>
   <td><strong>30000</strong>
   </td>
   <td><strong>5.39</strong>
   </td>
   <td>
   </td>
   <td><strong>10:25:00</strong>
   </td>
   <td>
   </td>
   <td>
   </td>
   <td>
   </td>
  </tr>
  <tr>
   <td rowspan="3" >128/0.001
   </td>
   <td>11336
   </td>
   <td>4.98
   </td>
   <td>4x2
   </td>
   <td>3:19:00
   </td>
   <td>34.82
   </td>
   <td>1.05
   </td>
   <td>251.96
   </td>
  </tr>
  <tr>
   <td>14787
   </td>
   <td>4.99
   </td>
   <td>4x2
   </td>
   <td>4:32:00
   </td>
   <td>47.46
   </td>
   <td>1.10
   </td>
   <td>251.26
   </td>
  </tr>
  <tr>
   <td>15768
   </td>
   <td>5.00
   </td>
   <td>4x2
   </td>
   <td>4:43:00
   </td>
   <td>49.34
   </td>
   <td>1.08
   </td>
   <td>251.06
   </td>
  </tr>
  <tr>
   <td><strong>AVG</strong>
   </td>
   <td><strong>13964</strong>
   </td>
   <td><strong>4.99</strong>
   </td>
   <td>
   </td>
   <td><strong>4:11:20</strong>
   </td>
   <td><strong>43.87</strong>
   </td>
   <td><strong>1.08</strong>
   </td>
   <td><strong>251.43</strong>
   </td>
  </tr>
  <tr>
   <td><strong>MEDIAN</strong>
   </td>
   <td><strong>14787</strong>
   </td>
   <td><strong>4.99</strong>
   </td>
   <td>
   </td>
   <td><strong>4:32:00</strong>
   </td>
   <td><strong>47.46</strong>
   </td>
   <td><strong>1.08</strong>
   </td>
   <td><strong>251.26</strong>
   </td>
  </tr>
  <tr>
   <td rowspan="3" >128/0.001
   </td>
   <td>14957
   </td>
   <td>4.99
   </td>
   <td>2x4
   </td>
   <td>4:36:00
   </td>
   <td>48.23
   </td>
   <td>1.11
   </td>
   <td>251.63
   </td>
  </tr>
  <tr>
   <td>18855
   </td>
   <td>5.00
   </td>
   <td>2x4
   </td>
   <td>5:50:00
   </td>
   <td>61.08
   </td>
   <td>1.11
   </td>
   <td>251.30
   </td>
  </tr>
  <tr>
   <td>13863
   </td>
   <td>4.99
   </td>
   <td>2x4
   </td>
   <td>4:18:00
   </td>
   <td>45.04
   </td>
   <td>1.12
   </td>
   <td>251.39
   </td>
  </tr>
  <tr>
   <td><strong>AVG</strong>
   </td>
   <td><strong>15892</strong>
   </td>
   <td><strong>4.99</strong>
   </td>
   <td>
   </td>
   <td><strong>4:54:40</strong>
   </td>
   <td><strong>51.45</strong>
   </td>
   <td><strong>1.11</strong>
   </td>
   <td><strong>251.44</strong>
   </td>
  </tr>
  <tr>
   <td><strong>MEDIAN</strong>
   </td>
   <td><strong>14957</strong>
   </td>
   <td><strong>4.99</strong>
   </td>
   <td>
   </td>
   <td><strong>4:36:00</strong>
   </td>
   <td><strong>48.23</strong>
   </td>
   <td><strong>1.11</strong>
   </td>
   <td><strong>251.39</strong>
   </td>
  </tr>
  <tr>
   <td rowspan="3" >256/0.001
   </td>
   <td>13505
   </td>
   <td>4.98
   </td>
   <td>4x2
   </td>
   <td>5:02:00
   </td>
   <td>52.68
   </td>
   <td>1.34
   </td>
   <td>251.19
   </td>
  </tr>
  <tr>
   <td>14277
   </td>
   <td>5.00
   </td>
   <td>4x2
   </td>
   <td>5:26:00
   </td>
   <td>56.98
   </td>
   <td>1.37
   </td>
   <td>251.69
   </td>
  </tr>
  <tr>
   <td>9311
   </td>
   <td>4.98
   </td>
   <td>4x2
   </td>
   <td>3:35:00
   </td>
   <td>37.55
   </td>
   <td>1.39
   </td>
   <td>251.50
   </td>
  </tr>
  <tr>
   <td><strong>AVG</strong>
   </td>
   <td><strong>12364</strong>
   </td>
   <td><strong>4.99</strong>
   </td>
   <td>
   </td>
   <td><strong>4:41:00</strong>
   </td>
   <td><strong>49.07</strong>
   </td>
   <td><strong>1.37</strong>
   </td>
   <td><strong>251.46</strong>
   </td>
  </tr>
  <tr>
   <td><strong>MEDIAN</strong>
   </td>
   <td><strong>13505</strong>
   </td>
   <td><strong>4.98</strong>
   </td>
   <td>
   </td>
   <td><strong>5:02:00</strong>
   </td>
   <td><strong>52.68</strong>
   </td>
   <td><strong>1.37</strong>
   </td>
   <td><strong>251.50</strong>
   </td>
  </tr>
  <tr>
   <td colspan="8" >45000 training steps or loss vale 5.0, whichever happens first
   </td>
  </tr>
  <tr>
   <td rowspan="3" >16/0.0001
   </td>
   <td>39401
   </td>
   <td>4.99
   </td>
   <td>1x1
   </td>
   <td>9:46:00
   </td>
   <td>18.50
   </td>
   <td>0.89
   </td>
   <td>45.46
   </td>
  </tr>
  <tr>
   <td>39401
   </td>
   <td>5.00
   </td>
   <td>1x1
   </td>
   <td>9:39:00
   </td>
   <td>18.28
   </td>
   <td>0.88
   </td>
   <td>45.46
   </td>
  </tr>
  <tr>
   <td>40484
   </td>
   <td>5.00
   </td>
   <td>1x1
   </td>
   <td>10:01:00
   </td>
   <td>18.97
   </td>
   <td>0.89
   </td>
   <td>45.45
   </td>
  </tr>
  <tr>
   <td><strong>AVG</strong>
   </td>
   <td><strong>39762</strong>
   </td>
   <td><strong>5.00</strong>
   </td>
   <td>
   </td>
   <td><strong>9:48:40</strong>
   </td>
   <td><strong>18.58</strong>
   </td>
   <td><strong>0.89</strong>
   </td>
   <td><strong>45.46</strong>
   </td>
  </tr>
  <tr>
   <td><strong>MEDIAN</strong>
   </td>
   <td><strong>39401</strong>
   </td>
   <td><strong>5.00</strong>
   </td>
   <td>
   </td>
   <td><strong>9:46:00</strong>
   </td>
   <td><strong>18.50</strong>
   </td>
   <td><strong>0.89</strong>
   </td>
   <td><strong>45.46</strong>
   </td>
  </tr>
  <tr>
   <td rowspan="3" >32/0.0001
   </td>
   <td>38649
   </td>
   <td>5.00
   </td>
   <td>1x1
   </td>
   <td>12:43:00
   </td>
   <td>24.11
   </td>
   <td>1.18
   </td>
   <td>45.50
   </td>
  </tr>
  <tr>
   <td>38640
   </td>
   <td>4.99
   </td>
   <td>1x1
   </td>
   <td>12:40:00
   </td>
   <td>24.00
   </td>
   <td>1.18
   </td>
   <td>45.47
   </td>
  </tr>
  <tr>
   <td>40968
   </td>
   <td>4.97
   </td>
   <td>1x1
   </td>
   <td>13:41:00
   </td>
   <td>25.92
   </td>
   <td>1.20
   </td>
   <td>45.46
   </td>
  </tr>
  <tr>
   <td><strong>AVG</strong>
   </td>
   <td><strong>39419</strong>
   </td>
   <td><strong>4.99</strong>
   </td>
   <td>
   </td>
   <td><strong>13:01:20</strong>
   </td>
   <td><strong>24.68</strong>
   </td>
   <td><strong>1.19</strong>
   </td>
   <td><strong>45.48</strong>
   </td>
  </tr>
  <tr>
   <td><strong>MEDIAN</strong>
   </td>
   <td><strong>38649</strong>
   </td>
   <td><strong>4.99</strong>
   </td>
   <td>
   </td>
   <td><strong>12:43:00</strong>
   </td>
   <td><strong>24.11</strong>
   </td>
   <td><strong>1.18</strong>
   </td>
   <td><strong>45.47</strong>
   </td>
  </tr>
  <tr>
   <td colspan="8" >Training with 8 V100s (15000 training steps or loss value 5.0, whichever happens first)
   </td>
  </tr>
  <tr>
   <td rowspan="3" >128/0.001
   </td>
   <td>13569
   </td>
   <td>4.99
   </td>
   <td>2x4
   </td>
   <td>3:26:00
   </td>
   <td>154.94
   </td>
   <td>0.91
   </td>
   <td>1,083.08
   </td>
  </tr>
  <tr>
   <td>14108
   </td>
   <td>5.00
   </td>
   <td>2x4
   </td>
   <td>3:34:00
   </td>
   <td>160.59
   </td>
   <td>0.91
   </td>
   <td>1,080.61
   </td>
  </tr>
  <tr>
   <td>11278
   </td>
   <td>5.00
   </td>
   <td>2x4
   </td>
   <td>2:57:00
   </td>
   <td>133.33
   </td>
   <td>0.94
   </td>
   <td>1,084.72
   </td>
  </tr>
  <tr>
   <td><strong>AVG</strong>
   </td>
   <td><strong>12985</strong>
   </td>
   <td><strong>5.00</strong>
   </td>
   <td>
   </td>
   <td><strong>3:19:00</strong>
   </td>
   <td><strong>149.62</strong>
   </td>
   <td><strong>0.92</strong>
   </td>
   <td><strong>1,082.80</strong>
   </td>
  </tr>
  <tr>
   <td><strong>MEDIAN</strong>
   </td>
   <td><strong>13569</strong>
   </td>
   <td><strong>5.00</strong>
   </td>
   <td>
   </td>
   <td><strong>3:26:00</strong>
   </td>
   <td><strong>154.94</strong>
   </td>
   <td><strong>0.91</strong>
   </td>
   <td><strong>1,083.08</strong>
   </td>
  </tr>
</table>


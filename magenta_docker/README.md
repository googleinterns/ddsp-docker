# DDSP Docker

Docker image for training autoencoder on [Google Cloud AI Platform](https://cloud.google.com/ai-platform).

### Before you begin
Make sure that you have completed the following steps:
* Set up your [GCP project](https://cloud.google.com/resource-manager/docs/creating-managing-projects)
* Create a [Google Cloud Storage Bucket](https://cloud.google.com/storage/docs/creating-buckets)
* Enable [AI Platform Training and Prediction, Container Registry, and Compute Engine APIs](https://pantheon.corp.google.com/flows/enableapi?apiid=ml.googleapis.com,compute_component,containerregistry.googleapis.com)
* Install [Docker](https://docs.docker.com/engine/install/)
* [Configure Docker for Cloud Container Registry](https://cloud.google.com/container-registry/docs/pushing-and-pulling)
* [Upload the training data](https://cloud.google.com/storage/docs/uploading-objects) in the [TFRecord](https://www.tensorflow.org/tutorials/load_data/tfrecord) format to the GCS bucket. You can preprocess your audio files into this format using the `ddsp_prepare_tfrecord` tool as described in [Making a TFRecord dataset from your own sounds](https://github.com/magenta/ddsp/tree/master/ddsp/training/data_preparation).

### Quickstart:

#### Define some environment variables

We recommend setting `$REGION` accordingly to your location. We also recommend to [setup hostname](https://cloud.google.com/container-registry/docs/pushing-and-pulling#tag_the_local_image_with_the_registry_name) in `$IMAGE_URI` based of the `$REGION` choice as if your Docker images are stored in different region than the job is computed additional charges will be applied. 

```bash
export PROJECT_ID=[YOUR_PROJECT_ID]
export SAVE_DIR=gs://[YOUR_STORAGE_BUCKET_NAME]/[PATH_IN_STORAGE_BUCKET]
export FILE_PATTERN=gs://[YOUR_STORAGE_BUCKET_NAME]/[PATH_IN_STORAGE_BUCKET]/train.tfrecord*
export IMAGE_REPO_NAME=ddsp_train
export IMAGE_TAG=ai_platform
export IMAGE_URI=gcr.io/$PROJECT_ID/$IMAGE_REPO_NAME:$IMAGE_TAG
export REGION=us-central1
export JOB_NAME=ddsp_container_job_$(date +%Y%m%d_%H%M%S)
```
#### Build the image and push it to Container Registry
In the folder containing `Dockerfile` and `task.py` run following commands: 
```bash
docker build -f Dockerfile -t $IMAGE_URI ./
docker push $IMAGE_URI
```

#### Submit the training to AI Platform
```bash
gcloud ai-platform jobs submit training $JOB_NAME \
  --region $REGION \
  --config config_single_vm.yaml \
  --master-image-uri $IMAGE_URI \
  -- \
  --save_dir=$SAVE_DIR \
  --file_pattern=$FILE_PATTERN \
  --batch_size=16 \
  --learning_rate=0.0001 \
  --num_steps=40000 \
  --early_stop_loss_value=5.0
```
##### AI Platform flags:
* `--region` - Region when the training job is run
* `--config` - Cluster configuration. In the example above, training on multiple VMs with multiple GPUs is set. For more information about various configurations take a look at **Note on cluster configuration and hyperparameters** below.
* `--master-image-uri` - URI of the Docker image you've built and submitted to Container Registry

##### Program flags:
* `--save_dir` - **Mandatory flag**. Bucket directory where checkpoints and summary events will be saved during training.
* `--file_pattern` - **Mandatory flag**. Pattern of the data files names. Must include a whole bucket directory.
* `--restore_dir` - Bucket directory from which checkpoints will be restored before training. When not provided defaults to save_dir. If there are no checkpoints in the given directory, training will resume.
* `--batch_size` - Batch size.
* `--learning_rate` - Learning rate.
* `--num_steps` - Number of training steps.
* `--early_loss_stop_value` - Early stopping. When the total_loss reaches below this value training stops.
* `--steps_per_save` - Steps per model save.
* `--restore_per_summary` - Steps per training summary save.
* `--hypertune` - If True enables metric reporting for hyperparameter tuning.

##### Additional configuration flags
* `--gin_param` - Gin parameter bindings. Using this flag requires some familiarity with the Magenta DDSP source code. Take a look at parameters you can specify in [Gin config files](https://github.com/magenta/ddsp/tree/master/ddsp/training/gin).
* `--gin_search_path` - Additional gin file search path. Must be path inside Docker container and necessary gin configs should be added at the Docker image building stage.
* `--gin_file` - Additional Gin config file. If the file is in gstorage bucket specify a whole gstorage path.


You can add your own Gin config files in two ways:
* Add Gin config file to the gstorage bucket and specify `--gin-file` as a gstorage path:
 ```bash 
 --gin_file=gs://[YOUR_STORAGE_BUCKET_NAME]/[PATH_IN_STORAGE_BUCKET]/config_file.gin
 ```
 * Add copying local Gin configs to the Dockerfile, build and push the image. Specify `--gin_search_path` flag as a directory inside the Docker container where gin file is located and `--gin-file` as a copied file name.


### Note on cluster configuration and hyperparameters

There are two cluster configurations prepared:
* `config_single_vm.yaml` - 1 VM configuration with 1 NVIDIA Tesla T4 GPUs. Training with this configuration and recommended parameters (*batch_size: 16, learning_rate:0.0001, num_steps:40000, early_stop_loss_value:5.0*) takes around 10 hours and consumes around 19 [ML units](https://cloud.google.com/ai-platform/training/pricing#ml-units).

* `config_multiple_vms.yaml` - 4 VM configuration with 8 NVIDIA Tesla T4 GPUs. Training with this configuration and recommended parameters (*batch_size: 128, learning_rate:0.001, num_steps:15000, early_stop_loss_value:5.0*) takes around 5 hours and consumes around 44 [ML units](https://cloud.google.com/ai-platform/training/pricing#ml-units).

Feel free to experiment and define your [cluster configurations](https://cloud.google.com/ai-platform/training/docs/using-gpus).

### Note on dataset location

Instead of uploading the preprocessed dataset into the GCS bucket, you can copy it inside the Docker container. To do so you need to place the folder with files in the same folder as Dockerfile and rebuild the image with the following code snippet added into Dockerfile:

```docker
COPY [FOLDER_WITH_DATA] /root/data
```
Then you should set the file pattern variable as follows:

```bash
export FILE_PATTERN=/root/data/train.tfrecord*
```
and complete the remaining steps as described above.

### Enabling Hyperparameter Tuning

In order to run a [hyperparameter tuning job on AI Platform](https://cloud.google.com/ai-platform/training/docs/hyperparameter-tuning-overview) you will have to add the following flag:

```bash
--hypertune=True
```
and use a configuration file that specifies the hyperparameter tuning configuration for your training job.
You can use the existing one in `docker/utils/hypertune_configurations/config_hypertune.yaml` used for tuning the learning rate or you can learn more about adding hyperparameter configuration information to your configuration YAML file [here](https://cloud.google.com/ai-platform/training/docs/using-hyperparameter-tuning#job-config).

### Enabling Tensorboard visualization

To enable Tensorboard you have to authenticate to `gcloud` and run the following command:

```bash
gcloud auth login
tensorboard --logdir=<path_to_save_dir> --port=8080
```

Then open your browser and go to `127.0.0.1:8080` to visualise your training.

If you want to share your ML experiment results you can use [TensorBoard.dev](https://tensorboard.dev/).
You have to install the latest version of TensorBoard to use the uploader:

```bash
pip install -U tensorboard
tensorboard dev upload --logdir <path_to_save_dir> \
    --name "(optional) <name>" \
    --description "(optional) <description>"
```

Then view your experiment on TensorBoard.dev. Follow the link provided to view your experiment, or share it with others.

To get a copy of the data uploaded to TensorBoard.dev run the following command:

```bash
tensorboard dev export --outdir OUTPUT_PATH
```

To delete an experiment you've uploaded to TensorBoard.dev run the following command. You can find your experiment id in the bottom left corner on your TensorBoard.dev link:

```bash
tensorboard dev delete --experiment_id EXPERIMENT_ID
```

### User Interaction Script:

Another way to build the image and submit the training on AI Platform is to use user_interaction.py.
To use it as a script, first add the path to where you have downloaded it and assign the execution permissions:

```bash
export PATH=<path_to_user_interaction.py>:$PATH
chmod +x user_interaction.py
```

Then just run `./user_interaction.py` from the directory you have it saved in and follow the instructions prompted.

The script will allow you to input the paths to the GCS Bucket where you have stored the preprocessed dataset and where you want to save the trained model and also choose parameters for the training job.
After submitting the training job, the script also enables TensorBoard visualisation on your local machine and uploads the logs to TensorBoard.dev for easily sharing the results of your ML experiment.

#### Paths
* `data_path` - Path to where the preprocessed dataset is saved.
* `save_dir` - Path to where checkpoints and summary events will be saved.
* `restore_dir` - Path from which checkpoints will be restored if you want to resume a training. Can be skipped and defaults to `save_dir`.

#### AI Platform parameters
* `config_path` - Path to a configuration file for training on AI Platform.
* `image_URI` - URI of the Docker image that will be built and submitted to Container Registry.
* `job_name` - Name for the training job that has to be unique in the GCP Project.
* `region`- Region where job is run.

#### Training parameters - all have default values that will be used if skipped at input
* `batch_size` - The batch size the training code will use (Default: 64).
* `learning_rate` - The learning rate the training code will use (Default: 0.0001).
* `no_of_steps` - Number of steps to execute before training stops (Default: 10000).
* `steps_per_save` - Number of steps after a snapshot is saved (Default: 300).
* `steps_per_summary` - Number of steps after a summary is saved (Default: 300).
* `early_stop_loss_value` - The training will be stopped before it finishes the number of steps if the loss value reaches this (Default: 5).

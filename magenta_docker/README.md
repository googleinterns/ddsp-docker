# DDSP Docker

Docker image for training autoencoder on [Google Cloud AI Platform](https://cloud.google.com/ai-platform).

### Before you begin
Make sure that you have complited following steps:
* Setup your [GCP project](https://cloud.google.com/resource-manager/docs/creating-managing-projects)
* Create a [Google Cloud Storage Bucket](https://cloud.google.com/storage/docs/creating-buckets)
* Enable [AI Platform Training and Prediction, Container Registry, and Compute Engine APIs](https://pantheon.corp.google.com/flows/enableapi?apiid=ml.googleapis.com,compute_component,containerregistry.googleapis.com)
* Install [Docker](https://docs.docker.com/engine/install/)
* [Configure Docker for Cloud Container Registry](https://cloud.google.com/container-registry/docs/pushing-and-pulling)
* [Upload the training data](https://cloud.google.com/storage/docs/uploading-objects) in the [TFRecord](https://www.tensorflow.org/tutorials/load_data/tfrecord) format to the storage bucket. You can preprocess your audio files into this format using `ddsp_prepare_tfrecord` tool as described in [Making a TFRecord dataset from your own sounds](https://github.com/magenta/ddsp/tree/master/ddsp/training/data_preparation).

### Quickstart:

#### Define some environment variables

If you are located outside Europe we recommend setting `$REGION` accordingly to your location. We also recommend to [setup hostname](https://cloud.google.com/container-registry/docs/pushing-and-pulling#tag_the_local_image_with_the_registry_name) in `$IMAGE_URI` based of the `$REGION` choice as if your Docker images are stored in different region than the job is computed additional charges will be applied. 

```bash
export PROJECT_ID=[YOUR_PROJECT_ID]
export IMAGE_REPO_NAME=ddsp_train
export IMAGE_TAG=ai_platform
export IMAGE_URI=eu.gcr.io/$PROJECT_ID/$IMAGE_REPO_NAME:$IMAGE_TAG
export REGION=europe-west4
export SAVE_DIR=gs://[YOUR_STORAGE_BUCKET_NAME]/[PATH_IN_STORAGE_BUCKET]
export JOB_NAME=ddsp_container_job_$(date +%Y%m%d_%H%M%S)
export DATA_PATTERN=gs://[YOUR_STORAGE_BUCKET_NAME]/[PATH_IN_STORAGE_BUCKET]/train.tfrecord*
```
#### Build the image and push it to Container Registry

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
  --data_pattern=$DATA_PATTERN \
  --batch_size=128 \
  --learning_rate=0.001 \
  --num_steps=15000 \
  --early_stop_loss_value=5.0
```
##### AI Platform flags:
* `--region` - Region when job is run
* `--config` - Cluster configuration. In the example above, training on multiple VMs with multiple GPUs is set. For more information about various configuartions take a look at **Note on cluster configuration and hyperparameters** below.
* `--master-image-uri` - URI of the Docker image you've built and submitted to Container Registry

##### Program flags:
* `--save_dir` - **Mandatory flag**. Bucket directory where checkpoints and summary events will be saved during training.
* `--data_pattern` - **Mandatory flag**. Pattern of the data files name. Must include a whole bucket directory.
* `--restore_dir` - Bucket directory from which checkpoints will be restored before training. When not provided defaults to save_dir. If there are no checkpoints in provided directory, training will resume.
* `--steps_per_save` - Steps per model save.
* `--restore_per_summary` - Steps per training summary save.
* `--batch_size` - Batch size.
* `--learning_rate` - Learning rate.
* `--num_steps` - Number of training steps.
* `--early_loss_stop_value` - Early stopping. When the total_loss reaches below this value training stops.


### Note on cluster configuration and hyperparameters

TODO(werror): Write about prepared cluster configurations and hyperparameters
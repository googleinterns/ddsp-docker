# DDSP Docker

Docker image for training autoencoder on Google Cloud AI Platform.

As the application is using the modified version of train_util.py for now the Docker image must be build from ddsp/ddsp context. 

### Before you begin
Make sure that you have complited following steps:
* Install [Docker](https://docs.docker.com/engine/install/)
* Setup your [GCP project](https://cloud.google.com/resource-manager/docs/creating-managing-projects)
* Create [storage bucket](https://cloud.google.com/storage/docs/creating-buckets)
* [Upload the training data](https://cloud.google.com/storage/docs/uploading-objects) in the [TFRecord](https://www.tensorflow.org/tutorials/load_data/tfrecord) format to the storage bucket. You can preprocess your audio files into this format using `ddsp_prepare_tfrecord` tool as described in [Making a TFRecord dataset from your own sounds](https://github.com/magenta/ddsp/tree/master/ddsp/training/data_preparation).

### Quickstart:

#### Define some environment variables

If you are located outside Europe we recommend setting `$REGION` accordingly to your location. We also recommend to [setup hostname](https://cloud.google.com/container-registry/docs/managing) in `$IMAGE_URI` based of the `$REGION` choice as if your Docker images are stored in different region than the job is computed additional charges will be applied. 

```bash
export PROJECT_ID=[YOUR_PROJECT_ID]
export IMAGE_REPO_NAME=ddsp_train
export IMAGE_TAG=ai_platform
export IMAGE_URI=eu.gcr.io/$PROJECT_ID/$IMAGE_REPO_NAME:$IMAGE_TAG
export REGION=europe-west4
export SAVE_DIR=gs://[YOUR_STORAGE_BUCKET_NAME]
export JOB_NAME=ddsp_container_job_$(date +%Y%m%d_%H%M%S)
```
#### Build the image and push it to Container Registry

```bash
docker build -f docker/Dockerfile -t $IMAGE_URI ./
docker push $IMAGE_URI
```

#### Submit the training to AI Platform
```bash
gcloud ai-platform jobs submit training $JOB_NAME \ 
--region $REGION \
--config docker/utils/cluster_configurations/config_mul.yaml \
--master-image-uri $IMAGE_URI \
-- \
--gin_param=batch_size=16 \
--save_dir=$SAVE_DIR
```

### Note on cluster configuration and hyperparameters

TODO(werror): Write about prepared cluster configurations and hyperparameters
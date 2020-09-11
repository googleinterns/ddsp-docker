#! /bin/bash
export PROJECT_ID=$(gcloud config list project --format "value(core.project)")
export IMAGE_REPO_NAME=ddsp_train
export IMAGE_TAG=gce_vm
export IMAGE_URI=eu.gcr.io/$PROJECT_ID/$IMAGE_REPO_NAME:$IMAGE_TAG
export PREPROCESSING_IMAGE_URI=eu.gcr.io/$PROJECT_ID/data_preprocessing:$IMAGE_TAG

apt-get install -yq python3 python-pip
pip install --upgrade pip virtualenv

mv ddsp_docker-web_interface /opt/app

virtualenv -p python3 /opt/app/vm_code/env
source /opt/app/vm_code/env/bin/activate
/opt/app/vm_code/env/bin/pip install -r /opt/app/vm_code/requirements.txt


gcloud compute firewall-rules create default-allow-http-8080 \
--allow tcp:8080 \
--source-ranges 0.0.0.0/0 \
--target-tags http-server \
--description "Allow port 8080 access to http-server"

source docker_setup.sh &

cd /opt/app/vm_code
/opt/app/vm_code/env/bin/gunicorn -b 0.0.0.0:8080 main:app --timeout 300

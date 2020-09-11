#! /bin/bash
apt-get remove docker docker-engine docker.io containerd runc
apt-get update
apt-get -y install \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -
add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/debian \
   $(lsb_release -cs) \
   stable"
apt-get update
apt-get -y install docker-ce docker-ce-cli containerd.io

gcloud auth configure-docker -q

docker build -f data_preprocessing/Dockerfile -t $PREPROCESSING_IMAGE_URI ./data_preprocessing
docker push $PREPROCESSING_IMAGE_URI

docker build -f magenta_docker/Dockerfile -t $IMAGE_URI ./magenta_docker
docker push $IMAGE_URI

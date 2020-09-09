#! /bin/bash
export PROJECT_ID=$(gcloud config list project --format "value(core.project)")
export IMAGE_REPO_NAME=ddsp_train
export IMAGE_TAG=gce_vm
export IMAGE_URI=eu.gcr.io/$PROJECT_ID/$IMAGE_REPO_NAME:$IMAGE_TAG

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

# docker build -f magenta_docker/Dockerfile -t $IMAGE_URI ./
# docker push $IMAGE_URI

apt-get install -yq supervisor python python-pip
pip install --upgrade pip virtualenv
useradd -m -d /home/pythonapp pythonapp
export HOME=/root
mv ddsp_docker-web_interface /opt/app
virtualenv -p python3 /opt/app/vm_code/env
source /opt/app/vm_code/env/bin/activate
/opt/app/vm_code/env/bin/pip install -r /opt/app/vm_code/requirements.txt

# Installs ddsp library for data preprocessing 
# wget https://github.com//magenta/ddsp/archive/master.zip
# unzip master.zip
# cd ddsp-master && python setup.py install
# cd ..

chown -R pythonapp:pythonapp /opt/app
cp /opt/app/vm_code/python-app.conf /etc/supervisor/conf.d/python-app.conf

gcloud compute firewall-rules create default-allow-http-8080 \
--allow tcp:8080 \
--source-ranges 0.0.0.0/0 \
--target-tags http-server \
--description "Allow port 8080 access to http-server"

supervisorctl reread
supervisorctl update
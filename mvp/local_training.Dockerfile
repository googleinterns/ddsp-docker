# Install tensorflow 2.2 base image for cpu
FROM gcr.io/deeplearning-platform-release/tf2-cpu.2-2

WORKDIR /root

# Installs necessary dependencies.
RUN apt-get update && apt-get install -y --no-install-recommends \
         wget \
         curl \
         python-dev && \
     rm -rf /var/lib/apt/lists/*

# Installs pandas, google-cloud-storage
# and ddsp library
RUN pip install pandas google-cloud-storage
RUN apt-get update && apt-get install -y libsndfile-dev
RUN pip install --upgrade pip && pip install --upgrade ddsp
RUN apt-get install -y tree

RUN mkdir ~/data
RUN mkdir ~/model
RUN mkdir /root/tmp
RUN mkdir /root/tmp/ddsp

# Copies dataset into the docker image
ARG data_path
COPY $data_path ~/data

# Set up the entry point to invoke the trainer.
ENTRYPOINT ["ddsp_run", "--gin_param=TFRecordProvider.file_pattern='~/data/train.tfrecord*'"]

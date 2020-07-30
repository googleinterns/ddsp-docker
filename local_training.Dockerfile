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

COPY ./data/ddsp_training/data ~/data

# Set up the entry point to invoke the trainer.
ENTRYPOINT ["ddsp_run", "--mode=train", "--alsologtostderr", "--save_dir=~/model",\
  "--gin_file=models/solo_instrument.gin",\
  "--gin_file=datasets/tfrecord.gin",\
  "--gin_param=TFRecordProvider.file_pattern='~/data/train.tfrecord*'",\
  "--gin_param=batch_size=16",\
  "--gin_param=train_util.train.num_steps=1",\
  "--gin_param=train_util.train.steps_per_save=1",\
  "--gin_param=trainers.Trainer.checkpoints_to_keep=1"]

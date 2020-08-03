FROM gcr.io/deeplearning-platform-release/tf2-gpu.2-2
WORKDIR /root

# Installs sndfile library for reading and writing audio files 
RUN apt-get update && apt-get install -y libsndfile-dev

# Instals ddsp library and upgrade tensorflow
RUN pip install --upgrade pip && pip install --upgrade tensorflow && pip install --upgrade ddsp
RUN pip show tensorflow

# Installs google cloud sdk, this is mostly for using gsutil to export model.
RUN wget -nv \
    https://dl.google.com/dl/cloudsdk/release/google-cloud-sdk.tar.gz && \
    mkdir /root/tools && \
    tar xvzf google-cloud-sdk.tar.gz -C /root/tools && \
    rm google-cloud-sdk.tar.gz && \
    /root/tools/google-cloud-sdk/install.sh --usage-reporting=false \
        --path-update=false --bash-completion=false \
        --disable-installation-options && \
    rm -rf /root/.config/* && \
    ln -s /root/.config /config && \
    # Remove the backup directory that gcloud creates
    rm -rf /root/tools/google-cloud-sdk/.install/.backup

# Path configuration
ENV PATH $PATH:/root/tools/google-cloud-sdk/bin
# Make sure gsutil will use the default service account
RUN echo '[GoogleCompute]\nservice_account = default' > /etc/boto.cfg

RUN mkdir /root/trainer
COPY trainer/ddsp_run_multiple_vms.py /root/trainer/ddsp_run_multiple_vms.py

RUN mkdir /root/trainer/gin && mkdir /root/trainer/gin/optimization
COPY ./trainer/gin/optimization/base.gin /root/trainer/gin/optimization/base.gin

RUN mkdir /root/trainer/gin/models
COPY ./trainer/gin/models/solo_instrument.gin /root/trainer/gin/models/solo_instrument.gin 
COPY ./trainer/gin/models/ae.gin /root/trainer/gin/models/ae.gin 

RUN mkdir /root/trainer/gin/datasets
COPY ./trainer/gin/datasets/tfrecord.gin /root/trainer/gin/datasets/tfrecord.gin
COPY ./trainer/gin/datasets/base.gin /root/trainer/gin/datasets/base.gin

RUN mkdir /root/tmp
RUN mkdir /root/tmp/ddsp

ENTRYPOINT ["python", "trainer/ddsp_run_multiple_vms.py", "--mode=train", \
     "--alsologtostderr", \
     "--save_dir=gs://werror-2020.appspot.com/mvp/dist", \
     "--gin_file=models/solo_instrument.gin", \
     "--gin_file=datasets/tfrecord.gin", \
     "--gin_param=TFRecordProvider.file_pattern='gs://werror-2020.appspot.com/mvp/data/train.tfrecord*'", \
     "--gin_param=batch_size=16", \
     "--gin_param=train_util.train.num_steps=128", \
     "--gin_param=train_util.train.steps_per_save=64", \
     "--gin_param=trainers.Trainer.checkpoints_to_keep=10"]



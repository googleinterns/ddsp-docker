# Install tensorflow 2.2 base image for gpu
FROM gcr.io/deeplearning-platform-release/tf2-gpu.2-2

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
RUN pip install cloudml-hypertune

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

# Copies additional source code
RUN mkdir /root/trainer
COPY trainer/ddsp_run_hypertune.py /root/trainer/ddsp_run_hypertune.py
COPY trainer/helper_functions.py /root/trainer/helper_functions.py
COPY trainer/magenta_ddsp_internals/train_util.py /root/trainer/magenta_ddsp_internals/train_util.py
COPY trainer/magenta_ddsp_internals/trainers.py /root/trainer/magenta_ddsp_internals/trainers.py

RUN mkdir /root/trainer/gin && mkdir /root/trainer/gin/optimization
COPY ./trainer/gin/optimization/base.gin /root/trainer/gin/optimization/base.gin

RUN mkdir /root/trainer/gin/models
COPY ./trainer/gin/models/solo_instrument.gin /root/trainer/gin/models/solo_instrument.gin 
COPY ./trainer/gin/models/ae.gin /root/trainer/gin/models/ae.gin 

RUN mkdir /root/trainer/gin/datasets
COPY ./trainer/gin/datasets/tfrecord.gin /root/trainer/gin/datasets/tfrecord.gin
COPY ./trainer/gin/datasets/base.gin /root/trainer/gin/datasets/base.gin

RUN mkdir /root/tmp
RUN mkdir /root/tmp/hypertune

# Set up the entry point to invoke the trainer.
ENTRYPOINT ["python", "trainer/ddsp_run_hypertune.py"]

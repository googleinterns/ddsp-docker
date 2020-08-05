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

# Set up the entry point to invoke the trainer.
ENTRYPOINT ["ddsp_run"]
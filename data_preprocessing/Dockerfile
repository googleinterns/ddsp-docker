# Uses one of AI Platform base images.
# You can try using different images however only this one has been tested.
FROM gcr.io/deeplearning-platform-release/tf2-gpu.2-2

# Installs sndfile library for reading and writing audio files.
RUN apt-get update && \
    apt-get install --no-install-recommends -y libsndfile-dev

# Upgrades Tensorflow and Tensorflow Probability
# Newer version of Tensorflow is needed for multiple VMs training
RUN pip install --upgrade pip && \
    pip install --upgrade tensorflow tensorflow-probability

WORKDIR /root
# Installs Magenta DDSP from Github.
RUN wget https://github.com//magenta/ddsp/archive/master.zip && \
    unzip master.zip && \
    cd ddsp-master && \
    python setup.py install

COPY preprocessing_task.py /root/preprocessing_task.py
COPY magenta_stats_utils/utils.py /root/magenta_stats_utils/utils.py

# These parameters can be also specified as part of the job submission arguments.
ENTRYPOINT ["python", "preprocessing_task.py"]

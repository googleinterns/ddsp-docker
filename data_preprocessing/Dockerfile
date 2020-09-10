# Uses one of AI Platform base images.
# You can try using different images however only this one has been tested.
FROM gcr.io/deeplearning-platform-release/tf2-cpu.2-2
WORKDIR /root

# Installs sndfile library for reading and writing audio files.
RUN apt-get update && apt-get install -y libsndfile-dev

# Upgrades Tensorflow and Tensorflow Probability
# Newer version of Tensorflow is needed for multiple VMs training
RUN pip install --upgrade pip && pip install --upgrade tensorflow tensorflow-probability

# Installs Magenta DDSP from Github.
RUN wget https://github.com//magenta/ddsp/archive/master.zip
RUN unzip master.zip
RUN cd ddsp-master && python setup.py install

# These parameters can be also specified as part of the job submission arguments.
ENTRYPOINT ["ddsp_prepare_tfrecord", "--num_shards=10", "--alsologtostderr"]
# CMD echo hello >> /root/blabla.txt

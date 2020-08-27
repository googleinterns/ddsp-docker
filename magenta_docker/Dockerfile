FROM gcr.io/deeplearning-platform-release/tf2-gpu.2-2
WORKDIR /root

# Installs sndfile library for reading and writing audio files 
RUN apt-get update && apt-get install -y libsndfile-dev

# Upgrades Tensorflow and Tensorflow Probability
# Newer version of Tensorflow is needed for multiple VMs training
RUN pip install --upgrade pip && pip install --upgrade tensorflow tensorflow-probability
RUN pip show tensorflow

RUN wget https://github.com/werkaaa/ddsp/archive/ddsp_run_change.zip
RUN unzip ddsp_run_change.zip
RUN cd ddsp-ddsp_run_change && python setup.py install

# Copies running script
COPY task.py task.py

# These parameters can be also specified as part of the job submission arguments
ENTRYPOINT ["python", "task.py"]
 
FROM gcr.io/deeplearning-platform-release/tf2-gpu.2-2
WORKDIR /root

# Installs sndfile library for reading and writing audio files 
RUN apt-get update && apt-get install -y libsndfile-dev

# Upgrades Tensorflow and Tensorflow Probability
# Newer version of Tensorflow is needed for multiple VMs training
RUN pip install --upgrade pip && pip install --upgrade tensorflow tensorflow-probability
RUN pip show tensorflow

# Install cloudml-hypertune package needed for hyperparameter tuning
RUN pip install cloudml-hypertune

RUN wget https://github.com/ana-simionescu/ddsp/archive/master.zip
RUN unzip master.zip
RUN cd ddsp-master && python setup.py install

# Copies running script
COPY task.py task.py

# These parameters can be also specified as part of the job submission arguments
ENTRYPOINT ["python", "task.py"]

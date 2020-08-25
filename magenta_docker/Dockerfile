FROM gcr.io/deeplearning-platform-release/tf2-gpu.2-2
WORKDIR /root

# Installs sndfile library for reading and writing audio files 
RUN apt-get update && apt-get install -y libsndfile-dev

# Upgrades Tensorflow and Tensorflow Probability
# Newer version of Tensorflow is needed for multiple VMs training
RUN pip install --upgrade pip && pip install --upgrade tensorflow tensorflow-probability
RUN pip show tensorflow

RUN wget https://github.com/werkaaa/ddsp/archive/93139bb0e8696d2a2f442893384374a2dc56aee5.zip
RUN unzip 93139bb0e8696d2a2f442893384374a2dc56aee5.zip
RUN cd ddsp-93139bb0e8696d2a2f442893384374a2dc56aee5 && python setup.py install

# Copies running script
COPY task.py task.py

# These parameters can be also specified as part of the job submission arguments
ENTRYPOINT ["python", "task.py"]
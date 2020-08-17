#!/usr/bin/env python
import os

# Determining the way the library will be used
modeOptions = {1 : "train", 2 : "eval", 3 : "sample"}

print("You want to train, evaluate or sample a model?\n\
[1] train\n[2] evaluate\n[3] sample")
while True:
    mode = input()
    if mode not in modeOptions:
        print("Insert only 1, 2 or 3")
        continue
    else:
        mode = modeOptions[mode]
        break

print("You chose to " + mode + " the model.\n")

# Determining if the image will run locally or remotely
placeOptions = {1 : "locally", 2 : "on the Google Cloud AI Platform"}
print("You want to " + mode + " locally or on the Google Cloud AI Platform?\n\
[1] locally\n[2] Google Cloud AI Platform")
while True:
    place = input()
    if place not in [1, 2]:
        print("Insert only 1 or 2")
        continue
    else:
        break

print("You chose to " + mode + " " + placeOptions[place] + "\n")

# Determining path for data retrieval
dataPath = raw_input("Please insert a path for data retrieving. This can be a local directory or a GCS Bucket:\n")

# Determining path for storing model, snapshots and summaries
storingPath = raw_input("\nPlease insert a path for storing the model, snapshots and summaries.\
 This can be a local directory or a GCS Bucket:\n")

# Determining path for recovering a snapshot
recoveryPath = raw_input("\nPlease insert path for recovering a snapshot or a completed model.\
 This can be a local directory or a GCS Bucket:\n")

imageURI = raw_input("\nPlease insert a IMAGE URI:")

configPath = raw_input("\nPlease insert the path to a configuration file:")

os.system("export PATH=/usr/local/google/home/anasimionescu/.local/bin:$PATH")

if place == 1:
    #Building the image
    buildCommand = "docker build -f local_training.Dockerfile -t " + imageURI + " ./" + " --build-arg data_path=" + dataPath
    os.system(buildCommand)

    print("Docker image built")

    # Run the image locally
    runCommand = "docker run " + imageURI + " --mode=" + mode + " --save_dir=" + storingPath\
                    + " --alsologtostderr"\
                    + " --gin_file=models/solo_instrument.gin"\
                    + " --gin_file=datasets/tfrecord.gin"\
                    + " --gin_param=batch_size=16"\
                    + " --gin_param=train_util.train.num_steps=1"\
                    + " --gin_param=train_util.train.steps_per_save=1"\
                    + " --gin_param=trainers.Trainer.checkpoints_to_keep=1"
    print("Running image...")
    os.system(runCommand)

    # Enabling Tensorboard
    print("Enabling Tensorboard")
    os.system("gcloud auth login")
    tensorboardCommand = "tensorboard --logdir=" + storingPath + " --port=8080"
    os.system(tensorboardCommand)
elif place == 2:
    #Building the image
    buildCommand = "docker build -f ai_platform_training.Dockerfile -t " + imageURI + " ./"
    os.system(buildCommand)
    print("Docker image built")

    # Push the image on Google Cloud Registry
    pushing_image = "docker push " + imageURI
    os.system(pushing_image)
    print("Imaged pushed to Google Cloud Registry")

    print("Please insert a job name:")
    jobName = raw_input()

    # Submit the job on AI Platform
    print("Submitting the job on AI Platform")
    submitting_job = "gcloud beta ai-platform jobs submit training " + jobName\
    + " --region europe-west1 --master-image-uri " + imageURI + " --config " + configPath + " -- --mode=" + mode\
    + " --save_dir=" + storingPath\
    + " --alsologtostderr"\
    + " --gin_file=models/solo_instrument.gin"\
    + " --gin_file=datasets/tfrecord.gin"\
    + " --gin_param=\"TFRecordProvider.file_pattern='" + dataPath + "/train.tfrecord*'\""\
    + " --gin_param=magenta_ddsp_internals.trainers.Trainer.checkpoints_to_keep=10"\
   # + " --gin_param=early_stop_loss_value=5"
    os.system(submitting_job)

    # Enabling Tensorboard
    print("Enabling Tensorboard")
    os.system("gcloud auth login")
    tensorboardCommand = "tensorboard --logdir=" + storingPath + " --port=8082"
    os.system(tensorboardCommand)

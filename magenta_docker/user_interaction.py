#!/usr/bin/env python
import os

# Determining path for data retrieval
data_path = raw_input('Insert a path for data retrieving. '
'This must be a GCS Bucket:\n')

# Determining path for storing model, snapshots and summaries
save_dir = raw_input('\nInsert a path for saving the model, '
'snapshots and summaries. This must be a GCS Bucket:\n')

# Determining path for restoring the model
restore_dir = raw_input('\nInsert a path from which checkpoints will '
'be restored before training. Skip for using the same path as for saving:\n')
if restore_dir == "":
    restore_dir = save_dir

config_path = raw_input('\nInsert the path to a configuration file '
'or skip for the default one:\n')
if config_path == "":
    config_path = "./config_single_vm.yaml"

image_URI = raw_input('\nInsert an IMAGE URI. '
'The template is: gcr.io/<GCP_PROJECT_ID>/<IMAGE_REPO_NAME>:<IMAGE_TAG> :\n')

os.system("export PATH=/usr/local/google/home/$USER/.local/bin:$PATH")

#Building the image
build_command = "docker build -f Dockerfile -t " + image_URI + " ./"
os.system(build_command)
print("Docker image built")

# Push the image on Google Cloud Registry
pushing_image = "docker push " + image_URI
os.system(pushing_image)
print("Image pushed to Google Cloud Registry")

job_name = raw_input("\nPlease insert a job name:\n")

region = raw_input('\nInsert the region you want to train '
'your model in or skip for the default value (europe-west4): ')
if region == "":
    region = "europe-west4"

batch_size = raw_input('\nInsert batch size '
'or skip for the default value (128): ')
if batch_size == "":
    batch_size = "128"

learning_rate = raw_input('\nInsert the learning rate '
'or skip for the default value (0.001): ')
if learning_rate == "":
    learning_rate = "0.001" 

no_of_steps = raw_input('\nInsert the number of steps for training '
'or skip for the default value (15000): ')
if no_of_steps == "":
    no_of_steps = "15000"

steps_per_save = raw_input('\nInsert the number of steps per save '
'or skip for the default value (300): ')
if steps_per_save == "":
    steps_per_save = "300"

steps_per_summary = raw_input('\nInsert the number of steps per summary '
'or skip for the default value (300): ')
if steps_per_summary == "":
    steps_per_summary = "300"

early_stop_loss_value = raw_input('\nInsert the early stop loss value '
'or skip for the default value (5): ')
if early_stop_loss_value == "":
    early_stop_loss_value = "5"

# Submit the job on AI Platform
print("Submitting the job on AI Platform")
submitting_job = "gcloud beta ai-platform jobs submit training " + job_name\
+ " --region " + region + " --master-image-uri " + image_URI + " --config " + config_path\
+ " -- --save_dir=" + save_dir\
+ " --restore_dir=" + restore_dir\
+ " --file_pattern=" + data_path + "/train.tfrecord*"\
+ " --batch_size=" + batch_size\
+ " --learning_rate=" + learning_rate\
+ " --num_steps=" + no_of_steps\
+ " --steps_per_summary=" + steps_per_summary\
+ " --steps_per_save=" + steps_per_save
os.system(submitting_job)

# Enabling Tensorboard
print("Enabling Tensorboard")
os.system("gcloud auth login")
tensorboard_command = "tensorboard --logdir=" + save_dir + " --port=8082"
os.system(tensorboard_command)

# Uploading logs to TensorBoard.dev
print("Uploading logs to TensorBoard.dev")
tensorboard_dev_command = "tensorboard dev upload --logdir " + save_dir\
+ " --name \"" + job_name + "\""
os.system(tensorboard_dev_command)

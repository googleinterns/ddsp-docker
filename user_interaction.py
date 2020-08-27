#!/usr/bin/env python
import os

# # Determining path for data retrieval
data_path = raw_input('Insert a path for data retrieving. '
'This must be a GCS Bucket:\n')

# Determining path for storing model, snapshots and summaries
save_dir = raw_input('\nInsert a path for saving the model, '
'snapshots and summaries. This must be a GCS Bucket:\n')

restore_dir = raw_input('\nInsert a path from which checkpoints will'
' be restored before training. Skip for using the same path as for saving:\n')
if restore_dir == "":
    restore_dir = save_dir

gin_path = raw_input('\nInsert an additional gin file search path or skip'
'for only using the default paths:\n')

config_path = raw_input('\nInsert the path to a configuration file'
' or skip for the default one:')

image_URI = raw_input('\nInsert a IMAGE URI.'
' The template is: gcr.io/<GCP_PROJECT_ID>/<IMAGE_REPO_NAME>:<IMAGE_TAG> :')

os.system("export PATH=/usr/local/google/home/$USER/.local/bin:$PATH")

#Building the image
build_command = "docker build -f ai_platform_training.Dockerfile -t " + image_URI + " ./"
os.system(build_command)
print("Docker image built")

# Push the image on Google Cloud Registry
pushing_image = "docker push " + image_URI
os.system(pushing_image)
print("Imaged pushed to Google Cloud Registry")

print("Please insert a job name:")
job_name = raw_input()

region = raw_input('\nInsert the region you want to train '
'your model in or skip for the default value (europe-west4):')
if region == "":
    region = "europe-west4"

batch_size = raw_input('\nInsert batch size'
' or skip for the default value (128):')
if batch_size == "":
    batch_size = "32"

learning_rate = raw_input('\nInsert the learning rate'
' or skip for the default value (0.001):')
if learning_rate == "":
    learning_rate = "0.001" 

no_of_steps = raw_input('\nInsert the number of steps for training'
' or skip for the default value (10000):')
if no_of_steps == "":
    no_of_steps = "10000"

steps_per_save = raw_input('\nInsert the number of steps per save'
' or skip for the default value (300):')
if steps_per_save == "":
    steps_per_save = "300"

steps_per_summary = raw_input('\nInsert the number of steps per summary'
' or skip for the default value (300):')
if steps_per_summary == "":
    steps_per_summary = "300"

no_of_checkpoints = raw_input('\nInsert the number of checkpoints to '
'keep or skip for the default value (10):')
if no_of_checkpoints == "":
    no_of_checkpoints = "10"

early_stop_loss_value = raw_input('\nInsert the early stop loss value'
' or skip for the default value (5):')
if early_stop_loss_value == "":
    early_stop_loss_value = "5"

# Submit the job on AI Platform
print("Submitting the job on AI Platform")
submitting_job = "gcloud beta ai-platform jobs submit training " + job_name\
+ " --region " + region + " --master-image-uri " + image_URI + " --config " + config_path + " -- --mode=train"\
+ " --save_dir=" + save_dir\
+ " --restore_dir=" + restore_dir\
+ " --gin_search_path=" + gin_path\
+ " --alsologtostderr"\
+ " --hp_tuning=True"\
+ " --gin_file=models/solo_instrument.gin"\
+ " --gin_file=datasets/tfrecord.gin"\
+ " --gin_param=\"TFRecordProvider.file_pattern='" + data_path\
+ "/train.tfrecord*'\""\
+ " --gin_param=early_stop_loss_value=" + early_stop_loss_value\
+ " --gin_param=magenta_ddsp_internals.train_util.train.batch_size=" + batch_size\
+ " --gin_param=magenta_ddsp_internals.train_util.train.num_steps=" + no_of_steps\
+ " --gin_param=magenta_ddsp_internals.train_util.train.steps_per_summary=" + steps_per_summary\
+ " --gin_param=magenta_ddsp_internals.train_util.train.steps_per_save=" + steps_per_save
os.system(submitting_job)

# Enabling Tensorboard
print("Enabling Tensorboard")
os.system("gcloud auth login")
tensorboard_command = "tensorboard --logdir=" + storing_path + " --port=8082"
os.system(tensorboard_command)

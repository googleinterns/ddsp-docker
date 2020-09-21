"""Helper function for GCP communication."""
from datetime import datetime
import os
import subprocess
import tensorflow as tf
from os.path import basename
from subprocess import PIPE
from zipfile36 import ZipFile

def create_bucket(bucket_name, region):
  """Creates a new bucket."""
  create_command = "gsutil mb -l " + region + " " + bucket_name
  os.system(create_command)

def upload_blob(bucket_name, uploads_dir):
  """Uploads files to the bucket."""
  upload_command = (
      "gsutil -m cp -r " +
      uploads_dir + " " +
      bucket_name + "/audio")
  os.system(upload_command)

def download_file(bucket_name, downloads_dir, file_name):
  """Downloads file from bucket"""
  download_command = (
      "gsutil -m cp " +
      bucket_name + "/model/" +
      file_name + " " +
      downloads_dir)
  os.system(download_command)

def delete_bucket(bucket_name):
  """Deletes the bucket."""
  delete_command = "gsutil rm -r " + bucket_name
  _, command_err = subprocess.Popen(
      delete_command.split(),
      stdin=PIPE,
      stdout=PIPE,
      stderr=PIPE).communicate()
  if "Exception" in str(command_err):
    return "ERROR"
  else:
    return "BUCKET_DELETED"

def get_model(bucket_name, downloads_dir, instance_path):
  """Creates an archive with the model."""
  latest_checkpoint_fname = os.path.basename(tf.train.latest_checkpoint\
                                             (bucket_name + "/model")) + "*"
  download_file(bucket_name, downloads_dir, latest_checkpoint_fname)
  download_file(bucket_name, downloads_dir, "operative_config-0.gin")
  download_file(bucket_name, downloads_dir, "dataset_statistics.pkl")

  zip_path = os.path.join(instance_path, "model.zip")
  with ZipFile(zip_path, "w") as zip_obj:
    for folder_name, subfolders, filenames in os.walk(downloads_dir):
      for filename in filenames:
        #create complete filepath of file in directory
        file_path = os.path.join(folder_name, filename)
        # Add file to zip
        zip_obj.write(file_path, basename(file_path))
    zip_obj.close()

def run_preprocessing(bucket_name, region):
  """Runs preprocessing job on AI Platform"""
  job_name = (
      "preprocessing_job_" +
      str(int((datetime.now()-datetime(1970, 1, 1)).total_seconds())))
  set_job_name = "export PREPROCESSING_JOB_NAME=" + job_name
  os.system(set_job_name)
  input_audio_filepatterns = os.path.join(bucket_name, "audio/*")
  output_tfrecord_path = os.path.join(bucket_name, "tf_record/train.tfrecord")
  statistics_path = os.path.join(bucket_name, "model/")

  config_file = os.path.join(
      os.getcwd(),
      "../magenta_docker/config_single_vm.yaml")
  image_uri = subprocess.check_output("$PREPROCESSING_IMAGE_URI", shell=True)
  job_submission_command = (
      "gcloud ai-platform jobs submit training " + job_name +
      " --region " + region +
      " --config " + config_file +
      " --master-image-uri " + image_uri +
      " -- " +
      " --input_audio_filepatterns=" + input_audio_filepatterns +
      " --output_tfrecord_path=" +  output_tfrecord_path +
      " --statistics_path=" + statistics_path)

  _, command_err = subprocess.Popen(
      job_submission_command.split(),
      stdin=PIPE,
      stdout=PIPE,
      stderr=PIPE).communicate()

  if "master_config.image_uri Error" in str(command_err):
    return "DOCKER_IMAGE_ERROR"
  if "ERROR" not in str(command_err):
    return "JOB_SUBMITTED"

  return "ERROR"

def submit_job(request, bucket_name, region):
  """Submits training job to AI Platform"""
  preprocessing_job_name = subprocess.check_output("$PREPROCESSING_JOB_NAME",
                                                   shell=True)
  if not preprocessing_job_name:
    return "PREPROCESSING_NOT_SUBMITTED"

  job_name = subprocess.check_output("$PREPROCESSING_JOB_NAME", shell=True)
  preprocessing_status = check_job_status(job_name)
  if preprocessing_status in ["RUNNING", "QUEUED", "PREPARING"]:
    return "PREPROCESSING_NOT_FINISHED"

  if preprocessing_status == "SUCCEEDED":
    os.system("export PATH=/usr/local/google/home/$USER/.local/bin:$PATH")
    job_name = (
        "training_job_" +
        str(int((datetime.now()-datetime(1970, 1, 1)).total_seconds())))
    set_job_name = "export JOB_NAME=" + job_name
    os.system(set_job_name)
    if str(request.form["batch_size"]) in ["8", "16"]:
      config_file = os.path.join(
            os.getcwd(),
            "../magenta_docker/config_single_vm.yaml")
    if str(request.form["batch_size"]) == "32":
      config_file = os.path.join(
            os.getcwd(),
            "../magenta_docker/config_1vm_2gpus.yaml")
    if str(request.form["batch_size"]) == "64":
      config_file = os.path.join(
            os.getcwd(),
            "../magenta_docker/config_2vms_4gpus.yaml")
    if str(request.form["batch_size"]) == "128":
      config_file = os.path.join(
            os.getcwd(),
            "../magenta_docker/config_multiple_vms.yaml")
    image_uri = subprocess.check_output("$IMAGE_URI", shell=True)
    early_stop_loss_value = str(request.form["early_stop_loss_value"])
    job_submission_command = (
        "gcloud ai-platform jobs submit training " + job_name +
        " --region " + region +
        " --master-image-uri " + image_uri +
        " --config " + config_file +
        " -- --save_dir=" + bucket_name + "/model" +
        " --file_pattern=" + bucket_name + "/tf_record" + "/train.tfrecord*" +
        " --batch_size=" + str(request.form["batch_size"]) +
        " --learning_rate=" + str(request.form["learning_rate"]) +
        " --num_steps=" + str(request.form["num_steps"]) +
        " --steps_per_summary=" + str(request.form["steps_per_summary"]) +
        " --steps_per_save=" + str(request.form["steps_per_save"]) +
        " --early_stop_loss_value=" + early_stop_loss_value)

    _, command_err = subprocess.Popen(
        job_submission_command.split(),
        stdin=PIPE,
        stdout=PIPE,
        stderr=PIPE).communicate()

    if "master_config.image_uri Error" in str(command_err):
      return "DOCKER_IMAGE_ERROR"

    if "Quota" in str(command_err):
      return "QUOTA_ERROR"

    if "ERROR" not in str(command_err):
      return "JOB_SUBMITTED"

    return "ERROR"

  return "PREPROCESSING_ERROR"

def command_output_to_dict(command_output):
  """Transforms output string into dict."""
  command_output = command_output.replace("\"", "").replace("\'", "")
  output_dict = {
      x.split(": ")[0].replace(" ", ""): x.split(": ")[-1].replace(" ", "")
      for x in command_output.split("\\n")[:-1]}
  return output_dict

def check_job_status(job_name):
  """Checks job status."""
  job_status_command = "gcloud ai-platform jobs describe " + job_name
  job_info_str = str(subprocess.Popen(
      job_status_command.split(),
      stdin=PIPE,
      stdout=PIPE,
      stderr=PIPE).communicate()[0])

  if len(job_info_str) <= 3:
    return "JOB_NOT_EXIST"

  return command_output_to_dict(job_info_str)["state"]

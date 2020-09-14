"""Helper function for GCP communication."""
from datetime import datetime
import os
import subprocess
from subprocess import PIPE

def create_bucket(bucket_name, region):
  """Creates a new bucket."""
  create_command = "gsutil mb -l" + region + " " + bucket_name
  os.system(create_command)

def upload_blob(bucket_name, uploads_dir):
  """Uploads files to the bucket."""
  upload_command = (
      "gsutil -m cp -r " +
      uploads_dir + " " +
      bucket_name + "/audio")
  os.system(upload_command)

def run_preprocessing(bucket_name, region):
  """Runs preprocessing job on AI Platform"""
  job_name = (
      "preprocessing_job_" +
      str(int((datetime.now()-datetime(1970, 1, 1)).total_seconds())))
  os.environ["PREPROCESSING_JOB_NAME"] = job_name
  input_audio_filepatterns = os.path.join(bucket_name, "audio/*")
  output_tfrecord_path = os.path.join(bucket_name, "tf_record/train.tfrecord")
  statistics_path = os.path.join(bucket_name, "model/")

  config_file = os.path.join(
      os.getcwd(),
      "../magenta_docker/config_single_vm.yaml")
  image_uri = os.environ["PREPROCESSING_IMAGE_URI"]
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
  """Submit training job to AI Platform"""
  preprocessing_status = check_job_status(os.environ["PREPROCESSING_JOB_NAME"])
  if preprocessing_status in ["RUNNING", "QUEUED", "PREPARING"]:
    return "PREPROCESSING_NOT_FINISHED"

  if preprocessing_status == "SUCCEEDED":
    os.system("export PATH=/usr/local/google/home/$USER/.local/bin:$PATH")
    job_name = (
        "training_job_" +
        str(int((datetime.now()-datetime(1970, 1, 1)).total_seconds())))
    config_file = os.path.join(
        os.getcwd(),
        "../magenta_docker/config_multiple_vms.yaml")
    image_uri = os.environ["IMAGE_URI"]
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

"""Helper function for GCP communication."""
import datetime
import os
import subprocess
from subprocess import Popen, PIPE

def create_bucket(bucket_name):
    """Creates a new bucket."""
    create_command = "gsutil mb " + bucket_name
    os.system(create_command)

def upload_blob(bucket_name, uploads_dir):
    """Uploads files to the bucket."""
    upload_command = "gsutil -m cp -r " + uploads_dir + " " + bucket_name + "/audio"
    os.system(upload_command)        

def run_preprocessing(bucket_name, region):
    """Runs preprocessing job on AI Platform"""
    job_name = "preprocessing_job_" + str(int((datetime.datetime.now()-datetime.datetime(1970,1,1)).total_seconds()))
    config_file = os.path.join(os.getcwd(), "../magenta_docker/config_single_vm.yaml") 
    job_submission_command = (
        "gcloud ai-platform jobs submit training " + job_name +
        " --region " + region +
        " --config " + config_file +
        " --master-image-uri $PREPROCESSING_IMAGE_URI" +
        " -- " +
        " --input_audio_filepatterns=" + os.path.join(bucket_name, 'audio/*') +
        " --output_tfrecord_path=" + os.path.join(bucket_name, 'tf_record/train.tfrecord'))
    os.system(job_submission_command)

def command_output_to_dict(command_output):
    """Transforms output string into dict."""
    command_output = command_output.replace('"', '').replace('\'', '')
    output_dict = {x.split(': ')[0].replace(' ', ''):x.split(': ')[-1].replace(' ', '') for x in command_output.split('\\n')[:-1]}
    return output_dict

def check_job_status(job_name):
    """Checks job status."""
    job_status_command = 'gcloud ai-platform jobs describe ' + job_name
    job_info_str = str(subprocess.Popen(job_status_command.split(), stdin = PIPE, stdout = PIPE, stderr = PIPE).communicate()[0])
    if len(job_info_str) <= 3:
        return 'JOB_NOT_EXIST'
    else:
        return command_output_to_dict(job_info_str)['state']

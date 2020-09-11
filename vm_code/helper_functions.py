"""Helper function for GCP communication."""
import datetime
import os

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
    job_name = f"preprocessing_job_{int((datetime.datetime.now()-datetime.datetime(1970,1,1)).total_seconds())}"
    config_file = os.path.join(os.getcwd(), "../magenta_docker/config_single_vm.yaml") 
    job_submission_command = (
        f"gcloud ai-platform jobs submit training {job_name} "
        f" --region {region} "
        f" --config {config_file} "
        " --master-image-uri $PREPROCESSING_IMAGE_URI "
        "-- "
        f"--input_audio_filepatterns={os.path.join(bucket_name, 'audio/*')} "
        f"--output_tfrecord_path={os.path.join(bucket_name, 'tf_record/train.tfrecord')}")

    os.system(job_submission_command)

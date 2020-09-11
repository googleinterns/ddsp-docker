"""Helper function for GCP communication."""
import datetime
import os

def create_bucket():
    """Creates a new bucket.""" 
    try:
        os.system("sudo gsutil mb gs://ddsp-train-web")
    except:
        print("Bucket ddsp-train-web exists")
    else:
        print("Bucket ddsp-train-web created")


def upload_blob(uploads_dir):
    """Uploads files to the bucket."""
    upload_command = "sudo gsutil -m cp -r " + uploads_dir + " gs://ddsp-train-web" 
    os.system(upload_command)

    print("Files uploaded to gs://ddsp-train-web.")
        

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

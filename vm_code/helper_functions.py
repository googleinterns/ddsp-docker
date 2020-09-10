import os
from google.cloud import storage
from os import listdir

def create_bucket(bucket_name):
    """Creates a new bucket."""
    create_command = "gsutil mb " + bucket_name
    os.system(create_command)

def upload_blob(bucket_name, uploads_dir):
    """Uploads files to the bucket."""
    upload_command = "gsutil -m cp -r " + uploads_dir + " " + bucket_name
    os.system(upload_command)
        

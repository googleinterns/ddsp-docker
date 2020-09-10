import os
from google.cloud import storage
from os import listdir

def create_bucket():
    """Creates a new bucket.""" 
    try:
        os.system("gsutil mb gs://ddsp-train-web")
    except:
        print("Bucket ddsp-train-web exists")
    else:
        print("Bucket ddsp-train-web created")


def upload_blob(uploads_dir):
    """Uploads files to the bucket."""
    upload_command = "gsutil -m cp -r " + uploads_dir + " gs://ddsp-train-web" 
    os.system(upload_command)

    print("Files uploaded to gs://ddsp-train-web.")
        

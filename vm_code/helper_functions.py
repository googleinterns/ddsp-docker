import os
from google.cloud import storage
from os import listdir

def create_bucket():
    """Creates a new bucket."""
    bucket_name = "ddsp-training-web"
    storage_client = storage.Client()   
    try:
        bucket = storage_client.bucket(bucket_name)
        print("Bucket {} exists".format(bucket.name))
    except:
        bucket = storage_client.create_bucket(bucket_name)
        print("Bucket {} created".format(bucket.name))


def upload_blob(uploads_dir):
    """Uploads a file to the bucket."""
    bucket_name = "ddsp-training-web"

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    for filename in listdir(uploads_dir):
        source_file_name = os.path.join(uploads_dir, filename)
        destination_blob_name = filename
        
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)

        print(
            "File {} uploaded to {}.".format(
                source_file_name, destination_blob_name
            )
        )

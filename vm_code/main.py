"""Main app script."""
from datetime import datetime
import os
import subprocess

from flask import abort, Flask, render_template, request, send_file
from werkzeug.utils import secure_filename

import helper_functions

app = Flask(
    __name__,
    static_url_path='',
    static_folder='../web_interface')
app.config['UPLOAD_EXTENSIONS'] = ['.wav', '.mp3']
app.config['UPLOAD_PATH'] = 'uploads'
app.config['DOWNLOAD_PATH'] = 'downloads'
app.config['REGION'] = 'europe-west4'
app.config['BUCKET_NAME'] = 'gs://ddsp-train-1599841972'
app.config['TENSORBOARD_ID'] = ''

# Create a directory in a known location to save files to.
uploads_dir = os.path.join(app.instance_path, app.config['UPLOAD_PATH'])
os.makedirs(uploads_dir, exist_ok=True)
downloads_dir = os.path.join(app.instance_path, app.config['DOWNLOAD_PATH'])
os.makedirs(downloads_dir, exist_ok=True)

@app.route('/')
def main():
  return render_template('index_vm.html')

@app.route('/upload', methods=['POST'])
def upload_files():
  for uploaded_file in request.files.getlist('file'):
    filename = secure_filename(uploaded_file.filename)
    if filename != '':
      file_ext = os.path.splitext(filename)[1]
      if file_ext not in app.config['UPLOAD_EXTENSIONS']:
        abort(400)
      uploaded_file.save(os.path.join(uploads_dir, filename))
  helper_functions.create_bucket(
      app.config['BUCKET_NAME'],
      app.config['REGION'])
  helper_functions.upload_blob(app.config['BUCKET_NAME'], uploads_dir)
  return render_template('index_vm.html')

@app.route('/preprocess', methods=['POST'])
def preprocess():
  status = helper_functions.run_preprocessing(
      app.config['BUCKET_NAME'],
      app.config['REGION'])
  if status == 'DOCKER_IMAGE_ERROR':
    message = (
        'Docker image is not ready for preprocessing. '
        'Try once more in a minute!')
  elif status == 'JOB_SUBMITTED':
    message = 'Preprocessing started successfully!'
  else:
    message = 'There was a problem running preprocessing. Try once more!'
  return render_template('index_vm.html', message=message)

@app.route('/submit', methods=['POST'])
def job_submission():
  print(request.form)
  status = helper_functions.submit_job(
      request,
      app.config['BUCKET_NAME'],
      app.config['REGION'])
  if status == 'DOCKER_IMAGE_ERROR':
    message = (
        'Docker image is not ready for training. '
        'Try once more in a minute!')
  elif status == 'JOB_SUBMITTED':
    message = 'Training started successfully!'
  elif status == 'PREPROCESSING_NOT_FINISHED':
    message = 'Preprocessing is not yet finished. Try once more in a minute!'
  elif status == 'PREPROCESSING_ERROR':
    message = 'Preprocessing job failed. Run it once more!'
  elif status == 'PREPROCESSING_NOT_SUBMITTED':
    message = 'You haven\'t preprocessed the data!'
  else:
    message = 'There was a problem starting training. Try once more!'
  return render_template('index_vm.html', message=message)

@app.route('/check_status', methods=['POST'])
def check_status():
  if 'JOB_NAME' in os.environ:
    status = helper_functions.check_job_status(os.environ['JOB_NAME'])
    if status == 'JOB_NOT_EXIST':
      message = 'You haven\'t submitted training job yet!'
    else:
      message = 'Training job status: ' + status
  else:
    message = 'You haven\'t submitted training job yet!'

  return render_template('index_vm.html', message=message)

@app.route('/download', methods=['POST'])
def download_model():
  if 'JOB_NAME' in os.environ:
    status = helper_functions.check_job_status(os.environ['JOB_NAME'])
    if status == 'JOB_NOT_EXIST':
      message = 'You haven\'t submitted training job yet!'
      return render_template('index_vm.html', message=message)
    elif status == 'SUCCEEDED':
      helper_functions.get_model(app.config['BUCKET_NAME'],
                                 downloads_dir, app.instance_path)
      download_zip = os.path.join(app.instance_path, 'model.zip')
      return send_file(download_zip, as_attachment=True)
    else:
      message = 'Training job status: ' + status
      return render_template('index_vm.html', message=message)

@app.route('/delete_bucket', methods=['POST'])
def delete_bucket():
  status = helper_functions.delete_bucket(app.config['BUCKET_NAME'])
  if status == 'ERROR':
    message = 'There was a problem deleting bucket :/'
  else:
    message = 'Bucket deleted successfully!'
  return render_template('index_vm.html', message=message)


@app.route('/tensorboard', methods=['POST'])
def enable_tensorboard():
  #if 'JOB_NAME' in os.environ:
    #status = helper_functions.check_job_status(os.environ['JOB_NAME'])
    status = 'RUNNING'
    if status == 'JOB_NOT_EXIST':
      message = 'You haven\'t submitted training job yet!'
      return render_template('index_vm.html', message=message)
    elif status == 'RUNNING':
        tensorboard_command = ('tensorboard --logdir ' +
                               app.config['BUCKET_NAME'] + '/model ' +
                               '--port 6006 --bind_all &')
        os.system(tensorboard_command)
        link = subprocess.check_output("gcloud compute instances describe ddsp-docker --zone=europe-west4-a --format='get(networkInterfaces[0].accessConfigs[0].natIP)'", shell=True)
        link = str(link)
        link = link[2:-3]
        link = 'http://' + link + ':6006/'
        return render_template('index_vm.html', link=link)
    else:
      message = 'Training job status: ' + status
      return render_template('index_vm.html', message=message)
  #else:
   # message = 'You haven\'t submitted training job yet!'
    #return render_template('index_vm.html', message=message)

if __name__ == '__main__':
  app.run(host='127.0.0.1', port=8080, debug=True)

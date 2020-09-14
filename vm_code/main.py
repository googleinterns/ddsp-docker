"""Main app script."""
from datetime import datetime
import os

from flask import abort, Flask, render_template, request
from werkzeug.utils import secure_filename

import helper_functions

app = Flask(
    __name__,
    static_url_path='',
    static_folder='../web_interface')
app.config['UPLOAD_EXTENSIONS'] = ['.wav', '.mp3']
app.config['UPLOAD_PATH'] = 'uploads'
app.config['REGION'] = 'europe-west4'
app.config['BUCKET_NAME'] = (
    'gs://ddsp-train-' +
    str(int((datetime.now()-datetime(1970, 1, 1)).total_seconds())))

# Create a directory in a known location to save files to.
uploads_dir = os.path.join(app.instance_path, app.config['UPLOAD_PATH'])
os.makedirs(uploads_dir, exist_ok=True)

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

if __name__ == '__main__':
  app.run(host='127.0.0.1', port=8080, debug=True)

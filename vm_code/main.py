"""Main app script."""
import datetime
import os

from flask import Flask, send_from_directory, request, redirect, url_for, abort
import helper_functions
from werkzeug.utils import secure_filename

app = Flask(
    __name__,
    static_url_path='',
    static_folder='../web_interface')
app.config['UPLOAD_EXTENSIONS'] = ['.wav', '.mp3']
app.config['UPLOAD_PATH'] = 'uploads'
app.config['REGION'] = 'europe-west4'
app.config['BUCKET_NAME'] = "gs://ddsp-train-" + str(int((datetime.datetime.now()-datetime.datetime(1970,1,1)).total_seconds()))

# Create a directory in a known location to save files to.
uploads_dir = os.path.join(app.instance_path, app.config['UPLOAD_PATH'])
os.makedirs(uploads_dir, exist_ok=True)

@app.route('/')
def main():
    return send_from_directory(app.static_folder, 'index_vm.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    for uploaded_file in request.files.getlist('file'):
        filename = secure_filename(uploaded_file.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)
            uploaded_file.save(os.path.join(uploads_dir, filename))D
    helper_functions.create_bucket(app.config['BUCKET_NAME']))
    helper_functions.upload_blob(app.config['BUCKET_NAME'], uploads_dir)
    return redirect(url_for('main'))

@app.route('/preprocess', methods=['POST'])
def preprocess():
    helper_functions.run_preprocessing(app.config['BUCKET_NAME'], app.config['REGION'])
    return redirect(url_for('main'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
    

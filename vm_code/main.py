import os
import time
import calendar
from werkzeug.utils import secure_filename
from flask import Flask, send_from_directory, request, redirect, url_for, abort
import helper_functions

app = Flask(
    __name__,
    static_url_path='',
    static_folder='../web_interface')
app.config['UPLOAD_EXTENSIONS'] = ['.wav', '.mp3']
app.config['UPLOAD_PATH'] = 'uploads'

# Create a directory in a known location to save files to.
uploads_dir = os.path.join(app.instance_path, app.config['UPLOAD_PATH'])
os.makedirs(uploads_dir, exist_ok=True)

BUCKET_NAME = "gs://ddsp-train-" + str(calendar.timegm(time.gmtime()))

@app.route('/')
def main():
    return send_from_directory(app.static_folder, 'index_vm.html')

@app.route('/', methods=['POST'])
def upload_files():
    for uploaded_file in request.files.getlist('file'):
        filename = secure_filename(uploaded_file.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)
            uploaded_file.save(os.path.join(uploads_dir, filename))
    #helper_functions.create_bucket(BUCKET_NAME)
    #helper_functions.upload_blob(BUCKET_NAME, uploads_dir)
    create_command = "gsutil mb " + BUCKET_NAME
    os.system(create_command)
    upload_command = "gsutil -m cp -r " + uploads_dir + " " + BUCKET_NAME + "/audio"
    os.system(upload_command)
    return redirect(url_for('main'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
    
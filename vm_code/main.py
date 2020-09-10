from flask import Flask, send_from_directory
app = Flask(
    __name__,
    static_url_path='', 
    static_folder='../web_interface')

@app.route("/preprocess/", methods=['POST'])
def preprocess():
    preprocess_command = (
        ["ddsp_prepare_tfrecord",
         "--num_shards=10",
         "--alsologtostderr",
         "--input_audio_filepatterns=/usr/local/google/home/werror/Music/music/*wav",
         "--output_tfrecord_path=/usr/local/google/home/werror/ddsp_dist/preprocessed"])
    subprocess.run(args=ddsp_run_command, check=True)
    #return send_from_directory(app.static_folder, 'index_vm.html')

@app.route('/')
def main():
    return send_from_directory(app.static_folder, 'index_vm.html')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
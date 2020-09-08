from flask import Flask, send_from_directory
app = Flask(
    __name__,
    static_url_path='', 
    static_folder='../web_interface')


@app.route('/')
def main():
    return send_from_directory(app.static_folder, 'index_vm.html')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
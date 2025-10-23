from flask import Flask, send_file, abort
import os

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    idx = os.path.join(BASE_DIR, 'index.html')
    if not os.path.exists(idx):
        return '<h3>No reports generated yet.</h3>', 200
    return send_file(idx)

@app.route('/<path:subpath>')
def serve_reports(subpath):
    full = os.path.join(BASE_DIR, subpath)
    if not os.path.exists(full):
        abort(404)
    return send_file(full)

if __name__ == '__main__':
    print('Serving reports from', BASE_DIR)
    app.run(host='0.0.0.0', port=8080)


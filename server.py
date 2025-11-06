from flask import Flask, send_file, abort, jsonify, request
import os
import json

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 简单的访客计数器
visitor_count = 0
VISITOR_FILE = os.path.join(BASE_DIR, 'visitor_count.json')

def load_visitor_count():
    global visitor_count
    try:
        if os.path.exists(VISITOR_FILE):
            with open(VISITOR_FILE, 'r') as f:
                data = json.load(f)
                visitor_count = data.get('count', 0)
    except:
        visitor_count = 0

def save_visitor_count():
    try:
        with open(VISITOR_FILE, 'w') as f:
            json.dump({'count': visitor_count}, f)
    except:
        pass

# 加载访客计数
load_visitor_count()

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


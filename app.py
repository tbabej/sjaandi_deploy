import os
from pathlib import Path

from flask import Flask
from flask import render_template
from flask import request
from flask_dropzone import Dropzone


basedir = Path(__file__).resolve()  # absolute path of the app.py

app = Flask(__name__)

app.config.update(
    UPLOADED_PATH=os.path.join(basedir, 'uploads'),
    # Flask-Dropzone config:
    DROPZONE_ALLOWED_FILE_TYPE='image',
    DROPZONE_MAX_FILE_SIZE=3,
    DROPZONE_MAX_FILES=16,
    DROPZONE_UPLOAD_ON_CLICK=True,
    DROPZONE_REDIRECT_VIEW='collage',
)

dropzone = Dropzone(app)


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        for key, f in request.files.items():
            if key.startswith('file'):
                print('RECEIVED AN IMAGE!')
                # f.save(os.path.join(app.config['UPLOADED_PATH'], f.filename))
    return render_template('index.html')


@app.route('/collage')
def collage():
    return 'BEHOLD! HEREIN LIES YOUR BEAUTIFUL COLLAGE!'


if __name__ == "__main__":
    app.run(debug=True)

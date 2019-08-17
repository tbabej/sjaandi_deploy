import os
from pathlib import Path
import shutil

from flask import Flask
from flask import render_template
from flask import request
from flask_dropzone import Dropzone
import numpy as np
import imageio


BASEDIR: Path = Path(__file__).resolve().parents[0]
UPLOADS_DIR: Path = BASEDIR/'uploads'
debug = True


app = Flask(__name__)

app.config.update(
    UPLOADED_PATH=os.path.join(BASEDIR, 'uploads'),
    # Flask-Dropzone config:
    DROPZONE_ALLOWED_FILE_TYPE='image',
    DROPZONE_MAX_FILE_SIZE=3,
    DROPZONE_MAX_FILES=16,
    DROPZONE_UPLOAD_ON_CLICK=True,
    DROPZONE_REDIRECT_VIEW='collage',
)

dropzone = Dropzone(app)


def clear_uploads_folder(folder: Path = UPLOADS_DIR):
    shutil.rmtree(folder)
    os.makedirs(UPLOADS_DIR)


@app.route('/', methods=['POST', 'GET'])
def index():
    if debug:
        clear_uploads_folder()
        # TODO: set up logging instead of print statements
        print("CLEARED UPLOAD FOLDER")
    if request.method == 'POST':
        # TODO: handle cases with different images with the same name
        # TODO: handle when size is too small - can't upscale currently
        # f: werkzeug.datastructures.FileStorage
        for key, f in request.files.items():
            if key.startswith('file'):
                # img = imageio.imread(f)
                f.save(str(UPLOADS_DIR/f.filename))
                print('RECEIVED AND SAVED AN IMAGE!')
    return render_template('index.html')


@app.route('/collage')
def collage():
    files = [fname for fname in UPLOADS_DIR.iterdir() if fname.is_file()]
    for fname in files:
        # Note: imageio can read image directly from file bytestream
        img = imageio.imread(fname)[:,:,:3]  # remove alpha channel
        print(img.shape)
    return str(files)
    # return 'BEHOLD! HEREIN LIES YOUR BEAUTIFUL COLLAGE!'


if __name__ == "__main__":
    app.run(debug=True)

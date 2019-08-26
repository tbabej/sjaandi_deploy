import os
from pathlib import Path
import shutil
import tempfile
import uuid

from flask import Flask
from flask import render_template
from flask import request
from flask import session
from flask_session import Session
from flask_dropzone import Dropzone
import imageio
import numpy as np

from sjaandi import VisualSearchEngine
from sjaandi import get_data


BASEDIR: Path = Path(__file__).resolve().parents[0]
USERS_DIR: Path = BASEDIR/'static'/'users'
debug = True


app = Flask(__name__)
# Check Configuration section for more details
SESSION_TYPE = 'redis'
app.config.from_object(__name__)
Session(app)


app.config.update(
    # UPLOADED_PATH=os.path.join(BASEDIR, 'uploads'), # possibly unnecessary
    # Flask-Dropzone config:
    DROPZONE_ALLOWED_FILE_TYPE='image',
    DROPZONE_MAX_FILE_SIZE=5,
    DROPZONE_MAX_FILES=100,
    DROPZONE_UPLOAD_ON_CLICK=True,
    DROPZONE_REDIRECT_VIEW='collage',
)

dropzone = Dropzone(app)


def make_dummy_collage(username: str, folder: str):
    """
    Make and save a dummy collage into user folder.

    Uses a dummy image to pretend that is the collage.

    :param username: unique user id
    :param folder: stores images to make the collage
    :return: None
    """
    DUMMY_IMAGE_PATH = 'dummy.png'
    img = imageio.imread(DUMMY_IMAGE_PATH)[:,:,:3]
    print(type(img))
    save_folder: Path = USERS_DIR / username
    if not save_folder.exists():
        print("CREATING NEW USER'S DIRECTORY")
        os.makedirs(save_folder)
    filename = str(uuid.uuid4()) + '.png'
    save_path = save_folder/filename
    imageio.imwrite(save_path, img)


def make_collage(user: str, data_path: str):
    """
    Make and save collage into user folder.

    :param user: unique user id
    :param data_path: stores images to make the collage
    :return:
    """
    engine = VisualSearchEngine(data_path)
    new_collage = engine.make_collage()
    save_folder: Path = USERS_DIR/user
    if not save_folder.exists():
        print("CREATING NEW USER'S DIRECTORY")
        os.makedirs(save_folder)
    filename = str(uuid.uuid4()) + '.png'
    save_path = save_folder/filename
    imageio.imwrite(save_path, new_collage)


@app.route('/', methods=['POST', 'GET'])
def index():
    """
    1. check if user exists, if not, add it to session object
    2. create a temporary folder to store uploaded images
    3. save all uploaded images
    4. if new user, make folder for collages, if old user, folder already exists
    5. make collage
    6. save collage to user folder
    """
    if request.method == 'GET':
        pass
    elif request.method == 'POST':
        if 'user' not in session:
            print('Creating new user.')
            user_id = str(uuid.uuid4())
            session['user'] = user_id
        else:
            print('Existing user.')
            user_id = session['user']
        # TODO: handle cases with different images with the same name
        # TODO: handle when size is too small - can't upscale currently
        # f: werkzeug.datastructures.FileStorage
        with tempfile.TemporaryDirectory() as tempdir:
            for key, f in request.files.items():
                if key.startswith('file'):
                    # img = imageio.imread(f)
                    f.save(os.path.join(tempdir, f.filename))
                    print('RECEIVED AND SAVED AN IMAGE!')
            print("ALL IMAGES UPLOADED.")
            # make_dummy_collage(user_id, tempdir)
            make_collage(user_id, tempdir)
            print("COLLAGE MADE!")
    return render_template('index.html',
                           max_images=app.config['DROPZONE_MAX_FILES'],
                           max_file_size=app.config['DROPZONE_MAX_FILE_SIZE'])


@app.route('/collage')
def collage():
    if 'user' in session:
        user_path = USERS_DIR/session['user']
        collages = [str(f).split('sjaandi_deploy/')[1] for f in user_path.iterdir()]
        print(collages)
        return render_template('collages.html', collages=collages)
    else:
        return "<h1>You don't have any collages yet.</h1>"


@app.route('/user')
def user():
    if 'user' in session:
        return f"Your user id is: {session['user']}"
    else:
        return "This is a new user."


if __name__ == "__main__":
    app.run(debug=True)

import os
from pathlib import Path
import shutil
import tempfile
from typing import List
import uuid

from flask import Flask
from flask import render_template
from flask import request
from flask import session
from flask_session import Session
from flask_dropzone import Dropzone
import imageio
import numpy as np
import redis

from sjaandi import VisualSearchEngine
from sjaandi import get_data


BASEDIR: Path = Path(__file__).resolve().parents[0]
USERS_DIR: Path = BASEDIR/'static'/'users'
debug = True


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
        os.makedirs(str(save_folder))  # accepts str, not Path
    filename = str(uuid.uuid4()) + '.png'
    save_path = save_folder/filename
    imageio.imwrite(save_path, img)


def make_collage(user_id: str, data_path: str):
    """
    Make and save collage into user folder.

    :param user_id: unique user id
    :param data_path: stores images to make the collage
    :return:
    """

    new_collage = VisualSearchEngine(data_path).make_collage()
    save_folder: Path = USERS_DIR / user_id
    filename = str(uuid.uuid4()) + '.png'
    save_path = save_folder/filename
    imageio.imwrite(save_path, new_collage)


def sort_from_new_to_old(file_path_list: List[str]) -> List[str]:
    """
    Sort file paths from newest to oldest.

    Uses modification date as sorting criterion.

    :param file_path_list: list
    :return:
    """

    # all paths must exist
    if not all(map(os.path.exists, file_path_list)):
        raise FileNotFoundError("Some of the files don't exist!")

    return sorted(file_path_list, key=lambda f: os.path.getmtime(f), reverse=True)


def handle_user() -> str:
    """
    Handle user.

    Create a unique user_id if user is new.
    Create a user directory if it doesn't exist.

    :return: user id
    """

    if 'user' not in session:
        print('Creating new user.')
        user_id = str(uuid.uuid4())
        session['user'] = user_id
    else:
        print('Existing user.')
        user_id = session['user']

    # handle user directory
    user_dir = USERS_DIR / user_id
    if not user_dir.exists():
        print("CREATING NEW USER'S DIRECTORY")
        os.makedirs(user_dir)

    return user_id


def create_app():

    app = Flask(__name__)
    app.config.from_object(__name__)

    # Check Configuration section for more details
    # And here: http://codeomitted.com/flask-session-aws-redis/
    # From here: https://pythonhosted.org/Flask-Session/
    app.config['SESSION_TYPE'] = 'redis'
    # Note: to work locally, 'redis' should be pointing to 127.0.0.1 in the hosts file
    app.config['SESSION_REDIS'] = redis.Redis(host='redis', port=6379)
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

    @app.route('/', methods=['POST', 'GET'])
    def index():
        """
        1. check if user exists, if not, add it to session object
        2. create a temporary folder to store uploaded images
        3. save all uploaded images
        4. if new user, make folder for collages, if old user, folder already exists
        5. make collage
        6. save collage to user folder

        :return: rendered home page template
        """

        # handle users regardless of the method
        user_id = handle_user()

        if request.method == 'GET':
            pass
        elif request.method == 'POST':
            # TODO: handle cases with different images with the same name
            # f is werkzeug.datastructures.FileStorage
            with tempfile.TemporaryDirectory() as tempdir:
                for key, f in request.files.items():
                    if key.startswith('file'):
                        f.save(os.path.join(tempdir, f.filename))
                        print('RECEIVED AND SAVED AN IMAGE!')
                print("ALL IMAGES UPLOADED.")
                make_collage(user_id, tempdir)
                print("COLLAGE MADE!")
        return render_template('index.html',
                               max_images=app.config['DROPZONE_MAX_FILES'],
                               max_file_size=app.config['DROPZONE_MAX_FILE_SIZE'])

    @app.route('/collage')
    def collage():
        """
        Present all existing user's collages.

        Loop through existing files in user's directory and keep only .png
        Pass their paths to `collages.html` template.

        :return: rendered collages template
        """
        if 'user' in session:
            user_path = USERS_DIR/session['user']

            # only keep `.png` files
            sorted_file_paths = sort_from_new_to_old([str(f) for f in user_path.iterdir() if str(f).endswith('.png')])

            # only keep path after 'static/`; it will be used with url_for('static')
            collages_paths = [str(f).split('static/')[1] for f in sorted_file_paths]

            return render_template('collages.html', collages=collages_paths)
        else:
            return "<h1>You don't have any collages yet.</h1>"

    @app.route('/user')
    def user():
        """
        Inform the user of their unique user id.

        :return: information about the user id
        """

        if 'user' in session:
            return f"<h1>Your user id is: {session['user']}</h1>"
        else:
            return "This is a new user."

    return app


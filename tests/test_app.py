import os
from tempfile import mkdtemp
from uuid import uuid4
from typing import Tuple
from functools import partial
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import Chrome
import pytest
import numpy as np
import imageio


class InvalidParameterValueError(Exception):
    pass


APP_ADDRESS = 'http://localhost:5000/'


def save_random_image(full_name: str,
                      resolution: Tuple[int, int] = (300, 300),
                      channels: int = 3):
    """
    Save synthetic image of given resolution and extension to folder.

    :param full_name: filename, including a valid extension
    :param resolution: height and width of the image
    :param channels: channels in the image
    :return:
    """

    supported_channels = [1, 3, 4]
    if channels not in supported_channels:
        raise InvalidParameterValueError(f"Images that have {channels} channels are not supported.")

    img = np.random.randint(0, high=256, size=(*resolution, channels), dtype=np.uint8)
    try:
        imageio.imsave(full_name, img)
    except ValueError:
        print(f"Filename has wrong extension: {full_name}")
    except FileNotFoundError:
        print(f"Directory doesn't exist: {full_name}")


def save_random_file(file_path: str):
    """
    Create a file at given path, fill with random string, save.

    :param file_path: full path to the file to be created.
    :return:
    """
    with open(file_path, 'w') as f:
        f.write(str(uuid4()))
        f.close()


def make_folder_with_files(extension: str = '.jpg', n_files=5, file_type: str = 'random', **kwargs) -> str:
    """
    Make a temp folder with n files of given extension.

    .. note:: kwargs are passed through to file_creating_function and are function-specific

    :param extension: file extension, either with dot or not
    :param n_files: number of files to generate
    :param file_type: which type of file to create:
        - 'random': file with random string contents
        - 'image': random valid image
    :return: path to the folder with files
    """

    # assign file creating function
    if file_type == 'random':
        file_creating_function = partial(save_random_file, **kwargs)
    elif file_type == 'image' or file_type == 'images':
        file_creating_function = partial(save_random_image, **kwargs)
    else:
        raise InvalidParameterValueError(f"File type '{file_type}' is not supported.")

    # create files
    temp_dir = mkdtemp()
    for i in range(n_files):
        file_path = os.path.join(temp_dir, f"some-file-{i}.{extension.strip('.')}")
        try:
            file_creating_function(file_path)
        except TypeError:
            raise InvalidParameterValueError(f"Function '{file_creating_function.func.__name__}' cannot accept arguments {kwargs}.")

    return temp_dir


def get_browser(headed=True) -> Chrome:
    chrome_options = Options()
    if not headed:
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
    browser = webdriver.Chrome(options=chrome_options)
    return browser


@pytest.fixture()
def image():
    return np.random.randn(100, 100, 3)


@pytest.fixture()
def browser_headed():
    browser = get_browser(headed=False)
    yield browser
    browser.close()


def test_true():
    assert True

def test_get_homepage(browser_headed: Chrome):
    browser_headed.get(APP_ADDRESS)

def test_click_upload_and_nothing_happens(browser_headed: Chrome):
    browser_headed.get(APP_ADDRESS)
    upload_button = browser_headed.find_element_by_id("upload")
    upload_button.click()
    # self.browser.current_url -> http://localhost:5000/
    assert browser_headed.current_url == APP_ADDRESS

def test_can_get_collage_with_thirty_valid_images(browser_headed):
    # get the front page of app
    browser_headed.get(APP_ADDRESS)

    # create some temporary files
    folder = make_folder_with_files(file_type='image', n_files=30)
    filenames = os.listdir(folder)

    # upload files one by one
    for file_path in filenames:
        dropzone = browser_headed.find_element_by_class_name("dz-hidden-input")
        dropzone.send_keys(os.path.join(folder, file_path))

    # click and upload
    upload_button = browser_headed.find_element_by_id("upload")
    upload_button.click()

    # wait from here
    wait = WebDriverWait(browser_headed, 10)
    wait.until(lambda browser: browser.current_url != APP_ADDRESS)
    # behold of the beautiful result!

    # see if redirected correctly
    assert browser_headed.current_url == APP_ADDRESS + 'collage'

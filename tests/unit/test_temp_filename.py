import os
import utils  # Replace this with the actual import based on your project structure
import shutil

def test_directory_creation():
    if os.path.exists(utils.TEMP_PATH):
        shutil.rmtree(utils.TEMP_PATH)
    utils.get_temp_filename("txt")
    assert os.path.exists(utils.TEMP_PATH)

def test_file_extension():
    filename = utils.get_temp_filename("txt")
    assert filename.endswith('.txt')

def test_unique_filename():
    first_filename = utils.get_temp_filename("txt")
    second_filename = utils.get_temp_filename("txt")
    assert first_filename != second_filename

import glob
import os

from config import Config


def upload_file(file_info, file_name, downloader: callable):
    save_dir = os.getcwd()
    downloaded_file = downloader(file_info.file_path)

    _file = save_dir + f"/{Config.UPLOAD_DIR}/" + file_name
    with open(_file, "wb") as new_file:
        new_file.write(downloaded_file)
    return _file


def clear_uploads(user_id):
    save_dir = os.getcwd() + f"/{Config.UPLOAD_DIR}/"
    for file in glob.glob(save_dir + f"*{user_id}*.*"):
        os.unlink(file)

import base64
from functools import wraps
from flask_login import current_user
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
import os
from flask import flash, url_for
import re
from config import imagedir
from PIL import Image


def upload_photo(image_data):
    filename = secure_filename(image_data.filename)
    same_filename_count = 0
    base = os.path.splitext(filename)
    original_name, extension = base[0], base[1]
    re.sub(r'\(\d+\)$', '', original_name)
    while filename in os.listdir(path=imagedir):
        filename = original_name + '(' + str(same_filename_count) + ')' + extension
        same_filename_count += 1
    filepath = (os.path.join(imagedir, filename))
    image_data.save(filepath)
    make_thumbnail((500, 500), filepath)
    make_thumbnail((120, 120), filepath)
    flash('Photo was uploaded!')
    return filename


def delete_photo(photo_id):
    filepath = os.path.join(imagedir, photo_id)
    if os.path.exists(filepath):
        os.remove(filepath)
        delete_thumbnails(photo_id)


def delete_thumbnails(photo_id, fsize=500, ssize=120):
    thumbnaildir = os.path.join(imagedir, 'thumbnails')
    original_filename, extension = os.path.splitext(photo_id)
    first_tmb_filename = original_filename + '_thumbnail' + str(fsize) + extension
    second_tmb_filename = original_filename + '_thumbnail' + str(ssize) + extension
    os.remove(os.path.join(thumbnaildir, first_tmb_filename))
    os.remove(os.path.join(thumbnaildir, second_tmb_filename))


def make_thumbnail(size, filepath):
    filename, extension = os.path.splitext(os.path.basename(filepath))
    img = Image.open(filepath)
    img.thumbnail(size)
    os.chdir(os.path.join(imagedir, 'thumbnails'))
    filename = filename + '_thumbnail' + str(size[0]) + extension
    img.save(filename)


def get_thumbnail(photo_id, size, url=True):
    filename, extension = os.path.splitext(photo_id)
    thumbnail_name = filename + '_thumbnail' + str(size) + extension
    if url:
        return url_for('static', filename='images/thumbnails/' + thumbnail_name)
    image = Image.open(os.path.join(imagedir, 'thumbnails', thumbnail_name))
    return base64.encode(image)


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.permission == 'admin':
                return f(*args, **kwargs)
            if current_user.permission != permission:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
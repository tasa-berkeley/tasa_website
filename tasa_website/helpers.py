# Helper functions and stuff
import os
import random
import re
import string
import time

import dateutil.parser
from flask import abort
from flask import session
from PIL import Image
from werkzeug.utils import secure_filename

from . import ROOT

ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'gif', 'png', 'pdf', 'doc', 'docx'])

POSITIONS = [
    'President',
    'Internal Vice President',
    'External Vice President',
    'Treasurer',
    'Webmaster',
    'Outreach',
    # 'Design',
    # 'Marketing',
    'Public Relations',
    'Family Head',
    'Historian',
    'Senior Advisor',
    'Treasurer Intern',
    'Webmaster Intern',
    'Outreach Intern',
    'Design Intern',
    'Marketing Intern',
    'Public Relations Intern',
    'Family Head Intern',
    'Historian Intern'

]

IMAGE_MAXSIZE = (1024, 1024)

img_formats = {
    'image/jpeg': 'JPEG',
    'image/png': 'PNG',
    'image/gif': 'GIF'
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_time(time_str):
    # turns the ISO-8601 format time given to us into epoch time and a formatted string
    date_time = dateutil.parser.parse(time_str)
    time_str = date_time.strftime("%A %B %d %I:%M%p")
    unix_time = int(time.mktime(date_time.timetuple()) + date_time.microsecond/1000000.0)
    return time_str, unix_time

def guess_image_extension(image):
    image_type = image.content_type
    if image_type in img_formats:
        return img_formats[image_type]
    return None

def generate_random_filename(extension):
    file_name = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8))
    file_name += '.' + extension
    return file_name

def create_file_paths(sub_root, file_name):
    file_url = os.path.join(sub_root, file_name)
    file_path = os.path.join(ROOT, file_url)
    return file_url, file_path

def file_from_request(request):
    if 'file' not in request.files:
        raise ValueError('No file attached')
    request_file = request.files['file']
    if request_file.filename == '':
        raise ValueError('Filename is empty')
    if not allowed_file(request_file.filename):
        raise ValueError('Not a supported file format. Must be gif, png, jpg, pdf, doc, or docx')
    return request_file

def save_request_file(request, save_folder):
    f = file_from_request(request)
    filename = secure_filename(f.filename)
    f_url, f_path = create_file_paths(save_folder, filename)
    if guess_image_extension(f) is not None:
        # replace image extension in filename with jpg
        f_path = re.sub(r'\.[a-zA-Z]*$', '.jpg', f_path)
        f_url = re.sub(r'\.[a-zA-Z]*$', '.jpg', f_url)
        # compress and resize the image
        img = Image.open(f)
        img.thumbnail(IMAGE_MAXSIZE)
        img.save(f_path, format='JPEG', quality=95, optimize=True, progressive=True)
    else:
        f.save(f_path)
    return f_url

def check_file_in_request(request):
    return 'file' in request.files and request.files['file'].filename != ''

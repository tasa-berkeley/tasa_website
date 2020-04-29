from io import StringIO
import requests
import urllib

from PIL import Image

from . import secrets

def _api_endpoint(event_id):
    return 'https://graph.facebook.com/v2.5/{}'.format(event_id)

def get_event(event_id):
    res = requests.get(_api_endpoint(event_id), params={
        'access_token': secrets['facebook'],
    }).json()
    return res

def get_cover_photo(event_id):
    res = requests.get(_api_endpoint(event_id), params={
        'access_token': secrets['facebook'],
        'fields': 'cover',
    }).json()
    image_url = res['cover']['source']
    image_data =  urllib.urlopen(image_url)
    image_file = io.StringIO(image_data.read())
    image = Image.open(image_file)
    return image

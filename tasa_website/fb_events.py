import io
import requests
import urllib

from PIL import Image

from . import secrets

def _api_endpoint(event_id):
    return 'https://graph.facebook.com/v8.0/{}'.format(event_id)

def get_event(event_id):
    res = requests.get(_api_endpoint(event_id), params={
        'access_token': secrets['facebook'],
        'fields': "cover,description,name,place,start_time,end_time,is_online,id"
    }).json()
    return res

def get_cover_photo(res):
    image_url = res['cover']['source']
    image_data =  urllib.request.urlopen(image_url)
    image_file = io.BytesIO(image_data.read())
    image = Image.open(image_file)
    return image

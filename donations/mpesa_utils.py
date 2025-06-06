# mpesa_utils.py
import base64
import datetime
import os
from django.conf import settings
import requests


def get_mpesa_access_token():
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(api_url, auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET))
    return response.json()['access_token']


def generate_password():
    shortcode = settings.MPESA_SHORTCODE
    passkey = settings.MPESA_PASSKEY
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    data_to_encode = shortcode + passkey + timestamp
    encoded_string = base64.b64encode(data_to_encode.encode())
    return encoded_string.decode('utf-8'), timestamp
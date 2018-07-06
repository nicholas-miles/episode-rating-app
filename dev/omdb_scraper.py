# pylint: disable=no-member
"""
URL and JSON tools for OMDB retrieval
BeautifulSoup for web scraping
"""
# file modification
import json
from contextlib import closing
# analysis toolkits
import pandas as pd
import numpy as np
from requests import get
from requests.exceptions import RequestException


def get_api_key(filepath):
    """
    Retrieve the current OMDB API key, returns a string
    """
    with open(filepath, 'r') as api_file:
        return api_file.readline().replace('\n', '').replace('\r', '')


def is_good_response(resp, expected='html'):
    """
    Returns true if the response is the expected format, false otherwise
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200 and
            content_type is not None and
            content_type.find(expected) > -1)


def simple_get(url, expected='html', payload=None):
    """
    Attempts to get the content at \\url\\ by making an HTTP GET request
    """
    try:
        with closing(get(url, stream=True, params=payload)) as resp:
            if is_good_response(resp, expected):
                return resp.text
            return None

    except RequestException as err_msg:
        print('Error during requests to {0} : {1}'.format(url, str(err_msg)))
        return None


def get_omdb_data(imdb_id):
    """
    Retrieve data from OMDB given parameter set, returns a JSON file
    """
    url = 'http://www.omdbapi.com/'
    payload = {
        'apikey': get_api_key('../omdb_api_key.txt'),
        'i': imdb_id,
        'plot': 'short'
    }

    raw_json = simple_get(url, 'json', payload)

    if raw_json is None:
        return None

    return json.loads(raw_json)

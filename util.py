import requests
import re
import logging
from bs4 import BeautifulSoup
_r_learnprogramming_url = re.compile(r'http://(www.)?reddit.com/r/learnprogramming')

def downloadRedditUrl(url):
    logging.debug(u"Downloading url: {}".format(url))
    assert _r_learnprogramming_url.match(url)
    headers = { 'User-Agent': 'SearchingReddit bot version 0.1'}
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        raise Exception("Non-OK status code: {}".format(r.status_code))
    return r.text

def parseRedditPost(html):
    bs = BeautifulSoup(html)
    return bs.select('div.usertext-body')[1].text

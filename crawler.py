import requests
from bs4 import BeautifulSoup
import logging
import time
import os.path
from base64 import b16encode
import argparse
from util import *

class Crawler(object):
    def __init__(self, start_url, storage_dir):
        self.start_url = start_url 
        self.storage_dir = storage_dir

    @staticmethod
    def _make_absolute_url(url):
        return 'http://reddit.com' + url

    def crawl(self):
        logging.debug("Starting to crawl from page {}".format(self.start_url))
        current_page_url = self.start_url
        ok_url_count = 0
        error_url_count = 0
        logging.debug("TEST")
        while True:
            if (ok_url_count + error_url_count) % 100 == 0:
                logging.info("Crawled {} oks -- {} errors -- {}".format(ok_url_count + error_url_count, ok_url_count, error_url_count))
            #logging.debug("current page is {}".format(current_page_url))
            ok_url_count += 1
            current_page = downloadRedditUrl(current_page_url)
            bs = BeautifulSoup(current_page)
            all_posts_links = bs.findAll('a',attrs={'class':'title'});
            post_links = [Crawler._make_absolute_url(link['href']) for link in all_posts_links]
            try:
                for post_link in post_links:
                    ok_url_count += 1
                    html = downloadRedditUrl(post_link)
                    stored_text_file_name = os.path.join(self.storage_dir,
                            b16encode(post_link))
                    stored_text_file = open(stored_text_file_name, "w")
                    stored_text_file.write(html.encode('utf8'))
                    stored_text_file.close()
                    time.sleep(2)
            except Exception as e:
                error_url_count += 1
                logging.error("An error occured while crawling!")
                logging.error(u"An error occured while crawling {}".format(current_page_url))
                logging.exception(e)
            
            next_page_url = bs.find('a', attrs={'rel' : 'next'})['href']

            assert next_page_url is not None
            #logging.debug("First post is {}".format(post_links[0]))
            current_page_url = next_page_url
            time.sleep(2)

def main():
    logging.getLogger().setLevel(logging.DEBUG)
    # Supress request info messages
    logging.getLogger("requests").setLevel(logging.WARNING)

    logging.info("some message")

    parser = argparse.ArgumentParser(description='Crawl /r/learnprogramming')
    parser.add_argument("--start_url", dest="start_url", required=True)
    parser.add_argument("--storage_dir", dest="storage_dir", required=True)
    args = parser.parse_args()
    crawler = Crawler(args.start_url, args.storage_dir)
    crawler.crawl()

if __name__ == "__main__": # are we invoking it from cli
    main()

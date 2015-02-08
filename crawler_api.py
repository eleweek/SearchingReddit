import praw
import logging
import argparse
from distutils.dir_util import mkpath
from praw.helpers import submission_stream
from crawler_utils import save_submission


def get_as_much_stuff_as_possible(storage_dir):
    mkpath(storage_dir, mode=0755)
    r = praw.Reddit(user_agent='SearchingReddit project 0.2 by /u/godlikesme')
    for method_name in ["get_hot", "get_new", "get_top_from_all", "get_top_from_week",
                        "get_top_from_month", "get_top_from_year", "get_top_from_day",
                        "get_top_from_hour"]:
        method = getattr(r.get_subreddit('learnprogramming'), method_name)
        submissions = method(limit=1000)
        for s in submissions:
            save_submission(s, storage_dir)


def crawl_continuously(storage_dir):
    r = praw.Reddit(user_agent='SearchingReddit project 0.2 by /u/godlikesme')
    for s in submission_stream(r, "learnprogramming"):
        save_submission(s, storage_dir)


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser(description='Crawl /r/learnprogramming using api')
    parser.add_argument("--storage_dir", dest="storage_dir", required=True)
    args = parser.parse_args()

    get_as_much_stuff_as_possible(args.storage_dir)
    crawl_continuously(args.storage_dir)


if __name__ == "__main__":
    main()

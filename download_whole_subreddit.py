import logging
import argparse
from distutils.dir_util import mkpath
import time
import praw
from crawler_utils import save_submission


# Downloads all the self posts from given subreddit
# TODO: dynamically change ts_interval
def download_the_whole_subreddit(storage_dir, subreddit_name, ts_interval, largest_timestamp):
    mkpath(storage_dir, mode=0755)
    r = praw.Reddit(user_agent='SearchingReddit project 0.2 by /u/godlikesme')
    if largest_timestamp is None:
        largest_timestamp = int(time.time()) + 12*3600
    cts2 = largest_timestamp
    cts1 = largest_timestamp - ts_interval
    current_ts_interval = ts_interval
    # TODO start_timestamp = subreddit creation time
    while True:
        # get submissions here
        search_results = list(r.search('timestamp:{}..{}'.format(cts1, cts2), subreddit=subreddit_name, syntax='cloudsearch'))

        logging.debug("Got {} submissions in interval {}..{}".format(len(search_results), cts1, cts2))
        for submission in search_results:
            save_submission(submission, storage_dir)

        if len(search_results) == 25:
            current_ts_interval /= 2
            cts1 = cts2 - current_ts_interval
            logging.debug("Reducing ts interval to {}".format(current_ts_interval))
            continue

        cts2 = cts1
        cts1 = cts2 - current_ts_interval

        if len(search_results) <= 7:
            current_ts_interval *= 2
            logging.debug("Increasing ts interval to {}".format(current_ts_interval))


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser(description='Download the whole subreddit')
    parser.add_argument("--storage_dir", dest="storage_dir", required=True)
    parser.add_argument("--subreddit", dest="subreddit", required=True, help="Download the whole subreddit")
    parser.add_argument("--timestamp_interval", dest="timestamp_interval", type=int, required=True)
    parser.add_argument("--largest_timestamp", dest="largest_timestamp", type=int, required=False, default=None)
    args = parser.parse_args()

    download_the_whole_subreddit(args.storage_dir, args.subreddit, args.timestamp_interval, args.largest_timestamp)

if __name__ == "__main__":
    main()

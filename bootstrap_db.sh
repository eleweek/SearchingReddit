echo "Script for bootstrapping the search engine databases"
echo ""
echo "This script will create the necessary folders, gets the posts from reddit, indexes them and runs the web server."
echo "It will get posts for 60 seconds."

rm -rf docs_dir/
rm -rf index_dir/
mkdir docs_dir
mkdir index_dir

timeout 60s python download_whole_subreddit.py --storage_dir docs_dir/ --timestamp_interval 9000 --subreddit learnprogramming
python indexer.py --stored_documents_dir docs_dir/ --index_dir index_dir/

INDEXES_DIR=index_dir/ python web_ui.py

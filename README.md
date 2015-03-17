SearchingReddit
===============

# Goal

This is an example of small search engine that allows people to search over /r/learnprogramming subreddit.

The goal of the project is to build a small but functional search engine and live stream it on youtube: http://www.youtube.com/c/AlexanderPutilin


# Setting up

1) NLTK files:

```
>>> import nltk
>>> nltk.download("punkt")
```

2) Database:  
To run the search engine, you need to download posts from reddit and run the indexer to create the final database. You have 2 options for doing this.

&nbsp;&nbsp; a. Using the bootstrap script:  
&nbsp;&nbsp;&nbsp;&nbsp; You can create a functional development environment by just running a single command. This will result in a database with very little results, but it's very easy to set up and enough to start developing.

`$ ./db_bootstrap.sh`

&nbsp;&nbsp;b. Doing it manually:  
&nbsp;&nbsp;&nbsp;&nbsp; If you want to run your own search engine, or need more result for your development, you can get the reddit data manually. This will allow you to have as much results as you need.

&nbsp;&nbsp;&nbsp;&nbsp; First, you need to create two directories. One for the reddit documents and one for the indexed database. Let's call them `docs_dir` and `index_dir`.

&nbsp;&nbsp;&nbsp;&nbsp; To get reddit data into the documents directory, you need to run `download_whole_subreddit.py` like this.

`python download_whole_subreddit.py --storage_dir docs_dir/ --timestamp_interval 9000 --subreddit learnprogramming`

&nbsp;&nbsp;&nbsp;&nbsp; This command will download reddit posts from the /r/learnprogramming subreddit to the `docs_dir` directory. It will keep running and downloading posts until you stop it.

&nbsp;&nbsp;&nbsp;&nbsp; After downloading the data, you need to index it so the search engine can use it. To do this you need to run `indexer.py` like this.

`python indexer.py --stored_documents_dir docs_dir/ --index_dir index_dir/`

&nbsp;&nbsp;&nbsp;&nbsp; This command will index the posts from the documents directory and put them into the `index_dir` folder.

&nbsp;&nbsp;&nbsp;&nbsp; After indexing, you can run the web server by running `web_ui.py`. You also need to supply the index directory as an environment variable.

`INDEXES_DIR=index_dir/ python web_ui.py`

&nbsp;&nbsp;&nbsp;&nbsp; Running this will run the search engine with the database in the `index_dir` directory.

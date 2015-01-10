#!/usr/bin/env python
from util import *
import argparse
import base64
import os
import pickle
from collections import defaultdict
from lang_proc import to_doc_terms 

# Two main types of indexes
# -- Forward index
# -- Inverted index

# Forward index
# doc1 -> [learning, python, how, to]
# doc2 -> [learning, C++]
# doc3 -> [python, C++]

# Inverted index
# learning -> [doc1, doc2]
# python -> [doc1, doc3]
# how -> [doc1]
# to -> [doc1]
# C++ -> [doc2, doc3]

# TODO: improve this:
# Indexer assumes that collection fits in RAM
class Indexer(object):
    def __init__(self):
        self.inverted_index = dict()
        self.forward_index  = dict()
        self.url_to_id      = dict()
        self.doc_count      = 0

    # TODO: remove these assumptions
    # assumes that add_document() is never called twice for a document
    # assumes that a document has an unique url
    # parsed_text is a list of Terms
    def add_document(self, url, parsed_text):
        self.doc_count += 1
        assert url not in self.url_to_id
        current_id = self.doc_count
        self.url_to_id[url] = current_id
        self.forward_index[current_id] = parsed_text
        for position,term in enumerate(parsed_text):
            # TODO: defaultdict
            if term not in self.inverted_index:
                self.inverted_index[term] = []
            self.inverted_index[term].append((position, current_id))
    
    def save_on_disk(self, index_dir):

        def dump_pickle_to_file(source, file_name):
            file_path = os.path.join(index_dir, file_name)
            pickle.dump(source, open(file_path, "w"))

        dump_pickle_to_file(self.inverted_index, "inverted_index")
        dump_pickle_to_file(self.forward_index, "forward_index")
        dump_pickle_to_file(self.url_to_id, "url_to_id")

class Searcher(object):
    def __init__(self, index_dir):
        self.inverted_index = dict()
        self.forward_index  = dict()
        self.url_to_id      = dict()

        def load_pickle_from_file(file_name):
            file_path = os.path.join(index_dir, file_name)
            dst = pickle.load(open(file_path))
            return dst

        self.inverted_index = load_pickle_from_file("inverted_index")
        self.forward_index = load_pickle_from_file("forward_index")
        self.url_to_id = load_pickle_from_file("url_to_id")

        self.id_to_url = {v : k for k,v in self.url_to_id.iteritems()}
    
    """
    # query [word1, word2] -> returns all documents that contain one of these words
    # sort of OR
    def find_documents(self, query_terms):
        return sum([self.inverted_index[word] for word in query_terms], [])
    """

    # The algorithms based on:
    # http://rcrezende.blogspot.com/2010/08/smallest-relevant-text-snippet-for.html
    def generate_snippet(self, query_terms, doc_id):
        query_terms_in_window = []
        best_window_len = 100500 # TODO: inf would be better :)
        terms_in_best_window = 0
        best_window = []
        for pos, term in enumerate(self.forward_index[doc_id]):
            if term in query_terms:
                query_terms_in_window.append((term, pos))
                if len(query_terms_in_window) > 1 and query_terms_in_window[0][0] == term:
                    query_terms_in_window.pop(0)
                current_window_len = pos - query_terms_in_window[0][1] + 1
                tiw = len(set(map(lambda x: x[0], query_terms_in_window))) 
                if tiw > terms_in_best_window or (tiw == terms_in_best_window and current_window_len < best_window_len):
                    terms_in_best_window = tiw
                    best_window = query_terms_in_window[:]
                    best_window_len = current_window_len

        doc_len = len(self.forward_index[doc_id])
        # TODO: 15 should be a named constant
        snippet_start = max(best_window[0][1] - 15, 0)
        snippet_end = min(doc_len, best_window[len(best_window) - 1][1] + 1 + 15)

        return [(term.full_word, term in query_terms) for term in self.forward_index[doc_id][snippet_start:snippet_end]]

    def find_documents_AND(self, query_terms):
        # docid -> number of query words
        query_term_count = defaultdict(set)
        for query_term in query_terms:
            for (pos, docid) in self.inverted_index.get(query_term, []):
                query_term_count[docid].add(query_term)

        return [doc_id for doc_id,unique_hits in query_term_count.iteritems() if len(unique_hits) == len(query_terms)]

    # sort of OR
    def find_documents_OR(self, query_terms):
        docids = set()
        for query_term in query_terms:
            for (pos, docid) in self.inverted_index.get(query_term, []):
                docids.add(docid)

        return docids

    def get_document_text(self, doc_id):
        return self.forward_index[doc_id]

    def get_url(self, doc_id):
        return self.id_to_url[doc_id]


def create_index_from_dir(stored_documents_dir, index_dir):
    indexer = Indexer()
    for filename in os.listdir(stored_documents_dir):
        opened_file = open(os.path.join(stored_documents_dir, filename))
        # TODO: words are separated not just by space, but by commas, semicolons, etc
        doc_raw = parseRedditPost(opened_file.read())      
        parsed_doc = to_doc_terms(doc_raw)
        indexer.add_document(base64.b16decode(filename), parsed_doc)

    indexer.save_on_disk(index_dir)

def main():
    parser = argparse.ArgumentParser(description='Index /r/learnprogramming')
    parser.add_argument("--stored_documents_dir", dest="stored_documents_dir", required=True)
    parser.add_argument("--index_dir", dest="index_dir", required=True)
    args = parser.parse_args()
    create_index_from_dir(args.stored_documents_dir, args.index_dir)

if __name__ == "__main__": # are we invoking it from cli
    main()

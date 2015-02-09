#!/usr/bin/env python
import argparse
import os
import pickle
from collections import defaultdict
from lang_proc import to_doc_terms
import json
import shelve


class BaseIndexes(object):
    # TODO: remove these assumptions
    # assumes that add_document() is never called twice for a document
    # assumes that a document has an unique url
    # parsed_text is a list of Terms
    def add_document(self, url, parsed_text):
        self.doc_count += 1
        assert url not in self.url_to_id
        current_id = self.doc_count
        self.url_to_id[url] = current_id
        self.id_to_url[current_id] = url
        self.forward_index[current_id] = parsed_text
        for position, term in enumerate(parsed_text):
            self.inverted_index[term].append((position, current_id))

    def get_documents(self, query_term):
        return self.inverted_index.get(query_term, [])

    def get_document_text(self, doc_id):
        return self.forward_index[str(doc_id)]

    def get_url(self, doc_id):
        return self.id_to_url[str(doc_id)]


class InMemoryIndexes(BaseIndexes):
    def __init__(self):
        # map(dict): from word to ids of documents that contain the word
        self.inverted_index = defaultdict(list)
        # list of parsed documents (map from doc id to list of words in a document)
        self.forward_index = dict()
        self.url_to_id = dict()
        self.id_to_url = dict()
        self.doc_count = 0

    def start_indexing(self):
        pass

    def save_on_disk(self, index_dir):

        def dump_pickle_to_file(source, file_name):
            file_path = os.path.join(index_dir, file_name)
            pickle.dump(source, open(file_path, "w"))

        dump_pickle_to_file(self.inverted_index, "inverted_index")
        dump_pickle_to_file(self.forward_index, "forward_index")
        dump_pickle_to_file(self.url_to_id, "url_to_id")

    def load_from_disk(self, index_dir):
        def load_pickle_from_file(file_name):
            file_path = os.path.join(index_dir, file_name)
            dst = pickle.load(open(file_path))
            return dst

        self.inverted_index = load_pickle_from_file("inverted_index")
        self.forward_index = load_pickle_from_file("forward_index")
        self.url_to_id = load_pickle_from_file("url_to_id")
        self.id_to_url = {v: k for k, v in self.url_to_id.iteritems()}
        print len(self.forward_index)


class ShelveIndexes(BaseIndexes):
    def __init__(self):
        # map(dict): from word to ids of documents that contain the word
        self.inverted_index = None
        # list of parsed documents (map from doc id to list of words in a document)
        self.forward_index = None
        self.url_to_id = None
        self.id_to_url = dict()
        self.doc_count = 0

    def save_on_disk(self, index_dir):
        self.inverted_index.close()
        self.forward_index.close()
        self.url_to_id.close()

    def load_from_disk(self, index_dir):
        self.inverted_index = shelve.open(os.path.join(index_dir, "inverted_index"))
        self.forward_index = shelve.open(os.path.join(index_dir, "forward_index"))
        self.url_to_id = shelve.open(os.path.join(index_dir, "url_to_id"))
        self.id_to_url = {v: k for k, v in self.url_to_id.iteritems()}
        print len(self.forward_index)

    def start_indexing(self, index_dir):
        self.inverted_index = shelve.open(os.path.join(index_dir, "inverted_index"), "n")
        self.forward_index = shelve.open(os.path.join(index_dir, "forward_index"), "n")
        self.url_to_id = shelve.open(os.path.join(index_dir, "url_to_id"), "n")

    def add_document(self, url, parsed_text):
        self.doc_count += 1
        assert url.encode('utf8') not in self.url_to_id
        current_id = self.doc_count
        self.url_to_id[url.encode('utf8')] = current_id
        self.id_to_url[current_id] = url
        self.forward_index[str(current_id)] = parsed_text
        for position, term in enumerate(parsed_text):
            stem = term.stem.encode('utf8')
            postings_list = self.inverted_index[stem] if stem in self.inverted_index else []
            postings_list.append((position, current_id))
            self.inverted_index[stem] = postings_list

    def get_documents(self, query_term):
        return self.inverted_index.get(query_term.stem.encode('utf8'), [])

    def get_document_text(self, doc_id):
        return self.forward_index[str(doc_id)]

    def get_url(self, doc_id):
        return self.id_to_url[doc_id]


class Searcher(object):
    def __init__(self, index_dir, IndexesImplementation):
        self.indexes = IndexesImplementation()
        self.indexes.load_from_disk(index_dir)

    # The algorithms based on:
    # http://rcrezende.blogspot.com/2010/08/smallest-relevant-text-snippet-for.html
    def generate_snippet(self, query_terms, doc_id):
        query_terms_in_window = []
        best_window_len = 100500  # TODO: inf would be better :)
        terms_in_best_window = 0
        best_window = []
        for pos, term in enumerate(self.indexes.get_document_text(doc_id)):
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

        doc_len = len(self.indexes.get_document_text(doc_id))
        # TODO: 15 should be a named constant
        snippet_start = max(best_window[0][1] - 15, 0)
        snippet_end = min(doc_len, best_window[len(best_window) - 1][1] + 1 + 15)

        return [(term.full_word, term in query_terms) for term in self.indexes.get_document_text(doc_id)[snippet_start:snippet_end]]

    def find_documents_AND(self, query_terms):
        # docid -> number of query words
        query_term_count = defaultdict(set)
        for query_term in query_terms:
            for (pos, docid) in self.indexes.get_documents(query_term):
                query_term_count[docid].add(query_term)

        return [doc_id for doc_id, unique_hits in query_term_count.iteritems() if len(unique_hits) == len(query_terms)]

    # sort of OR
    def find_documents_OR(self, query_terms):
        docids = set()
        for query_term in query_terms:
            for (pos, docid) in self.indexes.get_documents(query_term):
                docids.add(docid)

        return docids


def create_index_from_dir_API(stored_documents_dir, index_dir, IndexesImplementation=ShelveIndexes):
    indexer = IndexesImplementation()
    indexer.start_indexing(index_dir)
    indexed_docs_num = 0
    for filename in os.listdir(stored_documents_dir):
        indexed_docs_num += 1
        opened_file = open(os.path.join(stored_documents_dir, filename))
        doc_json = json.load(opened_file)
        parsed_doc = to_doc_terms(doc_json['text'])
        indexer.add_document(doc_json['url'], parsed_doc)
        if indexed_docs_num % 100 == 0:
            print "Indexed: ", indexed_docs_num

    indexer.save_on_disk(index_dir)


def main():
    parser = argparse.ArgumentParser(description='Index /r/learnprogramming')
    parser.add_argument("--stored_documents_dir", dest="stored_documents_dir", required=True)
    parser.add_argument("--index_dir", dest="index_dir", required=True)
    args = parser.parse_args()
    create_index_from_dir_API(args.stored_documents_dir, args.index_dir)


if __name__ == "__main__":
    main()

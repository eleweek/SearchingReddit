#!/usr/bin/env python
import argparse
import os
from collections import defaultdict
from lang_proc import to_doc_terms
import json
import shelve
import math
from progressbar import ProgressBar, Percentage, Bar, RotatingMarker
import workaround


class ShelveIndexes(object):
    def __init__(self):
        # map(dict): from word to ids of documents that contain the word
        self.inverted_index = None
        # list of parsed documents (map from doc id to list of words in a document)
        self.forward_index = None
        self.url_to_id = None
        self.id_to_url = dict()
        self.doc_count = 0
        self.block_count = 0 

    def total_doc_count(self):
        return self._doc_count
    
    def average_doclen(self):
        return self._avgdl
            

    def save_on_disk(self, index_dir):
        self.inverted_index.close()
        self.forward_index.close()
        self.url_to_id.close()
        self._merge_blocks()

    def load_from_disk(self, index_dir):
        self.inverted_index = shelve.open(os.path.join(index_dir, "inverted_index"))
        self.forward_index = shelve.open(os.path.join(index_dir, "forward_index"))
        self.url_to_id = shelve.open(os.path.join(index_dir, "url_to_id"))
        self.id_to_url = {v: k for k, v in self.url_to_id.items()}

        # TODO: avgdl and total doc count should be calculated when indexing
        self._doc_count = 0
        total_word_count = 0
        """
        for (docid, text) in self.forward_index.iteritems():
            self._doc_count += 1
            total_word_count += len(text.parsed_text)
        self._avgdl = total_word_count / self._doc_count
        """

        print "LOADED!"

    def start_indexing(self, index_dir):
        self.forward_index = shelve.open(os.path.join(index_dir, "forward_index"), "n", writeback=True)
        self.url_to_id = shelve.open(os.path.join(index_dir, "url_to_id"), "n", writeback=True)
        self.index_dir = index_dir

    def sync(self):
        self.inverted_index.sync()
        self.forward_index.sync()
        self.url_to_id.sync()

    def _merge_blocks(self):
        print "Merging blocks!"
        blocks = [shelve.open(os.path.join(self.index_dir, "inverted_index_block{}".format(i))) for i in xrange(self.block_count)]
        keys = set() 
        for block in blocks:
            keys |= set(block.keys())
        print "Total word count", len(keys)
        merged_index = shelve.open(os.path.join(self.index_dir, "inverted_index"), "n")
        key_ind = 0
        for key in keys:
            key_ind += 1
            print "MERGING", key_ind, key
            merged_index[key] = sum([block.get(key, []) for block in blocks],[])

        merged_index.close()

    def _create_new_ii_block(self):
        print "Created a new block!"
        if self.inverted_index:
            self.inverted_index.close()
        self.inverted_index = shelve.open(os.path.join(self.index_dir, "inverted_index_block{}".format(self.block_count)), "n", writeback=True)
        self.block_count += 1

    def add_document(self, url, doc):
        if self.doc_count % 2000 == 0:
            self._create_new_ii_block()

        self.doc_count += 1
        assert url.encode('utf8') not in self.url_to_id
        current_id = self.doc_count
        self.url_to_id[url.encode('utf8')] = current_id
        self.id_to_url[current_id] = url
        self.forward_index[str(current_id)] = doc
        for position, term in enumerate(doc.parsed_text):
            stem = term.stem.encode('utf8')
            if stem not in self.inverted_index:
                self.inverted_index[stem] = []
            self.inverted_index[stem].append(workaround.InvertedIndexHit(current_id, position, doc.score))

    def get_documents(self, query_term):
        return self.inverted_index.get(query_term.stem.encode('utf8'), [])

    def get_document_text(self, doc_id):
        return self.forward_index[str(doc_id)].parsed_text

    def get_url(self, doc_id):
        return self.id_to_url[doc_id]


class SerpPagination(object):
    def __init__(self, page, page_size, total_doc_num):
        self.page = page
        self.page_size = page_size
        self.pages = (total_doc_num / page_size) + 1

    def iter_pages(self):
        if self.pages == 1:
            return [1]
        if self.page <= 6:
            left_part = range(1, self.page)
        else:
            left_part = [1, None] + range(self.page - 4, self.page)
        right_part = range(self.page, min(self.pages + 1, self.page + 5))

        result = left_part + right_part
        if result[-1] != self.page:
            result.append(None)

        return result




class SearchResults(object):
    def __init__(self, docids_with_relevance):
        self.docids, self.relevances = zip(*docids_with_relevance) if docids_with_relevance else ([], [])

    def get_page(self, page, page_size):
        start_num = (page-1)*page_size
        return self.docids[start_num:start_num+page_size]

    def get_pagination(self, page, page_size):
        return SerpPagination(page, page_size, len(self.docids))

    def total_doc_num(self):
        return len(self.docids)


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
        snippet_start = max(best_window[0][1] - 8, 0)
        snippet_end = min(doc_len, best_window[len(best_window) - 1][1] + 1 + 8)

        snippet = [(term.full_word, term in query_terms) for term in self.indexes.get_document_text(doc_id)[snippet_start:snippet_end]]
        # TODO 50 should be a named constant too!
        if len(snippet) > 50:
            excessive_len = len(snippet) - 50
            snippet = snippet[:len(snippet) / 2 - excessive_len / 2] + [("...", False)]  + snippet[len(snippet) / 2 + excessive_len / 2:]

        
        return snippet

    """
    def find_documents_AND(self, query_terms):
        # docid -> number of query words
        query_term_count = defaultdict(set)
        for query_term in query_terms:
            for (pos, docid) in self.indexes.get_documents(query_term):
                query_term_count[docid].add(query_term)

        return SearchResults(self.rank_docids([doc_id for doc_id, unique_hits in query_term_count.iteritems() if len(unique_hits) == len(query_terms)]))
    """

    def find_documents_and_rank_by_points(self, query_terms):
        docids_and_relevance = set()
        for query_term in query_terms:
            for hit in self.indexes.get_documents(query_term):
                docids_and_relevance.add((hit.docid, hit.score))

        return SearchResults(sorted(list(docids_and_relevance), key=lambda x: x[1], reverse=True))

    def _bm25(self, docid, query_terms_to_posting_lists_sizes):
        result = 0
        text = self.indexes.get_document_text(docid)
        text_len = len(text)
        for qt, nd_containing in query_terms_to_posting_lists_sizes.iteritems():
            term_frequency = float(len(filter(lambda t: qt == t, text))) / text_len
            inverted_document_frequency = math.log((self.indexes.total_doc_count() - nd_containing + 0.5) / (nd_containing + 0.5))
            k1 = 1.5
            b = 0.75
            result += inverted_document_frequency * (term_frequency * (k1+1)) / (term_frequency + k1*(1 - b + b * query_terms_to_posting_lists_sizes[qt] / self.indexes.average_doclen()))

        return result

    def find_documents_and_rank_by_bm25(self, query_terms):
        docids = set()
        query_terms_to_posting_lists_sizes = dict()
        for query_term in query_terms:
            posting_list = self.indexes.get_documents(query_term)
            query_terms_to_posting_lists_sizes[query_term] = len(posting_list)
            for hit in posting_list:
                docids.add(hit.docid)

        docids_and_relevance = set()
        for docid in docids:
            docids_and_relevance.add((docid, self._bm25(docid, query_terms_to_posting_lists_sizes)))

        return SearchResults(sorted(list(docids_and_relevance), key=lambda x: x[1], reverse=True))



def create_index_from_dir_API(stored_documents_dir, index_dir, IndexesImplementation=ShelveIndexes):
    indexer = IndexesImplementation()
    indexer.start_indexing(index_dir)
    filenames = [name for name in os.listdir(stored_documents_dir)]
    # widgets = [' Indexing: ', Percentage(), ' ', Bar(marker=RotatingMarker())]
    indexed_docs_num = 0
    # progressbar = ProgressBar(widgets=widgets, maxval=len(filenames))
    for filename in filenames:
        indexed_docs_num += 1
        # progressbar.update(indexed_docs_num)
        opened_file = open(os.path.join(stored_documents_dir, filename))
        doc_json = json.load(opened_file)
        parsed_doc = to_doc_terms(doc_json['text'])
        print indexed_docs_num
        if indexed_docs_num % 100 == 0:
            print indexed_docs_num, "Syncing..."
            indexer.sync()
            print indexed_docs_num, "Synced!"

        indexer.add_document(doc_json['url'], workaround.Document(parsed_doc, int(doc_json['score'])))
        # progressbar.update(indexed_docs_num)
    indexer.save_on_disk(index_dir)


def main():
    parser = argparse.ArgumentParser(description='Index /r/learnprogramming')
    parser.add_argument("--stored_documents_dir", dest="stored_documents_dir", required=True)
    parser.add_argument("--index_dir", dest="index_dir", required=True)
    args = parser.parse_args()
    create_index_from_dir_API(args.stored_documents_dir, args.index_dir)


if __name__ == "__main__":
    main()

from nltk.stem.porter import PorterStemmer
from nltk.tokenize import sent_tokenize, TreebankWordTokenizer
from nltk.corpus import stopwords
_stop_words = stopwords.words('english')
import itertools
import string


class Term(object):
    def __init__(self, full_word):
        self.full_word = full_word
        # TODO: Lemmatization requires downloads
        # wnl = WordNetLemmatizer()
        # lemmas = [wnl.lemmatize(token) for token in tokens]
        self.stem = PorterStemmer().stem(full_word).lower()

    def __eq__(self, other):
        return self.stem == other.stem

    def __hash__(self):
        return hash(self.stem)

    def __repr__(self):
        return "Term {}({})".format(self.stem.encode('utf8'), self.full_word.encode('utf8'))

    def __str__(self):
        return repr(self)

    def is_punctuation(self):
        return self.stem in string.punctuation

    def is_stop_word(self):
        return self.full_word in _stop_words


def stem_and_tokenize_text(text):
    sents = sent_tokenize(text)
    tokens = list(itertools.chain(*[TreebankWordTokenizer().tokenize(sent) for sent in sents]))
    terms = [Term(token) for token in tokens]
    return filter(lambda term: not term.is_punctuation(), terms)


def to_query_terms(query_raw):
    # In case query and doc require different processing in the future
    return stem_and_tokenize_text(query_raw)


def to_doc_terms(doc_raw):
    # In case query and doc require different processing in the future
    return stem_and_tokenize_text(doc_raw)

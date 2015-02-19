class Document(object):
    def __init__(self, parsed_text, score):
        self.parsed_text = parsed_text
        self.score = score


class InvertedIndexHit(object):
    def __init__(self, docid, position, score):
        self.docid = docid
        self.position = position
        self.score = score

from flask import Flask, render_template, redirect, url_for, g
from flask_bootstrap import Bootstrap
from flask_wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from indexer import Searcher, InMemoryIndexes, ShelveIndexes
from lang_proc import to_query_terms
import logging

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)
Bootstrap(app)


@app.before_request
def init_searcher():
    # TODO dir configurable
    g.searcher = Searcher("indexes_shelves", ShelveIndexes)


class SearchForm(Form):
    user_query = StringField('user_query', validators=[DataRequired()])
    search_button = SubmitField("Search!")


@app.route("/", methods=["GET", "POST"])
def index():
    search_form = SearchForm(csrf_enabled=False)
    if search_form.validate_on_submit():
        return redirect(url_for("search_results", query=search_form.user_query.data))
    return render_template("index.html", form=search_form)


@app.route("/search_results/<query>", defaults={'page': 1})
@app.route("/search_results/<query>/<int:page>")
def search_results(query, page):
    query_terms = to_query_terms(query)
    app.logger.info("Requested [{}]".format(" ".join(map(str, query_terms))))
    page_size = 25
    search_results = g.searcher.find_documents_OR(query_terms)
    docids = search_results.get_page(page, page_size)
    urls = [g.searcher.indexes.get_url(docid) for docid in docids]
    texts = [g.searcher.generate_snippet(query_terms, docid) for docid in docids]

    return render_template("search_results.html", offset=((page-1)*page_size), total_pages_num=search_results.total_pages(page_size), page=page, query=query, urls_and_texts=zip(urls, texts))

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')

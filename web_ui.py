from flask import Flask, render_template, redirect, url_for, request, abort
from flask_bootstrap import Bootstrap
from flask_wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from indexer import Searcher, ShelveIndexes
from lang_proc import to_query_terms
import logging
import cgi
from datetime import datetime
import os
import workaround # NOQA

searcher = Searcher(os.environ["INDEXES_DIR"], ShelveIndexes)
app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)
Bootstrap(app)


def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


app.jinja_env.globals['url_for_other_page'] = url_for_other_page


class SearchForm(Form):
    user_query = StringField('Query', validators=[DataRequired()])
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
    start_time = datetime.now()
    query_terms = to_query_terms(query)
    app.logger.info("Requested [{}]".format(" ".join(map(str, query_terms))))
    page_size = 25
    search_results = searcher.find_documents_and_rank_by_points(query_terms)
    docids = search_results.get_page(page, page_size)
    pagination = search_results.get_pagination(page, page_size)
    if page > pagination.pages:
        abort(404)
    docs = []
    for docid in docids:
        docs.append((searcher.indexes.get_url(docid), searcher.generate_snippet(query_terms, docid), searcher.indexes.get_title(docid)))
    finish_time = datetime.now()

    return render_template("search_results.html",
                           processing_time=(finish_time-start_time),
                           offset=((page-1)*page_size),
                           total_doc_num=search_results.total_doc_num(),
                           pagination=pagination,
                           query=cgi.escape(query),
                           docs=docs)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')

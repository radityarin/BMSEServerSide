import flask
from flask import request, jsonify
import sqlite3
from bmse import BooleanModelSearchEngine

app = flask.Flask(__name__)
app.config["DEBUG"] = True

@app.route('/', methods=['GET'])
def home():
    return '''<h1>API for Information Retrieval FINAL PROJECT - Boolean Model Search Engine </h1>
<p>An API that returns News based on boolean form query</p>'''

@app.route('/news/all', methods=['GET'])
def api_all():
    bmse = BooleanModelSearchEngine()
    a = bmse.ask('')
    result_dict = {}
    result_dict["success"] = True
    result_dict["message"] = "News Loaded"
    result_dict["data"] = a
    return jsonify(result_dict)

@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404

@app.route('/news', methods=['GET'])
def api_filter():
    query_parameters = request.args
    raw_query = query_parameters.get('query')
    query = raw_query.replace("%20"," ")
    bmse = BooleanModelSearchEngine()
    a = bmse.ask(query)
    result_dict = {}
    result_dict["success"] = True
    result_dict["message"] = "News Loaded"
    result_dict["data"] = a
    return jsonify(result_dict)

if __name__ == "__main__": 
        app.run() 
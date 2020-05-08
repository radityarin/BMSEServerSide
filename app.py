import flask
from flask import request, jsonify
import sqlite3
import numpy as np
import re

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

class Stack:
    def __init__(self):
        self.items = []

    def isEmpty(self):
        return len(self.items) == 0

    def push(self, item):
        self.items.append(item)

    def pop(self):
        return self.items.pop()

    def peek(self):
        return self.items[len(self.items)-1]
    
    def values(self):
        return self.items


class BooleanModelSearchEngine(object):
    
    def __init__(self):
        data = openfile('data/dokuji.txt')
        self.corpus = data
        self.terms = []
        self.incidence_matrix = {}
        self.parsed_documents = {}
        self.cleaned_documents = {}
        self.query = None
        self.postfix = None
        self.postfix_evaluation = None
        self.result_list = []
        self.precedence = {'(': 1, ')': 1, 'or': 2, 'OR':2, 'and': 3, 'AND':3, 'not': 4, 'NOT':4}
        self.fit()

    def fit(self):
        self.parsing()
        self.clean_documents()
        self.find_terms()
        self.create_incidence_matrix()

    def ask(self,query):
        self.query = query
        query_length = len(query.split())
        self.postfix = self.infix_to_postfix(query)
        self.postfix_evaluation = self.evaluate_postfix()
        self.get_result_list()
        return self.show_result()

    def get_result_list(self):
        for i in range(len(self.postfix_evaluation)):
            if self.postfix_evaluation[i] == 1:
                temp = [self.parsed_documents[i+1][0],self.parsed_documents[i+1][2]]
                self.result_list.append(temp)

    def show_result(self):
        result_json = []
        count_id = 1
        for doc in self.result_list:
            dict_result = {}
            dict_result["id"] = count_id
            dict_result["title"] = doc[0]
            dict_result["link"] = doc[1]
            result_json.append(dict_result)
            count_id+=1
        return result_json

    def parsing(self):
        pattern_title = r'<TITLE>((.|\n)*?)<\/TITLE>'
        pattern_text = r'<TEXT>((.|\n)*?)<\/TEXT>'
        pattern_link = r'<LINK>((.|\n)*?)<\/LINK>'
        title = re.findall(pattern_title, self.corpus)
        text = re.findall(pattern_text, self.corpus)
        link = re.findall(pattern_link, self.corpus)
        read_pd = np.load('data/parsed_documents.npy',allow_pickle='TRUE').item()
        self.parsed_documents = read_pd

    def clean_sentence(self,sentence):
        number_removed = re.sub('[^a-zA-Z]', ' ', sentence)
        lower_case_sentence = number_removed.lower()
        stemmed_docs = self.stemmer.stem(lower_case_sentence)
        words = stemmed_docs.split()
        return words

    def clean_documents(self):
        read_cd = np.load('data/cleaned_documents.npy',allow_pickle='TRUE').item()
        self.cleaned_documents = read_cd

    def find_terms(self):
        for doc in self.cleaned_documents:
            for word in self.cleaned_documents[doc][1]:
                if word not in self.terms:
                    self.terms.append(word)

    def create_incidence_matrix(self):
        for term in self.terms:
            term_availability = []
            for doc in self.cleaned_documents:
                if term in self.cleaned_documents[doc][1]:
                    term_availability.append(1)
                else:
                    term_availability.append(0)
            self.incidence_matrix[term] = term_availability
        read_im = np.load('data/incidence_matrix.npy',allow_pickle='TRUE').item()
        self.incidence_matrix = read_im

    def infix_to_postfix(self, query):
        stack = Stack()
        output = []
        if len(query.split()) == 0:
            return None
        elif len(query.split()) == 1:
            return [query]
        else :
            for item in query.split():
                if item not in list(self.precedence.keys()):
                    output.append(item)
                elif item == '(':
                    stack.push(item)
                elif item == ')':
                    while stack.isEmpty() != True and stack.peek() != '(':
                        output.append(stack.pop())
                else:
                    while (stack.isEmpty() != True) and (self.precedence[stack.peek()] >= self.precedence[item]):
                        output.append(stack.pop())
                    stack.push(item)

            while (stack.isEmpty() != True and stack.peek() != '('):
                output.append(stack.pop())
            return output

    def invert_matrix(self,matrix):
        for i in range(len(matrix)):
            matrix[i] = 1 if not matrix[i] else 0
        return matrix

    def operate_boolean(self,val1, val2, operator):
        result_boolean = []
        for i in range(len(val1)):
            if operator == 'and':
                result_boolean.append(val1[i] and val2[i])
            elif operator == 'or':
                result_boolean.append(val1[i] or val2[i])
        return result_boolean

    def evaluate_postfix(self):
        stack = Stack()
        if self.postfix == None:
            listofones = [1] * len(self.incidence_matrix[self.terms[0]])
            return listofones
        elif len(self.postfix) > 1:
            for item in self.postfix:
                if item not in list(self.precedence.keys()) and item in self.terms:
                    stack.push(self.incidence_matrix[item])
                elif item == "not" or item == "NOT":
                    if stack.peek() in self.terms:
                        stack.push(self.invert_matrix(self.incidence_matrix[stack.pop()]))
                    else:
                        stack.push(self.invert_matrix(stack.pop()))
                else:
                    if item not in list(self.precedence.keys()) and item not in self.terms:
                        listofzeros = [0] * len(self.incidence_matrix[self.terms[0]])
                        stack.push(listofzeros)
                        continue
                    val1 = stack.pop()
                    val2 = stack.pop()
                    hasil = self.operate_boolean(val1, val2, item)
                    stack.push(hasil)
        else :
            if self.postfix[0] in self.terms:
                stack.push(self.incidence_matrix[self.postfix[0]])
        if len(stack.values()) > 0:
            result = stack.peek()
        else:
            result = []
        return result

def openfile(dir):
    f1 = open(dir, "r", encoding="latin-1")
    text = f1.read()
    f1.close()
    return text

if __name__ == "__main__": 
        app.run() 
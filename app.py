from flask import Flask, render_template, url_for, jsonify
import mysql.connector
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='1234',
        database='BLOG'
    )

def tuple_to_dict(old_tuple):
    if not old_tuple:
        return dict()

    new_dict = dict()
    for i, attr in enumerate(old_tuple):
        match i:
            case 0:
                new_dict['article-id'] = attr
            case 1:
                new_dict['article-title'] = attr
            case 2:
                new_dict['article-content'] = attr
            case 3:
                new_dict['publish-date'] = attr

    return new_dict

def tuple_to_list(old_tuple):
    articles_list = []

    for article in old_tuple:
        article_dict = {'article-id': '',
                       'article-title': '',
                       'article-content': '',
                       'publish-date': ''
                        }

        for i, attr in enumerate(article):
            match i:
                case 0:
                    article_dict['article-id'] = attr
                case 1:
                    article_dict['article-title'] = attr
                case 2:
                    article_dict['article-content'] = attr
                case 3:
                    article_dict['publish-date'] = attr

        articles_list.append(article_dict)

    return articles_list

from home import *

if __name__ == '__main__':
    app.run(debug=True)

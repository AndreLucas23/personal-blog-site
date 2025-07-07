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

from views import *

if __name__ == '__main__':
    app.run(debug=True)

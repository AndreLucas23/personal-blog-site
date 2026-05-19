from flask import Flask, render_template, url_for, jsonify
import mysql.connector
from flask_cors import CORS

import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

from home import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

from flask import Flask, jsonify
from flask_cors import CORS
import mysql.connector

import logging

from home import home_bp

app = Flask(__name__)
CORS(app)
app.register_blueprint(home_bp)

@app.errorhandler(mysql.connector.Error)
def handle_db_error(error):
    logging.error(f'Erro do banco de dados: [{error.errno}] {error.msg}')    

    return jsonify({
        'status': 'error',
        'message': 'Houve um erro interno ao processar os dados do banco'
    }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

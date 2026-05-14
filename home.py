from app import app, get_db_connection, tuple_to_dict, tuple_to_list
from flask import render_template, jsonify, Response, request, redirect, url_for

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/articles', methods=['GET'])
def get_articles():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT ARTICLE_ID, ARTICLE_TITLE, ARTICLE_CONTENT, PUBLISH_DATE \
    FROM ARTICLES')
    all_articles = cursor.fetchall()
    conn.close()

    articles_list = []

    for article in all_articles:
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


    return jsonify(articles_list)

@app.route('/articles', methods=['POST'])
def add_article():
    data = request.get_json()
    article_title = data.get('new-title')
    article_content = data.get('new-content')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO ARTICLES(ARTICLE_TITLE, ARTICLE_CONTENT) ' \
    'VALUES (%s, %s)', (article_title, article_content))
    conn.commit()
    conn.close()

    return jsonify({'message': 'artigo criado com sucesso'}), 201

@app.route('/articles/<int:remove_id>', methods=['DELETE'])
def remove_article(remove_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM ARTICLES ' \
    'WHERE ARTICLE_ID = %s', (remove_id,))
    conn.commit()
    conn.close()

    return jsonify({'message': 'artigo removido com sucesso'}), 200

@app.route('/articles/id/<int:search_id>', methods=['GET'])
def search_by_id(search_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT ARTICLE_ID, ARTICLE_TITLE, ARTICLE_CONTENT, PUBLISH_DATE ' \
    'FROM ARTICLES WHERE ARTICLE_ID LIKE %s', (f'{search_id}%',))
    search_articles = cursor.fetchall()
    conn.close()

    articles_list = tuple_to_list(search_articles)

    return jsonify(articles_list), 200

@app.route('/articles/title/<string:search_title>', methods=['GET'])
def search_by_title(search_title):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT ARTICLE_ID, ARTICLE_TITLE, ARTICLE_CONTENT, PUBLISH_DATE ' \
    'FROM ARTICLES WHERE ARTICLE_TITLE LIKE %s', (f'%{search_title}%',))
    search_articles = cursor.fetchall()
    conn.close()

    articles_list = tuple_to_list(search_articles)

    return jsonify(articles_list), 200

@app.route('/open/<int:article_id>')
def open_article(article_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT ARTICLE_ID, ARTICLE_TITLE, ARTICLE_CONTENT, PUBLISH_DATE ' \
    'FROM ARTICLES WHERE ARTICLE_ID = %s', (article_id,))
    article = cursor.fetchone()
    conn.close()

    article = tuple_to_dict(article)

    return render_template('article.html', article=article), 200

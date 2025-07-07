from app import app, get_db_connection
from flask import render_template, jsonify, Response, request, redirect, url_for

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/articles', methods=['GET'])
def get_articles():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT ARTICLE_ID, ARTICLE_TITLE, ARTICLE_CONTENT, PUBLISH_DATE, AUTHOR_ID \
    FROM ARTICLES')
    articles = cursor.fetchall()

    articlesList = []

    for article in articles:
        articleDict = {'article-id': '', 
                       'article-title': '',
                       'article-content': '',
                       'publish-date': '',
                       'author-id': ''
                        }
        i = 0

        for attr in article:
            match i:
                case 0:
                    articleDict['article-id'] = attr
                case 1:
                    articleDict['article-title'] = attr
                case 2:
                    articleDict['article-content'] = attr
                case 3:
                    articleDict['publish-date'] = attr
                case 4:
                    articleDict['author-id'] = attr

            i = i + 1

        articlesList.append(articleDict)

    conn.close()

    return jsonify(articlesList)

@app.route('/articles', methods=['POST'])
def add_article():
    data = request.get_json()
    article_title = data.get('new-title')
    article_content = data.get('new-content')
    author_id = data.get('author-id')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO ARTICLES(ARTICLE_TITLE, ARTICLE_CONTENT, AUTHOR_ID) ' \
    'VALUES (%s, %s, 1)', (article_title, article_content))
    conn.commit()
    conn.close()

    return jsonify({'message': 'artigo criado com sucesso'}), 201

@app.route('/articles/<int:remove_id>', methods=['DELETE'])
def remove_article(remove_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM ARTICLES WHERE ARTICLE_ID = %s', (remove_id,))
    conn.commit()
    conn.close()

    return jsonify({'message': 'artigo removido com sucesso'}), 200

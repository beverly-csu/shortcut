import hashlib
import re
import time
from flask_cors import CORS
import requests
from flask import Flask, jsonify, request, redirect
from flask_sqlalchemy import SQLAlchemy
import jwt
from datetime import datetime, timedelta

CODE_SUCCESS = {'code': 1000}
CODE_ERROR_VALUE = {'code': 1300}
CODE_ERROR_TOKEN = {'code': 1301}
CODE_ERROR_DATA = {'code': 1302}
CODE_DATABASE_ERROR = {'code': 1500}

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shcut.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
cors = CORS(app, resources={r"/*": {"origins": "*"}})
db = SQLAlchemy(app)
SECRET_KEY = 'test'


class Users(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(32), unique=True)
    password = db.Column(db.String(512), nullable=True)
    email = db.Column(db.String(64), unique=True)
    date_reg = db.Column(db.DateTime, default=datetime.utcnow)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    token = db.Column(db.String(512))


class Links(db.Model):
    link_id = db.Column(db.Integer, primary_key=True)
    short_url = db.Column(db.String(128), unique=True)
    full_url = db.Column(db.String(512))
    title = db.Column(db.String(64))
    date_create = db.Column(db.DateTime, default=datetime.utcnow)
    access = db.Column(db.String(32))
    secret_code = db.Column(db.String(32))
    owner = db.Column(db.String(32))


class LinksAdditional(db.Model):
    link_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Text)
    redirects = db.Column(db.Text)


def debug(message):
    print('DEBUG: ', message)


def get_user_data(login):
    if available_login(login) is False:
        user_data = Users.query.filter_by(login=login).first()
        user_links = Links.query.filter_by(owner=login).all()
        count, redirects = len(user_links), 0
        return {
            'code': 1000,
            'profile': {
                'login': login,
                'email': user_data.email,
                'date_reg': user_data.date_reg,
                'first_name': user_data.first_name,
                'last_name': user_data.last_name
            },
            'week_graphic': 'nothing',
            'links_count': count,
            'links_redirects': redirects
        }
    else:
        return CODE_ERROR_VALUE


def available_short(url):
    try:
        status = Links.query.filter_by(short_url=url).all()
        if len(status) == 0:
            return True
        else:
            return False
    except Exception as error:
        debug(error)
        return False


def available_login(login):
    try:
        status = Users.query.filter_by(login=login).all()
        if len(status) == 0:
            return True
        else:
            return False
    except Exception as error:
        debug(error)
        return False


def available_email(email):
    try:
        status = Users.query.filter_by(email=email).all()
        if len(status) == 0:
            return True
        else:
            return False
    except Exception as error:
        debug(error)
        return False


def get_user(login):
    try:
        user_data = Users.query.filter_by(login=login).first()
        user_data = dict(
            code=1000,
            login=user_data.login,
            email=user_data.email,
            password=user_data.password
        )
        return user_data
    except Exception as error:
        debug(error)
        return CODE_DATABASE_ERROR


def create_user(data):
    try:
        if available_login(data['login']) and available_email(data['email']):
            user_instance = Users(login=data['login'], password=data['password'], email=data['email'],
                                  first_name=data['first_name'], last_name=data['last_name'])
            db.session.add(user_instance)
            db.session.commit()
            return {'code': 1000}
        else:
            return CODE_ERROR_VALUE
    except Exception as error:
        debug(error)
        db.session.rollback()
        return {'code': 1500}


def update_user(login, data):
    try:
        if available_login(login) is False:
            Users.query.filter_by(login=login).update(
                dict(password=data['password'], first_name=data['first_name'], last_name=data['last_name']))
            db.session.commit()
            return {'code': 1000}
        else:
            return CODE_ERROR_VALUE
    except Exception as error:
        debug(error)
        db.session.rollback()
        return {'code': 1500}


def delete_user(login):
    try:
        if available_login(login) is False:
            Users.query.filter_by(login=login).delete()
            db.session.commit()
            return {'code': 1000}
        else:
            return CODE_ERROR_VALUE
    except Exception as error:
        debug(error)
        db.session.rollback()
        return {'code': 1500}


def auth_user(data):
    try:
        res = get_user(data['login'])
        if res['code'] == 1000:
            if res['password'] == data['password']:
                token = jwt.encode({'login': data['login']}, SECRET_KEY, algorithm='HS256')
                return {'code': 1000, 'token': token}
            else:
                return CODE_ERROR_DATA
        else:
            return CODE_ERROR_DATA
    except Exception as error:
        debug(error)
        return CODE_DATABASE_ERROR


def check_token(token):
    try:
        token = token.split()[1]
        token_data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {'code': 1000, 'login': token_data['login']}
    except Exception:
        return {'code': 1301}


def check_available(data, keys):
    if data is not None:
        for key in keys:
            if key not in data:
                return False
        return True
    else:
        return False


def link_validator(url):
    if url.startswith(('https://', 'http://')):
        return url
    else:
        return 'http://' + url


def get_week():
    date_format = '%d %B %Y'
    today = datetime.now()
    week = [today.strftime(date_format), (today - timedelta(days=1)).strftime(date_format),
            (today - timedelta(days=2)).strftime(date_format), (today - timedelta(days=3)).strftime(date_format),
            (today - timedelta(days=4)).strftime(date_format), (today - timedelta(days=5)).strftime(date_format),
            (today - timedelta(days=6)).strftime(date_format)]
    return list(reversed(week))


def get_today():
    date_format = '%d %B %Y'
    today = datetime.now().strftime(date_format)
    return today


def get_link(url):
    if available_short(url) is False:
        link_data = Links.query.filter_by(short_url=url).first()
        return {
            'code': 1000,
            'short_url': link_data.short_url,
            'full_url': link_data.full_url,
            'title': link_data.title,
            'date_create': time.strftime('%d %B %Y %H:%M', datetime.timetuple(link_data.date_create)),
            'access': link_data.access,
            'secret_code': link_data.secret_code,
            'owner': link_data.owner,
        }
    else:
        return CODE_ERROR_VALUE


def get_link_info(full_url, login):
    match = re.search('<title>(.*?)</title>', requests.get(full_url).text)
    title = match.group(1) if match else 'Заголовок отсутствует'
    hash_len = 8
    while True:
        short_url = hashlib.sha1(str(login + full_url).encode("UTF-8"))
        short_url = short_url.hexdigest()
        short_url = short_url[:hash_len]
        link_data = get_link(short_url)
        if link_data['code'] == 1000 and link_data['owner'] != login:
            hash_len += 1
        elif link_data['code'] == 1000 and link_data['owner'] == login:
            return CODE_ERROR_VALUE
        else:
            return {
                'code': 1000,
                'title': title,
                'short_url': short_url,
                'full_url': full_url,
            }


def create_link(data, login):
    data['full_url'] = link_validator(data['full_url'])
    redirects = [0, 0, 0, 0, 0, 0, 0]
    try:
        link_data = Links(short_url=data['short_url'], full_url=data['full_url'], title=data['title'],
                          access=data['access'], owner=login, secret_code=data['secret_code'])
        link_additional = LinksAdditional(date=str(get_week()), redirects=str(redirects))
        db.session.add(link_data)
        db.session.add(link_additional)
        db.session.commit()
        return CODE_SUCCESS
    except Exception as error:
        db.session.rollback()
        print('DEBUG:', error)
        return CODE_DATABASE_ERROR


@app.route('/user', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def user():
    token_data = check_token(request.headers.get('Authorization'))
    data = request.json
    if request.method == 'POST':
        if check_available(data, ['login', 'password']):
            print(auth_user(data))
            return jsonify(auth_user(data))
        else:
            return jsonify(CODE_ERROR_DATA)
    if token_data['code'] == 1000:
        if request.method == 'GET':
            return jsonify(get_user_data(token_data['login']))
        elif request.method == 'PATCH':
            if check_available(data, ['password', 'first_name', 'last_name']):
                return jsonify(update_user(token_data['login'], data))
            else:
                return jsonify(CODE_ERROR_DATA)
        elif request.method == 'DELETE':
            return jsonify(delete_user(token_data['login']))


@app.route('/reg', methods=['POST'])
def user_reg():
    if request.method == 'POST':
        data = request.json
        if check_available(data, ['login', 'password', 'email', 'first_name', 'last_name']):
            return jsonify(create_user(data))
        else:
            return jsonify(CODE_ERROR_DATA)


@app.route('/link', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def link():
    token_data = check_token(request.headers.get('Authorization'))
    if token_data['code'] == 1000:
        if request.method == 'GET':
            pass
        elif request.method == 'POST':
            data = request.json
            if check_available(data, ['full_url', 'short_url', 'title', 'access', 'secret_code']):
                return jsonify(create_link(data, token_data['login']))
            else:
                return jsonify(CODE_ERROR_DATA)
        elif request.method == 'PATCH':
            pass
        elif request.method == 'DELETE':
            pass


@app.route('/link_info', methods=['POST'])
def link_info():
    token_data = check_token(request.headers.get('Authorization'))
    if token_data['code'] == 1000:
        if request.method == 'POST':
            data = request.json
            if check_available(data, ['full_url']):
                return jsonify(get_link_info(data['full_url'], token_data['login']))
            else:
                return jsonify(CODE_ERROR_DATA)
    else:
        return jsonify(CODE_ERROR_TOKEN)


@app.route('/available', methods=['POST'])
def available():
    if request.method == 'POST':
        data = request.json
        if check_available(data, ['email']):
            if available_email(data['email']):
                return CODE_SUCCESS
            else:
                return CODE_ERROR_VALUE
        elif check_available(data, ['login']):
            if available_login(data['login']):
                return CODE_SUCCESS
            else:
                return CODE_ERROR_VALUE


@app.route('/<short_url>')
def user_redirect(short_url):
    if request.method == 'GET':
        link_data = get_link(short_url)
        if link_data['code'] == 1000:
            if link_data['access'] == 'public':
                return redirect(link_data['full_url'])
            elif link_data['access'] == 'authorized':
                token_data = check_token(request.headers.get('Authorization'))
                if token_data['code'] == 1000:
                    return redirect(link_data['full_url'])
                else:
                    return 'You dont have access for this link. Please login.'
            elif link_data['access'] == 'code':
                pass
        else:
            return 'Sorry, We didnt find this link.'


if __name__ == '__main__':
    app.run()
